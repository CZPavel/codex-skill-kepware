# USER GUIDE

## 1. Prerequisites

- Kepware installed (KEPServerEX / ThingWorx Kepware Server / Kepware Edge)
- Config API and/or IoT Gateway REST Server enabled
- Python 3.10+

## 2. Discovery checklist (mandatory first)

Collect before any change:
- product variant and exact version
- integration target (MQTT broker, ThingWorx/FIOT, custom REST, OPC UA client)
- required tag list and write permissions
- TLS/auth requirements
- allowed maintenance window and rollback plan

## 3. Security and safety mode

- Default to dry-run.
- Do not run production writes/deletes without explicit approval.
- Keep secrets in environment variables, not command history files.

Suggested env vars:

```powershell
$env:KEPWARE_CONFIG_API_URL = "https://localhost:57513"
$env:KEPWARE_CONFIG_API_USER = "<user>"
$env:KEPWARE_CONFIG_API_PASS = "<password>"
$env:KEPWARE_REST_SERVER_URL = "https://localhost:39320/iotgateway"
$env:KEPWARE_REST_USER = "<user>"
$env:KEPWARE_REST_PASS = "<password>"
```

## 4. Config API bootstrap

List MQTT agents, create one, and add one iot_item:

```powershell
python .github/skills/kepware-connectivity/scripts/kepware_config_api_mqtt_bootstrap.py `
  --mqtt-client-name mqtt_agent_demo `
  --iot-item-name iot_item_demo `
  --tag-id "Channel1.Device1.Tag1"
```

Run real changes only after approval:

```powershell
python .github/skills/kepware-connectivity/scripts/kepware_config_api_mqtt_bootstrap.py `
  --no-dry-run `
  --mqtt-client-name mqtt_agent_demo `
  --iot-item-name iot_item_demo `
  --tag-id "Channel1.Device1.Tag1"
```

Custom payload mode (recommended for strict production schemas):

```powershell
python .github/skills/kepware-connectivity/scripts/kepware_config_api_mqtt_bootstrap.py `
  --no-dry-run `
  --mqtt-client-name mqtt_agent_demo `
  --mqtt-client-json .\mqtt_client_payload.json `
  --iot-item-json .\iot_item_payload.json
```

## 5. REST Server smoke test

Browse + read:

```powershell
python .github/skills/kepware-connectivity/scripts/kepware_rest_server_smoketest.py `
  --tag-id "Channel1.Device1.Tag1"
```

Write test (explicitly enabled only):

```powershell
python .github/skills/kepware-connectivity/scripts/kepware_rest_server_smoketest.py `
  --enable-write `
  --write-tag-id "Channel1.Device1.Tag1" `
  --write-value "1"
```

## 6. Verify ports and listeners

```powershell
Get-NetTCPConnection -State Listen |
  Where-Object LocalPort -in 39320,57212,57412,57512,57413,57513,49311,49320 |
  Sort-Object LocalPort
```

## 7. Common failure patterns

- `401/403`: wrong credentials/permissions.
- `404`: wrong endpoint path or agent/tag name.
- TLS failure: certificate trust mismatch.
- CORS blocked: missing origin in REST Server allowed origins.
- write errors: write endpoint disabled or tag not writable.

## 8. Update artifacts after each integration change

- `.github/skills/kepware-connectivity/SKILL.md`
- `.github/skills/kepware-connectivity/docs/TECHNICAL.md`
- `.github/skills/kepware-connectivity/docs/USER_GUIDE.md`
- `.github/skills/kepware-connectivity/CHANGELOG.md`
- `.github/skills/kepware-connectivity/project_context.md`
