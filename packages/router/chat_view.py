from sqladmin import BaseView, expose
from fastapi import Request
from fastapi.templating import Jinja2Templates
from pathlib import Path

BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


class ChatView(BaseView):
    name = "Чат"
    icon = "fa-solid fa-comments"

    @expose("/chat", methods=["GET"])
    def chat_page(self, request: Request):
        return templates.TemplateResponse("chat.html", {"request": request})