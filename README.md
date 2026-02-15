# Codex Skill: Kepware Connectivity

Samostatny repozitar pro skill `kepware-connectivity`.
Repo pokryva integraci KEPServerEX / ThingWorx Kepware Server / Kepware Edge pres OPC UA, IoT Gateway a Configuration API.

## Kdy pouzit
- Provisioning MQTT clientu a iot_items pres Config API.
- Smoke test REST Server browse/read/write.
- Hardening portu, TLS certifikatu a auth politik.

## Kdy nepouzit
- Ciste frontend/UI bez OT konektivity.
- Neodsouhlasene produkcni zasahy (mazani, reset, firewall, role, klice).

## Struktura
- `.github/skills/kepware-connectivity/SKILL.md`
- `.github/skills/kepware-connectivity/scripts/`
- `.github/skills/kepware-connectivity/docs/`
- `docs/`
- `project_context.md`

## Instalace skillu
```powershell
python C:\Users\P.J\.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py --repo CZPavel/codex-skill-kepware --path .github/skills/kepware-connectivity --name kepware-connectivity
```

## Validace
```powershell
python C:\Users\P.J\.codex\skills\.system\skill-creator\scripts\quick_validate.py .github/skills/kepware-connectivity
python .github/skills/kepware-connectivity/scripts/kepware_config_api_mqtt_bootstrap.py --help
python .github/skills/kepware-connectivity/scripts/kepware_rest_server_smoketest.py --help
```
