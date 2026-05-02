# Oracle Integration Copilot — Build Requirements

## Context

I'm interviewing for a **Junior AI Consultant** role at Capgemini on the Oracle Cloud + AI engineering team. The role is heavy on Oracle Fusion Cloud integrations (Financials, SCM, HCM), Oracle Integration Cloud (OIC), REST/SOAP, and **using Claude Code as a daily driver for AI-assisted development**.

I'm building this project Friday evening through Sunday night and sharing the GitHub repo with the interviewers before Wednesday's interview. The repo itself is the artifact — README, commits, and code quality all matter.

## The Project

**Oracle Integration Copilot**: a Python tool that takes a plain-English integration requirement and produces a draft Oracle Integration Cloud (OIC) integration design — endpoints, data mappings, transformation logic, error handling, and a sample REST payload. It uses retrieval-augmented generation (RAG) over Oracle's public integration documentation plus a small curated example set.

### Example interaction

**Input** (plain English):
> "Every night at 2am, pull new hires from Workday and create employee records in Oracle HCM. Skip contractors. Send a Slack alert if any record fails."

**Output** (structured Markdown spec):
- Integration pattern recommendation (Scheduled Orchestration)
- Source: Workday REST `/workers` endpoint with filter
- Target: Oracle HCM `workersV2` REST endpoint
- Field-level mapping table (source field → target field → transformation)
- Filter logic (`workerType != 'Contractor'`)
- Error handling block (fault handler → Slack notification)
- Sample request/response JSON
- A "things a senior would double-check" section

## Why this project (the pitch)

It hits five JD bullets at once: Oracle Fusion + OIC awareness, REST/JSON/XML fluency, Python, AI-assisted development, and POC/MVP work. It also reuses the exact stack from my Incedo internship (LangChain + FAISS + RAG), so the interview narrative is clean: *"At Incedo I built a RAG chatbot for customer queries; this weekend I built one for Oracle integration design."*

I do **not** have an Oracle license. The whole project must run locally against public docs and mock endpoints. **Do not invent things that require a real Oracle environment.**

---

## Hard Constraints

1. **Python 3.11+**, single repo, runs locally with `pip install -r requirements.txt` and `python -m copilot`.
2. **No Oracle license required.** All Oracle interactions are mocked or come from public documentation.
3. **Stack must include**: LangChain, FAISS (vector store), an embeddings model, an LLM (Claude via Anthropic API by default; the user has an API key), Pydantic for output schemas.
4. **Two interfaces**: a CLI (`python -m copilot "my requirement"`) AND a minimal Streamlit web UI (`streamlit run app.py`). Web UI is for the demo; CLI is for serious users.
5. **Reproducible.** A fresh clone + 3 commands should get it running. Document this clearly in the README.
6. **Cost-aware.** First run builds the FAISS index from cached docs in `data/oracle_docs/`. Subsequent runs load from disk. Don't re-embed on every run.
7. **Tests.** At minimum, pytest unit tests for the parsing layer, the retrieval layer (with mock embeddings), and the output schema validation. Aim for >70% coverage on `copilot/` (excluding the LLM call itself).
8. **No secrets in the repo.** API keys come from `.env` (use `python-dotenv`). Include `.env.example`.

---

## Architecture

```
oracle-integration-copilot/
├── README.md                  # The thing the interviewer reads first
├── CLAUDE.md                  # Project rules for Claude Code (provided)
├── REQUIREMENTS.md            # This file
├── pyproject.toml             # or requirements.txt — pick one, prefer pyproject
├── .env.example
├── .gitignore
├── app.py                     # Streamlit demo UI
├── copilot/
│   ├── __init__.py
│   ├── __main__.py            # CLI entry point
│   ├── config.py              # env loading, model config
│   ├── ingest.py              # build FAISS index from data/oracle_docs/
│   ├── retriever.py           # RAG retrieval logic
│   ├── parser.py              # parses NL requirement → structured intent (Pydantic)
│   ├── designer.py            # the main agent: intent + retrieved context → spec
│   ├── schemas.py             # Pydantic models for IntegrationIntent, IntegrationSpec
│   ├── prompts/
│   │   ├── parser.txt
│   │   ├── designer.txt
│   │   └── critic.txt         # optional self-review pass
│   └── renderers/
│       └── markdown.py        # IntegrationSpec → polished markdown
├── data/
│   ├── oracle_docs/           # cached public docs (committed)
│   │   ├── oic_patterns.md
│   │   ├── hcm_rest_workers.md
│   │   ├── erp_rest_invoices.md
│   │   └── ... (10–20 curated docs)
│   └── examples/              # 3–5 worked examples (input → output) for few-shot
│       ├── workday_to_hcm.md
│       ├── coupa_to_erp.md
│       └── salesforce_to_erp.md
├── tests/
│   ├── test_parser.py
│   ├── test_retriever.py
│   ├── test_schemas.py
│   └── fixtures/
└── docs/
    └── architecture.md        # one-page diagram + design choices
```

---

## Component Specs

### `schemas.py` — Pydantic models

Define these models. They're the contract between every layer.

**`IntegrationIntent`** (parser output):
- `pattern`: Literal["scheduled", "event_driven", "request_response", "file_based"]
- `source_system`: str (e.g., "Workday", "Salesforce")
- `target_system`: str (e.g., "Oracle HCM", "Oracle ERP")
- `objects`: list[str] (e.g., ["worker", "address"])
- `schedule`: Optional[str] (cron-like or natural)
- `filters`: list[str]
- `notifications`: list[str]
- `raw_requirement`: str

**`FieldMapping`**:
- `source_field`: str
- `target_field`: str
- `transformation`: Optional[str]  # e.g., "uppercase", "date format YYYY-MM-DD"
- `required`: bool
- `notes`: Optional[str]

**`IntegrationSpec`** (designer output):
- `title`: str
- `pattern`: str
- `source`: dict (system, endpoint, auth, sample_payload)
- `target`: dict (system, endpoint, auth, sample_payload)
- `mappings`: list[FieldMapping]
- `filters`: list[str]
- `error_handling`: list[str]
- `monitoring`: list[str]
- `assumptions`: list[str]   # what the AI guessed and the engineer should verify
- `open_questions`: list[str]
- `references`: list[str]    # URLs/doc names cited from RAG

### `parser.py`

One function: `parse_requirement(text: str) -> IntegrationIntent`.

Uses an LLM call with a strict JSON-mode prompt and Pydantic validation. If parsing fails, retry once with the validation error appended to the prompt. After the second failure, raise a clear exception.

### `ingest.py`

- Reads every `.md` file in `data/oracle_docs/`.
- Chunks by heading (use LangChain's `MarkdownHeaderTextSplitter`), then by ~800 chars with 150 overlap.
- Embeds with `sentence-transformers/all-MiniLM-L6-v2` by default (free, local) — but make the embedding model swappable via config so OpenAI/Voyage embeddings work too.
- Persists FAISS index to `data/index/`.
- Skips ingestion if index exists and source files haven't changed (use a hash file).

### `retriever.py`

- Loads the FAISS index.
- `retrieve(intent: IntegrationIntent, k: int = 6) -> list[Document]`
- Builds the query from intent fields, not just raw text — e.g., `"OIC {pattern} {source_system} to {target_system} {objects}"`.
- Returns documents with source metadata so the designer can cite them.

### `designer.py`

Main function: `design(intent: IntegrationIntent) -> IntegrationSpec`.

1. Retrieves relevant docs.
2. Pulls 1–2 most-similar few-shot examples from `data/examples/`.
3. Calls the LLM with the designer prompt (intent + retrieved docs + examples).
4. Validates output against `IntegrationSpec`.
5. Optionally runs a critic pass (`prompts/critic.txt`) that re-reads the spec and adds items to `open_questions` and `assumptions`. Make this toggleable via `--critic` flag (default on).

### `renderers/markdown.py`

`render(spec: IntegrationSpec) -> str`. Produces a polished Markdown doc with:
- Title and TL;DR
- A Mermaid sequence diagram of the integration flow
- Mapping table (proper Markdown table)
- Sample JSON payloads in fenced code blocks
- Assumptions and open questions in a callout
- Sources

### `app.py` (Streamlit)

Two-pane layout: requirement textbox on the left, rendered spec on the right. A spinner during generation. A "Download as Markdown" button. **This is what the interviewer will see in the demo video.** Keep it tasteful — neutral palette, no emoji explosion, monospace where appropriate.

### CLI (`__main__.py`)

```
python -m copilot "Sync Workday hires to Oracle HCM nightly" \
  --output spec.md \
  --no-critic \
  --k 8
```

Flags: `--output`, `--no-critic`, `--k` (retrieval count), `--model`, `--verbose`.

---

## Data — what to put in `data/oracle_docs/`

Curate ~10–20 short Markdown files distilled from **public** Oracle sources. Cite the URL at the top of each file. Suggested coverage:

- OIC integration patterns overview (scheduled, app-driven, event, file-based)
- OIC fault handling and error notifications
- Oracle HCM REST: `workers`, `workRelationships`, `assignments`
- Oracle ERP REST: `invoices`, `suppliers`, `purchaseOrders`
- Oracle SCM REST: `items`, `inventoryOnhandQuantities`
- OIC connection types (REST adapter, SOAP adapter, FTP adapter)
- OIC orchestration vs. app-driven flows
- Common transformation patterns (XSLT basics, lookups, expressions)
- One on Oracle Cloud Infrastructure auth basics (OAuth client credentials)
- One on idempotency / retry patterns

You don't need to scrape — manually summarize each topic in 200–500 words with the source URL. **This is part of the value:** it shows you read the docs and can distill them.

For `data/examples/`, write 3 full input→output examples by hand (or generate them and hand-edit). They serve as few-shot anchors and as documentation for the interviewer.

---

## What "impressive" looks like in this repo

The interviewer will likely spend **5–10 minutes** in the repo. Optimize for that window:

1. **README that sells the project in 30 seconds.** Hero GIF/screenshot of the Streamlit UI generating a spec, then a "Why I built this" paragraph that names Capgemini's Oracle practice explicitly. Then quickstart, then architecture diagram.
2. **A clear architecture doc** (`docs/architecture.md`) with one diagram showing: NL input → Parser → Retriever ⇄ FAISS → Designer → Critic → Renderer → Output. Include a paragraph on each design choice and what you'd do differently with more time.
3. **Commit history that tells a story.** Don't squash everything into one commit. Commits like `feat: add markdown renderer with mermaid diagrams`, `test: cover parser retry logic`, `docs: add architecture overview` show engineering maturity.
4. **A "Limitations & Future Work" section** in the README — interviewers love candidates who know what their thing *can't* do. Examples: "no live OIC deployment", "doesn't yet handle SOAP-only legacy adapters", "could add a runtime adapter that posts the generated spec to a real OIC instance via the OIC REST API".
5. **One genuinely clever thing.** Pick *one*: (a) the critic pass that surfaces assumptions, (b) a Mermaid diagram auto-generated from the spec, (c) a `--diff` mode that compares two specs, or (d) an eval harness that runs the 3 example inputs and checks output structure. Don't try to do all four — pick one and polish it.
6. **A 90-second demo video** linked in the README (Loom or a `.mp4` in the repo). Capgemini interviewers may not run the code; the video guarantees they see it work.

---

## What NOT to do

- **No fake Oracle credentials, no fake OIC API calls that look real.** Be honest in code comments and docs about what's mocked.
- **No 50-file boilerplate dump.** If a file isn't needed, don't create it. Engineers spot padding instantly.
- **No emoji-laden README.** Clean, professional, technical tone. One screenshot, one diagram, prose.
- **No `print()` debugging left in code.** Use `logging` with a configurable level.
- **No committed `.env`, no committed FAISS index larger than 10MB, no committed `__pycache__`.**
- **No silent failures.** If retrieval returns nothing, the designer should say so in `open_questions`, not hallucinate Oracle endpoints.
- **No claim of Oracle expertise I don't have.** The README should frame this as "AI-assisted exploration of OIC integration design" — accurate and honest.

---

## Build Order (recommended)

Friday night:
1. Scaffold repo, `pyproject.toml`, `.gitignore`, `README.md` skeleton, `CLAUDE.md`.
2. Write `schemas.py` first — it's the contract.
3. Hand-write 3 docs in `data/oracle_docs/` and 1 example in `data/examples/` to unblock everything else.
4. Build `ingest.py` and verify the FAISS index loads.

Saturday:
5. Build `parser.py` with retry logic + tests.
6. Build `retriever.py` + tests.
7. Build `designer.py` end-to-end with a single hand-crafted prompt.
8. Build `renderers/markdown.py`.
9. CLI (`__main__.py`) — get the full pipeline working from the terminal.
10. Fill out the rest of `data/oracle_docs/` (target: 10+ docs) and `data/examples/` (target: 3+ examples).

Sunday:
11. Streamlit UI.
12. The "one clever thing" (recommendation: the critic pass — it's the best interview talking point).
13. Architecture diagram + `docs/architecture.md`.
14. README polish, screenshot, demo video.
15. Final test pass, push, share repo.

---

## Final acceptance checklist

Before pushing the final commit, verify:

- [ ] `git clone` + `pip install -e .` + `cp .env.example .env` + edit + `python -m copilot "test"` works on a fresh checkout.
- [ ] Streamlit app loads and renders a spec for at least 3 different inputs without errors.
- [ ] `pytest` passes; coverage report shows >70% on `copilot/`.
- [ ] README has: hero image, 30-second pitch, quickstart, architecture diagram, limitations, demo video link.
- [ ] No secrets, no `__pycache__`, no oversized binaries committed.
- [ ] Commit history reads like a real engineer built this — not one giant `Initial commit`.
- [ ] At least one file in `data/oracle_docs/` cites a real Oracle URL I actually read.
