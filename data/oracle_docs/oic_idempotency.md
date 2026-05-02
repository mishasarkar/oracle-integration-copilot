# Oracle Integration Cloud: Idempotency and Retry Patterns

Source: https://docs.oracle.com/en/cloud/paas/application-integration/integrations-user/designing-reliable-integrations.html

## Why Idempotency Matters

OIC scheduled integrations can run more than once due to:
- Manual re-trigger after a failed run
- Clock drift causing overlapping scheduled windows
- OIC infrastructure failover replaying a partially complete instance

If the integration is not idempotent, reruns create duplicate records in the target system (duplicate invoices, duplicate hires). Designing for idempotency is non-negotiable in production.

## Idempotency Strategies

### 1. Lookup-Before-Write (Check-Then-Act)

Before creating a record, query the target to see if it already exists using a stable business key.

```
For each source record:
  GET /workers?q=PersonNumber="{workerId}"
  If found → PATCH (update if needed)
  If not found → POST (create)
```

**Pros:** simple, always correct  
**Cons:** doubles the API call count; can be slow for large batches  
**When to use:** target system has no native upsert; record count < 1,000 per run

### 2. Upsert Endpoint

Some Oracle APIs support upsert semantics natively — the same POST will create or update based on a business key match.

Oracle ERP Purchase Orders support upsert via `MERGE` semantics in some contexts. Check the target API documentation for `mergeAction` or `upsert` parameters.

### 3. Watermark / High-Water Mark

Track the last successfully processed timestamp or sequence ID in a persistent store (OIC process tracking variable, ATP database table, or OCI Object Storage file). On each run, only process records newer than the watermark.

```
Read lastRunTime from tracking store
Query source: GET /records?q=modifiedDate>="{lastRunTime}"
Process records
Update lastRunTime to current time on success
```

**Critical:** only update the watermark after successful processing. If the integration fails midway, the next run reprocesses from the last committed watermark.

### 4. Idempotency Keys (Header-Based)

Some REST APIs accept an `Idempotency-Key` header. Send a stable UUID derived from the source record key. If the server receives the same key twice, it returns the previous response without re-executing.

Oracle Fusion REST APIs do not currently support `Idempotency-Key` headers — apply strategies 1–3 instead.

## Handling Partial Batch Failures

When processing 500 records and record 347 fails:
- **Wrong approach:** fail the whole run — forces complete re-processing
- **Right approach:** use a scope fault handler to absorb per-record errors, log the failed record key, and continue with record 348

At the end of the run, report a summary: `"Processed 499/500 records. 1 failed: [WorkerNumber: W-1234]"`.

## Retry Patterns for Transient Errors

OIC does not have built-in retry with backoff on REST invoke actions. Implement manually:

```
Assign: retryCount = 0, success = false
While retryCount < 3 and success = false:
  Try:
    Invoke target API
    Assign: success = true
  Fault (HTTP 429 or 5xx):
    Assign: retryCount = retryCount + 1
    Wait: 5 seconds * retryCount  (exponential-ish backoff)
If success = false:
  Log permanent failure
  Send alert
```

Only retry on transient errors (5xx, timeout, 429 Too Many Requests). Do not retry on 4xx client errors — they will fail again.

## Dead Letter Pattern

For records that fail after all retries:
1. Write the failed record payload + error details to an ATP table (`integration_dead_letters`)
2. Include: source record key, error message, timestamp, integration name, OIC instance ID
3. Build a separate "resubmit" integration that reads from this table, applies a fix if needed, and retries

This pattern gives operations teams a clean path to resolve data quality issues without rerunning the entire batch.

## Testing Idempotency

Before go-live, verify:
1. Run the integration twice in a row — confirm no duplicate records in the target
2. Kill the integration mid-run — confirm the next run picks up correctly from the watermark
3. Inject a deliberately bad record — confirm it is skipped and logged without stopping the batch
