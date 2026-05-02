# Oracle ERP Cloud REST API: Invoices (Accounts Payable)

Source: https://docs.oracle.com/en/cloud/saas/financials/24d/farfa/op-invoices-get.html

## Overview

The Oracle Financials Cloud AP Invoices REST API manages supplier invoices in the Accounts Payable module. It is the primary target for procure-to-pay integrations that create invoices from purchase orders or external procurement systems (Coupa, SAP Ariba, Jaggaer).

## Base URL

```
https://{host}/fscmRestApi/resources/11.13.18.05/invoices
```

## Key Operations

### GET /invoices

Returns paginated invoice records with optional expansion of lines and distributions.

**Common query parameters:**
- `q=InvoiceStatus="UNPAID" and InvoiceDate>="2024-01-01"`
- `expand=invoiceLines,invoiceDistributions`
- `limit=500`, `offset=0`

### POST /invoices (create)

Creates a new AP invoice. The minimum viable payload:

```json
{
  "InvoiceNumber": "INV-2024-001",
  "InvoiceCurrencyCode": "USD",
  "InvoiceAmount": 5000.00,
  "InvoiceDate": "2024-03-15",
  "BusinessUnit": "Vision Operations",
  "Supplier": "Acme Corp",
  "SupplierSite": "ACME-US-PRIMARY",
  "PaymentTerms": "NET30",
  "invoiceLines": [
    {
      "LineNumber": 1,
      "LineType": "ITEM",
      "Amount": 5000.00,
      "Description": "Professional Services Q1",
      "PurchasingCategory": "IT Services"
    }
  ]
}
```

### PATCH /invoices/{InvoiceId}

Updates a draft invoice. Cannot update a validated or paid invoice via REST.

## Key Fields

| Field | Type | Notes |
|---|---|---|
| `InvoiceId` | integer | System-generated; use as path param for PATCH/DELETE |
| `InvoiceNumber` | string | Must be unique per supplier and business unit |
| `InvoiceCurrencyCode` | string | ISO 4217 (e.g., `"USD"`, `"EUR"`) |
| `InvoiceAmount` | decimal | Matches sum of invoice lines |
| `InvoiceDate` | date | ISO 8601 |
| `BusinessUnit` | string | Oracle ERP business unit name |
| `Supplier` | string | Supplier name (must match Supplier master) |
| `SupplierSite` | string | Supplier site code |
| `PaymentTerms` | string | Payment terms code (e.g., `"NET30"`, `"IMMEDIATE"`) |
| `InvoiceStatus` | string | Read-only: `"UNPAID"`, `"PAID"`, `"CANCELLED"` |
| `Source` | string | Source system identifier (e.g., `"COUPA"`, `"MANUAL"`) |
| `Description` | string | Invoice-level description |
| `PurchaseOrder` | string | PO number if PO-matched invoice |

## Invoice Lines

Each invoice must have at least one line. Line types:
- `ITEM` — standard goods/services line
- `TAX` — tax line (usually auto-calculated)
- `FREIGHT` — shipping charges
- `MISCELLANEOUS` — other charges

## Supplier Matching

The `Supplier` field must match an active supplier in the Supplier master exactly (case-sensitive). If no match is found, the POST returns a 400 error. Best practice: look up `SupplierId` via `GET /suppliers?q=SupplierName="..."` and use `SupplierId` instead of the name string.

## Validation and Approval

Invoices created via REST are in `NEEDS_REVALIDATION` status. To validate and route for approval:
1. POST the invoice (creates in draft)
2. Call the `validate` action: `POST /invoices/{InvoiceId}/action/validate`
3. Invoice moves to approval workflow automatically if AP configuration requires it

## Authentication

Same OAuth 2.0 client credentials as other Oracle Financials endpoints. Use the Oracle ERP Cloud adapter in OIC for automatic token management.

## Integration Notes

- Always include `Source` field to identify the originating system for reconciliation
- Check for existing invoices by `InvoiceNumber` before creating to prevent duplicates
- For high-volume integrations (>1,000 invoices), consider Oracle's FBDI (File-Based Data Import) bulk load instead of REST
