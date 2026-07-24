"""Генерация видео через RouterAI async API."""
import os, json, time, asyncio, httpx
from pydantic import BaseModel, Field
from packages.shared.config import settings

# Базовая модель (быстрая, стабильная)
VIDEO_MODEL = os.getenv("VIDEO_MODEL", "google/veo-3.1-fast")
# Премиум модель
VIDEO_MODEL_PREMIUM = "kwaivgi/kling-v3.0-pro"
SAVE_DIR = "/app/workspace/generated"
POLL_INTERVAL = 5
MAX_POLL_TIME = 300
MAX_RETRIES = 3  # retry при 429 Too many active


class GenerateVideoSchema(BaseModel):
    prompt: str = Field(description="Описание видео на английском (детальное, с движением)")
    duration: int = Field(
        default=6,
        description="Длительность: базовая (Google Veo) = 4/6/8 сек, премиум (Kling) = 3-15 сек"
    )
    aspect_ratio: str = Field(default="16:9", description="16:9 | 9:16 | 1:1")
    premium: bool = Field(
        default=False,
        description="Использовать Kling (3-15 сек, ~17₽/сек) вместо Google Veo (4/6/8 сек)"
    )


async def _create_task(client, model, prompt, duration, aspect_ratio, resolution):
    """Создаёт задачу с retry при 429 (rate limit)."""
    for attempt in range(MAX_RETRIES):
        resp = await client.post(
            f"{settings.LLM_API_BASE}/videos",
            headers={"Authorization": f"Bearer {settings.LLM_API_KEY}", "Content-Type": "application/json"},
            json={"model": model, "prompt": prompt, "duration": duration, "aspect_ratio": aspect_ratio, "resolution": resolution},
        )
        if resp.status_code == 429:
            wait = (attempt + 1) * 10
            print(f"[Video] ⏳ 429 rate limit, wait {wait}s (attempt {attempt+1}/{MAX_RETRIES})")
            await asyncio.sleep(wait)
            continue
        return resp
    return resp


async def generate_video(prompt: str, duration: int = 6, aspect_ratio: str = "16:9", premium: bool = False) -> str:
    model = VIDEO_MODEL_PREMIUM if premium else VIDEO_MODEL

    # Валидация длительности
    if premium:
        if not (3 <= duration <= 15):
            return json.dumps({"error": f"Премиум (Kling): duration 3-15 сек (получено: {duration})"}, ensure_ascii=False)
        cost_per_sec = 17
        resolution = "720p"
    else:
        if duration not in (4, 6, 8):
            return json.dumps({"error": f"Базовая (Veo): duration должен быть 4, 6 или 8 сек (получено: {duration}). Выбери ближайшее."}, ensure_ascii=False)
        cost_per_sec = 8  # примерная цена Veo Fast
        resolution = "1080p"

    estimated_cost = duration * cost_per_sec

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print(f"[Video] 🎬 Создаю задачу: {model}, {duration}с, ~{estimated_cost}₽")

            create_resp = await _create_task(client, model, prompt, duration, aspect_ratio, resolution)

            print(f"[Video] 📥 Response status: {create_resp.status_code}")

            if create_resp.status_code not in (200, 202):
                return json.dumps({
                    "error": f"Create failed: {create_resp.status_code}",
                    "body": create_resp.text[:300]
                }, ensure_ascii=False)

            task_data = create_resp.json()
            task_id = task_data.get("id")
            if not task_id:
                return json.dumps({"error": "No task ID"}, ensure_ascii=False)

            print(f"[Video] ✅ Задача создана: {task_id}")

            polling_url = f"{settings.LLM_API_BASE}/videos/{task_id}"
            start_time = time.time()
            status = "pending"

            while time.time() - start_time < MAX_POLL_TIME:
                await asyncio.sleep(POLL_INTERVAL)
                status_resp = await client.get(polling_url, headers={"Authorization": f"Bearer {settings.LLM_API_KEY}"})
                if status_resp.status_code != 200:
                    continue
                status_data = status_resp.json()
                status = status_data.get("status")
                print(f"[Video] 📊 Статус: {status}")

                if status == "completed":
                    unsigned_urls = status_data.get("unsigned_urls", [])
                    if not unsigned_urls:
                        return json.dumps({"error": "No URLs"}, ensure_ascii=False)

                    # Скачивание С авторизацией
                    print(f"[Video] ⬇️ Скачиваю видео...")
                    download_resp = await client.get(
                        unsigned_urls[0],
                        headers={"Authorization": f"Bearer {settings.LLM_API_KEY}"},
                    )
                    if download_resp.status_code != 200:
                        return json.dumps({"error": f"Download {download_resp.status_code}"}, ensure_ascii=False)

                    os.makedirs(SAVE_DIR, exist_ok=True)
                    filename = f"video_{int(time.time())}_{os.getpid()}.mp4"
                    filepath = os.path.join(SAVE_DIR, filename)
                    with open(filepath, "wb") as f:
                        f.write(download_resp.content)

                    print(f"[Video] ✅ Сохранено: {filepath}")

                    # Реальная стоимость из API
                    real_cost = status_data.get("usage", {}).get("cost")
                    cost_str = f"~{real_cost:.2f}₽" if real_cost else f"~{estimated_cost}₽"

                    return json.dumps({
                        "status": "success",
                        "local_path": filepath,
                        "public_url": f"/static/generated/{filename}",
                        "format": "mp4",
                        "duration": duration,
                        "aspect_ratio": aspect_ratio,
                        "resolution": resolution,
                        "model": model,
                        "premium": premium,
                        "cost": cost_str,
                    }, ensure_ascii=False)

                elif status in ("failed", "cancelled", "expired"):
                    error_msg = status_data.get("error", "Unknown")
                    return json.dumps({"error": f"Video {status}: {error_msg}"}, ensure_ascii=False)

            return json.dumps({"error": f"Timeout after {MAX_POLL_TIME}s (status: {status})"}, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": f"{type(e).__name__}: {str(e)[:200]}"}, ensure_ascii=False)
