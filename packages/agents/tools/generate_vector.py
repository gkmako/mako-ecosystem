"""Генерация векторной графики (SVG) через Recraft v4.1-pro-vector."""
import os
import json
import httpx
from pydantic import BaseModel, Field
from packages.shared.config import settings

VECTOR_MODEL = os.getenv("VECTOR_MODEL", "recraft/recraft-v4.1-pro-vector")


class GenerateVectorSchema(BaseModel):
    """Генерация векторной графики (логотипы, иконки, инфографика)."""
    prompt: str = Field(description="Описание векторного изображения на английском (логотип, иконка, паттерн и т.п.)")
    style: str = Field(
        default="icon",
        description="Стиль: icon | logo | illustration | pattern"
    )


async def generate_vector(prompt: str, style: str = "icon") -> str:
    """Генерирует векторное изображение (SVG)."""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.LLM_API_BASE}/images/generations",
                headers={
                    "Authorization": f"Bearer {settings.LLM_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": VECTOR_MODEL,
                    "prompt": prompt,
                    "style": style,
                    "n": 1,
                },
            )

            if response.status_code != 200:
                return json.dumps({"error": f"Vector API error {response.status_code}: {response.text[:200]}"}, ensure_ascii=False)

            data = response.json()
            images = data.get("data", [])
            if not images:
                return "Векторное изображение не сгенерировано."

            b64_json = images[0].get("b64_json", "")
            if not b64_json:
                return "Пустой ответ от API."

            # SVG всегда в base64
            data_url = f"data:image/svg+xml;base64,{b64_json}"

            return json.dumps({
                "status": "success",
                "image_url": data_url,
                "format": "svg",
                "model": VECTOR_MODEL,
            }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": f"{type(e).__name__}: {str(e)[:200]}"}, ensure_ascii=False)
