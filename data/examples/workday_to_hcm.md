# Example: Workday New Hires → Oracle HCM (Scheduled Orchestration)

## Input Requirement

> "Every night at 2am, pull new hires from Workday and create employee records in Oracle HCM. Skip contractors. Send a Slack alert if any record fails."

## Parsed Intent

```json
{
  "pattern": "scheduled",
  "source_system": "Workday",
  "target_system": "Oracle HCM",
  "objects": ["worker", "employment"],
  "schedule": "0 2 * * *",
  "filters": ["workerType != 'CONTRACTOR'"],
  "notifications": ["Slack webhook alert on record-level failure"],
  "raw_requirement": "Every night at 2am, pull new hires from Workday and create employee records in Oracle HCM. Skip contractors. Send a Slack alert if any record fails."
}
```

## Generated Integration Spec

**Title:** Workday New Hires → Oracle HCM Nightly Sync

**Pattern:** Scheduled Orchestration — runs at 02:00 UTC via OIC built-in scheduler.

### Source

- **System:** Workday HCM
- **Endpoint:** `GET /ccx/api/v1/{tenant}/workers?type=Employee&hiredAfter={lastRunDate}&limit=100`
- **Auth:** OAuth 2.0 client credentials (Workday ISU — Integration System User)
- **Sample response:**
```json
{
  "data": [
    {
      "id": "3aa5550b7fe348b08d40",
      "descriptor": "John Smith",
      "workerType": "Employee",
      "hireDate": "2024-03-15T00:00:00.000Z",
      "primaryJob": {
        "jobTitle": "Software Engineer",
        "businessSite": { "descriptor": "San Francisco HQ" },
        "manager": { "id": "abc123", "descriptor": "Jane Doe" }
      }
    }
  ],
  "total": 12
}
```

### Target

- **System:** Oracle HCM Cloud
- **Endpoint:** `POST /hcmRestApi/resources/11.13.18.05/workers`
- **Auth:** OAuth 2.0 client credentials (Oracle Fusion API Client Registration)
- **Sample payload sent:**
```json
{
  "PersonNumber": "WD-3aa5550b7fe348b08d40",
  "FirstName": "John",
  "LastName": "Smith",
  "DateOfBirth": "1990-01-15",
  "LegalEmployerName": "Vision Corporation",
  "WorkerType": "Employee",
  "DateStart": "2024-03-15",
  "BusinessUnitShortCode": "CORP",
  "AssignmentStatusTypeCode": "ACTIVE_ASSIGN",
  "JobCode": "SOFTWARE_ENG",
  "DepartmentName": "Engineering",
  "LocationCode": "SF-HQ"
}
```

### Field Mappings

| Source Field | Target Field | Transformation | Required |
|---|---|---|---|
| `id` | `PersonNumber` | Prefix with "WD-" | Yes |
| `legalName.firstName` | `FirstName` | Direct | Yes |
| `legalName.lastName` | `LastName` | Direct | Yes |
| `dateOfBirth` | `DateOfBirth` | `fn:substring($date, 1, 10)` → ISO 8601 date | Yes |
| `hireDate` | `DateStart` | `fn:substring($date, 1, 10)` | Yes |
| `workerType` | `WorkerType` | Lookup: "Employee"→"Employee", "Contingent_Worker"→skip | Yes |
| `primaryJob.businessSite.descriptor` | `LocationCode` | Lookup table: site name → OIC location code | No |
| `primaryJob.manager.id` | `ManagerId` | Look up Oracle PersonId from Workday manager ID | No |

### Filters

- Exclude records where `workerType = "Contingent_Worker"` or `workerType = "Non-Employee"`
- Only include records where `hireDate >= scheduledStartDate` (watermark-based)

### Error Handling

1. Scope fault handler wraps each record's HCM POST call
2. On fault: extract `$fault.message` and `WorkdayWorkerId`
3. POST to Slack webhook: `{"text": "OIC HCM Sync failed for worker {WorkdayWorkerId}: {faultMessage}"}`
4. Absorb fault and continue with next record
5. Global fault handler catches integration-level failures (auth error, source API down)
6. End-of-run: send summary Slack message with counts (processed / skipped / failed)

### Monitoring

- Enable OIC instance tracking with business identifier: `WorkerNumber`
- Log request/response payloads for failed instances (30-day retention)
- Set OIC activity stream alert for: 0 records processed (possible upstream issue)

### Assumptions

- Workday API v35+ is used; tenant URL is `{tenant}.workday.com`
- Oracle HCM `LegalEmployerName` "Vision Corporation" is a placeholder; must match actual legal entity
- `BusinessUnitShortCode` is assumed static per environment; parameterise if multi-BU
- Manager lookup assumes a separate Workday ID → Oracle PersonId mapping table exists

### Open Questions

- Should existing HCM records be updated if the worker rehires, or only new records created?
- What is the exact Workday filter for "hired since last run"? Is there a `hiredAfterDate` parameter or must we compare against a persisted watermark?
- What is the OIC concurrent instance limit for this environment?
- Are there any HCM-specific mandatory fields (e.g., `NationalIdNumber`) required for payroll activation?
