import json
from unittest.mock import MagicMock, patch

import pytest

from copilot.parser import parse_requirement, _extract_json
from copilot.schemas import IntegrationIntent


VALID_INTENT_DATA = {
    "pattern": "scheduled",
    "source_system": "Workday",
    "target_system": "Oracle HCM",
    "objects": ["worker"],
    "schedule": "0 2 * * *",
    "filters": ["workerType != 'CONTRACTOR'"],
    "notifications": ["Slack alert on failure"],
    "raw_requirement": "Every night at 2am, sync Workday hires to Oracle HCM",
}


def _mock_response(text: str) -> MagicMock:
    response = MagicMock()
    response.content = [MagicMock(text=text)]
    return response


class TestExtractJson:
    def test_plain_json_passthrough(self):
        raw = '{"key": "value"}'
        assert _extract_json(raw) == raw

    def test_strips_json_code_fence(self):
        raw = '```json\n{"key": "value"}\n```'
        result = _extract_json(raw)
        assert result == '{"key": "value"}'

    def test_strips_plain_code_fence(self):
        raw = '```\n{"key": "value"}\n```'
        result = _extract_json(raw)
        assert result == '{"key": "value"}'

    def test_strips_surrounding_whitespace(self):
        raw = '  \n{"key": "value"}\n  '
        assert _extract_json(raw).strip() == '{"key": "value"}'


class TestParseRequirement:
    @patch("copilot.parser._get_client")
    def test_success_on_first_attempt(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_response(
            json.dumps(VALID_INTENT_DATA)
        )
        mock_get_client.return_value = mock_client

        intent = parse_requirement("Sync Workday hires to Oracle HCM nightly")

        assert isinstance(intent, IntegrationIntent)
        assert intent.pattern == "scheduled"
        assert intent.source_system == "Workday"
        assert intent.target_system == "Oracle HCM"
        assert mock_client.messages.create.call_count == 1

    @patch("copilot.parser._get_client")
    def test_raw_requirement_overwritten_with_input(self, mock_get_client):
        data = dict(VALID_INTENT_DATA, raw_requirement="something else")
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_response(json.dumps(data))
        mock_get_client.return_value = mock_client

        intent = parse_requirement("My actual requirement text")

        assert intent.raw_requirement == "My actual requirement text"

    @patch("copilot.parser._get_client")
    def test_retries_on_invalid_json(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [
            _mock_response("not valid json {{"),
            _mock_response(json.dumps(VALID_INTENT_DATA)),
        ]
        mock_get_client.return_value = mock_client

        intent = parse_requirement("Sync Workday hires to Oracle HCM nightly")

        assert mock_client.messages.create.call_count == 2
        assert intent.pattern == "scheduled"

    @patch("copilot.parser._get_client")
    def test_retry_prompt_includes_error_context(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [
            _mock_response("not valid json"),
            _mock_response(json.dumps(VALID_INTENT_DATA)),
        ]
        mock_get_client.return_value = mock_client

        parse_requirement("Some requirement")

        second_call_args = mock_client.messages.create.call_args_list[1]
        prompt_text = second_call_args[1]["messages"][0]["content"]
        assert "Previous attempt failed" in prompt_text

    @patch("copilot.parser._get_client")
    def test_raises_after_two_failures(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_response("{{not json}}")
        mock_get_client.return_value = mock_client

        with pytest.raises(ValueError, match="Failed to parse requirement after 2 attempts"):
            parse_requirement("Some requirement")

        assert mock_client.messages.create.call_count == 2

    @patch("copilot.parser._get_client")
    def test_handles_json_in_code_fence(self, mock_get_client):
        fenced = f"```json\n{json.dumps(VALID_INTENT_DATA)}\n```"
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_response(fenced)
        mock_get_client.return_value = mock_client

        intent = parse_requirement("Sync Workday hires to Oracle HCM nightly")

        assert intent.pattern == "scheduled"

    @patch("copilot.parser._get_client")
    def test_raises_on_invalid_pydantic_schema(self, mock_get_client):
        bad_data = dict(VALID_INTENT_DATA, pattern="invalid_pattern_value")
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_response(json.dumps(bad_data))
        mock_get_client.return_value = mock_client

        with pytest.raises(ValueError, match="Failed to parse requirement after 2 attempts"):
            parse_requirement("Some requirement")
