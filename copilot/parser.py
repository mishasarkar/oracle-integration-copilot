from __future__ import annotations

import json
import logging
from pathlib import Path

from anthropic import Anthropic

from copilot.config import CLAUDE_MODEL
from copilot.schemas import IntegrationIntent

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent / "prompts" / "parser.txt"
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


def parse_requirement(text: str) -> IntegrationIntent:
    """Parse a plain-English integration requirement into a structured IntegrationIntent."""
    schema = IntegrationIntent.model_json_schema()
    base_prompt = _PROMPT_PATH.read_text(encoding="utf-8").format(
        schema=json.dumps(schema, indent=2),
        requirement=text,
    )
    prompt = base_prompt

    client = _get_client()
    last_error: Exception | None = None

    for attempt in range(2):
        try:
            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = _extract_json(response.content[0].text)
            data = json.loads(raw)
            data["raw_requirement"] = text
            return IntegrationIntent(**data)
        except Exception as exc:
            last_error = exc
            if attempt == 0:
                logger.warning("Parse attempt 1 failed (%s); retrying with error context.", exc)
                prompt = base_prompt + f"\n\nPrevious attempt failed with: {exc}. Ensure output is valid JSON matching the schema."
            else:
                raise ValueError(
                    f"Failed to parse requirement after 2 attempts: {exc}"
                ) from exc

    raise ValueError(f"Failed to parse requirement: {last_error}")
