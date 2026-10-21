"""
D04 -- sensibilidad real de PESO_RIESGO / UMBRAL_CRUCE_KM sobre las 4 rutas
reales generadas para D03 (mismos origenes/destinos, mismos hotspots reales
de /hotspots y /hotspots-inseguridad). Replica exactamente la logica de
frontend/src/utils/riesgoRuta.js y geoRiesgo.js (distanciaAPolilinea,
calcularZonasCruzadasPorRuta, calcularCoberturaPorFuente,
calcularRutasConScore/nivelRelativoEnLote), sin reinventar la formula --
solo parametrizada para poder variar PESO_RIESGO y UMBRAL_CRUCE_KM.
"""
import json
import math
from pathlib import Path

BASE = Path(__file__).parent

ORDEN_NIVELES = ["bajo", "medio", "alto", "critico"]


def cargar(nombre):
    with open(BASE / nombre, encoding="utf-8") as f:
        return json.load(f)


hotspots = cargar("hotspots_trim.json")          # [id, lat, lng, nivel]
insg_general = cargar("insgGeneral_trim.json")
insg_moto = cargar("insgMoto_trim.json")
rutas_por_caso = cargar("rutas_coords.json")


def zonas_unificadas():
    zonas = []
    for id_, lat, lng, nivel in hotspots:
        zonas.append({"id": f"sin-{id_}", "lat": lat, "lng": lng, "nivel": nivel, "tipo": "siniestro"})
    for id_, lat, lng, nivel in insg_general:
        zonas.append({"id": f"insg-g-{id_}", "lat": lat, "lng": lng, "nivel": nivel, "tipo": "inseguridad"})
    for id_, lat, lng, nivel in insg_moto:
        zonas.append({"id": f"insg-m-{id_}", "lat": lat, "lng": lng, "nivel": nivel, "tipo": "inseguridad"})
    return zonas


ZONAS = zonas_unificadas()


def distancia_km(a_lat, a_lng, b_lat, b_lng):
    R = 6371
    d_lat = math.radians(b_lat - a_lat)
    d_lng = math.radians(b_lng - a_lng)
    lat1 = math.radians(a_lat)
    lat2 = math.radians(b_lat)
    h = math.sin(d_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(d_lng / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def distancia_a_punto_en_segmento(p_lat, p_lng, a, b):
    lat_media = math.radians((a[0] + b[0]) / 2)
    km_lat = 111.32
    km_lng = 111.32 * math.cos(lat_media)
    ax, ay = a[1] * km_lng, a[0] * km_lat
    bx, by = b[1] * km_lng, b[0] * km_lat
    px, py = p_lng * km_lng, p_lat * km_lat
    dx, dy = bx - ax, by - ay
    largo2 = dx * dx + dy * dy
    t = ((px - ax) * dx + (py - ay) * dy) / largo2 if largo2 > 0 else 0
    t = max(0, min(1, t))
    cx, cy = ax + t * dx, ay + t * dy
    return math.hypot(px - cx, py - cy)


def distancia_a_polilinea(p_lat, p_lng, coords):
    if not coords:
        return float("inf")
    if len(coords) == 1:
        return distancia_km(p_lat, p_lng, coords[0][0], coords[0][1])
    return min(distancia_a_punto_en_segmento(p_lat, p_lng, coords[i], coords[i + 1]) for i in range(len(coords) - 1))


def zonas_cruzadas(ruta_coords, umbral_km):
    cruces = []
    for z in ZONAS:
        d = distancia_a_polilinea(z["lat"], z["lng"], ruta_coords)
        if d <= umbral_km:
            cruces.append({**z, "dist": d})
    return cruces


def cobertura_por_fuente(ruta_coords, umbral_km):
    out = {}
    for fuente in ("siniestro", "inseguridad"):
        zonas_f = [z for z in ZONAS if z["tipo"] == fuente]
        puntos = ruta_coords
        if len(puntos) > 120:
            paso = math.ceil(len(puntos) / 120)
            puntos = puntos[::paso]
        cubiertos = sum(
            1 for (lat, lng) in puntos
            if any(distancia_km(lat, lng, z["lat"], z["lng"]) <= umbral_km for z in zonas_f)
        )
        out[fuente] = cubiertos / len(puntos) if puntos else 0
    return out


def nivel_relativo_en_lote(score, indice, scores):
    if score == 0:
        return "bajo"
    if len(scores) <= 1:
        return "medio" if score <= 4 else "alto"
    if len(set(scores)) == 1:
        return "medio" if score <= 4 else "alto"
    ordenados = sorted(scores)
    rank = ordenados.index(score)
    percentil = rank / (len(ordenados) - 1)
    es_peor = score == ordenados[-1]
    otros = [s for j, s in enumerate(scores) if j != indice]
    promedio_otros = sum(otros) / len(otros) if otros else 0
    if es_peor and promedio_otros > 0 and score >= promedio_otros * 1.4:
        return "critico"
    if percentil >= 0.6:
        return "alto"
    if percentil >= 0.3:
        return "medio"
    return "bajo"


def evaluar_caso(rutas, peso_riesgo, umbral_cruce_km):
    resultados = []
    for r in rutas:
        coords = r["coords"]
        cruces = zonas_cruzadas(coords, umbral_cruce_km)
        riesgo = sum(peso_riesgo[z["nivel"]] for z in cruces)
        cobertura = cobertura_por_fuente(coords, umbral_cruce_km)
        resultados.append({
            "km": r["km"], "min": r["min"], "riesgo": riesgo,
            "n_cruces": len(cruces), "cobertura": cobertura,
        })
    scores = [r["riesgo"] for r in resultados]
    for i, r in enumerate(resultados):
        r["nivel_relativo"] = nivel_relativo_en_lote(r["riesgo"], i, scores)
    return resultados


CONFIGURACIONES = {
    "base (PESO_RIESGO actual, UMBRAL_CRUCE_KM=0.6)": {
        "peso": {"bajo": 1, "medio": 2, "alto": 3, "critico": 5},
        "umbral": 0.6,
    },
    "peso_lineal (bajo=1,medio=2,alto=3,critico=4)": {
        "peso": {"bajo": 1, "medio": 2, "alto": 3, "critico": 4},
        "umbral": 0.6,
    },
    "peso_agresivo (critico=8)": {
        "peso": {"bajo": 1, "medio": 2, "alto": 3, "critico": 8},
        "umbral": 0.6,
    },
    "umbral_mas_estricto (0.3 km)": {
        "peso": {"bajo": 1, "medio": 2, "alto": 3, "critico": 5},
        "umbral": 0.3,
    },
    "umbral_mas_laxo (1.0 km)": {
        "peso": {"bajo": 1, "medio": 2, "alto": 3, "critico": 5},
        "umbral": 1.0,
    },
}


def main():
    for nombre_caso, rutas in rutas_por_caso.items():
        print(f"\n=== {nombre_caso} ===")
        for nombre_cfg, cfg in CONFIGURACIONES.items():
            resultados = evaluar_caso(rutas, cfg["peso"], cfg["umbral"])
            orden_rapida = min(range(len(resultados)), key=lambda i: resultados[i]["min"])
            orden_segura = min(range(len(resultados)), key=lambda i: resultados[i]["riesgo"])
            print(f"  -- {nombre_cfg} --  (mas_rapida=Ruta{orden_rapida+1}, menor_riesgo=Ruta{orden_segura+1})")
            for i, r in enumerate(resultados):
                print(f"     Ruta{i+1}: km={r['km']} min={r['min']} riesgo={r['riesgo']} "
                      f"n_cruces={r['n_cruces']} nivel_relativo={r['nivel_relativo']} "
                      f"cob_sin={r['cobertura']['siniestro']:.2f} cob_inseg={r['cobertura']['inseguridad']:.2f}")


if __name__ == "__main__":
    main()
