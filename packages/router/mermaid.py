from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import subprocess
import tempfile
import os
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

mermaid_router = APIRouter(prefix="/api/mermaid", tags=["mermaid"])

class MermaidRenderRequest(BaseModel):
    code: str
    config: dict = {}

@mermaid_router.post("/render-elk")
async def render_mermaid_with_elk(request: MermaidRenderRequest):
    """Render mermaid diagram with ELK layout using mmdc CLI"""
    try:
        # Временный файл с кодом
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False) as f:
            f.write(request.code)
            input_file = f.name
        
        output_file = input_file.replace('.mmd', '.svg')
        
        # Конфиг для ELK
        elk_config = {
            "theme": request.config.get("theme", "default"),
            "flowchart": {
                "curve": request.config.get("curve", "basis"),
                "htmlLabels": True,
                "useMaxWidth": True,
            },
        }
        
        config_file = input_file.replace('.mmd', '.json')
        with open(config_file, 'w') as f:
            json.dump(elk_config, f)
        
        # Puppeteer config для chromium
        puppeteer_config = {
            "executablePath": "/usr/bin/chromium",
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu"
            ]
        }
        puppeteer_file = input_file.replace('.mmd', '.puppeteer.json')
        with open(puppeteer_file, 'w') as f:
            json.dump(puppeteer_config, f)
        
        # mmdc CLI
        proc = await asyncio.create_subprocess_exec(
            'mmdc',
            '-i', input_file,
            '-o', output_file,
            '-c', config_file,
            '-p', puppeteer_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        
        # Cleanup
        for f in (input_file, config_file, puppeteer_file):
            if os.path.exists(f):
                os.unlink(f)
        
        if proc.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            logger.error(f"mmdc failed: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        
        with open(output_file, 'r') as f:
            svg_content = f.read()
        os.unlink(output_file)
        
        return svg_content
        
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Rendering timeout")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="mmdc CLI not found")
    except Exception as e:
        logger.error(f"Mermaid render error: {e}")
        raise HTTPException(status_code=500, detail=str(e))