# Oracle Integration Cloud: Fault Handling and Error Notifications

Source: https://docs.oracle.com/en/cloud/paas/application-integration/integrations-user/adding-fault-handling.html

## Overview

OIC provides a structured fault handling framework that separates business errors from technical errors and supports granular retry and notification logic.

## Types of Faults

**Business faults** — returned by the target system when the request is valid but the business rule rejects it (e.g., duplicate record, invalid field value). These are wrapped in a SOAP fault or an HTTP 4xx response.

**Technical faults** — connectivity issues, timeouts, authentication failures (HTTP 5xx, connection refused). OIC surfaces these as `RuntimeFaultMessage`.

## Scope Fault Handlers

A **Scope** activity groups a set of actions. You can attach a fault handler to any scope. When a fault occurs inside the scope, execution jumps to the fault handler instead of terminating the entire integration.

Use scope fault handlers for **per-record error handling** inside a for-each loop:

```
For Each Record
  └── Scope
       ├── [normal path] Transform → Call Target API
       └── [fault handler] Log error → Send Slack notification → continue
```

This ensures one bad record does not stop the entire batch.

## Global Fault Handler

The **global fault handler** catches any fault not caught by a scope handler. It fires at the integration level.

Best practice: always configure a global fault handler that:
1. Logs the fault message and stack trace to OIC monitoring
2. Sends an alert (email or Slack) with the integration name and instance ID
3. Re-throws or terminates cleanly

## Notification Adapter (Slack, Email)

OIC includes a built-in **Notification** action (email) and supports Slack via the REST adapter or the dedicated Slack adapter.

**Email notification:**
- Add a "Notification" action inside a fault handler
- Configure SMTP or use Oracle's built-in notification service
- Include `$integration.name`, `$fault.message`, `$fault.errorCode` in the body

**Slack webhook:**
- Configure a REST connection to `https://hooks.slack.com`
- POST a JSON payload: `{"text": "OIC fault in {integration}: {message}"}`
- Use the REST invoke action inside the fault handler

## Retry Patterns

OIC does not have native retry with backoff on invoke actions. Common workarounds:

1. **Manual retry loop**: use a while loop with a counter and `wait` action between attempts (max 3 retries, 5-second wait)
2. **Oracle Advanced Queuing (AQ)**: enqueue failed records into an AQ queue; a separate retry integration dequeues and reprocesses
3. **Dead letter table**: write failed records to an ATP (Autonomous Transaction Processing) database table for manual review and resubmission

## Re-throw vs Absorb

- **Re-throw**: propagate the fault up — use this in a scope handler when you want the global handler to also fire
- **Absorb (handle silently)**: log and continue — use this for non-critical records in a bulk sync where partial success is acceptable

## Fault Variables

Inside a fault handler, these variables are available:
- `$fault.name` — fault type name
- `$fault.message` — human-readable error message  
- `$fault.errorCode` — HTTP status or fault code
- `$fault.infoCode` — Oracle-specific info code

## OIC Instance Tracking

Enable **instance tracking** in integration settings to retain full request/response payloads for failed instances. Required for debugging in production. Storage can be controlled by retention period (default 30 days).

## Best Practices

1. Every integration with a for-each loop should have a scope fault handler inside the loop
2. Global fault handler is mandatory for any production integration
3. Include the OIC instance ID in all alert messages for traceability
4. Log the source record key (e.g., WorkerNumber, InvoiceNumber) in fault messages
5. Test fault paths explicitly — do not assume they work because the happy path works
