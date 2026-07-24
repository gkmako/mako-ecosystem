"""Генерация изображений через Recraft v4.1-pro."""
import os
import json
import time
import base64
import httpx
from pydantic import BaseModel, Field
from packages.shared.config import settings

IMAGE_MODEL = os.getenv("IMAGE_MODEL", "recraft/recraft-v4.1-pro")
SAVE_DIR = "/app/workspace/generated"


class GenerateImageSchema(BaseModel):
    prompt: str = Field(description="Детальное описание изображения на английском")
    style: str = Field(default="general", description="Стиль: general | realistic | digital_illustration | icon | logo")


async def generate_image(prompt: str, style: str = "general") -> str:
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.LLM_API_BASE}/images/generations",
                headers={
                    "Authorization": f"Bearer {settings.LLM_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={"model": IMAGE_MODEL, "prompt": prompt, "style": style, "n": 1},
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

            # Сохраняем в файл (обход проблемы 1.5M токенов в ToolMessage)
            os.makedirs(SAVE_DIR, exist_ok=True)
            filename = f"img_{int(time.time())}_{os.getpid()}.png"
            filepath = os.path.join(SAVE_DIR, filename)
            
            with open(filepath, "wb") as f:
                f.write(base64.b64decode(b64_json))

            # Возвращаем ТОЛЬКО путь и метаданные (НЕ base64)
            return json.dumps({
                "status": "success",
                "local_path": filepath,
                "public_url": f"/static/generated/{filename}",
                "format": "png",
                "revised_prompt": prompt,
                "model": IMAGE_MODEL,
                "note": "Изображение сохранено на диск. Используй local_path для работы с файлом."
            }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": f"{type(e).__name__}: {str(e)[:200]}"}, ensure_ascii=False)
