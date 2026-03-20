import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from graph.workflow import build_workflow, route_after_critic, AgentState


def make_state(**kwargs) -> AgentState:
    base = {
        "task_description": "Test task",
        "task_id": "task-123",
        "run_id": "run-456",
        "research_output": None,
        "draft_output": None,
        "code_output": None,
        "critic_score": None,
        "critic_feedback": None,
        "revision_count": 0,
        "final_output": None,
    }
    return {**base, **kwargs}


class TestRoutingLogic:
    def test_routes_to_finalize_when_score_high(self):
        state = make_state(critic_score=0.85, revision_count=0)
        assert route_after_critic(state) == "finalize"

    def test_routes_to_researcher_when_score_low(self):
        state = make_state(critic_score=0.6, revision_count=0)
        assert route_after_critic(state) == "researcher"

    def test_routes_to_finalize_after_max_revisions(self):
        state = make_state(critic_score=0.5, revision_count=3)
        assert route_after_critic(state) == "finalize"

    def test_boundary_score_exactly_threshold(self):
        state = make_state(critic_score=0.8, revision_count=0)
        assert route_after_critic(state) == "finalize"

    def test_revision_count_increments_on_retry(self):
        state = make_state(critic_score=0.6, revision_count=1)
        result = route_after_critic(state)
        assert result == "researcher"

    def test_no_infinite_loop_at_revision_limit(self):
        for score in [0.1, 0.3, 0.5, 0.79]:
            state = make_state(critic_score=score, revision_count=3)
            assert route_after_critic(state) == "finalize", \
                f"Should finalize at revision_count=3 regardless of score {score}"


class TestWorkflowBuilds:
    def test_workflow_compiles_without_error(self):
        workflow = build_workflow()
        assert workflow is not None

    def test_workflow_has_expected_nodes(self):
        workflow = build_workflow()
        node_names = set(workflow.nodes.keys())
        expected = {"researcher", "writer", "coder", "critic", "finalize"}
        assert expected.issubset(node_names)


class TestAgentStateDefaults:
    def test_state_has_required_fields(self):
        state = make_state()
        required_keys = [
            "task_description", "task_id", "run_id",
            "revision_count", "research_output", "draft_output",
            "code_output", "critic_score", "final_output"
        ]
        for key in required_keys:
            assert key in state

    def test_revision_count_starts_at_zero(self):
        state = make_state()
        assert state["revision_count"] == 0
