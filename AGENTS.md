# AGENTS Instructions

## Validace skillu
```powershell
python C:\Users\P.J\.codex\skills\.system\skill-creator\scripts\quick_validate.py .github/skills/kepware-connectivity
python .github/skills/kepware-connectivity/scripts/kepware_config_api_mqtt_bootstrap.py --help
python .github/skills/kepware-connectivity/scripts/kepware_rest_server_smoketest.py --help
```

## Instalacni test
```powershell
python C:\Users\P.J\.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py --repo CZPavel/codex-skill-kepware --path .github/skills/kepware-connectivity --dest C:\PYTHON_test\_skill_split_work\install_test\skills
```

## Publikace
- Zakaz force push.
- Pred releasem aktualizovat `CHANGELOG.md` a `VALIDATION.md`.
- Pred push overit, ze v repu nejsou tajemstvi.
