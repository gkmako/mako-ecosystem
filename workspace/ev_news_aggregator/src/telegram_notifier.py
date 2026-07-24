import asyncio
import httpx
from typing import List, Dict, Optional
from loguru import logger


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        """
        Инициализация Telegram нотификатора.
        
        Args:
            bot_token (str): Токен Telegram бота
            chat_id (str): ID чата для отправки сообщений
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        
    async def send_message(self, text: str) -> bool:
        """
        Отправляет сообщение в Telegram.
        
        Args:
            text (str): Текст сообщения
            
        Returns:
            bool: Успешность отправки
        """
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram нотификация не настроена (отсутствует токен или chat_id)")
            return False
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": self.chat_id,
                        "text": text,
                        "parse_mode": "HTML"
                    }
                )
                response.raise_for_status()
                logger.info("Сообщение успешно отправлено в Telegram")
                return True
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения в Telegram: {e}")
            return False
            
    async def send_news_digest(self, news_list: List[Dict], title: str = "Новые новости по электромобилям в РФ") -> bool:
        """
        Отправляет дайджест новостей в Telegram.
        
        Args:
            news_list (List[Dict]): Список новостей
            title (str): Заголовок дайджеста
            
        Returns:
            bool: Успешность отправки
        """
        if not news_list:
            logger.info("Нет новостей для отправки в Telegram")
            return True
            
        # Формирование текста сообщения
        message_text = f"<b>{title}</b>\n\n"
        
        for i, news in enumerate(news_list[:10], 1):  # Ограничим 10 новостями
            message_text += f"{i}. <b>{news['title']}</b>\n"
            message_text += f"   Источник: {news['source']}\n"
            if news.get('summary'):
                # Ограничим длину описания
                summary = news['summary'][:200] + "..." if len(news['summary']) > 200 else news['summary']
                message_text += f"   Описание: {summary}\n"
            message_text += f"   <a href='{news['link']}'>Читать далее</a>\n\n"
            
        # Если сообщение слишком длинное, обрежем его
        if len(message_text) > 4000:
            message_text = message_text[:4000] + "\n\n<i>... (сообщение обрезано)</i>"
            
        return await self.send_message(message_text)
        
    async def send_test_message(self) -> bool:
        """
        Отправляет тестовое сообщение.
        
        Returns:
            bool: Успешность отправки
        """
        return await self.send_message("✅ Telegram нотификатор настроен корректно!")