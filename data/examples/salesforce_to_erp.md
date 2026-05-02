# Example: Salesforce Closed-Won Opportunities → Oracle ERP Invoices (Scheduled)

## Input Requirement

> "Every night, sync Salesforce opportunities that closed today as invoices in Oracle ERP Financials. Only include closed-won deals. Map the opportunity owner to the Oracle salesperson."

## Parsed Intent

```json
{
  "pattern": "scheduled",
  "source_system": "Salesforce",
  "target_system": "Oracle ERP",
  "objects": ["opportunity", "invoice"],
  "schedule": "0 1 * * *",
  "filters": ["StageName = 'Closed Won'", "CloseDate = today"],
  "notifications": [],
  "raw_requirement": "Every night, sync Salesforce opportunities that closed today as invoices in Oracle ERP Financials. Only include closed-won deals. Map the opportunity owner to the Oracle salesperson."
}
```

## Generated Integration Spec

**Title:** Salesforce Closed-Won Opportunities → Oracle ERP Invoices Nightly

**Pattern:** Scheduled Orchestration — runs at 01:00 UTC daily.

### Source

- **System:** Salesforce CRM
- **Endpoint:** `GET /services/data/v58.0/query?q=SELECT+Id,Name,Amount,CloseDate,AccountId,Account.Name,OwnerId,Owner.Email+FROM+Opportunity+WHERE+StageName='Closed+Won'+AND+CloseDate=TODAY`
- **Auth:** OAuth 2.0 connected app (client credentials flow); access token via `https://{instance}.salesforce.com/services/oauth2/token`
- **Sample response:**
```json
{
  "totalSize": 3,
  "done": true,
  "records": [
    {
      "Id": "0065g00000BzKPqAAN",
      "Name": "Acme Corp - Enterprise License Q1",
      "Amount": 48000.00,
      "CloseDate": "2024-03-15",
      "AccountId": "0015g000003OHJPAA4",
      "Account": { "Name": "Acme Corp" },
      "OwnerId": "0055g00000Abc123AAA",
      "Owner": { "Email": "john.smith@company.com" }
    }
  ]
}
```

### Target

- **System:** Oracle ERP Cloud (Accounts Receivable)
- **Endpoint:** `POST /fscmRestApi/resources/11.13.18.05/receivablesInvoices`
- **Auth:** OAuth 2.0 client credentials (Oracle Fusion API Client Registration)
- **Sample payload sent:**
```json
{
  "TransactionNumber": "SF-0065g00000BzKPqAAN",
  "TransactionDate": "2024-03-15",
  "DueDate": "2024-04-14",
  "BillToCustomerName": "Acme Corp",
  "CurrencyCode": "USD",
  "TransactionClass": "INV",
  "BusinessUnit": "Vision Operations",
  "SalesRepresentative": "John Smith",
  "lines": [
    {
      "LineNumber": 1,
      "Description": "Acme Corp - Enterprise License Q1",
      "Quantity": 1,
      "UnitSellingPrice": 48000.00,
      "LineType": "LINE",
      "RevenueAccount": "01-000-4110-00"
    }
  ]
}
```

### Field Mappings

| Source Field | Target Field | Transformation | Required |
|---|---|---|---|
| `Id` | `TransactionNumber` | Prefix with "SF-" | Yes |
| `CloseDate` | `TransactionDate` | Direct (already ISO 8601) | Yes |
| `CloseDate` | `DueDate` | Add 30 days: `xp20:add-dayTimeDuration-to-date($date, "P30D")` | Yes |
| `Account.Name` | `BillToCustomerName` | Direct; lookup Oracle customer if name differs | Yes |
| `Amount` | `UnitSellingPrice` | Direct | Yes |
| `Owner.Email` | `SalesRepresentative` | Look up Oracle salesperson name by email | No |
| `Name` | `lines[0].Description` | Direct | Yes |

### Filters

- SOQL WHERE clause restricts to `StageName = 'Closed Won'` and `CloseDate = TODAY`
- Skip records where `Amount = 0` or `Amount` is null (zero-value opportunities)
- Deduplicate: check if `TransactionNumber = "SF-{OpportunityId}"` already exists in Oracle AR before creating

### Error Handling

1. Scope fault handler per opportunity record
2. On fault: log Salesforce Opportunity ID, amount, and error to OIC activity stream
3. Global fault handler: if Salesforce SOQL query itself fails, abort and log
4. End-of-run Assign: capture count of created / skipped / failed invoices

### Monitoring

- Business identifier tracking: Salesforce Opportunity ID
- Daily reconciliation: compare count of Closed Won opps in Salesforce to Oracle invoices created that day

### Assumptions

- Oracle AR customer master contains entries matching Salesforce `Account.Name` exactly
- Payment terms default to NET30; parameterise if different terms apply per customer segment
- Revenue account code `01-000-4110-00` is a placeholder; actual account segments are client-specific
- Oracle `SalesRepresentative` field lookup assumes sales reps have the same email in both systems

### Open Questions

- Should re-opened opportunities (StageName changed back from Closed Won) result in a credit memo in Oracle AR?
- What happens to opportunities closed in prior periods that were missed due to integration downtime?
- Is there a Salesforce record type filter required (only "New Business" opps, not renewals)?
- Should the Salesforce Opportunity ID be stored as a custom attribute in Oracle AR for reconciliation?
