import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from packages.langgraph_app.two_agent_graph import create_two_agent_graph

async def main():
    # Замени base_url и api_key на данные твоего провайдера (routerai.ru или аналог)
    api_base = "https://routerai.ru/api/v1" 
    api_key = "sk-0aytUQ6UtSa1ogqBZJDUkyf6pqsckRjJ"

    llm_main = ChatOpenAI(model="qwen/qwen3-coder-plus", base_url=api_base, api_key=api_key)
    llm_reviewer = ChatOpenAI(model="deepseek/deepseek-v4-pro", base_url=api_base, api_key=api_key)

    graph = create_two_agent_graph(
        main_model=llm_main,
        reviewer_model=llm_reviewer,
        reviewer_system_prompt="Ты строгий ревьюер. Если ответ идеален, напиши 'APPROVED'. Если есть ошибки, напиши 'REJECTED: [ошибки]'.",
        max_iterations=2
    )

    initial_state = {"messages": [HumanMessage(content="Напиши функцию на Python для сложения двух чисел.")]}
    
    print("--- Запуск графа ---")
    final_state = await graph.ainvoke(initial_state)
    
    print("\n--- История сообщений ---")
    for msg in final_state["messages"]:
        print(f"[{msg.type}] {msg.content}\n")

if __name__ == "__main__":
    asyncio.run(main())
