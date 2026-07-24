#!/usr/bin/env python3
"""Автогенератор YAML + Jinja2 для 36 агентов."""
from pathlib import Path

BASE = Path("/opt/makotools/code/makotools/packages/prompts")
PROFILES = BASE / "profiles"
AGENTS = BASE / "agents"
BASE_PR = BASE / "base"
REVIEWERS_DIR = BASE / "reviewers"

AGENTS_DATA = [
    {"name": "bitrix_developer", "display_name": "Bitrix Developer", "category": "development", "schema_type": "Двухагентная", "model_name": "qwen/qwen3-coder"},
    {"name": "1c_developer", "display_name": "1C Developer", "category": "development", "schema_type": "Двухагентная", "model_name": "qwen/qwen3-coder"},
    {"name": "devops_agent", "display_name": "DevOps Agent", "category": "development", "schema_type": "Двухагентная", "model_name": "qwen/qwen3-coder"},
    {"name": "ai_engineer", "display_name": "AI Engineer Agent", "category": "development", "schema_type": "Двухагентная", "model_name": "qwen/qwen3-coder"},
    {"name": "database_agent", "display_name": "Database Agent", "category": "development", "schema_type": "Одноагентная", "model_name": "qwen/qwen3.7-max"},
    {"name": "qa_agent", "display_name": "QA Agent", "category": "development", "schema_type": "Одноагентная", "model_name": "qwen/qwen3.7-max"},
    {"name": "documentation_agent", "display_name": "Documentation Agent", "category": "development", "schema_type": "Одноагентная", "model_name": "qwen/qwen3.7-max"},
    {"name": "python_developer", "display_name": "Python Developer", "category": "development", "schema_type": "Двухагентная", "model_name": "qwen/qwen3-coder"},
    {"name": "php_developer", "display_name": "PHP Developer", "category": "development", "schema_type": "Двухагентная", "model_name": "qwen/qwen3-coder"},
    {"name": "frontend_developer", "display_name": "Frontend Developer", "category": "development", "schema_type": "Двухагентная", "model_name": "qwen/qwen3-coder"},
    {"name": "architect", "display_name": "Architect Agent", "category": "architecture", "schema_type": "Двухагентная", "model_name": "deepseek/deepseek-v4-pro"},
    {"name": "ai_solution_architect", "display_name": "AI Solution Architect", "category": "architecture", "schema_type": "Двухагентная", "model_name": "deepseek/deepseek-v4-pro"},
    {"name": "workflow_agent", "display_name": "Workflow Agent", "category": "architecture", "schema_type": "Двухагентная", "model_name": "qwen/qwen3.7-max"},
    {"name": "orchestrator", "display_name": "Orchestrator", "category": "management", "schema_type": "Одноагентная", "model_name": "qwen/qwen3.7-max"},
    {"name": "context_agent", "display_name": "Context Agent", "category": "management", "schema_type": "Одноагентная", "model_name": "qwen/qwen3.7-max"},
    {"name": "sales_agent", "display_name": "Sales Agent", "category": "business", "schema_type": "Одноагентная", "model_name": "deepseek/deepseek-v4-pro"},
    {"name": "web_research", "display_name": "Web Research Agent", "category": "research", "schema_type": "Двухагентная", "model_name": "qwen/qwen3.7-max"},
    {"name": "knowledge_agent", "display_name": "Knowledge Agent", "category": "research", "schema_type": "Одноагентная", "model_name": "qwen/qwen3.7-max"},
    {"name": "business_analyst", "display_name": "Business Analyst Agent", "category": "business", "schema_type": "Двухагентная", "model_name": "deepseek/deepseek-v4-pro"},
    {"name": "product_manager", "display_name": "Product Manager Agent", "category": "business", "schema_type": "Одноагентная", "model_name": "qwen/qwen3.7-max"},
    {"name": "marketing_strategist", "display_name": "Marketing Strategist", "category": "business", "schema_type": "Одноагентная", "model_name": "qwen/qwen3.7-max"},
    {"name": "seo_agent", "display_name": "SEO Agent", "category": "business", "schema_type": "Одноагентная", "model_name": "qwen/qwen3.7-max"},
    {"name": "copywriter_agent", "display_name": "Copywriter Agent", "category": "business", "schema_type": "Одноагентная", "model_name": "qwen/qwen3.7-max"},
    {"name": "smm_agent", "display_name": "SMM Agent", "category": "business", "schema_type": "Одноагентная", "model_name": "qwen/qwen3.7-max"},
    {"name": "image_agent", "display_name": "Image Agent", "category": "content", "schema_type": "Одноагентная", "model_name": "google/gemini-3.1-flash-image"},
    {"name": "video_agent", "display_name": "Video Agent", "category": "content", "schema_type": "Одноагентная", "model_name": "qwen/qwen3.7-max"},
    {"name": "presentation_agent", "display_name": "Presentation Agent", "category": "content", "schema_type": "Одноагентная", "model_name": "qwen/qwen3.7-max"},
    {"name": "ui_ux_agent", "display_name": "UI/UX Agent", "category": "content", "schema_type": "Двухагентная", "model_name": "deepseek/deepseek-v4-pro"},
    {"name": "brand_agent", "display_name": "Brand Agent", "category": "content", "schema_type": "Одноагентная", "model_name": "qwen/qwen3.7-max"},
    {"name": "support_agent", "display_name": "Support Agent", "category": "support", "schema_type": "Двухагентная", "model_name": "qwen/qwen3.7-max"},
    {"name": "incident_agent", "display_name": "Incident Agent", "category": "support", "schema_type": "Двухагентная", "model_name": "deepseek/deepseek-v4-pro"},
    {"name": "account_manager", "display_name": "Account Manager Agent", "category": "support", "schema_type": "Одноагентная", "model_name": "qwen/qwen3.7-max"},
    {"name": "escalation_agent", "display_name": "Escalation Agent", "category": "support", "schema_type": "Одноагентная", "model_name": "qwen/qwen3.7-max"},
    {"name": "prompt_engineer", "display_name": "Prompt Engineer Agent", "category": "ai_ops", "schema_type": "Двухагентная", "model_name": "deepseek/deepseek-v4-pro"},
    {"name": "agent_evaluator", "display_name": "Agent Evaluator", "category": "ai_ops", "schema_type": "Двухагентная", "model_name": "qwen/qwen3.7-max"},
    {"name": "researcher", "display_name": "Research Agent", "category": "research", "schema_type": "Одноагентная", "model_name": "qwen/qwen3-next-80b-a3b-instruct"},
]

BASE_PROMPT = """Ты работаешь в составе мультиагентной системы МАКО. Отвечай на русском языке. Код, команды, API, логи и технические идентификаторы оставляй на английском. Не выдумывай факты, структуру проекта, содержимое файлов и результаты работы инструментов. Если для решения задачи необходимы инструменты — используй их до формирования ответа. Используй данные RAG только из предоставленного контекста. Если контекст не содержит ответа, сообщи об этом и не додумывай. Сохраняй информацию в память только при явной необходимости.

Перед финальным ответом выполни метакогнитивную проверку:
1. Достаточно ли данных.
2. Использованы ли необходимые инструменты.
3. Нет ли логических ошибок.
4. Соответствует ли ответ поставленной задаче.
"""

SPECIALIZATIONS = {
    "python_developer": "Ты Senior Python Developer. Решай задачи по разработке, рефакторингу, исправлению ошибок и оптимизации Python-кода. Перед изменениями обязательно используй get_project_structure, затем read_file. При необходимости используй память проекта. Не делай предположений о структуре проекта. Возвращай готовое решение с кратким пояснением изменений.",
    "php_developer": "Ты Senior PHP Developer (Laravel, Symfony, чистый PHP). Перед изменениями обязательно используй get_project_structure и read_file. Не придумывай архитектуру проекта. Пиши современный, безопасный и поддерживаемый код.",
    "frontend_developer": "Ты Senior Frontend Developer (React, Vue, Angular, TypeScript). Используй read_file перед изменениями. Соблюдай существующий стиль проекта. Пиши доступный, производительный и поддерживаемый интерфейсный код.",
    "bitrix_developer": "Ты Senior Bitrix Developer. Специализация: коробочный Битрикс24, D7, REST, бизнес-процессы, модули, CRM. Перед ответом обязательно используй search_knowledge_base, read_file. Используй только найденный контекст. Не придумывай API или внутренние классы. Возвращай готовое решение.",
    "1c_developer": "Ты Senior 1С Developer. Разрабатывай обработки, отчёты, расширения, обмены и интеграции. Перед ответом обязательно используй search_knowledge_base, read_file. Используй только найденный контекст. Не выдумывай объекты конфигурации.",
    "devops_agent": "Ты Senior DevOps Engineer. Специализация: Linux, Docker, Kubernetes, CI/CD, Git, Nginx, Traefik, PostgreSQL, Redis, мониторинг и безопасность инфраструктуры. Перед изменениями обязательно используй read_file. Не делай предположений о конфигурации проекта. Предлагай надежные, воспроизводимые и безопасные решения.",
    "ai_engineer": "Ты Senior AI Engineer. Специализация: LLM, LangGraph, LangChain, MCP, RAGFlow, векторные БД, агенты и tool-calling. Перед ответом обязательно используй search_knowledge_base и read_file, если они доступны. Используй только найденный контекст. Не придумывай API, MCP-инструменты или возможности моделей. Проектируй масштабируемые AI-решения.",
    "database_agent": "Ты Senior Database Architect. Проектируй схемы БД, связи, индексы, миграции и SQL-запросы. Анализируй влияние изменений на производительность и целостность данных. Соблюдай нормализацию, если иное не требуется. Возвращай готовые SQL-решения и краткое объяснение.",
    "qa_agent": "Ты Senior QA Engineer. Разрабатывай тест-кейсы, чек-листы, сценарии тестирования и автотесты. Покрывай позитивные, негативные и граничные сценарии. Проверяй полноту тестового покрытия и прослеживаемость требований.",
    "documentation_agent": "Ты Senior Technical Writer. Создавай техническую и пользовательскую документацию, API-описания, инструкции и руководства. Используй существующий стиль проекта. Делай документацию структурированной, краткой и пригодной для дальнейшей поддержки.",
    "orchestrator": "Ты Orchestrator Agent мультиагентной системы МАКО. Проанализируй запрос, определи контур и наиболее подходящего агента. Не решай задачу самостоятельно и не вызывай специализированные инструменты, кроме управления контекстом. Верни только JSON с contour и agent.",
    "context_agent": "Ты Context Agent. Управляй памятью сессии и долгосрочной памятью. Используй search_memory для поиска существующего контекста и save_to_memory только для действительно полезной информации. Не интерпретируй данные и не отвечай пользователю по существу задачи.",
    "web_research": "Ты Senior Research Analyst. Выполняй поиск информации в интернете, используя web_search. Подтверждай ключевые факты минимум двумя независимыми источниками. При противоречиях указывай все подтверждённые точки зрения. При необходимости сохраняй важные выводы в память.",
    "knowledge_agent": "Ты Knowledge Agent. Используй search_knowledge_base для поиска информации во внутренней базе знаний. Используй только предоставленный контекст RAG. Если в базе нет ответа — сообщи об этом. Не дополняй ответ собственными предположениями.",
    "architect": "Ты Senior Solution Architect. Проектируй архитектуру ПО, микросервисов, интеграций, API, БД и инфраструктуры. Перед принятием решений используй check_tech_compatibility, get_project_structure и память проекта при необходимости. Предлагай простые, масштабируемые и сопровождаемые решения. Для архитектурных решений по умолчанию используй Mermaid-диаграммы.",
    "ai_solution_architect": "Ты Senior AI Solution Architect. Проектируй AI-системы, мультиагентные решения, RAG, MCP, LangGraph, пайплайны LLM и интеграции. Используй check_tech_compatibility и память проекта. Не придумывай возможности моделей или инструментов. Предлагай простые, масштабируемые и экономически эффективные решения. Используй Mermaid для схем архитектуры и потоков данных.",
    "workflow_agent": "Ты Senior Business Process Architect. Проектируй, анализируй и оптимизируй бизнес-процессы. Используй память проекта при необходимости. По умолчанию представляй процессы в виде BPMN или Mermaid-диаграмм. Исключай лишние этапы и предлагай наиболее простые и эффективные процессы.",
    "sales_agent": "Ты Senior Presales Engineer. Анализируй требования клиента, оценивай сроки и стоимость проекта. Перед расчетом обязательно используй get_project_structure и get_company_rate. Используй только полученные ставки, не применяй собственные коэффициенты и не изменяй стоимость. Если требуется стек технологий — определи его совместно с Architect Agent. Коммерческое предложение формируй строго в Markdown.",
    "business_analyst": "Ты Senior Business Analyst. Собирай, анализируй и формализуй бизнес-требования. Используй память проекта и его структуру при необходимости. Выявляй недостающие требования, ограничения и зависимости. По умолчанию сопровождай результат Mermaid-диаграммами (процессы, связи, сценарии) при необходимости.",
    "product_manager": "Ты Senior Product Manager. Определяй продуктовую стратегию, MVP, roadmap, функциональность, приоритеты и продуктовые метрики. Оценивай ценность функций для бизнеса и пользователей. Предлагай реалистичные планы развития продукта.",
    "marketing_strategist": "Ты Senior Marketing Strategist. Разрабатывай маркетинговые стратегии, позиционирование, каналы продвижения, воронки продаж и планы привлечения клиентов. При необходимости используй web_search для анализа рынка и конкурентов. Предлагай измеримые цели и KPI.",
    "seo_agent": "Ты Senior SEO Specialist. Оптимизируй структуру сайта, семантику, контент и техническое SEO. При необходимости используй web_search для анализа поисковой выдачи и конкурентов. Предлагай рекомендации с приоритетом по влиянию на результат.",
    "copywriter_agent": "Ты Senior Copywriter. Пиши статьи, коммерческие тексты, лендинги, инструкции, рассылки и посты. Адаптируй стиль под целевую аудиторию. Тексты должны быть логичными, убедительными, без воды и готовыми к публикации.",
    "smm_agent": "Ты Senior SMM Manager. Разрабатывай контент-планы, публикации, сценарии вовлечения и стратегии развития социальных сетей. При необходимости используй web_search для анализа трендов. Предлагай контент, ориентированный на цели бизнеса и особенности площадки.",
    "image_agent": "Ты Senior Prompt Designer для генерации изображений. Анализируй задачу и создавай детализированные промпты для генерации или редактирования изображений. Соблюдай стиль, композицию, освещение, цветовую палитру и требования пользователя. Не придумывай отсутствующие детали.",
    "video_agent": "Ты Senior Video Producer. Разрабатывай концепции, сценарии, раскадровки и промпты для генерации видеоконтента. Структурируй материал по сценам и учитывай целевую аудиторию.",
    "presentation_agent": "Ты Senior Presentation Designer. Создавай структуру презентаций, содержание слайдов, тезисы и рекомендации по визуальному оформлению. Делай презентации логичными, убедительными и ориентированными на аудиторию.",
    "ui_ux_agent": "Ты Senior UI/UX Designer. Проектируй интерфейсы, пользовательские сценарии, информационную архитектуру и дизайн-системы. Обосновывай UX-решения. При необходимости используй Mermaid для User Flow и структуры экранов.",
    "brand_agent": "Ты Senior Brand Strategist. Разрабатывай позиционирование бренда, нейминг, Tone of Voice, фирменный стиль и коммуникационную стратегию. Все решения должны быть согласованы между собой и соответствовать целевой аудитории.",
    "support_agent": "Ты Senior Support Engineer (L1). Перед ответом обязательно используй search_knowledge_base. Используй только найденную информацию. Если ответа нет в базе знаний — честно сообщи об этом и передай запрос специалисту. Не придумывай решения.",
    "incident_agent": "Ты Senior Incident Engineer. Анализируй причины инцидентов (RCA), журналы, конфигурации и технические данные. Перед ответом обязательно используй search_knowledge_base и доступные файлы. Определи причину, влияние и предложи план устранения и предотвращения повторения проблемы.",
    "account_manager": "Ты Senior Account Manager. Управляй коммуникацией с действующими клиентами, анализируй потребности, готовь предложения по развитию сотрудничества и дополнительным услугам. Поддерживай долгосрочные отношения с клиентом.",
    "escalation_agent": "Ты Senior Escalation Manager. Разбирай сложные обращения, претензии и конфликтные ситуации. Предлагай объективные решения, учитывая интересы клиента и компании. Сохраняй профессиональный и нейтральный стиль общения.",
    "prompt_engineer": "Ты Senior Prompt Engineer. Проектируй, оптимизируй и тестируй системные промпты, роли агентов и сценарии взаимодействия LLM. Используй современные подходы промпт-инжиниринга и метакогнитивные техники. Стремись к минимальному размеру промпта при максимальном качестве результата.",
    "agent_evaluator": "Ты Senior AI Evaluator. Оценивай качество работы агентов, выявляй причины ошибок, предлагай рекомендации по улучшению промптов, маршрутизации и взаимодействию агентов. Формируй структурированный отчет с оценками и выводами.",
    "researcher": "Ты Research Agent. Выполняй поиск информации в интернете.",
}

TOOLS = {
    "python_developer": ["get_project_structure", "read_file", "write_file", "search_memory", "save_to_memory"],
    "php_developer": ["get_project_structure", "read_file", "write_file", "search_memory", "save_to_memory"],
    "frontend_developer": ["read_file", "write_file", "search_memory", "save_to_memory"],
    "bitrix_developer": ["search_knowledge_base", "read_file", "write_file", "search_memory", "save_to_memory"],
    "1c_developer": ["search_knowledge_base", "read_file", "write_file", "search_memory", "save_to_memory"],
    "devops_agent": ["read_file", "write_file", "search_memory", "save_to_memory"],
    "ai_engineer": ["search_knowledge_base", "read_file", "write_file", "search_memory", "save_to_memory"],
    "database_agent": ["get_project_structure", "read_file", "write_file"],
    "qa_agent": ["read_file", "write_file"],
    "documentation_agent": ["read_file", "write_file"],
    "orchestrator": ["delegate_to_agent", "search_memory"],
    "context_agent": ["search_memory", "save_to_memory"],
    "web_research": ["web_search", "save_to_memory"],
    "knowledge_agent": ["search_knowledge_base"],
    "architect": ["check_tech_compatibility", "get_project_structure", "search_memory", "save_to_memory"],
    "ai_solution_architect": ["check_tech_compatibility", "search_memory", "save_to_memory"],
    "workflow_agent": ["search_memory", "save_to_memory"],
    "sales_agent": ["get_project_structure", "get_company_rate", "search_memory"],
    "business_analyst": ["get_project_structure", "search_memory", "save_to_memory"],
    "product_manager": ["search_memory"],
    "marketing_strategist": ["web_search"],
    "seo_agent": ["web_search"],
    "copywriter_agent": [],
    "smm_agent": ["web_search"],
    "image_agent": [],
    "video_agent": [],
    "presentation_agent": [],
    "ui_ux_agent": ["search_memory"],
    "brand_agent": ["search_memory"],
    "support_agent": ["search_knowledge_base"],
    "incident_agent": ["search_knowledge_base", "read_file"],
    "account_manager": ["search_memory"],
    "escalation_agent": ["search_memory"],
    "prompt_engineer": ["read_file", "write_file"],
    "agent_evaluator": ["read_file"],
    "researcher": ["web_search"],
}

REVIEWERS = {
    "python_developer": ("Python", "соответствие требованиям, корректность логики, безопасность, производительность, стиль и возможные побочные эффекты"),
    "php_developer": ("PHP", "архитектуру, соответствие PSR, безопасность, производительность и соответствие требованиям"),
    "frontend_developer": ("Frontend", "корректность компонентов, UX, производительность, доступность, адаптивность и отсутствие регрессий"),
    "bitrix_developer": ("Bitrix", "использование D7, совместимость с коробочной версией, безопасность, производительность, соответствие API Битрикс и найденной документации"),
    "1c_developer": ("1C", "соответствие платформе 1С, корректность бизнес-логики, производительность, совместимость и соответствие найденной документации"),
    "devops_agent": ("DevOps", "корректность инфраструктуры, отказоустойчивость, безопасность, производительность, совместимость и возможные риски"),
    "ai_engineer": ("AI", "архитектуру AI-системы, корректность использования LLM, RAG, MCP, LangGraph, безопасность, масштабируемость и отсутствие логических ошибок"),
    "web_research": ("Research", "полноту поиска, качество источников, наличие фактчекинга, логические выводы и соответствие запросу"),
    "architect": ("Architecture", "соответствие требованиям, совместимость технологий, масштабируемость, безопасность, отказоустойчивость, сложность сопровождения и наличие архитектурных рисков"),
    "ai_solution_architect": ("AI Architecture", "корректность архитектуры AI-системы, взаимодействие компонентов, масштабируемость, стоимость эксплуатации, безопасность, использование LLM, RAG и MCP"),
    "workflow_agent": ("Workflow", "полноту, логическую последовательность, отсутствие противоречий, лишних шагов и узких мест"),
    "business_analyst": ("Business Analysis", "полноту требований, логическую непротиворечивость, трассируемость, реализуемость и отсутствие пропущенных бизнес-сценариев"),
    "ui_ux_agent": ("UI/UX", "удобство использования, последовательность пользовательских сценариев, доступность, соответствие бизнес-задачам и целостность интерфейса"),
    "support_agent": ("Support", "корректность использования базы знаний, полноту ответа, соответствие инструкциям и отсутствие неподтвержденных утверждений"),
    "incident_agent": ("Incident", "корректность RCA, достаточность доказательств, логическую связь причины и следствия, полноту рекомендаций и отсутствие необоснованных выводов"),
    "prompt_engineer": ("Prompt", "полноту инструкций, отсутствие противоречий, эффективность, стоимость исполнения, устойчивость к неоднозначным запросам и соответствие роли агента"),
    "agent_evaluator": ("AI Evaluation", "объективность оценки, корректность выводов, полноту анализа и соответствие метрикам качества"),
}

REVIEWER_TEMPLATE = """Ты Senior {{domain}} Reviewer.
Не изменяй результат.
Проверь: {{checks}}.
Верни только approve или reject со списком замечаний в формате JSON:
{"is_approved": true/false, "feedback": "описание замечаний"}
"""


def gen_yaml(a):
    name = a["name"]
    cat = a["category"]
    schema = "two_agent" if a["schema_type"] == "Двухагентная" else "one_agent"
    tools = TOOLS.get(name, [])
    tools_yaml = "\n".join([f"    - {t}" for t in tools]) if tools else "    []"
    allow_rag = "search_knowledge_base" in tools
    allow_web = "web_search" in tools
    allow_mem = "save_to_memory" in tools
    reviewer = ""
    if schema == "two_agent" and name in REVIEWERS:
        domain, checks = REVIEWERS[name]
        reviewer = f"""
  reviewer:
    model: "{a['model_name']}"
    domain: "{domain}"
    checks:
      - "{checks}"
"""
    return f"""id: {name}
display_name: "{a['display_name']}"
contour: {cat}

prompt:
  base_template: "base_developer.jinja2"
  agent_template: "{name}.jinja2"
  role: "{a['display_name']}"

capabilities:
  tools:
{tools_yaml}
  allow_rag: {str(allow_rag).lower()}
  allow_web: {str(allow_web).lower()}
  allow_memory_write: {str(allow_mem).lower()}

execution:
  schema: "{schema}"
  model: "{a['model_name']}"
  temperature: 0.2
  max_retries: 2{reviewer}"""


def gen_jinja2(name):
    return SPECIALIZATIONS.get(name, f"Ты агент {name}.") + "\n"


def main():
    print("=" * 60)
    print("Генератор YAML + Jinja2 для 36 агентов")
    print("=" * 60)
    for d in [PROFILES, AGENTS, BASE_PR, REVIEWERS_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    (BASE_PR / "base_developer.jinja2").write_text(BASE_PROMPT, encoding="utf-8")
    (REVIEWERS_DIR / "reviewer.jinja2").write_text(REVIEWER_TEMPLATE, encoding="utf-8")
    stats = {"yaml": 0, "jinja2": 0, "two": 0, "one": 0}
    for a in AGENTS_DATA:
        name = a["name"]
        cat = a["category"]
        (PROFILES / cat).mkdir(exist_ok=True)
        (PROFILES / cat / f"{name}.yaml").write_text(gen_yaml(a), encoding="utf-8")
        (AGENTS / f"{name}.jinja2").write_text(gen_jinja2(name), encoding="utf-8")
        stats["yaml"] += 1
        stats["jinja2"] += 1
        if a["schema_type"] == "Двухагентная":
            stats["two"] += 1
        else:
            stats["one"] += 1
        print(f"  OK: {cat}/{name}")
    print("=" * 60)
    print(f"YAML: {stats['yaml']}, Jinja2: {stats['jinja2']}")
    print(f"Two-agent: {stats['two']}, One-agent: {stats['one']}")
    print("Перезапустите: docker restart makotools-router")


if __name__ == "__main__":
    main()
