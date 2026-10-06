"""E2E HTTP de MotoSafe GBA (SES-068).

Recorre la misma cadena que el navegador: frontend servido por Vite (build de
producción con `vite preview`) -> proxy /api -> backend FastAPI -> PostGIS.
No usa mocks. Pensado para una instancia aislada (base efímera), nunca para la
base personal ni para el :5173/:8000 que publica Tailscale Funnel.

Variables de entorno:
    E2E_BASE   URL del frontend, ej. http://localhost:4173
    E2E_USER   usuario de prueba de esa instancia
    E2E_PASS   contraseña de prueba de esa instancia

Imprime un renglón por verificación y termina con código 1 si alguna falla.
"""
import os
import sys
import uuid
from collections import Counter

import httpx

BASE = os.environ['E2E_BASE'].rstrip('/') + '/api'
fallas = []


def verificar(nombre, condicion, detalle=''):
    print(f"{'OK ' if condicion else 'FALLA'} {nombre}{(' — ' + detalle) if detalle else ''}")
    if not condicion:
        fallas.append(nombre)


with httpx.Client(timeout=60) as c:
    r = c.get(f'{BASE}/hotspots')
    verificar('sin sesión /hotspots responde 401', r.status_code == 401, str(r.status_code))

    r = c.post(f'{BASE}/auth/login', json={'username': os.environ['E2E_USER'], 'password': 'incorrecta'})
    verificar('login con contraseña incorrecta responde 401', r.status_code == 401, str(r.status_code))
    r = c.post(f'{BASE}/auth/login', json={'username': os.environ['E2E_USER'], 'password': os.environ['E2E_PASS']})
    verificar('login correcto responde 200', r.status_code == 200, str(r.status_code))
    # La cookie de sesión es Secure (auth.py). Un navegador la reenvía a
    # http://localhost porque lo considera contexto seguro; httpx no, así que se
    # reenvía a mano. Se verifica también que salga con HttpOnly y Secure.
    set_cookie = r.headers.get('set-cookie', '')
    verificar('cookie de sesión HttpOnly, Secure y SameSite=Lax',
              all(x in set_cookie.lower() for x in ('httponly', 'secure', 'samesite=lax')))
    c.headers['Cookie'] = set_cookie.split(';', 1)[0]
    r = c.get(f'{BASE}/auth/me')
    verificar('/auth/me con sesión', r.status_code == 200 and r.json().get('auth_habilitado') is True, r.text[:80])

    salud = c.get(f'{BASE}/health').json()
    verificar('/health ok, umbrales y scikit-learn coinciden',
              salud.get('estado') == 'ok' and salud.get('umbrales_riesgo_actualizados') and salud.get('version_sklearn_coincide'),
              str(salud))

    r = c.get(f'{BASE}/hotspots')
    hotspots = r.json() if r.status_code == 200 else []
    niveles = Counter(h['nivel_riesgo'] for h in hotspots)
    verificar('/hotspots devuelve 740 zonas con nivel y clima', r.status_code == 200 and len(hotspots) == 740
              and all('clima' in h for h in hotspots), f'{len(hotspots)} zonas, niveles {dict(niveles)}')

    r = c.get(f'{BASE}/corredores')
    verificar('/corredores devuelve 243', r.status_code == 200 and len(r.json()) == 243, f'{r.status_code} {len(r.json()) if r.status_code == 200 else ""}')
    for tipo, esperado in (('general', 633), ('moto', 502)):
        r = c.get(f'{BASE}/hotspots-inseguridad', params={'tipo': tipo})
        datos = r.json() if r.status_code == 200 else []
        verificar(f'/hotspots-inseguridad {tipo} devuelve {esperado}', len(datos) == esperado
                  and all('ajustado_por_horario' in d for d in datos),
                  f'{len(datos)}; ajustadas por horario: {sum(bool(d.get("ajustado_por_horario")) for d in datos)}')

    r = c.post(f'{BASE}/predecir', json={'hora': 22, 'dia_semana': 'Saturday', 'comuna': '1',
                                          'tipo_de_via': 'AVENIDA', 'contraparte': 'AUTO'})
    proba = r.json() if r.status_code == 200 else {}
    probabilidades = proba.get('probabilidades', {})
    verificar('/predecir devuelve probabilidades que suman 1', r.status_code == 200
              and set(probabilidades) == {'GRAVE', 'LEVE', 'MORTAL'}
              and abs(sum(probabilidades.values()) - 1) < 0.01, str(probabilidades))

    autor_a, autor_b = str(uuid.uuid4()), str(uuid.uuid4())
    r = c.post(f'{BASE}/reportes', json={'lat': -34.6037, 'lng': -58.3816, 'categoria': 'robo', 'autor_id': autor_a})
    nuevo = r.json() if r.status_code == 201 else {}
    verificar('crear reporte responde 201 con token de borrado', r.status_code == 201 and len(nuevo.get('delete_token', '')) >= 32, str(r.status_code))
    rid = nuevo.get('id')

    listado = c.get(f'{BASE}/reportes').json()
    listado = listado if isinstance(listado, list) else []
    propio = next((x for x in listado if x.get('id') == rid), None)
    verificar('GET /reportes lo lista sin exponer token ni autor',
              propio is not None and 'delete_token' not in propio and 'autor_id' not in propio)

    r = c.post(f'{BASE}/reportes/{rid}/confirmar', json={'autor_id': autor_a, 'tipo': 'confirma'})
    verificar('el autor no puede confirmar su propio reporte', 400 <= r.status_code < 500, str(r.status_code))
    r = c.post(f'{BASE}/reportes/{rid}/confirmar', json={'autor_id': autor_b, 'tipo': 'confirma'})
    verificar('otro dispositivo confirma (201)', r.status_code == 201, str(r.status_code))
    # Un segundo voto del mismo dispositivo actualiza el anterior (UNIQUE +
    # ON CONFLICT DO UPDATE en main.py), no lo suma.
    r = c.post(f'{BASE}/reportes/{rid}/confirmar', json={'autor_id': autor_b, 'tipo': 'desmiente'})
    votos = next((x for x in c.get(f'{BASE}/reportes').json() if x.get('id') == rid), {})
    verificar('cambiar el voto lo reemplaza: 0 confirmaciones y 1 desmentida',
              r.status_code == 201 and votos.get('confirmaciones') == 0 and votos.get('desmentidas') == 1,
              f"{r.status_code}; confirmaciones={votos.get('confirmaciones')} desmentidas={votos.get('desmentidas')}")

    r = c.delete(f'{BASE}/reportes/{rid}', headers={'X-Report-Delete-Token': 'x' * 40})
    verificar('borrar con token inválido responde 404', r.status_code == 404, str(r.status_code))
    r = c.delete(f'{BASE}/reportes/{rid}', headers={'X-Report-Delete-Token': nuevo.get('delete_token', '')})
    verificar('borrar con el token correcto', r.status_code in (200, 204), str(r.status_code))
    restantes = c.get(f'{BASE}/reportes').json()
    verificar('el reporte ya no aparece', isinstance(restantes, list) and all(x.get('id') != rid for x in restantes))

    r = c.get(f'{BASE}/reportes-prensa')
    verificar('/reportes-prensa responde 200', r.status_code == 200, f'{r.status_code}, {len(r.json()) if r.status_code == 200 else ""} filas')

    # Obelisco -> Plaza Italia: ruta real con TomTom (consume la clave del .env local).
    r = c.get(f'{BASE}/rutas', params={'origen_lat': -34.6037, 'origen_lng': -58.3816,
                                        'destino_lat': -34.5810, 'destino_lng': -58.4210})
    rutas = r.json() if r.status_code == 200 else []
    verificar('/rutas devuelve al menos una ruta con pasos', r.status_code == 200 and rutas and rutas[0]['pasos'],
              f'{r.status_code}; ' + '; '.join(f"{x['km']} km {x['min']} min" for x in rutas))

    r = c.get(f'{BASE}/trafico/tiles/12/1382/2466.png')
    verificar('tesela de tráfico PNG', r.status_code == 200 and r.content[:4] == b'\x89PNG', f'{r.status_code} {r.headers.get("content-type")}')

    c.post(f'{BASE}/auth/logout')
    c.headers.pop('Cookie', None)  # el navegador borra la cookie con la respuesta de logout
    r = c.get(f'{BASE}/auth/me')
    verificar('después de salir /auth/me responde 401', r.status_code == 401, str(r.status_code))

print(f'\n{len(fallas)} fallas' + (f": {', '.join(fallas)}" if fallas else ''))
sys.exit(1 if fallas else 0)
