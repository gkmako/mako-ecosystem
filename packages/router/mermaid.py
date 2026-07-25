from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import subprocess
import tempfile
import os
import json
import asyncio

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
        
        # mmdc CLI
        proc = await asyncio.create_subprocess_exec(
            'mmdc',
            '-i', input_file,
            '-o', output_file,
            '-c', config_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        
        # Cleanup input/config
        for f in (input_file, config_file):
            if os.path.exists(f):
                os.unlink(f)
        
        if proc.returncode != 0:
            raise HTTPException(status_code=500, detail=stderr.decode())
        
        with open(output_file, 'r') as f:
            svg_content = f.read()
        os.unlink(output_file)
        
        return svg_content
        
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Rendering timeout")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="mmdc CLI not found. Install: npm install -g @mermaid-js/mermaid-cli")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))