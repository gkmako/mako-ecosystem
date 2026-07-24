from fastapi import FastAPI, File, UploadFile, HTTPException, Request
import aiofiles
import os
from werkzeug.utils import secure_filename

app = FastAPI()

# Максимальный размер файла (1MB)
MAX_FILE_SIZE = 1024 * 1024

@app.post('/upload')
async def upload_file(request: Request, file: UploadFile = File(...)):
    # Проверяем Content-Length заголовок до загрузки файла
    content_length = request.headers.get('content-length')
    if content_length and int(content_length) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail='File size exceeds the limit of 1MB')

    # Безопасное имя файла
    filename = secure_filename(file.filename)
    if not filename:
        raise HTTPException(status_code=400, detail='Invalid file name')

    # Путь для сохранения файла
    file_location = f"uploaded_files/{filename}"
    os.makedirs(os.path.dirname(file_location), exist_ok=True)

    # Асинхронное сохранение файла с проверкой размера
    file_size = 0
    async with aiofiles.open(file_location, 'wb') as out_file:
        while True:
            chunk = await file.read(1024 * 1024)  # Читаем по 1MB за раз
            if not chunk:
                break
            file_size += len(chunk)
            if file_size > MAX_FILE_SIZE:
                # Удаляем частично загруженный файл
                os.remove(file_location)
                raise HTTPException(status_code=413, detail='File size exceeds the limit of 1MB')
            await out_file.write(chunk)

    return {'filename': filename, 'size': file_size, 'location': file_location}