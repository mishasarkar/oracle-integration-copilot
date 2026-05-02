from unittest.mock import MagicMock, patch

import pytest

from copilot.schemas import IntegrationIntent
from copilot.retriever import retrieve


@pytest.fixture
def workday_hcm_intent():
    return IntegrationIntent(
        pattern="scheduled",
        source_system="Workday",
        target_system="Oracle HCM",
        objects=["worker", "employment"],
        schedule="0 2 * * *",
        filters=["workerType != 'CONTRACTOR'"],
        raw_requirement="Sync Workday hires to Oracle HCM nightly",
    )


@pytest.fixture
def coupa_erp_intent():
    return IntegrationIntent(
        pattern="event_driven",
        source_system="Coupa",
        target_system="Oracle ERP",
        objects=["purchase_order"],
        raw_requirement="Sync Coupa approved POs to Oracle ERP",
    )


def _make_mock_doc(content: str, source: str) -> MagicMock:
    doc = MagicMock()
    doc.page_content = content
    doc.metadata = {"source": source}
    return doc


@patch("copilot.retriever._get_vectorstore")
def test_retrieve_returns_documents(mock_get_vs, workday_hcm_intent):
    mock_doc = _make_mock_doc("OIC scheduled integration pattern for HCM", "oic_patterns.md")
    mock_vs = MagicMock()
    mock_vs.similarity_search.return_value = [mock_doc]
    mock_get_vs.return_value = mock_vs

    docs = retrieve(workday_hcm_intent, k=1)

    assert len(docs) == 1
    assert docs[0].metadata["source"] == "oic_patterns.md"


@patch("copilot.retriever._get_vectorstore")
def test_retrieve_passes_correct_k(mock_get_vs, workday_hcm_intent):
    mock_vs = MagicMock()
    mock_vs.similarity_search.return_value = []
    mock_get_vs.return_value = mock_vs

    retrieve(workday_hcm_intent, k=8)

    mock_vs.similarity_search.assert_called_once()
    _, kwargs = mock_vs.similarity_search.call_args
    assert kwargs.get("k") == 8 or mock_vs.similarity_search.call_args[0][1] == 8


@patch("copilot.retriever._get_vectorstore")
def test_retrieve_query_includes_intent_fields(mock_get_vs, workday_hcm_intent):
    mock_vs = MagicMock()
    mock_vs.similarity_search.return_value = []
    mock_get_vs.return_value = mock_vs

    retrieve(workday_hcm_intent, k=6)

    call_query = mock_vs.similarity_search.call_args[0][0]
    assert "scheduled" in call_query
    assert "Workday" in call_query
    assert "Oracle HCM" in call_query
    assert "worker" in call_query


@patch("copilot.retriever._get_vectorstore")
def test_retrieve_event_driven_query(mock_get_vs, coupa_erp_intent):
    mock_vs = MagicMock()
    mock_vs.similarity_search.return_value = []
    mock_get_vs.return_value = mock_vs

    retrieve(coupa_erp_intent, k=6)

    call_query = mock_vs.similarity_search.call_args[0][0]
    assert "event_driven" in call_query
    assert "Coupa" in call_query
    assert "Oracle ERP" in call_query


@patch("copilot.retriever._get_vectorstore")
def test_retrieve_handles_empty_results(mock_get_vs, workday_hcm_intent):
    mock_vs = MagicMock()
    mock_vs.similarity_search.return_value = []
    mock_get_vs.return_value = mock_vs

    docs = retrieve(workday_hcm_intent, k=6)

    assert docs == []


@patch("copilot.retriever._get_vectorstore")
def test_retrieve_returns_multiple_documents(mock_get_vs, workday_hcm_intent):
    mock_docs = [
        _make_mock_doc("OIC scheduled pattern", "oic_patterns.md"),
        _make_mock_doc("HCM Workers REST API", "hcm_rest_workers.md"),
        _make_mock_doc("OIC fault handling", "oic_fault_handling.md"),
    ]
    mock_vs = MagicMock()
    mock_vs.similarity_search.return_value = mock_docs
    mock_get_vs.return_value = mock_vs

    docs = retrieve(workday_hcm_intent, k=3)

    assert len(docs) == 3
    sources = {d.metadata["source"] for d in docs}
    assert "oic_patterns.md" in sources
    assert "hcm_rest_workers.md" in sources
