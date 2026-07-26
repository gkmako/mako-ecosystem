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
    format: str = "svg"


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
        w, h = sizes["A1"]
    else:
        w, h = sizes[format_name]
    if orientation == "Landscape":
        w, h = h, w
    return w, h


def _write_puppeteer_config(path: str, width_mm: float, height_mm: float) -> None:
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
        "format": "Custom",
        "width": f"{int(width_mm)}mm",
        "height": f"{int(height_mm)}mm",
        "printBackground": True,
        "preferCSSPageSize": False,
        "margin": {
            "top": "10mm",
            "right": "10mm",
            "bottom": "10mm",
            "left": "10mm",
        },
    }
    with open(path, "w") as f:
        json.dump(cfg, f, indent=2)


def _write_mermaid_config(path: str, user_config: dict, use_elk: bool) -> None:
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
    vb = re.search(r'viewBox\s*=\s*["\']([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)["\']', svg_text)
    if vb:
        return float(vb.group(3)), float(vb.group(4))
    w = re.search(r'<svg[^>]*\bwidth\s*=\s*["\']([\d.]+)', svg_text)
    h = re.search(r'<svg[^>]*\bheight\s*=\s*["\']([\d.]+)', svg_text)
    if w and h:
        return float(w.group(1)), float(h.group(1))
    return 800.0, 600.0


def _ensure_svg_has_dimensions(svg_text: str) -> str:
    if 'width="' not in svg_text or 'height="' not in svg_text:
        vb = re.search(r'viewBox\s*=\s*["\']([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)["\']', svg_text)
        if vb:
            w, h = vb.group(3), vb.group(4)
            svg_text = re.sub(
                r'<svg([^>]*)>',
                f'<svg\\1 width="{w}" height="{h}">',
                svg_text,
                count=1
            )
    return svg_text


def _cleanup(*files: str | None) -> None:
    for f in files:
        if f and os.path.exists(f):
            try:
                os.unlink(f)
            except OSError:
                pass


async def _render_pdf_with_playwright(
    svg_content: str,
    sheet_w_mm: float,
    sheet_h_mm: float,
    margin_mm: float,
    fit_to_page: bool,
) -> bytes:
    """Рендерит SVG в PDF через Playwright + системный chromium.
    
    Playwright = тот же браузер → рендерит foreignObject корректно.
    """
    from playwright.async_api import async_playwright

    if fit_to_page:
        svg_style = "max-width: 100%; max-height: 100%; width: auto; height: auto;"
    else:
        svg_style = "width: auto; height: auto;"

    html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@page {{
    size: {sheet_w_mm}mm {sheet_h_mm}mm;
    margin: {margin_mm}mm;
}}
html, body {{
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    background: white;
    display: flex;
    align-items: center;
    justify-content: center;
}}
svg {{
    {svg_style}
    display: block;
}}
</style>
</head>
<body>
{svg_content}
</body>
</html>"""

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path="/usr/bin/chromium",
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions",
                "--no-first-run",
            ],
            headless=True,
        )
        try:
            page = await browser.new_page()
            await page.set_content(html_content, wait_until="networkidle")
            pdf_bytes = await page.pdf(
                width=f"{int(sheet_w_mm)}mm",
                height=f"{int(sheet_h_mm)}mm",
                margin={
                    "top": f"{int(margin_mm)}mm",
                    "right": f"{int(margin_mm)}mm",
                    "bottom": f"{int(margin_mm)}mm",
                    "left": f"{int(margin_mm)}mm",
                },
                print_background=True,
                prefer_css_page_size=False,
            )
            return pdf_bytes
        finally:
            await browser.close()


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

        _write_mermaid_config(config_file, request.config, use_elk=True)
        _write_puppeteer_config(puppeteer_file, 594, 841)

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
    """Legacy endpoint. Renders PDF with A1 sheet using Playwright."""
    files_to_cleanup = []
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False) as f:
            f.write(request.code)
            input_file = f.name
        files_to_cleanup.append(input_file)

        use_elk = request.config.get("layout") == "elk"
        config_file = input_file.replace(".mmd", ".config.json")
        files_to_cleanup.append(config_file)
        _write_mermaid_config(config_file, request.config, use_elk=use_elk)

        puppeteer_file = input_file.replace(".mmd", ".pup.json")
        files_to_cleanup.append(puppeteer_file)
        _write_puppeteer_config(puppeteer_file, 594, 841)

        svg_file = input_file.replace(".mmd", ".svg")
        files_to_cleanup.append(svg_file)

        await _run_mmdc([
            "mmdc", "-i", input_file, "-o", svg_file,
            "-c", config_file, "-p", puppeteer_file, "--quiet",
        ])

        with open(svg_file, "r", encoding="utf-8") as f:
            svg_content = f.read()

        svg_content = _ensure_svg_has_dimensions(svg_content)

        # Playwright генерирует PDF с точным размером A1
        pdf_bytes = await _render_pdf_with_playwright(
            svg_content=svg_content,
            sheet_w_mm=594,
            sheet_h_mm=841,
            margin_mm=10,
            fit_to_page=True,
        )

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
    """Advanced PDF export with user-defined parameters using Playwright."""
    files_to_cleanup = []
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False) as f:
            f.write(request.code)
            input_file = f.name
        files_to_cleanup.append(input_file)

        format_name = request.pdf_options.format if request.pdf_options else "A4"
        orientation = request.pdf_options.orientation if request.pdf_options else "Portrait"
        margin_mm = request.pdf_options.margin_mm if request.pdf_options else 10.0
        fit_mode = request.pdf_options.fit_mode if request.pdf_options else "fit_to_page"

        sheet_w_mm, sheet_h_mm = _get_sheet_size_mm(format_name, orientation)
        use_elk = request.config.get("layout") == "elk"

        config_file = input_file.replace(".mmd", ".config.json")
        files_to_cleanup.append(config_file)
        _write_mermaid_config(config_file, request.config, use_elk=use_elk)

        puppeteer_file = input_file.replace(".mmd", ".pup.json")
        files_to_cleanup.append(puppeteer_file)
        _write_puppeteer_config(puppeteer_file, 594, 841)

        svg_file = input_file.replace(".mmd", ".svg")
        files_to_cleanup.append(svg_file)

        await _run_mmdc([
            "mmdc", "-i", input_file, "-o", svg_file,
            "-c", config_file, "-p", puppeteer_file, "--quiet",
        ])

        with open(svg_file, "r", encoding="utf-8") as f:
            svg_content = f.read()

        svg_content = _ensure_svg_has_dimensions(svg_content)

        pdf_bytes = await _render_pdf_with_playwright(
            svg_content=svg_content,
            sheet_w_mm=sheet_w_mm,
            sheet_h_mm=sheet_h_mm,
            margin_mm=margin_mm,
            fit_to_page=(fit_mode == "fit_to_page"),
        )

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
    result = {"status": "ok"}

    try:
        proc = await asyncio.create_subprocess_exec(
            "mmdc", "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
        result["mmdc_version"] = stdout.decode().strip()
    except Exception as e:
        result["mmdc_error"] = str(e)

    try:
        from playwright.async_api import async_playwright
        result["playwright"] = "ok"
    except Exception as e:
        result["playwright_error"] = str(e)

    try:
        if os.path.exists("/usr/bin/chromium"):
            result["chromium"] = "/usr/bin/chromium"
        else:
            result["chromium_error"] = "not found"
    except Exception as e:
        result["chromium_error"] = str(e)

    return result