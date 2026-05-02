# Oracle Integration Cloud: Connection Types and Adapters

Source: https://docs.oracle.com/en/cloud/paas/application-integration/integrations-user/managing-connections.html

## Overview

A **Connection** in OIC encapsulates the credentials and endpoint configuration for a system. Every integration trigger and invoke action references a connection. OIC ships with 80+ pre-built adapters.

## REST Adapter

Use for any HTTP/HTTPS-based API that does not have a dedicated adapter.

**Configuration:**
- Connection URL: base URL of the target API (e.g., `https://api.workday.com/v1`)
- Security: None, Basic Auth, API Key, OAuth 2.0 (client credentials, auth code)
- SSL certificate: upload if the target uses a self-signed cert

**In integration:** the REST invoke action lets you define the resource path, method, request/response schema (JSON or XML), and query parameters dynamically using mapper expressions.

**Limitations:** does not auto-paginate; you must implement pagination logic with a while loop and offset variable.

## Oracle Applications Adapter (Oracle Cloud Apps)

Pre-built adapter for Oracle Fusion Cloud (HCM, ERP, SCM, CX). Recommended over generic REST for Oracle-to-Oracle integrations.

**Features:**
- Auto-discovery of available REST resources from the Fusion catalog
- Handles OAuth token refresh transparently
- Schema import: browse and select Oracle business objects (Workers, Invoices, POs) with full field metadata
- Supports both REST and SOAP Oracle APIs

**Configuration:**
- Connection type: Oracle ERP Cloud / Oracle HCM Cloud / Oracle SCM Cloud (choose the matching module)
- Host: `https://{tenant}.fa.{dc}.oraclecloud.com`
- Username / password or OAuth client credentials

## SOAP Adapter

For WSDL-based web services, common in older Oracle on-premises integrations or third-party services.

**Configuration:**
- WSDL URL or uploaded WSDL file
- Security: WS-Security UsernameToken, SAML, or None
- Endpoint override (optional): override the WSDL endpoint for environment-specific URLs

## FTP Adapter

For file-based integrations via FTP or SFTP.

**Configuration:**
- Host, port, credentials (username/password or SSH key)
- Directory paths for read and write
- File name patterns (regex or wildcard)

**Operations:** list files, read file, write file, move file, delete file.

## File Adapter (Local/Stage)

Used within integrations to create, read, or write files in OIC's internal staging area. Works in conjunction with the FTP adapter or Oracle Object Storage adapter.

## Oracle Object Storage Adapter

For integrations that read from or write to OCI Object Storage buckets (e.g., data lake landing zones, large file transfers).

## Salesforce Adapter

Pre-built adapter for Salesforce CRM. Supports SOQL queries, standard and custom objects, and Salesforce change data capture events.

## Workday Adapter (via REST)

Workday does not have a dedicated OIC adapter. Connect via the REST adapter using Workday's REST API (v35+) with OAuth 2.0 bearer token. Workday also exposes SOAP-based APIs (Human Resources WSDL) — use the SOAP adapter for those.

## Connection Testing

Always use the **Test** button in OIC connection configuration before saving. A green status confirms network reachability and authentication. A red status usually means:
- Incorrect base URL (trailing slash can matter)
- Wrong credentials or expired client secret
- Firewall rule blocking OIC's egress IPs

## Security Policies

OIC enforces TLS 1.2+ for all outbound connections. Ensure the target system supports TLS 1.2 or higher.
