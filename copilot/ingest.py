import hashlib
import logging
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from copilot.config import EMBEDDING_MODEL, FAISS_INDEX_PATH, ORACLE_DOCS_PATH

logger = logging.getLogger(__name__)

_HEADERS_TO_SPLIT_ON = [
    ("#", "h1"),
    ("##", "h2"),
    ("###", "h3"),
]


def _compute_docs_hash(docs_path: Path) -> str:
    hasher = hashlib.sha256()
    for md_file in sorted(docs_path.glob("*.md")):
        hasher.update(md_file.read_bytes())
    return hasher.hexdigest()


def _index_is_current(index_path: Path, docs_hash: str) -> bool:
    hash_file = index_path / "source_hash.txt"
    if not (index_path / "index.faiss").exists():
        return False
    if not hash_file.exists():
        return False
    return hash_file.read_text().strip() == docs_hash


def build_index(force: bool = False) -> FAISS:
    """Build (or load from cache) the FAISS vector index from oracle_docs."""
    docs_path = Path(ORACLE_DOCS_PATH)
    index_path = Path(FAISS_INDEX_PATH)

    docs_hash = _compute_docs_hash(docs_path)

    if not force and _index_is_current(index_path, docs_hash):
        logger.info("FAISS index is up to date — loading from %s", index_path)
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        return FAISS.load_local(
            str(index_path), embeddings, allow_dangerous_deserialization=True
        )

    logger.info("Building FAISS index from %s", docs_path)

    md_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=_HEADERS_TO_SPLIT_ON, strip_headers=False
    )
    char_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)

    all_chunks = []
    for md_file in sorted(docs_path.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        header_chunks = md_splitter.split_text(text)
        chunks = char_splitter.split_documents(header_chunks)
        for chunk in chunks:
            chunk.metadata["source"] = md_file.name
        all_chunks.extend(chunks)
        logger.debug("  %s → %d chunks", md_file.name, len(chunks))

    if not all_chunks:
        raise ValueError(f"No markdown documents found in {docs_path}")

    logger.info("Embedding %d chunks with %s …", len(all_chunks), EMBEDDING_MODEL)
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vectorstore = FAISS.from_documents(all_chunks, embeddings)

    index_path.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(index_path))
    (index_path / "source_hash.txt").write_text(docs_hash)

    logger.info("FAISS index saved to %s (%d chunks)", index_path, len(all_chunks))
    return vectorstore
