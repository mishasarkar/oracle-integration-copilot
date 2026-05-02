import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent

ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
EMBEDDING_MODEL: str = os.getenv(
    "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)
FAISS_INDEX_PATH: str = os.getenv(
    "FAISS_INDEX_PATH", str(BASE_DIR / "data" / "index")
)
ORACLE_DOCS_PATH: str = os.getenv(
    "ORACLE_DOCS_PATH", str(BASE_DIR / "data" / "oracle_docs")
)
