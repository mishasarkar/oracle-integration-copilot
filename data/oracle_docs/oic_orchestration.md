# Oracle Integration Cloud: Orchestration Design Patterns

Source: https://docs.oracle.com/en/cloud/paas/application-integration/integrations-user/creating-orchestrated-integrations.html

## Scheduled vs App-Driven Orchestration

Both patterns use the same visual canvas and action palette. The difference is the trigger:

| Aspect | Scheduled | App-Driven |
|---|---|---|
| Trigger | Built-in cron scheduler | Inbound HTTP call (REST/SOAP) |
| Concurrency | Configurable max instances | One instance per inbound call |
| Use case | Batch sync, nightly feeds | Real-time API, webhooks |
| Response | None (fire-and-forget) | Optional response payload |
| Testing | Manual trigger in console | Postman / curl |

## Key Orchestration Actions

### Invoke (REST / SOAP / Adapter)

Calls an external system using a configured connection. Each invoke is a configured step that maps request fields from earlier steps and captures the response for later use.

### Mapper

Transforms data between steps using XPath expressions and built-in functions. Common patterns:
- Field rename: map `src:worker_id` → `tgt:PersonNumber`
- String functions: `fn:upper-case()`, `fn:substring()`, `fn:concat()`
- Date format: `xp20:format-dateTime($date, "[Y0001]-[M01]-[D01]")`
- Conditional: `xp20:if-absent($field, "DEFAULT_VALUE")`
- Lookup: reference a lookup table configured in OIC

### For Each (Loop)

Iterates over an array in the message. Key settings:
- **Sequential** (default): processes one record at a time — safer but slower
- **Parallel**: processes multiple records simultaneously — faster but harder to debug
- Use sequential mode for integrations with per-record error handling

### Switch / If-Then-Else

Conditional branching. Evaluated using XPath boolean expressions.

### Assign

Sets a variable value mid-flow. Used to maintain counters, accumulate results, or build dynamic strings.

### Wait

Pauses execution for a specified duration. Use sparingly — long waits consume an OIC worker thread.

### Stage File

Reads or writes files from/to OIC's internal staging area. Used in conjunction with FTP or Object Storage adapters for file-based integrations.

## Mapper Best Practices

1. Always map required target fields first; use static values for fields not present in the source
2. Use `xp20:if-absent($field, "")` to handle null source fields gracefully
3. Date formats must match the target API spec exactly — mismatches cause silent data corruption, not errors
4. Test mappers independently using the mapper test panel before running end-to-end

## For-Each Loop Pattern for Bulk Sync

```
Invoke Source API (GET with pagination)
  │
  ├── Assign: totalProcessed = 0, errors = []
  │
  └── For Each record in response.items
       └── Scope
            ├── [normal] Invoke Target API (POST/PATCH)
            │             Assign: totalProcessed + 1
            └── [fault]  Log error details
                          Invoke Slack notification
                          Continue (absorb fault)
  │
  Assign: remaining = response.hasMore
  While remaining = true
    └── [repeat with next page]
```

## Pagination Pattern

OIC does not auto-paginate. Implement with a while loop:

1. Set `offset = 0`, `hasMore = true`
2. While `hasMore`:
   - Call `GET /resource?limit=500&offset={offset}`
   - Process records in for-each
   - If `response.hasMore = false`: set `hasMore = false`
   - Else: `offset = offset + 500`

## Instance Tracking and Debugging

Enable **business identifier tracking** to tag each integration instance with a meaningful business key (e.g., `WorkerNumber`, `InvoiceNumber`). This makes searching the OIC activity stream orders of magnitude faster during incident response.

## Integration Versioning

OIC supports versioning integrations. Each version is independently deployable. Strategy:
- Use version 1.0 for initial release
- Increment minor version for backward-compatible changes
- Increment major version when trigger schema changes
- Keep the old version active during a migration window, then deactivate
