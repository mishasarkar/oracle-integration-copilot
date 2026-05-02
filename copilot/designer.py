from __future__ import annotations

import json
import logging
from pathlib import Path

from anthropic import Anthropic

from copilot.config import CLAUDE_MODEL
from copilot.retriever import retrieve
from copilot.schemas import IntegrationIntent, IntegrationSpec

logger = logging.getLogger(__name__)

_DESIGNER_PROMPT = Path(__file__).parent / "prompts" / "designer.txt"
_CRITIC_PROMPT = Path(__file__).parent / "prompts" / "critic.txt"
_EXAMPLES_DIR = Path(__file__).parent.parent / "data" / "examples"

_client: Anthropic | None = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic()
    return _client


def _extract_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _load_examples(n: int = 2) -> str:
    parts = []
    for path in sorted(_EXAMPLES_DIR.glob("*.md"))[:n]:
        parts.append(f"### {path.stem.replace('_', ' ').title()}\n{path.read_text('utf-8')}")
    return "\n\n---\n\n".join(parts) if parts else "(no examples available)"


def design(intent: IntegrationIntent, k: int = 6, use_critic: bool = True) -> IntegrationSpec:
    """Retrieve relevant docs, call the LLM, validate and return an IntegrationSpec."""
    docs = retrieve(intent, k=k)

    if not docs:
        logger.warning("No documents retrieved — spec will rely entirely on LLM knowledge.")

    context = "\n\n".join(
        f"**[{doc.metadata.get('source', 'unknown')}]**\n{doc.page_content}"
        for doc in docs
    )
    references = sorted({doc.metadata.get("source", "unknown") for doc in docs})

    examples = _load_examples()
    schema = IntegrationSpec.model_json_schema()

    prompt = _DESIGNER_PROMPT.read_text("utf-8").format(
        intent=intent.model_dump_json(indent=2),
        context=context or "(no relevant documentation retrieved)",
        examples=examples,
        schema=json.dumps(schema, indent=2),
    )

    client = _get_client()
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = _extract_json(response.content[0].text)
    data = json.loads(raw)

    if not data.get("references"):
        data["references"] = references
    else:
        data["references"] = list(set(data["references"]) | set(references))

    # Drop any mappings the LLM produced with null required fields
    if "mappings" in data:
        data["mappings"] = [
            m for m in data["mappings"]
            if m.get("source_field") and m.get("target_field")
        ]

    spec = IntegrationSpec(**data)

    if use_critic:
        spec = _run_critic(spec, client)

    return spec


def _run_critic(spec: IntegrationSpec, client: Anthropic) -> IntegrationSpec:
    """Run a second LLM pass that surfaces hidden assumptions and open questions."""
    prompt = _CRITIC_PROMPT.read_text("utf-8").format(
        spec=spec.model_dump_json(indent=2)
    )

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    try:
        additions = json.loads(_extract_json(response.content[0].text))
        spec.assumptions.extend(additions.get("additional_assumptions", []))
        spec.open_questions.extend(additions.get("additional_open_questions", []))
    except Exception as exc:
        logger.warning("Critic pass could not be parsed (%s); skipping additions.", exc)

    return spec
