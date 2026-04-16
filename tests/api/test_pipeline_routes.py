import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from types import SimpleNamespace

from api.main import app

# We won't use AsyncClient here just to do a simple sync TestClient check
client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}

@patch("api.routes.memory.get_memory")
def test_read_artifact_not_found(mock_get_memory):
    # Mock the singleton
    mock_memory = MagicMock()
    mock_memory.read_artifact.return_value = {"exists": False}
    mock_get_memory.return_value = mock_memory
    
    response = client.get("/memory/artifact/week_1/01_research/missing.md")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

@patch("api.routes.memory.get_memory")
def test_read_artifact_success(mock_get_memory):
    mock_memory = MagicMock()
    mock_memory.read_artifact.return_value = {
        "exists": True,
        "content": "# Hello",
        "metadata": {"author": "system"}
    }
    mock_get_memory.return_value = mock_memory
    
    response = client.get("/memory/artifact/week_1/01_research/found.md")
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "# Hello"
    assert data["metadata"]["author"] == "system"


class _FakeGraph:
    def __init__(self, snapshot_values: dict):
        self._snapshot_values = snapshot_values

    def get_state(self, _config):
        return SimpleNamespace(values=self._snapshot_values)

    def update_state(self, _config, values, **_kwargs):
        merged = dict(self._snapshot_values)
        merged.update(values or {})
        self._snapshot_values = merged
        return _config

    async def ainvoke(self, update_data, config=None, **_kwargs):
        if update_data:
            merged = dict(self._snapshot_values)
            merged.update(update_data)
            self._snapshot_values = merged
        return dict(self._snapshot_values)


def _build_state_for_feedback() -> dict:
    return {
        "week_id": "2026-W16",
        "pipeline_status": "planning",
        "weekly_plan": [
            {
                "day": "monday",
                "date": "2026-04-20",
                "topic_id": "topic_a",
                "topic_title": "Topic A",
                "content_format": "carousel",
                "content_intent": "reach",
                "reasoning": "",
            },
            {
                "day": "tuesday",
                "date": "2026-04-21",
                "topic_id": "topic_b",
                "topic_title": "Topic B",
                "content_format": "reel",
                "content_intent": "engagement",
                "reasoning": "",
            },
        ],
        "selected_topics": [],
        "topic_queue": [],
        "topic_index": 0,
        "topic_total": 0,
        "raw_deep_research": {},
        "deep_research": {},
        "content": {},
        "pending_topic_id": "topic_a",
        "human_action_required": True,
        "human_action_type": "select_topics",
    }


@patch("api.routes.pipeline.get_node_context")
@patch("api.routes.pipeline.build_pipeline_graph")
def test_feedback_select_topics_requires_non_empty(mock_build_graph, _mock_get_context):
    mock_build_graph.return_value = _FakeGraph(_build_state_for_feedback())

    response = client.post(
        "/pipeline/2026-W16/feedback",
        json={"action": "select_topics", "selected_topics": []},
    )

    assert response.status_code == 422
    assert "cannot be empty" in response.json()["detail"]


@patch("api.routes.pipeline.get_node_context")
@patch("api.routes.pipeline.build_pipeline_graph")
def test_feedback_select_topics_rejects_unknown_topics(mock_build_graph, _mock_get_context):
    mock_build_graph.return_value = _FakeGraph(_build_state_for_feedback())

    response = client.post(
        "/pipeline/2026-W16/feedback",
        json={"action": "select_topics", "selected_topics": ["topic_x"]},
    )

    assert response.status_code == 422
    assert "Invalid selected_topics" in response.json()["detail"]


@patch("api.routes.pipeline.get_node_context")
@patch("api.routes.pipeline.build_pipeline_graph")
def test_feedback_select_topics_success(mock_build_graph, _mock_get_context):
    mock_build_graph.return_value = _FakeGraph(_build_state_for_feedback())

    response = client.post(
        "/pipeline/2026-W16/feedback",
        json={"action": "select_topics", "selected_topics": ["topic_b", "topic_a"]},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["state"]["selected_topics"] == ["topic_b", "topic_a"]
    assert data["state"]["topic_queue"] == ["topic_b", "topic_a"]
    assert data["state"]["pending_topic_id"] == "topic_b"
    assert data["state"]["topic_total"] == 2


@patch("api.routes.pipeline.get_node_context")
@patch("api.routes.pipeline.build_pipeline_graph")
def test_feedback_supply_deep_research_rejects_topic_mismatch(mock_build_graph, _mock_get_context):
    state = _build_state_for_feedback()
    state["human_action_type"] = "paste_deep_research"
    mock_build_graph.return_value = _FakeGraph(state)

    response = client.post(
        "/pipeline/2026-W16/feedback",
        json={
            "action": "supply_deep_research",
            "topic_id": "topic_b",
            "deep_research_text": "External deep research text",
        },
    )

    assert response.status_code == 422
    assert "does not match pending_topic_id" in response.json()["detail"]


@patch("api.routes.pipeline.get_node_context")
@patch("api.routes.pipeline.build_pipeline_graph")
def test_feedback_supply_deep_research_success(mock_build_graph, _mock_get_context):
    state = _build_state_for_feedback()
    state["human_action_type"] = "paste_deep_research"
    mock_build_graph.return_value = _FakeGraph(state)

    response = client.post(
        "/pipeline/2026-W16/feedback",
        json={
            "action": "supply_deep_research",
            "topic_id": "topic_a",
            "deep_research_text": "External deep research text",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["state"]["raw_deep_research"]["topic_a"] == "External deep research text"
