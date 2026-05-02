# Oracle ERP Cloud REST API: Suppliers

Source: https://docs.oracle.com/en/cloud/saas/financials/24d/farfa/op-suppliers-get.html

## Overview

The Suppliers REST API manages supplier master records in Oracle Financials Cloud (Accounts Payable). Used in procure-to-pay integrations to look up supplier IDs, onboard new suppliers from procurement systems, and sync supplier data from MDM (Master Data Management) tools.

## Base URL

```
https://{host}/fscmRestApi/resources/11.13.18.05/suppliers
```

## Key Operations

### GET /suppliers

Look up suppliers by name, number, or tax registration.

```
GET /suppliers?q=SupplierName="Acme Corp"&fields=SupplierId,SupplierName,SupplierNumber
```

### POST /suppliers

Create a new supplier. Minimum payload:

```json
{
  "SupplierName": "Acme Corp",
  "SupplierType": "VENDOR",
  "TaxOrganizationType": "CORPORATION",
  "supplierAddresses": [
    {
      "AddressName": "Headquarters",
      "Country": "US",
      "AddressLine1": "123 Main St",
      "City": "San Francisco",
      "State": "CA",
      "PostalCode": "94105"
    }
  ],
  "supplierSites": [
    {
      "SupplierSiteName": "ACME-US-PRIMARY",
      "SiteUsePayment": true,
      "BuyingPartyName": "Vision Operations"
    }
  ]
}
```

## Key Fields

| Field | Type | Notes |
|---|---|---|
| `SupplierId` | integer | System key; use when referencing from invoices/POs |
| `SupplierNumber` | string | Business key; often matches ERP or MDM vendor number |
| `SupplierName` | string | Legal entity name (max 360 chars) |
| `SupplierType` | string | `"VENDOR"`, `"EMPLOYEE"`, `"PARTY"` |
| `Status` | string | `"Active"`, `"Inactive"` |
| `TaxRegistrationNumber` | string | VAT/TIN; required for tax-compliant regions |
| `PaymentCurrencyCode` | string | Default payment currency |
| `PaymentTermsLookupCode` | string | Default payment terms |

## Supplier Sites

Supplier sites represent remit-to addresses and are required to create invoices. A supplier can have multiple sites across business units.

Key site fields:
- `SupplierSiteName` — unique code within the supplier (e.g., `"US-MAIN"`)
- `BuyingPartyName` — the Oracle business unit this site is active for
- `SiteUsePayment: true` — marks site as valid for payment

## Common OIC Integration Pattern

For Coupa → Oracle ERP supplier sync:
1. Query Coupa suppliers API for active suppliers
2. For each, call `GET /suppliers?q=SupplierNumber="{coupaVendorId}"`
3. If not found → `POST /suppliers` to create
4. If found and data changed → `PATCH /suppliers/{SupplierId}` to update
5. Propagate `SupplierId` back to Coupa as external reference

## Duplicate Prevention

Oracle allows multiple suppliers with the same name (unlike invoices). Use `SupplierNumber` (mapped from the source system's vendor ID) as the deduplication key. Always query by number before creating.
