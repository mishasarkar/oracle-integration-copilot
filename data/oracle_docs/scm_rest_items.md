# Oracle SCM Cloud REST API: Items and Inventory

Source: https://docs.oracle.com/en/cloud/saas/supply-chain-management/24d/fasrp/index.html

## Overview

Oracle SCM Cloud provides REST APIs for Item Master management and inventory queries. These are the most common integration targets for product information management (PIM), ERP-SCM synchronisation, and warehouse management system (WMS) integrations.

## Item Master API

Base URL:
```
https://{host}/fscmRestApi/resources/11.13.18.05/items
```

### GET /items

Retrieve items with optional category and organization filters.

```
GET /items?q=ItemStatus="Active" and OrganizationCode="M1"&limit=200
```

### POST /items

Create a new item in the item master.

Minimum payload:
```json
{
  "ItemNumber": "AS54888",
  "Description": "Adjustable Shelf",
  "OrganizationCode": "M1",
  "LifeCyclePhaseCode": "Active",
  "ItemClass": "Root Item Class",
  "UOMCode": "Ea"
}
```

### Key Item Fields

| Field | Type | Notes |
|---|---|---|
| `ItemId` | integer | System-generated key |
| `ItemNumber` | string | Business key; must be unique per organization |
| `Description` | string | Short description (max 240 chars) |
| `OrganizationCode` | string | Inventory organization (e.g., `"M1"`, `"V1"`) |
| `LifeCyclePhaseCode` | string | `"Active"`, `"Inactive"`, `"Discontinued"` |
| `ItemClass` | string | Item classification hierarchy |
| `UOMCode` | string | Unit of measure (e.g., `"Ea"`, `"Kg"`, `"Box"`) |
| `PrimaryUOMCode` | string | Primary stocking UOM |
| `BuyerCode` | string | Assigned buyer |
| `Planner` | string | MRP planner code |
| `LeadTime` | integer | Days (for purchasing lead time) |

## Inventory On-Hand Quantities

```
https://{host}/fscmRestApi/resources/11.13.18.05/inventoryOnhandQuantities
```

### GET /inventoryOnhandQuantities

Returns current stock levels by item, organization, and subinventory.

```
GET /inventoryOnhandQuantities?q=OrganizationCode="M1" and ItemNumber="AS54888"
```

Key response fields:
- `OnhandQuantity` — current on-hand quantity
- `ReservedQuantity` — quantity reserved for sales orders
- `AvailableQuantity` — on-hand minus reserved
- `SubinventoryCode` — storage location code
- `UOMCode` — unit of measure

## Common OIC Integration Patterns

### PIM → Oracle SCM Item Sync (Scheduled)

1. Query PIM system for items modified since last run
2. For each item, call `GET /items?q=ItemNumber="{sku}"` to check existence
3. Create (POST) or update (PATCH) the item
4. Sync item categories via `/itemClasses` child resource

### SCM On-Hand → WMS Sync (Scheduled)

1. Query `/inventoryOnhandQuantities` for all active items in target org
2. Transform Oracle quantity fields to WMS format
3. Push updated stock levels to WMS via WMS REST or file drop

## Organization Codes

Organization codes are specific to each Oracle Cloud tenant. Common examples in Oracle demo data: `M1` (Manufacturing), `V1` (Vision Corp), `D1` (Distribution). Real tenants have custom codes — always verify with the client's Oracle admin.

## Bulk Loading Alternative

For initial loads of 10,000+ items, use Oracle's Product Hub FBDI (File-Based Data Import) spreadsheet templates rather than REST. REST is best for incremental sync (hundreds of records per run).
