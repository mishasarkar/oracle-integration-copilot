# Architecture Overview

## System Diagram

```
┌──────────────────────────────────────────────────────────┐
│                    User Interface                         │
│          CLI (python -m copilot "...")                    │
│          Streamlit UI (streamlit run app.py)              │
└─────────────────────────┬────────────────────────────────┘
                          │ plain-English requirement
                          ▼
              ┌───────────────────────┐
              │      parser.py        │
              │  LLM → JSON → Pydantic│
              │  IntegrationIntent    │
              └───────────┬───────────┘
                          │ structured intent
          ┌───────────────┼───────────────────┐
          │               │                   │
          ▼               ▼                   │
  ┌──────────────┐  ┌──────────────┐          │
  │ retriever.py │  │ data/examples│          │
  │ FAISS search │  │ few-shot     │          │
  └──────┬───────┘  └──────┬───────┘          │
         │                 │                  │
         │ top-k chunks    │ 1-2 examples      │
         └────────┬────────┘                  │
                  │                           │
                  ▼                           │
         ┌────────────────┐◄──────────────────┘
         │  designer.py   │
         │  LLM call with │
         │  intent + docs │
         │  + examples    │
         └────────┬───────┘
                  │ IntegrationSpec (draft)
                  ▼
         ┌────────────────┐
         │  critic pass   │  (optional, --no-critic to skip)
         │  Second LLM    │
         │  adds items to │
         │  assumptions + │
         │  open_questions│
         └────────┬───────┘
                  │ IntegrationSpec (final)
                  ▼
         ┌────────────────────────┐
         │ renderers/markdown.py  │
         │ → Mermaid diagram      │
         │ → Field mapping table  │
         │ → JSON payloads        │
         │ → Assumptions callout  │
         └────────────────────────┘
```

## Component Design Choices

### Pydantic Schemas as Contract (`schemas.py`)

Every layer speaks the same language: `IntegrationIntent` (parser output) and `IntegrationSpec` (designer output). This means:
- The parser is independently testable with no dependency on the designer
- Prompt changes only affect the layer that owns the prompt, not downstream code
- Adding a new output field is one change in `schemas.py` and one in the prompt — nothing else

Alternative considered: free-form dict passing between layers. Rejected because validation errors surface late and are harder to debug.

### Local Embeddings + FAISS (`ingest.py`)

`sentence-transformers/all-MiniLM-L6-v2` runs entirely locally — no API cost, no latency, no rate limits. The model is ~90 MB and produces 384-dimensional vectors, which is more than sufficient for a 10–20 doc corpus.

FAISS is persisted to disk and reloaded on subsequent runs using a SHA-256 hash of the source documents. If docs change, the index is automatically rebuilt. If not, startup is under 1 second.

Alternative considered: ChromaDB (simpler API). Rejected because FAISS is faster for local use and matches the internship stack mentioned in the pitch.

### Retrieval Query Construction (`retriever.py`)

The retrieval query is built from intent fields, not the raw requirement text:
```python
query = f"OIC {intent.pattern} {intent.source_system} to {intent.target_system} {' '.join(intent.objects)}"
```

This produces more precise retrieval than using the raw text. A requirement like "Every night at 2am, pull new hires from Workday..." contains time references and business context that would dilute the semantic signal. The structured intent (`scheduled`, `Workday`, `Oracle HCM`, `worker`) maps cleanly to the terminology used in the oracle docs.

### Parser Retry Logic (`parser.py`)

The parser makes up to 2 LLM calls. On the first failure (invalid JSON or Pydantic validation error), the error message is appended to the prompt and a second call is made. This handles cases where the LLM wraps its output in a code fence or includes a preamble.

After 2 failures, a `ValueError` is raised with a clear message. The integration test covers both the success-on-retry path and the double-failure path.

Alternative considered: structured outputs / JSON mode in the Anthropic API. Decided against it to keep the solution model-agnostic and to avoid vendor lock-in on a specific API feature.

### Critic Pass (`designer.py`)

The critic is a second LLM call that reads the full generated spec and adds items to `assumptions` and `open_questions`. It is the "one clever thing" in this project.

The design rationale: a single LLM call tends to be overconfident. The designer prompt asks for a complete spec, which biases the model toward filling in gaps with guesses. The critic prompt asks a *different question* — "what is wrong or missing?" — which activates a different cognitive mode. In practice, the critic reliably surfaces 3–5 additional assumptions that the designer omitted.

The critic is on by default but can be disabled with `--no-critic` for faster iteration during development.

### Renderer (`renderers/markdown.py`)

The renderer is a pure function: `IntegrationSpec → str`. It has no LLM calls and is deterministic. This makes it fast to iterate on and easy to test.

The Mermaid sequence diagram is generated programmatically from the spec's `pattern` field, covering all four integration patterns with realistic actor names and message flows.

Alternative considered: Jinja2 template for the renderer. Decided against it because the logic is simple enough that a Python function is easier to read and modify.

## What I Would Do Differently With More Time

1. **Eval harness.** Run the 3 example inputs through the pipeline and score the output structure (field coverage, mapping count, assumption count). This would let me tune prompts with confidence.
2. **Streaming in the Streamlit UI.** Stream the LLM output token by token instead of waiting for the full response. Reduces perceived latency significantly for large specs.
3. **OIC REST Management API integration.** Oracle exposes an API for managing integrations. With an OIC instance, you could POST the generated spec and have it create a draft integration automatically — closing the loop from design to artefact.
4. **Larger RAG corpus.** The current 10 docs cover common patterns. Adding SOAP adapter docs, HCM Payroll, Oracle Incentive Compensation, and OCI Streaming would meaningfully improve spec quality for less common integrations.
5. **Embedding model evaluation.** Compare `all-MiniLM-L6-v2` against a domain-tuned model (e.g., `voyage-code-2` or `text-embedding-3-small`) on retrieval precision for OIC-specific queries.
