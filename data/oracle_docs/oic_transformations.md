# Oracle Integration Cloud: Data Transformation Patterns

Source: https://docs.oracle.com/en/cloud/paas/application-integration/integrations-user/mapping-data.html

## Overview

OIC's mapper uses XPath 2.0 and XSLT 2.0 for field-level data transformation. The visual mapper generates the underlying XSLT automatically, but understanding the expression language is essential for complex mappings.

## Common XPath Transformation Functions

### String Operations

```xpath
fn:upper-case($src:firstName)                     → "JOHN"
fn:lower-case($src:email)                          → "john@example.com"
fn:concat($src:firstName, " ", $src:lastName)      → "John Smith"
fn:substring($src:nationalId, 1, 4)               → first 4 chars
fn:string-length($src:name)                        → character count
fn:normalize-space($src:address)                   → trim and collapse whitespace
fn:replace($src:phone, "[^0-9]", "")              → strip non-numeric chars
```

### Date and DateTime Operations

```xpath
xp20:format-dateTime($src:hireDate, "[Y0001]-[M01]-[D01]")
  → "2024-03-15"  (ISO 8601 date)

xp20:format-dateTime($src:timestamp, "[Y0001]-[M01]-[D01]T[H01]:[m01]:[s01]Z")
  → "2024-03-15T14:30:00Z"  (ISO 8601 datetime)

fn:current-date()
  → today's date

fn:current-dateTime()
  → current UTC datetime
```

### Conditional / Null Handling

```xpath
xp20:if-absent($src:middleName, "")
  → returns "" if middleName is null or missing

if ($src:workerType = "Employee") then "EMP" else "CTG"
  → conditional value mapping

fn:exists($src:contractEndDate)
  → true/false whether field is present
```

### Numeric Operations

```xpath
$src:amount * 100                   → multiply (e.g., dollars to cents)
fn:round($src:quantity, 2)          → round to 2 decimal places
fn:sum($src:lines/amount)          → sum a repeated element
```

## Lookup Tables

OIC supports configurable lookup tables for value mapping (e.g., mapping source system status codes to Oracle values).

**Setup:**
1. Go to OIC console → Designer → Lookups
2. Create a lookup with columns: `sourceValue`, `targetValue`
3. Populate with value pairs

**Usage in mapper:**
```xpath
lookupValue("StatusMapping", "sourceStatus", $src:status, "targetStatus", "UNKNOWN")
```

This replaces the source status code with the mapped Oracle value, returning "UNKNOWN" if no match.

## Common Transformation Patterns in Oracle Integrations

### Worker Type Mapping (Workday → Oracle HCM)

| Source (Workday) | Target (Oracle HCM WorkerType) |
|---|---|
| `Employee` | `Employee` |
| `Contingent Worker` | `ContingentWorker` |
| `Intern` | `Employee` (with employment category) |

### Date Format Normalization

Workday returns dates as `2024-03-15T00:00:00.000Z`. Oracle HCM expects `2024-03-15`. Use:
```xpath
fn:substring($src:hireDate, 1, 10)
```

### Boolean to Oracle Code

Oracle APIs often use string codes rather than booleans:
```xpath
if ($src:isPrimaryAssignment = "true") then "Y" else "N"
```

### Currency Amount Scaling

Some source systems store amounts in minor units (cents). Oracle expects decimal:
```xpath
$src:amountCents div 100
```

## XSLT Stylesheet (Advanced)

For complex transformations (e.g., flattening nested arrays, aggregations), OIC allows embedding a raw XSLT stylesheet. Access via mapper → Advanced → XSLT view. This is an escape hatch — prefer visual mapper for maintainability.

## Transformation Testing

Test individual mapper expressions in the OIC mapper panel without running the full integration:
1. Open the mapper for an invoke action
2. Click the target field expression
3. Use "Test" tab to supply sample input and verify output

Always test edge cases: null fields, empty strings, special characters, dates at UTC midnight.
