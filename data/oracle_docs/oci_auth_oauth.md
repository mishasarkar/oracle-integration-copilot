# Oracle Cloud Infrastructure: Authentication for OIC Integrations

Source: https://docs.oracle.com/en/cloud/paas/application-integration/rest-api/Authentication.html

## Overview

OIC integrations authenticate to Oracle Cloud APIs using OAuth 2.0. Understanding the auth flow is critical for configuring OIC connections correctly.

## OAuth 2.0 Client Credentials (Recommended for OIC)

The client credentials grant is the standard pattern for server-to-server integrations where no user context is needed.

**Flow:**
1. OIC sends a POST to the Oracle token endpoint:
   ```
   POST https://{host}/oauth/token
   Content-Type: application/x-www-form-urlencoded

   grant_type=client_credentials&client_id={id}&client_secret={secret}
   &scope=urn:opc:resource:consumer::all
   ```
2. Oracle returns a Bearer token (expires in ~3600 seconds)
3. OIC includes `Authorization: Bearer {token}` in all subsequent calls
4. The Oracle Applications adapter in OIC handles token refresh automatically

**Setup in Oracle Fusion Cloud:**
1. Security Console → API Client Registrations → Create
2. Assign roles (e.g., `ORA_HRC_REST_SERVICE_ACCESS_HUMAN_RESOURCES` for HCM)
3. Copy Client ID and generate a Client Secret

## Basic Authentication (Legacy)

Username and password Base64-encoded in the Authorization header. Supported but not recommended — use OAuth 2.0 for all new integrations.

## Third-Party API Authentication in OIC

**Workday REST API:**
- OAuth 2.0 client credentials
- Token endpoint: `https://{tenant}.workday.com/ccx/oauth2/{tenant}/token`
- Configure an OIC REST connection with the OAuth 2.0 client credentials policy

**Salesforce:**
- OAuth 2.0 connected app (client credentials or auth code flow)
- Use the OIC Salesforce adapter or generic REST adapter

**Slack incoming webhook:**
- No auth required for simple webhooks
- Configure a REST connection pointing to the webhook URL; set security policy to None

## Secret Management

Never hardcode credentials in OIC mapper expressions or Assign actions. All secrets are stored in:
1. **OIC connection configuration** — encrypted at rest by Oracle
2. **OCI Vault** — for enterprise secret rotation; reference via OIC's OCI Vault connection

Rotate client secrets on a schedule (90-day policy is common). Re-test OIC connections after rotation.

## Common Authentication Errors

| Error | Cause | Fix |
|---|---|---|
| `401 Unauthorized` | Expired or invalid credentials | Re-test connection; regenerate client secret |
| `403 Forbidden` | Missing API role | Add required role to the API client registration |
| `invalid_client` | Wrong client ID or secret | Verify in Oracle Security Console |
| `invalid_scope` | Incorrect scope string | Use `urn:opc:resource:consumer::all` |
