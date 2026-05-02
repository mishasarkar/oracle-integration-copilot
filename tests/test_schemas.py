import pytest
from pydantic import ValidationError

from copilot.schemas import FieldMapping, IntegrationIntent, IntegrationSpec


class TestIntegrationIntent:
    def test_valid_scheduled(self):
        intent = IntegrationIntent(
            pattern="scheduled",
            source_system="Workday",
            target_system="Oracle HCM",
            objects=["worker"],
            schedule="0 2 * * *",
            filters=["workerType != 'CONTRACTOR'"],
            notifications=["Slack alert on failure"],
            raw_requirement="Sync Workday hires to Oracle HCM nightly",
        )
        assert intent.pattern == "scheduled"
        assert intent.source_system == "Workday"
        assert len(intent.filters) == 1

    def test_valid_event_driven(self):
        intent = IntegrationIntent(
            pattern="event_driven",
            source_system="Coupa",
            target_system="Oracle ERP",
            objects=["purchase_order"],
            raw_requirement="When a PO is approved in Coupa, sync to Oracle ERP",
        )
        assert intent.pattern == "event_driven"
        assert intent.schedule is None
        assert intent.filters == []
        assert intent.notifications == []

    def test_invalid_pattern_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            IntegrationIntent(
                pattern="batch",  # not a valid literal
                source_system="Workday",
                target_system="Oracle HCM",
                objects=[],
                raw_requirement="test",
            )
        assert "pattern" in str(exc_info.value).lower()

    def test_defaults_are_empty_lists(self):
        intent = IntegrationIntent(
            pattern="request_response",
            source_system="Salesforce",
            target_system="Oracle ERP",
            objects=["opportunity"],
            raw_requirement="Look up customer",
        )
        assert intent.filters == []
        assert intent.notifications == []
        assert intent.schedule is None

    @pytest.mark.parametrize("pattern", ["scheduled", "event_driven", "request_response", "file_based"])
    def test_all_valid_patterns(self, pattern):
        intent = IntegrationIntent(
            pattern=pattern,
            source_system="Source",
            target_system="Target",
            objects=["object"],
            raw_requirement="test requirement",
        )
        assert intent.pattern == pattern


class TestFieldMapping:
    def test_required_fields_only(self):
        mapping = FieldMapping(
            source_field="worker_id",
            target_field="PersonNumber",
            required=True,
        )
        assert mapping.transformation is None
        assert mapping.notes is None
        assert mapping.required is True

    def test_full_mapping(self):
        mapping = FieldMapping(
            source_field="hireDate",
            target_field="DateStart",
            transformation="fn:substring($date, 1, 10)",
            required=True,
            notes="Strips time component from Workday ISO 8601 datetime",
        )
        assert mapping.transformation == "fn:substring($date, 1, 10)"
        assert mapping.notes is not None

    def test_not_required(self):
        mapping = FieldMapping(
            source_field="middleName",
            target_field="MiddleName",
            required=False,
        )
        assert mapping.required is False


class TestIntegrationSpec:
    def _make_spec(self, **kwargs):
        defaults = dict(
            title="Test Integration",
            pattern="scheduled",
            source={"system": "Workday", "endpoint": "/workers", "auth": "OAuth 2.0", "sample_payload": "{}"},
            target={"system": "Oracle HCM", "endpoint": "/workers", "auth": "OAuth 2.0", "sample_payload": "{}"},
            mappings=[
                FieldMapping(source_field="id", target_field="PersonNumber", required=True)
            ],
            filters=["workerType = 'Employee'"],
            error_handling=["Scope fault handler per record"],
            monitoring=["Instance tracking enabled"],
            assumptions=["Tenant URL must be substituted"],
            open_questions=["What is the batch size limit?"],
            references=["hcm_rest_workers.md"],
        )
        defaults.update(kwargs)
        return IntegrationSpec(**defaults)

    def test_valid_spec(self):
        spec = self._make_spec()
        assert spec.title == "Test Integration"
        assert len(spec.mappings) == 1
        assert spec.mappings[0].source_field == "id"

    def test_defaults_are_empty_lists(self):
        spec = IntegrationSpec(
            title="Minimal Spec",
            pattern="scheduled",
            source={"system": "A"},
            target={"system": "B"},
            mappings=[],
        )
        assert spec.filters == []
        assert spec.error_handling == []
        assert spec.assumptions == []
        assert spec.references == []

    def test_spec_serialisation(self):
        spec = self._make_spec()
        data = spec.model_dump()
        assert data["title"] == "Test Integration"
        assert isinstance(data["mappings"], list)
        assert data["mappings"][0]["source_field"] == "id"
