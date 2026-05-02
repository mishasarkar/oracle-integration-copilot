# Example: Coupa Approved PO → Oracle ERP Purchase Order (Event-Driven)

## Input Requirement

> "When a purchase order is approved in Coupa, create a corresponding purchase order in Oracle ERP. Include all line items. Notify the procurement team by email if creation fails."

## Parsed Intent

```json
{
  "pattern": "event_driven",
  "source_system": "Coupa",
  "target_system": "Oracle ERP",
  "objects": ["purchase_order", "po_line"],
  "schedule": null,
  "filters": ["status = 'approved'"],
  "notifications": ["email to procurement team on failure"],
  "raw_requirement": "When a purchase order is approved in Coupa, create a corresponding purchase order in Oracle ERP. Include all line items. Notify the procurement team by email if creation fails."
}
```

## Generated Integration Spec

**Title:** Coupa Approved PO → Oracle ERP Purchase Order Sync

**Pattern:** App-Driven Orchestration — Coupa sends a webhook on PO approval; OIC exposes the trigger endpoint.

### Source

- **System:** Coupa Procurement
- **Endpoint:** Coupa webhook configured to POST to OIC REST trigger URL on PO status change to `approved`
- **Auth:** Coupa signs webhook payloads with HMAC-SHA256; validate signature in OIC using a custom header check
- **Sample inbound payload:**
```json
{
  "id": 98765,
  "status": "approved",
  "po_number": "PO-2024-00341",
  "supplier": { "id": 42, "name": "Acme Corp", "number": "SUPP-042" },
  "currency_code": "USD",
  "total": 15000.00,
  "approved_at": "2024-03-15T14:22:00Z",
  "line_items": [
    {
      "line_num": 1,
      "description": "Laptop - Dell XPS 15",
      "quantity": 10,
      "unit_price": 1500.00,
      "total": 15000.00,
      "account_type": "IT Equipment"
    }
  ]
}
```

### Target

- **System:** Oracle ERP Cloud (Procurement)
- **Endpoint:** `POST /fscmRestApi/resources/11.13.18.05/purchaseOrders`
- **Auth:** OAuth 2.0 client credentials (Oracle Fusion API Client Registration)
- **Sample payload sent:**
```json
{
  "OrderNumber": "COUPA-PO-2024-00341",
  "ProcurementBUName": "Vision Operations",
  "SoldToLegalEntity": "Vision Corporation",
  "CurrencyCode": "USD",
  "Supplier": "Acme Corp",
  "SupplierSite": "ACME-US-PRIMARY",
  "Description": "Coupa PO 98765 — imported via OIC",
  "lines": [
    {
      "LineNumber": 1,
      "LineType": "Goods",
      "ItemDescription": "Laptop - Dell XPS 15",
      "Quantity": 10,
      "UnitPrice": 1500.00,
      "UOMCode": "Ea",
      "Category": "IT.Equipment"
    }
  ]
}
```

### Field Mappings

| Source Field | Target Field | Transformation | Required |
|---|---|---|---|
| `po_number` | `OrderNumber` | Prefix with "COUPA-" | Yes |
| `currency_code` | `CurrencyCode` | Direct (ISO 4217) | Yes |
| `supplier.number` | `Supplier` lookup | Look up Oracle SupplierId via GET /suppliers | Yes |
| `approved_at` | `OrderDate` | `fn:substring($date, 1, 10)` | Yes |
| `line_items[].line_num` | `lines[].LineNumber` | Direct | Yes |
| `line_items[].description` | `lines[].ItemDescription` | Direct | Yes |
| `line_items[].quantity` | `lines[].Quantity` | Direct | Yes |
| `line_items[].unit_price` | `lines[].UnitPrice` | Direct | Yes |
| `line_items[].account_type` | `lines[].Category` | Lookup: Coupa account type → Oracle category | No |

### Filters

- Only process webhook events where `status = "approved"` (Coupa also sends webhooks for draft/pending)
- Validate that `line_items` array is non-empty before calling Oracle

### Error Handling

1. Validate HMAC signature on inbound webhook; return 401 if invalid
2. Lookup supplier in Oracle before PO creation; return 422 with clear message if supplier not found
3. Wrap Oracle PO POST in a fault handler
4. On fault: send email to `procurement-alerts@company.com` with PO number and error detail
5. Return HTTP 200 to Coupa on receipt (prevents Coupa retry storm); handle errors asynchronously

### Monitoring

- Track business identifier: `Coupa PO Number`
- Alert on integration error rate > 5% in a 1-hour window
- Log all inbound payloads for audit (procurement data is audit-sensitive)

### Assumptions

- Coupa is configured to send webhooks to the OIC REST trigger URL (OIC team must share the URL with the Coupa admin)
- Oracle supplier master is pre-populated; Coupa supplier IDs map 1:1 to Oracle `SupplierNumber`
- Oracle `ProcurementBUName` is a single static value; parameterise if multiple BUs are in scope

### Open Questions

- Does Coupa retry the webhook if OIC returns a non-200? If yes, how many times and at what interval?
- Should a failed PO creation trigger an alert in Coupa, or just email?
- Is there a cross-reference table needed to map Coupa cost account codes to Oracle account segments?
