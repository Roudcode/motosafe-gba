"""Revisa las notas que geocodificar_en_zona dejó sin ubicar en la corrida de
prueba (corrida_dry_run.txt): qué devolvía Nominatim, en qué partido según el
validador y según display_name (texto completo de OSM), para separar
abstenciones correctas de rechazos de más."""
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import medir_zonas as m  # noqa: E402  (reusa la caché y el mismo pedido)

s = m.s
filas = []
for linea in (AQUI / 'corrida_dry_run_antes_del_ajuste.txt').read_text(encoding='utf-8').splitlines():
    hallado = re.search(r'fuera de (.+?) -- query: "(.+?)"\] (.+)$', linea)
    if not hallado:
        continue
    zona_txt, query, titulo = hallado.groups()
    zona, localidad = s.encontrar_zona(titulo) or (None, 'CABA')
    nivel = 'calle' if re.search(r' \d{2,5},', query) else ('interseccion' if ' y ' in query.split(',')[0] else 'barrio')
    r = m.buscar_con_cache(query)
    fila = {'titulo': titulo[:90], 'query': query, 'zona': zona_txt}
    if r is None:
        fila.update(resultado='sin resultado')
    else:
        fila.update(resultado=r.get('display_name', '')[:120], partido_validador=s._partido_del_resultado(r.get('address', {}), r.get('display_name', '')),
                    state=r.get('address', {}).get('state'))
    filas.append(fila)
    print(json.dumps(fila, ensure_ascii=False))
(AQUI / 'rechazos.json').write_text(json.dumps(filas, ensure_ascii=False, indent=1), encoding='utf-8')
