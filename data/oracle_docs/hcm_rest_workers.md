# Oracle HCM REST API: Workers

Source: https://docs.oracle.com/en/cloud/saas/human-resources/24d/farws/op-workers-get.html

## Overview

The Oracle HCM REST API `workers` resource (v2) is the primary endpoint for managing person and employment records. It provides full CRUD operations and supports bulk retrieval with filtering.

## Base URL

```
https://{host}/hcmRestApi/resources/11.13.18.05/workers
```

The version segment (`11.13.18.05`) is stable across quarterly updates unless Oracle publishes a breaking change. Always pin to a specific version in OIC connection configuration.

## Key Operations

### GET /workers (list)

Returns a paginated collection of worker records.

**Query parameters:**
- `q` — SCIM-like filter expression: `q=EffectiveStartDate >= "2024-01-01"`
- `fields` — comma-separated field selector to reduce payload size
- `limit` — page size (max 500)
- `offset` — pagination offset
- `expand` — comma-separated child resources: `workRelationships,assignments,addresses`

**Example:** Fetch active employees hired after January 1 2024:
```
GET /workers?q=EffectiveStartDate>="2024-01-01" and WorkerType="Employee"&limit=500&expand=workRelationships
```

### POST /workers (create)

Creates a new person and employment record in a single transaction.

**Minimum required fields:**
- `PersonId` — omit to let Oracle auto-assign
- `FirstName`, `LastName`
- `DateOfBirth`
- `LegalEmployerName` — must match an existing legal entity
- `WorkerType` — `"Employee"` or `"NonWorker"`
- `DateStart` — employment start date (ISO 8601)
- `BusinessUnitShortCode`
- `AssignmentStatusTypeCode` — e.g., `"ACTIVE_ASSIGN"`

### PATCH /workers/{PersonId} (update)

Updates an existing worker. Only supply changed fields. Use `PersonId` (numeric) or `PersonNumber` (alphanumeric) as the path parameter.

## Key Fields (Person Level)

| Field | Type | Notes |
|---|---|---|
| `PersonId` | integer | System-generated primary key |
| `PersonNumber` | string | Business key; often maps to HR system employee ID |
| `FirstName` | string | |
| `MiddleName` | string | Optional |
| `LastName` | string | |
| `DateOfBirth` | date | ISO 8601 (YYYY-MM-DD) |
| `NationalIdNumber` | string | SSN, NIN, etc.; stored encrypted |
| `GenderCode` | string | `"M"`, `"F"`, `"ORA_UNDISCLOSED"` |
| `CountryOfBirthCode` | string | ISO 3166-1 alpha-2 |

## Key Fields (Work Relationship / Assignment Level)

The `workRelationships` child resource holds employment terms.

| Field | Type | Notes |
|---|---|---|
| `WorkerType` | string | `"Employee"`, `"ContingentWorker"`, `"NonWorker"` |
| `LegalEmployerName` | string | Must match a valid Legal Entity in HCM |
| `DateStart` | date | Employment start date |
| `PrimaryFlag` | boolean | True for primary work relationship |
| `AssignmentStatusTypeCode` | string | `"ACTIVE_ASSIGN"`, `"SUSPEND_ASSIGN"` |
| `JobCode` | string | Job code from HCM job catalog |
| `LocationCode` | string | Work location code |
| `DepartmentName` | string | |
| `GradeCode` | string | Salary grade |
| `ManagerId` | integer | PersonId of the direct manager |

## Authentication

Oracle HCM REST API uses **OAuth 2.0 client credentials** flow (recommended for OIC) or Basic Auth.

- Token endpoint: `https://{host}/oauth/token`
- Grant type: `client_credentials`
- Scope: `urn:opc:resource:consumer::all`

In OIC, configure an **Oracle Applications adapter** connection instead of a generic REST connection — it handles token refresh automatically.

## Rate Limits and Pagination

- Default page size: 25 (set `limit` up to 500)
- Respect `hasMore` in the response links collection — loop until `hasMore: false`
- No documented per-minute rate limit but Oracle recommends avoiding concurrent bulk loads; use OIC sequential processing for large volumes
- For very large datasets (>10,000 records), prefer HCM Extract (BI Publisher) over REST

## Common Integration Patterns with OIC

1. **Inbound hire feed:** Scheduled OIC flow → GET /workers with date filter → transform → POST to target system
2. **Outbound hire sync:** External system POST → OIC App-Driven → POST /workers in HCM
3. **Position sync:** Query `/workers?expand=assignments` → extract assignment details → update workforce planning tool
