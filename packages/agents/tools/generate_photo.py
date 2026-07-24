"""Генерация фотореалистичных изображений через Flux 2.0-pro."""
import os, json, time, base64, httpx
from pydantic import BaseModel, Field
from packages.shared.config import settings

PHOTO_MODEL = os.getenv("PHOTO_MODEL", "black-forest-labs/flux.2-pro")
SAVE_DIR = "/app/workspace/generated"


class GeneratePhotoSchema(BaseModel):
    prompt: str = Field(description="Детальное описание сцены на английском (свет, ракурс, стиль камеры)")


async def generate_photo(prompt: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{settings.LLM_API_BASE}/images/generations",
                headers={"Authorization": f"Bearer {settings.LLM_API_KEY}", "Content-Type": "application/json"},
                json={"model": PHOTO_MODEL, "prompt": prompt, "n": 1},
            )
            if response.status_code != 200:
                return json.dumps({"error": f"API error {response.status_code}: {response.text[:200]}"}, ensure_ascii=False)
            data = response.json()
            images = data.get("data", [])
            if not images:
                return "Изображение не сгенерировано."
            b64_json = images[0].get("b64_json", "")
            if not b64_json:
                return "Пустой ответ от API."
            os.makedirs(SAVE_DIR, exist_ok=True)
            filename = f"photo_{int(time.time())}_{os.getpid()}.png"
            filepath = os.path.join(SAVE_DIR, filename)
            with open(filepath, "wb") as f:
                f.write(base64.b64decode(b64_json))
            return json.dumps({
                "status": "success",
                "local_path": filepath,
                "public_url": f"/static/generated/{filename}",
                "format": "png",
                "model": PHOTO_MODEL,
            }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"{type(e).__name__}: {str(e)[:200]}"}, ensure_ascii=False)
