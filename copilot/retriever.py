from __future__ import annotations

import logging

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from copilot.config import EMBEDDING_MODEL, FAISS_INDEX_PATH
from copilot.schemas import IntegrationIntent

logger = logging.getLogger(__name__)

_vectorstore: FAISS | None = None


def _get_vectorstore() -> FAISS:
    global _vectorstore
    if _vectorstore is None:
        from copilot.ingest import build_index
        _vectorstore = build_index()
    return _vectorstore


def retrieve(intent: IntegrationIntent, k: int = 6) -> list[Document]:
    """Return the k most relevant OIC doc chunks for the given intent."""
    query = (
        f"OIC {intent.pattern} integration "
        f"{intent.source_system} to {intent.target_system} "
        f"{' '.join(intent.objects)}"
    )
    logger.debug("Retrieval query: %r", query)

    docs = _get_vectorstore().similarity_search(query, k=k)
    logger.info("Retrieved %d document chunks", len(docs))
    return docs
