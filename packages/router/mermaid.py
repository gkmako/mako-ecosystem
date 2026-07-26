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
        w, h = sizes["A1"]
    else:
        w, h = sizes[format_name]

    if orientation == "Landscape":
        w, h = h, w
    return w, h


def _write_puppeteer_config(path: str, width_mm: float, height_mm: float) -> None:
    """Создать puppeteer-конфиг для mmdc (используется только для SVG)."""
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
    """Создать mermaid-конфиг для mmdc."""
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
    """Запустить mmdc CLI."""
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


def _ensure_svg_has_dimensions(svg_text: str) -> str:
    """Добавить явные width/height в SVG и исправить шрифты для WeasyPrint."""
    # 1. Добавить width/height если их нет
    if 'width="' not in svg_text or 'height="' not in svg_text:
        vb_match = re.search(r'viewBox\s*=\s*["\']([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)["\']', svg_text)
        if vb_match:
            w = vb_match.group(3)
            h = vb_match.group(4)
            svg_text = re.sub(
                r'<svg([^>]*)>',
                f'<svg\\1 width="{w}" height="{h}">',
                svg_text,
                count=1
            )
    
    # 2. Заменить шрифты Mermaid на системные (Liberation Sans = Arial-подобный)
    svg_text = svg_text.replace('"trebuchet ms"', '"Liberation Sans"')
    svg_text = svg_text.replace('trebuchet ms', 'Liberation Sans')
    svg_text = svg_text.replace('verdana', 'sans-serif')
    
    return svg_text


def _cleanup(*files: str | None) -> None:
    """Удалить временные файлы."""
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
    """
    Legacy endpoint. Renders PDF with A1 format using WeasyPrint.
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

        # Обеспечиваем наличие width/height и исправляем шрифты
        svg_content = _ensure_svg_has_dimensions(svg_content)

        # Используем WeasyPrint для конвертации SVG → PDF
        from weasyprint import HTML
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@page {{
    size: 594mm 841mm;
    margin: 10mm;
}}
body {{
    margin: 0;
    padding: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: "Liberation Sans", "DejaVu Sans", Arial, sans-serif;
}}
svg {{
    max-width: 100%;
    max-height: 100%;
    width: auto;
    height: auto;
    font-family: "Liberation Sans", "DejaVu Sans", Arial, sans-serif !important;
}}
svg text, svg tspan, svg foreignObject {{
    font-family: "Liberation Sans", "DejaVu Sans", Arial, sans-serif !important;
}}
svg foreignObject div, svg foreignObject span, svg foreignObject p {{
    font-family: "Liberation Sans", "DejaVu Sans", Arial, sans-serif !important;
    margin: 0;
    padding: 0;
}}
</style>
</head>
<body>
{svg_content}
</body>
</html>"""

        pdf_bytes = HTML(string=html_content).write_pdf()

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
    Advanced PDF export with user-defined parameters using WeasyPrint.
    """
    files_to_cleanup = []
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False) as f:
            f.write(request.code)
            input_file = f.name
        files_to_cleanup.append(input_file)

        # Получаем параметры из модального окна
        format_name = request.pdf_options.format if request.pdf_options else "A4"
        orientation = request.pdf_options.orientation if request.pdf_options else "Portrait"
        margin_mm = request.pdf_options.margin_mm if request.pdf_options else 10.0
        fit_mode = request.pdf_options.fit_mode if request.pdf_options else "fit_to_page"

        sheet_w_mm, sheet_h_mm = _get_sheet_size_mm(format_name, orientation)
        use_elk = request.config.get("layout") == "elk"

        # 1. Рендерим SVG через mmdc
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

        # 2. Обеспечиваем наличие width/height и исправляем шрифты
        svg_content = _ensure_svg_has_dimensions(svg_content)

        # 3. Определяем режим масштабирования
        if fit_mode == "fit_to_page":
            svg_style = "max-width: 100%; max-height: 100%; width: auto; height: auto;"
        else:  # actual_size_with_pagination
            # Для MVP: один большой лист, если не влезает — всё равно масштабируем
            svg_style = "max-width: 100%; max-height: 100%; width: auto; height: auto;"

        # 4. Оборачиваем SVG в HTML с CSS @page и шрифтами
        from weasyprint import HTML

        html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@page {{
    size: {sheet_w_mm}mm {sheet_h_mm}mm;
    margin: {margin_mm}mm;
}}
body {{
    margin: 0;
    padding: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: "Liberation Sans", "DejaVu Sans", Arial, sans-serif;
}}
svg {{
    {svg_style}
    font-family: "Liberation Sans", "DejaVu Sans", Arial, sans-serif !important;
}}
svg text, svg tspan, svg foreignObject {{
    font-family: "Liberation Sans", "DejaVu Sans", Arial, sans-serif !important;
}}
svg foreignObject div, svg foreignObject span, svg foreignObject p {{
    font-family: "Liberation Sans", "DejaVu Sans", Arial, sans-serif !important;
    margin: 0;
    padding: 0;
}}
</style>
</head>
<body>
{svg_content}
</body>
</html>"""

        # 5. Конвертируем HTML → PDF через WeasyPrint
        pdf_bytes = HTML(string=html_content).write_pdf()

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
    """Проверить доступность mmdc CLI и WeasyPrint."""
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
        from weasyprint import HTML
        result["weasyprint"] = "ok"
    except Exception as e:
        result["weasyprint_error"] = str(e)

    return result