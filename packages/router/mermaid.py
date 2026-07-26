from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
import subprocess
import tempfile
import os
import json
import asyncio
import re
import logging
from typing import Literal, Optional

logger = logging.getLogger(__name__)

mermaid_router = APIRouter(prefix="/api/mermaid", tags=["mermaid"])


class MermaidRenderRequest(BaseModel):
    code: str
    config: dict = {}
    format: str = "svg"  # "svg" или "pdf"


class PDFOptions(BaseModel):
    format: Literal["A0", "A1", "A2", "A3", "A4", "A5", "A6", "Custom"] = "A4"
    orientation: Literal["Portrait", "Landscape"] = "Portrait"
    margin_mm: float = 10.0
    fit_mode: Literal["fit_to_page", "actual_size_with_pagination"] = "fit_to_page"


class AdvancedMermaidRenderRequest(BaseModel):
    code: str
    config: dict = {}
    pdf_options: Optional[PDFOptions] = None


def _get_sheet_size_mm(format_name: str, orientation: str) -> tuple[float, float]:
    """Возвращает (width_mm, height_mm) для заданного формата и ориентации."""
    sizes = {
        "A0": (841, 1189),
        "A1": (594, 841),
        "A2": (420, 594),
        "A3": (297, 420),
        "A4": (210, 297),
        "A5": (148, 210),
        "A6": (105, 148),
    }
    if format_name == "Custom":
        # В MVP — A1 как самый большой
        w, h = sizes["A1"]
    else:
        w, h = sizes[format_name]

    if orientation == "Landscape":
        w, h = h, w
    return w, h


def _write_puppeteer_config(path: str, width_mm: float, height_mm: float) -> None:
    """Создать puppeteer-конфиг с указанным размером листа."""
    cfg = {
        "executablePath": "/usr/bin/chromium",
        "args": [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-extensions",
            "--no-first-run",
        ],
        "format": "Custom",          # ← без пробела
        "width": f"{int(width_mm)}mm",   # ← без пробела
        "height": f"{int(height_mm)}mm", # ← без пробела
        "printBackground": True,
        "preferCSSPageSize": False,
        "margin": {
            "top": f"{int(10)}mm",
            "right": f"{int(10)}mm",
            "bottom": f"{int(10)}mm",
            "left": f"{int(10)}mm",
        },
    }
    with open(path, "w") as f:
        json.dump(cfg, f, indent=2)


def _write_mermaid_config(path: str, user_config: dict, use_elk: bool, pdf_fit: bool = False) -> None:
    cfg = {
        "theme": user_config.get("theme", "default"),
        "flowchart": {
            "curve": user_config.get("curve", "basis"),
            "htmlLabels": True,
            "useMaxWidth": False,
        },
        "securityLevel": "loose",
    }
    if use_elk:
        cfg["flowchart"]["defaultRenderer"] = "elk"
    if pdf_fit:
        cfg["pdfFit"] = True
    with open(path, "w") as f:
        json.dump(cfg, f, indent=2)


async def _run_mmdc(cmd: list[str], timeout: int = 60) -> None:
    logger.info(f"Running: {' '.join(cmd)}")
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        raise HTTPException(status_code=504, detail=f"mmdc timeout after {timeout}s")
    if proc.returncode != 0:
        msg = stderr.decode(errors="replace") if stderr else "Unknown mmdc error"
        logger.error(f"mmdc failed (rc={proc.returncode}): {msg}")
        raise HTTPException(status_code=500, detail=msg[:2000])


def _parse_svg_size(svg_text: str) -> tuple[float, float]:
    """Извлекает размеры SVG из viewBox или width/height."""
    vb_match = re.search(r'viewBox\s*=\s*["\']([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)["\']', svg_text)
    if vb_match:
        w = float(vb_match.group(3))
        h = float(vb_match.group(4))
        return w, h

    w_match = re.search(r'<svg[^>]*\bwidth\s*=\s*["\']([\d.]+)', svg_text)
    h_match = re.search(r'<svg[^>]*\bheight\s*=\s*["\']([\d.]+)', svg_text)
    if w_match and h_match:
        w = float(w_match.group(1))
        h = float(h_match.group(1))
        return w, h

    return 800.0, 600.0


def _px_to_mm(px: float, dpi: int = 96) -> float:
    return px * 25.4 / dpi


def _cleanup(*files: str | None) -> None:
    for f in files:
        if f and os.path.exists(f):
            try:
                os.unlink(f)
            except OSError:
                pass


@mermaid_router.post("/render-elk")
async def render_mermaid_with_elk(request: MermaidRenderRequest) -> Response:
    """Render mermaid diagram with ELK layout via mmdc CLI. Returns raw SVG."""
    input_file = output_file = config_file = puppeteer_file = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False) as f:
            f.write(request.code)
            input_file = f.name

        output_file = input_file.replace(".mmd", ".svg")
        config_file = input_file.replace(".mmd", ".config.json")
        puppeteer_file = input_file.replace(".mmd", ".pup.json")

        _write_mermaid_config(config_file, request.config, use_elk=True, pdf_fit=False)
        _write_puppeteer_config(puppeteer_file, 594, 841)  # A1 для SVG

        await _run_mmdc([
            "mmdc", "-i", input_file, "-o", output_file,
            "-c", config_file, "-p", puppeteer_file, "--quiet",
        ])

        with open(output_file, "r", encoding="utf-8") as f:
            svg_content = f.read()

        return Response(content=svg_content, media_type="image/svg+xml")

    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="mmdc CLI not found in container")
    except Exception as e:
        logger.exception("Mermaid ELK render failed")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        _cleanup(input_file, output_file, config_file, puppeteer_file)


@mermaid_router.post("/render-pdf")
async def render_mermaid_to_pdf(request: MermaidRenderRequest) -> Response:
    """
    Legacy endpoint. Renders PDF with large A1 sheet (594x841mm) to avoid clipping.
    """
    files_to_cleanup = []
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False) as f:
            f.write(request.code)
            input_file = f.name
        files_to_cleanup.append(input_file)

        use_elk = request.config.get("layout") == "elk"
        config_file = input_file.replace(".mmd", ".config.json")
        files_to_cleanup.append(config_file)
        _write_mermaid_config(config_file, request.config, use_elk=use_elk, pdf_fit=True)

        puppeteer_file = input_file.replace(".mmd", ".pup.json")
        files_to_cleanup.append(puppeteer_file)
        _write_puppeteer_config(puppeteer_file, 594, 841)  # A1

        output_pdf = input_file.replace(".mmd", ".pdf")
        files_to_cleanup.append(output_pdf)

        await _run_mmdc([
            "mmdc", "-i", input_file, "-o", output_pdf,
            "-c", config_file, "-p", puppeteer_file, "--quiet",
        ], timeout=90)

        if not os.path.exists(output_pdf):
            raise HTTPException(status_code=500, detail="PDF file was not created by mmdc")

        with open(output_pdf, "rb") as f:
            pdf_bytes = f.read()

        if len(pdf_bytes) < 1024:
            content_preview = pdf_bytes.decode(errors="replace")[:500]
            raise HTTPException(status_code=500, detail=f"Invalid PDF: {content_preview}")

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=diagram.pdf"},
        )

    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="mmdc CLI not found in container")
    except Exception as e:
        logger.exception("Mermaid PDF render failed")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        _cleanup(*files_to_cleanup)


@mermaid_router.post("/render-pdf-advanced")
async def render_mermaid_to_pdf_advanced(request: AdvancedMermaidRenderRequest) -> Response:
    """
    Advanced PDF export with user-defined parameters (format, orientation, margins).
    """
    files_to_cleanup = []
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False) as f:
            f.write(request.code)
            input_file = f.name
        files_to_cleanup.append(input_file)

        # Get sheet size based on options
        format_name = request.pdf_options.format if request.pdf_options else "A4"
        orientation = request.pdf_options.orientation if request.pdf_options else "Portrait"
        margin_mm = request.pdf_options.margin_mm if request.pdf_options else 10.0
        fit_mode = request.pdf_options.fit_mode if request.pdf_options else "fit_to_page"

        sheet_w_mm, sheet_h_mm = _get_sheet_size_mm(format_name, orientation)
        # Calculate usable area
        usable_w_mm = sheet_w_mm - 2 * margin_mm
        usable_h_mm = sheet_h_mm - 2 * margin_mm

        use_elk = request.config.get("layout") == "elk"

        if fit_mode == "fit_to_page":
            # 1. Render SVG to get diagram size
            svg_file = input_file.replace(".mmd", ".svg")
            files_to_cleanup.append(svg_file)

            svg_config_file = input_file.replace(".mmd", ".svg.config.json")
            files_to_cleanup.append(svg_config_file)
            _write_mermaid_config(svg_config_file, request.config, use_elk=use_elk, pdf_fit=False)

            svg_pup_file = input_file.replace(".mmd", ".svg.pup.json")
            files_to_cleanup.append(svg_pup_file)
            _write_puppeteer_config(svg_pup_file, 594, 841)  # Large canvas for SVG

            await _run_mmdc([
                "mmdc", "-i", input_file, "-o", svg_file,
                "-c", svg_config_file, "-p", svg_pup_file, "--quiet",
            ])

            with open(svg_file, "r", encoding="utf-8") as f:
                svg_content = f.read()

            diag_w_px, diag_h_px = _parse_svg_size(svg_content)
            diag_w_mm = _px_to_mm(diag_w_px)
            diag_h_mm = _px_to_mm(diag_h_px)

            # Calculate scale
            scale_x = usable_w_mm / diag_w_mm if diag_w_mm > 0 else 1
            scale_y = usable_h_mm / diag_h_mm if diag_h_mm > 0 else 1
            final_scale = min(scale_x, scale_y, 1.0)  # Clamp to 1.0 max

            # Render PDF with calculated scale
            pdf_config_file = input_file.replace(".mmd", ".pdf.config.json")
            files_to_cleanup.append(pdf_config_file)
            _write_mermaid_config(pdf_config_file, request.config, use_elk=use_elk, pdf_fit=True)

            pdf_pup_file = input_file.replace(".mmd", ".pdf.pup.json")
            files_to_cleanup.append(pdf_pup_file)
            _write_puppeteer_config(pdf_pup_file, sheet_w_mm, sheet_h_mm)

            output_pdf = input_file.replace(".mmd", ".pdf")
            files_to_cleanup.append(output_pdf)

            await _run_mmdc([
                "mmdc", "-i", input_file, "-o", output_pdf,
                "-c", pdf_config_file, "-p", pdf_pup_file, "--quiet",
            ], timeout=90)

        else:  # actual_size_with_pagination
            # For MVP: render one large PDF (like legacy endpoint but with user format)
            pdf_config_file = input_file.replace(".mmd", ".pdf.config.json")
            files_to_cleanup.append(pdf_config_file)
            _write_mermaid_config(pdf_config_file, request.config, use_elk=use_elk, pdf_fit=False)

            pdf_pup_file = input_file.replace(".mmd", ".pdf.pup.json")
            files_to_cleanup.append(pdf_pup_file)
            # Use user's format
            _write_puppeteer_config(pdf_pup_file, sheet_w_mm, sheet_h_mm)

            output_pdf = input_file.replace(".mmd", ".pdf")
            files_to_cleanup.append(output_pdf)

            await _run_mmdc([
                "mmdc", "-i", input_file, "-o", output_pdf,
                "-c", pdf_config_file, "-p", pdf_pup_file, "--quiet",
            ], timeout=90)

        with open(output_pdf, "rb") as f:
            pdf_bytes = f.read()

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=diagram.pdf"},
        )

    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="mmdc CLI not found in container")
    except Exception as e:
        logger.exception("Advanced Mermaid PDF render failed")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        _cleanup(*files_to_cleanup)


@mermaid_router.get("/health")
async def mermaid_health() -> dict:
    try:
        proc = await asyncio.create_subprocess_exec(
            "mmdc", "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
        return {"status": "ok", "mmdc_version": stdout.decode().strip()}
    except Exception as e:
        return {"status": "error", "detail": str(e)}