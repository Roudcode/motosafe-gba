#!/bin/sh
set -eu

# La misma imagen del backend se usa para la tarea programada. Un scheduler del
# proveedor puede invocar este comando una vez por ejecución; Docker Compose
# usa el ciclo para que la demo sea autónoma.
INTERVALO_MINUTOS="${SCRAPER_INTERVAL_MINUTES:-180}"
case "$INTERVALO_MINUTOS" in
  ''|*[!0-9]*) echo "SCRAPER_INTERVAL_MINUTES debe ser un entero positivo" >&2; exit 1 ;;
esac
if [ "$INTERVALO_MINUTOS" -lt 1 ]; then
  echo "SCRAPER_INTERVAL_MINUTES debe ser mayor a cero" >&2
  exit 1
fi

# Tope de tiempo por corrida (SES-080). Una corrida colgada por red no debe
# dejar el ciclo trabado: al vencer, timeout la corta y se reintenta en el
# siguiente ciclo.
TOPE_MINUTOS="${SCRAPER_TIMEOUT_MINUTES:-45}"
case "$TOPE_MINUTOS" in
  ''|*[!0-9]*) echo "SCRAPER_TIMEOUT_MINUTES debe ser un entero positivo" >&2; exit 1 ;;
esac

while true; do
  echo "[motosafe-scraper] inicio $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  if timeout "${TOPE_MINUTOS}m" python scrapear_noticias_robos.py --guardar; then
    echo "[motosafe-scraper] finalizó correctamente"
  else
    echo "[motosafe-scraper] falló o superó ${TOPE_MINUTOS} minutos; se reintentará en ${INTERVALO_MINUTOS} minutos" >&2
  fi
  sleep "$((INTERVALO_MINUTOS * 60))"
done
