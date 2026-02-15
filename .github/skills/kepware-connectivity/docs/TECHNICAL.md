# TECHNICAL

## Scope

`kepware-connectivity` provides a repeatable integration workflow for:
- KEPServerEX
- ThingWorx Kepware Server
- Kepware Edge

Target use cases:
- OPC UA consumption from SCADA/MES/IT
- IoT Gateway MQTT Client publish/subscription flows
- IoT Gateway REST Client push flows
- IoT Gateway REST Server browse/read/write access
- Configuration API automation for MQTT agents and iot_items

## Architecture decision flow

1. Need standards-based pull from industrial clients: use OPC UA.
2. Need stream to broker/cloud: use IoT Gateway MQTT Client.
3. Need push into custom HTTP endpoint: use REST Client.
4. Need external app-driven browse/read/write over HTTP: use REST Server.
5. Need repeatable provisioning and deployment: use Configuration API.

## Service ports and validation

Use these as default expectations, then verify runtime configuration on host.

| Service | Port(s) |
|---|---|
| Config API HTTP/HTTPS | 57413 / 57513 (current docs), 57412 / 57512 (seen in some installs) |
| IoT Gateway service | 57212 |
| IoT Gateway REST Server Agent | 39320 |
| OPC UA server | 49311 and/or 49320 |

PowerShell validation:

```powershell
Get-NetTCPConnection -State Listen |
  Where-Object LocalPort -in 39320,57212,57412,57512,57413,57513,49311,49320 |
  Sort-Object LocalPort
```

## Security baseline

- Keep HTTPS on for Config API and REST Server.
- Disable anonymous login by default.
- Keep write endpoint disabled unless explicit write use case exists.
- Use dedicated service account with least privilege.
- Store credentials in env vars / secret manager, never in git.
- Enforce timeout + retry/backoff in all integration clients.

REST Server hardening knobs to review every deployment:
- network adapter binding
- port
- CORS allowed origins
- HTTPS cert (default self-signed vs imported PFX)
- write endpoint enabled/disabled
- allow anonymous login enabled/disabled

## Config API automation pattern

Minimum automation sequence used by this skill:

1. List current MQTT clients:
- `GET /config/v1/project/_iot_gateway/mqtt_clients`

2. Create MQTT client:
- `POST /config/v1/project/_iot_gateway/mqtt_clients`

3. Add tag mapping to client:
- `POST /config/v1/project/_iot_gateway/mqtt_clients/<agent_name>/iot_items`

4. Optional cleanup (approval required):
- `DELETE /config/v1/project/_iot_gateway/mqtt_clients/<agent_name>`

Script: `scripts/kepware_config_api_mqtt_bootstrap.py`

## REST Server smoke-test pattern

Default endpoint example:
- `https://localhost:39320/iotgateway/`

Test sequence:
1. `GET /browse`
2. `GET /read?ids=<TagName>`
3. `POST /write` only when explicit approval and endpoint enabled

Script: `scripts/kepware_rest_server_smoketest.py`

## Troubleshooting

1. Port is closed or occupied:
- check runtime config and listener process
- detect collisions via `netstat -ano`

2. TLS errors:
- verify certificate chain trust and hostname match
- confirm correct PFX import and binding

3. Auth failures (401/403):
- validate user manager account and rights
- check Basic credentials and target API scope

4. Browser/CORS errors:
- confirm exact origin in allowed origins
- avoid wildcard in production unless required

5. Write failures:
- verify write endpoint is enabled
- verify tag exists and is writable

## Official references

- Service port assignments:
  `https://support.ptc.com/help/kepware/kepware_server/en/kepware/server/port-assignments.html`
- Working with REST Server:
  `https://support.ptc.com/help/kepware/features/en/kepware/features/IOTGATEWAY/working_rest_server.html`
- Configure REST Server:
  `https://support.ptc.com/help/kepware/features/en/kepware/features/IOTGATEWAY/configure_rest_server.html`
- Configuration API reference (IoT Gateway examples):
  `https://support.ptc.com/help/kepware/features/en/kepware/features/IOTGATEWAY/configuration_api_reference.html`
- Kepware Edge IoT and Config API:
  `https://support.ptc.com/help/kepware/kepware_edge/en/kepware/kepware-edge/edge-iot.html`
- System requirements:
  `https://support.ptc.com/help/kepware/kepware_server/en/kepware/server/system-requirements.html`
