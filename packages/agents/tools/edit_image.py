"""Редактирование изображений (inpainting) через Recraft v4.1-pro."""
import os
import json
import base64
import httpx
from pydantic import BaseModel, Field
from packages.shared.config import settings

EDIT_MODEL = os.getenv("EDIT_IMAGE_MODEL", "recraft/recraft-v4.1-pro")


class EditImageSchema(BaseModel):
    """Редактирование изображения (inpainting, style transfer)."""
    image_url: str = Field(description="URL или data URL исходного изображения")
    prompt: str = Field(description="Описание изменений на английском (что добавить/убрать/изменить)")
    mode: str = Field(
        default="inpainting",
        description="Режим: inpainting | style_transfer | outpainting"
    )


async def edit_image(image_url: str, prompt: str, mode: str = "inpainting") -> str:
    """Редактирует существующее изображение через Recraft."""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Скачиваем исходное изображение (если URL)
            if image_url.startswith("data:"):
                # Извлекаем base64 из data URL
                b64_part = image_url.split(",", 1)[1]
                image_b64 = b64_part
            else:
                img_resp = await client.get(image_url, timeout=30.0)
                if img_resp.status_code != 200:
                    return json.dumps({"error": f"Failed to download source image: {img_resp.status_code}"}, ensure_ascii=False)
                image_b64 = base64.b64encode(img_resp.content).decode("utf-8")

            response = await client.post(
                f"{settings.LLM_API_BASE}/images/edits",
                headers={
                    "Authorization": f"Bearer {settings.LLM_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": EDIT_MODEL,
                    "image": image_b64,
                    "prompt": prompt,
                    "mode": mode,
                    "n": 1,
                },
            )

            if response.status_code != 200:
                return json.dumps({"error": f"Edit API error {response.status_code}: {response.text[:200]}"}, ensure_ascii=False)

            data = response.json()
            images = data.get("data", [])
            if not images:
                return "Изображение не отредактировано."

            b64_json = images[0].get("b64_json", "")
            if not b64_json:
                return "Пустой ответ от API."

            data_url = f"data:image/png;base64,{b64_json}"

            return json.dumps({
                "status": "success",
                "image_url": data_url,
                "mode": mode,
                "model": EDIT_MODEL,
            }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": f"{type(e).__name__}: {str(e)[:200]}"}, ensure_ascii=False)
