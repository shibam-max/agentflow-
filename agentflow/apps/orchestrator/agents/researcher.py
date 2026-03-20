import time
import logging
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.tools import DuckDuckGoSearchRun
from langchain_core.prompts import ChatPromptTemplate
from tools.rag_tool import retrieve_context

logger = logging.getLogger(__name__)

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
search_tool = DuckDuckGoSearchRun()


async def researcher_node(state: dict) -> dict:
    run_id = state["run_id"]
    task = state["task_description"]
    feedback = state.get("critic_feedback", "")
    revision = state.get("revision_count", 0)

    logger.info(f'{{"run_id":"{run_id}","agent":"researcher","revision":{revision}}}')
    start = time.time()

    search_query = f"{task} {feedback}" if feedback else task
    web_results = search_tool.run(search_query[:200])

    rag_context = await retrieve_context(task)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a research agent. Synthesize web search results and context into a concise research brief."),
        ("human", "Task: {task}\n\nWeb Results:\n{web}\n\nContext:\n{rag}\n\nCritic Feedback (if any): {feedback}\n\nProvide a structured research brief.")
    ])

    response = await llm.ainvoke(prompt.format_messages(task=task, web=web_results, rag=rag_context, feedback=feedback))

    duration_ms = int((time.time() - start) * 1000)
    logger.info(f'{{"run_id":"{run_id}","agent":"researcher","duration_ms":{duration_ms}}}')

    return {
        **state,
        "research_output": response.content,
        "revision_count": revision + (1 if revision > 0 else 0),
    }
