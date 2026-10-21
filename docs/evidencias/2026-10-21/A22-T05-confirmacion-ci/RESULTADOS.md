# A22 / T05 — confirmación de la primera corrida de CI en GitHub (2026-10-21, SES-149)

`gh` no estaba autenticado en esta máquina (`gh auth status` → "not logged into any GitHub hosts"). Se le
preguntó explícitamente a Rodo antes de intentar nada, como pidió; Rodo autorizó y corrió él mismo el paso
sensible (entrar a `github.com/login/device` y confirmar el código de un solo uso en su navegador real —
nunca se le pidió ni se vio su contraseña). Verificado después: `gh auth status` → logueado como
`Roudcode`, scopes `gist, read:org, repo`.

## Último workflow run

`gh run list --limit 5`: los 5 últimos runs en `main` son `success`. El más reciente:

- **Run**: [39613631419](https://github.com/Roudcode/motosafe-gba/actions/runs/39613631419)
- **Commit**: "Prepara etiquetado humano de prensa sin asignar resultados"
- **Resultado**: ✓ success, 2 jobs, ambos verdes.

### Job `frontend`

```
✓ npm ci
✓ npm run lint
✓ npm test
✓ npm run build
```

### Job `backend-sintaxis`

```
✓ python -m py_compile backend/main.py backend/migrar.py backend/evaluar_extractor_prensa.py
✓ pip install --require-hashes -r backend/requirements.lock
✓ python -m pytest -q
```

Del log real del job: contenedor de servicio real `postgis/postgis:16-3.4` (no un mock), `python-version:
3.12`, instalación completa con hashes vía `requirements.lock`, y **"146 passed, 1 warning in 16.27s"**.

## Conclusión

El CI corre limpio en GitHub tal como describe T05 (lint/tests/build del frontend, sintaxis Python 3.12 e
instalación `--require-hashes` del backend, tests reales contra PostGIS). El pendiente de A22/T05 ("falta
la corrida confirmada en GitHub") queda cerrado con este run real verificado.
