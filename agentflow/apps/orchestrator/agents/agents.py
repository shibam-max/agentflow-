import time
import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.4)
llm_critic = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)


async def writer_node(state: dict) -> dict:
    run_id = state["run_id"]
    start = time.time()
    logger.info(f'{{"run_id":"{run_id}","agent":"writer"}}')

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a professional writer. Create a well-structured, clear document based on the research provided."),
        ("human", "Task: {task}\n\nResearch:\n{research}\n\nWrite a comprehensive, well-organized response.")
    ])

    response = await llm.ainvoke(prompt.format_messages(
        task=state["task_description"],
        research=state.get("research_output", "")
    ))

    logger.info(f'{{"run_id":"{run_id}","agent":"writer","duration_ms":{int((time.time()-start)*1000)}}}')
    return {**state, "draft_output": response.content}


async def coder_node(state: dict) -> dict:
    run_id = state["run_id"]
    task = state["task_description"]

    needs_code = any(kw in task.lower() for kw in ["code", "script", "function", "algorithm", "data", "chart", "analyze"])
    if not needs_code:
        return {**state, "code_output": None}

    start = time.time()
    logger.info(f'{{"run_id":"{run_id}","agent":"coder"}}')

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a senior software engineer. Write clean, well-commented code to support the task. Include error handling."),
        ("human", "Task: {task}\n\nContext from writer:\n{draft}\n\nProvide relevant code with explanation.")
    ])

    response = await llm.ainvoke(prompt.format_messages(
        task=task,
        draft=state.get("draft_output", "")
    ))

    logger.info(f'{{"run_id":"{run_id}","agent":"coder","duration_ms":{int((time.time()-start)*1000)}}}')
    return {**state, "code_output": response.content}


async def critic_node(state: dict) -> dict:
    run_id = state["run_id"]
    start = time.time()
    logger.info(f'{{"run_id":"{run_id}","agent":"critic"}}')

    combined = f"""
DRAFT OUTPUT:
{state.get("draft_output", "")}

CODE OUTPUT:
{state.get("code_output", "N/A")}
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a quality critic. Evaluate the output on these dimensions:
- Completeness (addresses the task fully)
- Accuracy (factually correct based on research)
- Clarity (well-structured, readable)
- Relevance (stays on topic)

Respond ONLY in this format:
SCORE: <0.0-1.0>
FEEDBACK: <one paragraph of specific, actionable feedback>"""),
        ("human", "Original task: {task}\n\nOutput to review:\n{output}")
    ])

    response = await llm_critic.ainvoke(prompt.format_messages(
        task=state["task_description"],
        output=combined
    ))

    content = response.content
    score = 0.75
    feedback = content

    try:
        for line in content.split("\n"):
            if line.startswith("SCORE:"):
                score = float(line.replace("SCORE:", "").strip())
            if line.startswith("FEEDBACK:"):
                feedback = line.replace("FEEDBACK:", "").strip()
    except ValueError:
        pass

    logger.info(f'{{"run_id":"{run_id}","agent":"critic","score":{score},"duration_ms":{int((time.time()-start)*1000)}}}')
    return {**state, "critic_score": score, "critic_feedback": feedback}
