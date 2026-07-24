"""
PromptBuilder - сборка системных промптов для агентов и ревьюеров.
Поддерживает кэш промтов из БД + fallback на YAML-файлы.
"""
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from typing import Optional, Dict
import yaml
import asyncio
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Построитель промптов с кэшем из БД и fallback на YAML."""
    
    _prompt_cache: Dict[str, str] = {}
    _cache_loaded: bool = False
    _cache_loading: bool = False
    
    def __init__(self, prompts_dir: str = "/app/packages/prompts"):
        self.prompts_dir = Path(prompts_dir)
        if self.prompts_dir.exists():
            self.env = Environment(
                loader=FileSystemLoader(str(self.prompts_dir)),
                autoescape=False
            )
        else:
            self.env = None
    
    @classmethod
    def reload_cache(cls):
        """Перезагрузить кэш промтов из БД (синхронная версия)."""
        if cls._cache_loading:
            return
        
        cls._cache_loading = True
        try:
            try:
                loop = asyncio.get_running_loop()
                # Есть запущенный event loop - создаём задачу
                asyncio.create_task(cls._async_reload_cache())
            except RuntimeError:
                # Нет event loop - запускаем синхронно
                asyncio.run(cls._async_reload_cache())
        except Exception as e:
            logger.warning(f"[PromptBuilder] Failed to reload cache: {e}")
        finally:
            cls._cache_loading = False
    
    @classmethod
    async def _async_reload_cache(cls):
        """Асинхронная загрузка кэша из БД."""
        try:
            from packages.router.database import router_async_session
            from packages.router.models import PromptDB
            from sqlalchemy import select
            
            async with router_async_session() as session:
                result = await session.execute(
                    select(PromptDB).where(PromptDB.is_active == True)
                )
                prompts = result.scalars().all()
                cls._prompt_cache = {p.prompt_key: p.content for p in prompts}
                cls._cache_loaded = True
                logger.info(f"[PromptBuilder] Cache loaded: {len(cls._prompt_cache)} prompts")
        except Exception as e:
            logger.warning(f"[PromptBuilder] DB cache load failed: {e}. Using fallback.")
            cls._cache_loaded = True  # чтобы не пытаться снова
    
    @classmethod
    def get_prompt(cls, prompt_key: str) -> str:
        """Получить промт из кэша по ключу."""
        if not cls._cache_loaded:
            cls.reload_cache()
        return cls._prompt_cache.get(prompt_key, "")
    
    @classmethod
    def get_system_prompts(cls) -> str:
        """Получить агрегированные системные промты (system.*)."""
        if not cls._cache_loaded:
            cls.reload_cache()
        
        system_keys = [k for k in cls._prompt_cache.keys() if k.startswith("system.")]
        if not system_keys:
            return ""
        
        parts = []
        for key in sorted(system_keys):
            content = cls._prompt_cache[key]
            parts.append(content)
        
        return "\n\n".join(parts)
    
    @classmethod
    def get_chat_prompt(cls) -> str:
        """Получить промт для обычного чата (без агентов)."""
        return cls.get_prompt("chat.default")
    
    @classmethod
    def get_reviewer_prompt_by_domain(cls, domain: str) -> str:
        """Получить промт ревьюера по домену."""
        key = f"reviewer.{domain}"
        prompt = cls.get_prompt(key)
        if not prompt:
            # fallback на general
            prompt = cls.get_prompt("reviewer.general")
        return prompt
    
    @lru_cache(maxsize=None)
    def load_profile(self, agent_id: str) -> dict:
        """Загружает YAML-профиль агента из папки profiles."""
        profiles_dir = self.prompts_dir / "profiles"
        if not profiles_dir.exists():
            raise FileNotFoundError(f"Profiles directory not found at {profiles_dir}")
        for contour_dir in profiles_dir.iterdir():
            if contour_dir.is_dir():
                profile_path = contour_dir / f"{agent_id}.yaml"
                if profile_path.exists():
                    with open(profile_path, "r", encoding="utf-8") as f:
                        return yaml.safe_load(f)
        raise FileNotFoundError(f"Profile for {agent_id} not found in {profiles_dir}")

    def build_agent_prompt(
        self,
        agent_id: str,
        rag_context: Optional[str] = None
    ) -> str:
        """Собирает финальный system prompt для агента."""
        if not self.env:
            return "Error: Prompts directory not initialized."
        
        try:
            profile = self.load_profile(agent_id)
            prompt_config = profile["prompt"]
            capabilities = profile["capabilities"]
            
            # Загружаем базовый шаблон
            base_template = self.env.get_template(f"base/{prompt_config['base_template']}")
            
            # Загружаем специфичный шаблон агента
            agent_template = self.env.get_template(f"agents/{prompt_config['agent_template']}")
            specific_instructions = agent_template.render()
            
            # Рендерим базовый шаблон с переменными
            final_prompt = base_template.render(
                role=prompt_config["role"],
                specific_instructions=specific_instructions,
                tools=capabilities.get("tools", []),
                allow_rag=capabilities.get("allow_rag", False),
                rag_context=rag_context or ""
            )
        except Exception as e:
            logger.warning(f"[PromptBuilder] YAML build failed for {agent_id}: {e}")
            final_prompt = f"Ты — агент {agent_id}. Отвечай на русском."
        
        # Инжектируем системные промты из БД в начало
        system_prompts = self.get_system_prompts()
        if system_prompts:
            final_prompt = f"{system_prompts}\n\n---\n\n{final_prompt}"
        
        return final_prompt

    def build_reviewer_prompt(
        self,
        domain: str,
        checks: list
    ) -> str:
        """Собирает промпт для ревьюера."""
        # Сначала пробуем из БД
        db_prompt = self.get_reviewer_prompt_by_domain(domain)
        if db_prompt:
            return db_prompt
        
        # Fallback на YAML
        try:
            template = self.env.get_template("reviewers/reviewer_generic.jinja2")
            check_contents = []
            checks_dir = self.prompts_dir / "reviewers" / "reviewer_checks"
            for check in checks:
                check_path = checks_dir / f"{check}.md"
                if check_path.exists():
                    check_contents.append(check_path.read_text(encoding="utf-8"))
            return template.render(
                domain=domain,
                checks="\n\n".join(check_contents)
            )
        except Exception as e:
            logger.warning(f"[PromptBuilder] Reviewer YAML build failed: {e}")
            return f"Ты — ревьюер в домене {domain}. Проверь ответ и ответь в JSON: {{\"is_approved\": true/false, \"feedback\": \"...\"}}"


# При импорте модуля - инициализация кэша
try:
    PromptBuilder.reload_cache()
except Exception as e:
    logger.warning(f"[PromptBuilder] Initial cache load failed: {e}")