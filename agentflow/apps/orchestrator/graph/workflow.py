from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from agents.researcher import researcher_node
from agents.writer import writer_node
from agents.coder import coder_node
from agents.critic import critic_node


class AgentState(TypedDict):
    task_description: str
    task_id: str
    run_id: str
    research_output: Optional[str]
    draft_output: Optional[str]
    code_output: Optional[str]
    critic_score: Optional[float]
    critic_feedback: Optional[str]
    revision_count: int
    final_output: Optional[str]


def route_after_critic(state: AgentState) -> str:
    """Conditional edge: retry if quality below threshold, else finalize."""
    score = state.get("critic_score", 0.0)
    revisions = state.get("revision_count", 0)

    if score >= 0.8:
        return "finalize"
    if revisions >= 3:
        return "finalize"  # prevent infinite loops
    return "researcher"    # trigger revision with critic feedback


def finalize_node(state: AgentState) -> AgentState:
    return {
        **state,
        "final_output": state.get("draft_output", ""),
    }


def build_workflow() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("researcher", researcher_node)
    graph.add_node("writer", writer_node)
    graph.add_node("coder", coder_node)
    graph.add_node("critic", critic_node)
    graph.add_node("finalize", finalize_node)

    graph.set_entry_point("researcher")
    graph.add_edge("researcher", "writer")
    graph.add_edge("writer", "coder")
    graph.add_edge("coder", "critic")
    graph.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "researcher": "researcher",
            "finalize": "finalize",
        }
    )
    graph.add_edge("finalize", END)

    return graph.compile()
