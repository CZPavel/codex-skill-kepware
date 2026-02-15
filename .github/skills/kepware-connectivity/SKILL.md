---
name: kepware-connectivity
description: Bezpecne integrace a automatizace pro Kepware (KEPServerEX, ThingWorx Kepware Server, Kepware Edge). Pouzij pri OPC UA, IoT Gateway MQTT/REST Client/REST Server, Configuration API provisioning, certifikatech, troubleshootingu portu a tvorbe bootstrap/smoke-test skriptu; nepouzivej pro cisty frontend ani neodsouhlasene produkcni zasahy.
---

# Quick workflow
1. Run discovery first and collect:
   - Product variant: KEPServerEX, ThingWorx Kepware Server, or Kepware Edge.
   - Integration path: OPC UA, MQTT Client, REST Client, REST Server.
   - Target system: broker, FIOT/ThingWorx, custom REST endpoint, SCADA/MES.
   - Security constraints: TLS, cert source, auth model, anonymous policy.
   - Tag scope: exact tag IDs, write permissions, sampling policy.
2. Confirm non-destructive execution mode before changes:
   - No production changes without explicit approval.
   - No firewall edits without explicit approval.
   - No delete/reset operations without explicit approval.
3. Prefer scripts from `scripts/` for repeatable provisioning and smoke tests.
4. Keep secrets out of git and load from `.env` or runtime env vars.

# Default security baseline
- Keep HTTPS enabled for Config API and REST Server.
- Keep `Allow anonymous login` disabled unless explicitly required.
- Keep write endpoints disabled unless a write use case is approved.
- Use dedicated least-privilege service accounts.
- Set timeout, retry, and exponential backoff for all HTTP calls.

# Port and service baseline
Treat these as defaults only, then verify on host via runtime config and netstat:

| Service | Typical/default port(s) |
|---|---|
| Configuration API (HTTP/HTTPS) | 57413 / 57513 (current docs), 57412 / 57512 (seen in some deployments) |
| IoT Gateway service | 57212 |
| IoT Gateway REST Server Agent | 39320 |
| OPC UA Server | 49311 and/or 49320 depending on config/version |

Validation command examples:
- PowerShell: `Get-NetTCPConnection -State Listen | Where-Object LocalPort -in 39320,57212,57412,57512,57413,57513,49311,49320`
- CMD: `netstat -ano | findstr ":39320 :57212 :57412 :57512 :57413 :57513 :49311 :49320"`

# Config API playbook
1. Start from read-only discovery:
   - `GET /config/v1/project/_iot_gateway/mqtt_clients`
2. Provision MQTT client:
   - `POST /config/v1/project/_iot_gateway/mqtt_clients`
3. Add tag mapping to the agent:
   - `POST /config/v1/project/_iot_gateway/mqtt_clients/<agent_name>/iot_items`
4. Optional cleanup only with explicit approval:
   - `DELETE /config/v1/project/_iot_gateway/mqtt_clients/<agent_name>`

Use: `scripts/kepware_config_api_mqtt_bootstrap.py`
- Supports dry-run, retries/backoff, timeout, TLS verify toggle, basic auth.
- Supports custom JSON payload files when model properties differ by version.

# REST Server playbook
1. Confirm endpoint and TLS:
   - Default endpoint pattern: `https://localhost:39320/iotgateway/`
2. Smoke test browse/read:
   - `GET /browse`
   - `GET /read?ids=<TagName>`
3. Execute write only when explicitly enabled:
   - `POST /write`

Use: `scripts/kepware_rest_server_smoketest.py`
- Browse/read by default.
- Write request is gated by `--enable-write`.
- Supports auth, timeout, retries/backoff, and optional `--insecure`.

# REST Client notes
- URL format expects `tcp://<host>:<port>` or `ssl://<host>:<port>`.
- Use interval or on-data-change publish policies based on target requirements.
- Validate target endpoint capacity before high-rate publish.

# Troubleshooting checklist
- Ports listening and reachable from source host.
- HTTPS certificate chain trusted by client.
- User Manager / Security Policies configured (anonymous disabled by default).
- CORS allowed origins matches browser client origin.
- Write endpoint enabled only when required.
- Service account has expected rights in Config API and runtime operations.

# References
- Service ports: `https://support.ptc.com/help/kepware/kepware_server/en/kepware/server/port-assignments.html`
- REST Server usage: `https://support.ptc.com/help/kepware/features/en/kepware/features/IOTGATEWAY/working_rest_server.html`
- REST Server configuration: `https://support.ptc.com/help/kepware/features/en/kepware/features/IOTGATEWAY/configure_rest_server.html`
- Config API IoT Gateway examples: `https://support.ptc.com/help/kepware/features/en/kepware/features/IOTGATEWAY/configuration_api_reference.html`
- Kepware Edge IoT and Config API: `https://support.ptc.com/help/kepware/kepware_edge/en/kepware/kepware-edge/edge-iot.html`
- System requirements: `https://support.ptc.com/help/kepware/kepware_server/en/kepware/server/system-requirements.html`

# Bundle map
- `docs/TECHNICAL.md`: architecture, ports, security, troubleshooting.
- `docs/USER_GUIDE.md`: install/run/verification flow.
- `scripts/kepware_config_api_mqtt_bootstrap.py`: Config API bootstrap.
- `scripts/kepware_rest_server_smoketest.py`: REST Server smoke tests.
- `project_context.md`: project-specific integration facts.
- `CHANGELOG.md`: skill evolution log.

