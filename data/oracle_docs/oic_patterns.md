# Oracle Integration Cloud: Integration Patterns

Source: https://docs.oracle.com/en/cloud/paas/application-integration/integrations-user/understanding-oracle-integration.html

## Overview

Oracle Integration Cloud (OIC) supports four primary integration patterns. Selecting the right pattern is the first architectural decision in any OIC project.

## Scheduled Orchestration

A Scheduled Orchestration runs automatically at a configured interval using a built-in cron scheduler. Use it for bulk data synchronisation where near-real-time is not required.

**When to use:**
- Nightly or hourly batch extracts from a SaaS source (Workday, Salesforce, Coupa)
- Regular feeds into Oracle HCM, ERP, or SCM from external systems
- Any use case described as "every N hours", "daily", or "at 2am"

**Key configuration:**
- Schedule trigger: supports cron expression or simple recurrence (hourly, daily, weekly)
- Parallel execution control: set maximum concurrent instances to prevent overlapping runs
- Start parameter: `startTime` and `endTime` can be passed as schedule parameters for windowed extraction

**Common pattern:** OIC pulls from source → loops over records → calls target → scope fault handler per record.

## App-Driven Orchestration

An App-Driven Orchestration is triggered by an inbound call — REST, SOAP, or an adapter event. It may be synchronous (returns a response) or asynchronous (fire-and-forget).

**When to use:**
- Real-time API: a caller needs an immediate response (order validation, employee lookup)
- Event-driven: another system pushes data when something happens (Salesforce trigger, webhook)
- Integration described as "when X happens, do Y immediately"

**Key configuration:**
- REST trigger: define the resource path, method (POST/GET), request/response schemas
- SOAP trigger: upload WSDL; OIC generates the service endpoint automatically
- Async vs sync: toggle via "Request Only" (async) vs "Request/Response" (sync) in the trigger

## File Transfer (File-Based Integration)

Uses the FTP adapter or Oracle Object Storage adapter to move and transform files.

**When to use:**
- Legacy on-premises systems that only export flat files (CSV, fixed-width, XML)
- High-volume batch where REST API rate limits are a concern
- EDI, bank statement processing, or payroll file feeds

**Key configuration:**
- FTP adapter connection: hostname, port, credentials, directory paths
- Stage file action: read, write, zip/unzip, encrypt/decrypt
- List files → for-each loop → process record

## Event-Based Integration

Subscribes to Oracle Cloud Infrastructure (OCI) Events Service, Oracle Fusion Applications business events, or an external message queue (Oracle Advanced Queuing, Kafka via REST).

**When to use:**
- Oracle Fusion raises a business event you want to react to (e.g., "Employee Hire" event from HCM)
- Event-driven microservices architecture — OIC as the integration layer between services
- Low-latency requirement: react within seconds of the event occurring

**Key configuration:**
- Business event subscription: select the Fusion application and event type
- Filtering: use event condition expressions to narrow which events trigger the flow
- Deduplication: OIC delivers at-least-once; design idempotent target calls

## Choosing Between Patterns

| Requirement | Recommended Pattern |
|---|---|
| "Every night", "daily batch" | Scheduled Orchestration |
| "When an order is created" | App-Driven Orchestration (event/webhook) |
| "Look up employee in real time" | App-Driven Orchestration (sync request/response) |
| "File lands on SFTP, process it" | File Transfer |
| "React to Oracle Fusion business event" | Event-Based |
