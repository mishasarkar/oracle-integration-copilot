# Oracle Integration Copilot — Claude Code Project Rules

## What this project is

A RAG-powered Python tool that converts plain-English Oracle Integration Cloud (OIC)
requirements into structured integration design specs. It uses LangChain + FAISS for
retrieval and Claude (Anthropic API) for generation.

## Architecture

```
NL Requirement
  → copilot/parser.py       (LLM: extract IntegrationIntent)
  → copilot/retriever.py    (FAISS: retrieve relevant OIC docs)
  → copilot/designer.py     (LLM: generate IntegrationSpec + optional critic pass)
  → copilot/renderers/markdown.py  (render to polished Markdown)
```

## Key conventions

- **Pydantic schemas in `copilot/schemas.py` are the contract** between every layer.
  Change them carefully — tests and prompts depend on them.
- **No Oracle credentials, no live OIC calls.** All Oracle interactions are mocked or
  described from public docs. Be explicit in comments and docs about what's mocked.
- **FAISS index lives in `data/index/` and is gitignored.** It is rebuilt automatically
  on first run if missing. Do not commit it.
- **All paths are resolved relative to project root** via `BASE_DIR` in `config.py`.
  Never use `os.getcwd()` or bare relative paths in module code.
- **Logging over print.** Use `logging.getLogger(__name__)` everywhere.
- **Prompts are in `copilot/prompts/*.txt`**, not hardcoded in Python files. Keep them
  separately editable.

## Dev workflow

```bash
pip install -e ".[dev]"
cp .env.example .env  # add your ANTHROPIC_API_KEY
python -m copilot "Sync Workday hires to Oracle HCM nightly"
pytest
```

## What NOT to do

- Do not add fake Oracle API calls that look like production code.
- Do not re-embed on every run — the hash-based cache in `ingest.py` exists for a reason.
- Do not mock the Anthropic client in production code paths.
- Do not commit `.env`, `data/index/`, or `__pycache__`.
