# -*- coding: utf-8 -*-
"""
Identifica "corredores de riesgo": calles con muchos siniestros a lo largo de su
extension, en vez de zonas puntuales (los 740 hotspots de HDBSCAN). Se corre una
sola vez (analogo a como se generan los hotspots), sin red: solo agrupa datos
que ya estan en el repo. El resultado (data/corredores_candidatos.csv) despues
se le pasa a notebooks/fetch_corredores_geometria.py, que si necesita red (pega
a OSRM) y por eso lo corre el usuario en su propia maquina.

v2: cada calle larga se parte en sub-tramos (hasta 8, segun cuantos siniestros
tenga) en vez de agregar toda la avenida en un solo perfil. La primera version
agregaba por avenida entera y el contexto tipico (comuna/tipo de via/contraparte
mas frecuente) terminaba siendo casi el mismo para las 131 calles -- 95% caia
en nivel "alto" porque la moda de "contraparte" daba AUTO en el 100% de los
casos, y se perdia toda la variacion real que si existe a lo largo de una
avenida de 20km como Av. Gral. Paz. Partir en tramos devuelve esa variacion:
cada tramo tiene su propio perfil y su propio nivel de riesgo.
"""
import re
import pandas as pd
import numpy as np

BASE = "."

motos = pd.read_csv(f"{BASE}/data/motos_limpio.csv")
motos['contraparte_siniestro'] = motos['contraparte_siniestro'].str.strip().str.upper()
motos['tipo_de_via_siniestro'] = motos['tipo_de_via_siniestro'].str.strip().str.upper()

victimas = pd.read_csv(f"{BASE}/data/siniestros_viales_victimas.csv", encoding='utf-8-sig', sep=';', low_memory=False)
victimas['modo_desplazamiento_victima'] = victimas['modo_desplazamiento_victima'].str.strip().str.upper()
victimas['sexo_victima'] = victimas['sexo_victima'].str.strip().str.upper()
victimas_moto = victimas[victimas['modo_desplazamiento_victima'] == 'MOTO'].copy()
victimas_moto['edad_victima'] = pd.to_numeric(victimas_moto['edad_victima'], errors='coerce')
resumen_victima = victimas_moto.groupby('id_siniestro').agg(
    edad_victima=('edad_victima', 'mean'),
    sexo_victima=('sexo_victima', lambda x: x.mode().iloc[0] if not x.mode().empty else 'SD')
).reset_index()

motos = motos.merge(resumen_victima, on='id_siniestro', how='left')
motos.loc[(motos['edad_victima'] < 14) | (motos['edad_victima'] > 95), 'edad_victima'] = None
mediana_edad = motos['edad_victima'].median()
motos['edad_victima'] = motos['edad_victima'].fillna(mediana_edad)
motos['sexo_victima'] = motos['sexo_victima'].fillna('SD')
motos['comuna'] = motos['comuna'].astype('Int64').astype(str)

# --- calle primaria a partir de la direccion normalizada ---
# El campo trae intersecciones ("AV. X y CALLE Y") o direccion + altura ("AV. X 5925").
# Se toma la primera calle antes del " y " y se le saca el numero de altura al
# final, para que todos los siniestros de una misma avenida (distintas alturas
# o distintas bocacalles) queden agrupados bajo el mismo nombre de calle.
def calle_primaria(direccion):
    if pd.isna(direccion):
        return None
    partes = re.split(r'\s+[Yy]\s+', direccion, maxsplit=1)
    primaria = partes[0].strip()
    primaria = re.sub(r'\s+\d{2,6}(\s*\(.*\))?$', '', primaria).strip()
    primaria = primaria.rstrip(',').strip()
    return primaria or None

motos['calle'] = motos['direccion_normalizada_siniestro'].apply(calle_primaria)
con_calle = motos.dropna(subset=['calle', 'latitud_siniestro', 'longitud_siniestro']).copy()
print(f'Siniestros con calle identificable: {len(con_calle)} de {len(motos)}')

UMBRAL_MIN_SINIESTROS = 30
SINIESTROS_POR_TRAMO_OBJETIVO = 40
MAX_TRAMOS_POR_CALLE = 8


def punto_mas_lejano(lat, lon):
    """Los dos puntos mas alejados entre si de un conjunto (aproximacion
    planar, suficiente para elegir extremos dentro de CABA)."""
    if len(lat) == 1:
        return 0, 0
    dlat = lat[:, None] - lat[None, :]
    dlon = (lon[:, None] - lon[None, :]) * np.cos(np.radians(lat.mean()))
    dist2 = dlat ** 2 + dlon ** 2
    i, j = np.unravel_index(np.argmax(dist2), dist2.shape)
    return i, j


def stats_de_grupo(grupo):
    return {
        'cantidad_siniestros': len(grupo),
        'mortales': int((grupo['gravedad_siniestro'] == 'MORTAL').sum()),
        'graves': int((grupo['gravedad_siniestro'] == 'GRAVE').sum()),
        'comuna_moda': grupo['comuna'].mode().iloc[0] if not grupo['comuna'].mode().empty else None,
        'tipo_via_moda': grupo['tipo_de_via_siniestro'].mode().iloc[0] if not grupo['tipo_de_via_siniestro'].mode().empty else 'AVENIDA',
        'contraparte_moda': grupo['contraparte_siniestro'].mode().iloc[0] if not grupo['contraparte_siniestro'].mode().empty else 'AUTO',
        'edad_promedio': round(float(grupo['edad_victima'].mean()), 1),
        'sexo_moda': grupo['sexo_victima'].mode().iloc[0] if not grupo['sexo_victima'].mode().empty else 'SD',
    }


filas = []
for calle, grupo in con_calle.groupby('calle'):
    cantidad = len(grupo)
    if cantidad < UMBRAL_MIN_SINIESTROS:
        continue

    lat = grupo['latitud_siniestro'].to_numpy()
    lon = grupo['longitud_siniestro'].to_numpy()
    n_tramos = max(1, min(MAX_TRAMOS_POR_CALLE, cantidad // SINIESTROS_POR_TRAMO_OBJETIVO))

    if n_tramos == 1:
        i, j = punto_mas_lejano(lat, lon)
        stats = stats_de_grupo(grupo)
        stats.update({
            'calle': calle, 'tramo': 1, 'tramos_totales': 1,
            'lat_a': lat[i], 'lng_a': lon[i], 'lat_b': lat[j], 'lng_b': lon[j],
        })
        filas.append(stats)
        continue

    # Se proyectan los puntos sobre el eje que une los dos extremos de TODA la
    # calle, se ordenan por esa proyeccion (de punta a punta de la avenida) y
    # se parte en n_tramos contiguos: cada tramo es un pedazo real y continuo
    # de la calle, no una muestra aleatoria de puntos.
    i, j = punto_mas_lejano(lat, lon)
    eje_lat, eje_lon = lat[j] - lat[i], (lon[j] - lon[i]) * np.cos(np.radians(lat.mean()))
    norma2 = eje_lat ** 2 + eje_lon ** 2
    t = ((lat - lat[i]) * eje_lat + (lon - lon[i]) * eje_lon * np.cos(np.radians(lat.mean()))) / norma2
    orden = np.argsort(t)

    grupo_ordenado = grupo.iloc[orden].reset_index(drop=True)
    lat_ordenado = lat[orden]
    lon_ordenado = lon[orden]

    for num_tramo, idxs in enumerate(np.array_split(np.arange(len(grupo_ordenado)), n_tramos), start=1):
        sub = grupo_ordenado.iloc[idxs]
        stats = stats_de_grupo(sub)
        stats.update({
            'calle': calle, 'tramo': num_tramo, 'tramos_totales': n_tramos,
            'lat_a': lat_ordenado[idxs[0]], 'lng_a': lon_ordenado[idxs[0]],
            'lat_b': lat_ordenado[idxs[-1]], 'lng_b': lon_ordenado[idxs[-1]],
        })
        filas.append(stats)

candidatos = pd.DataFrame(filas).sort_values(['cantidad_siniestros'], ascending=False)
candidatos.to_csv(f"{BASE}/data/corredores_candidatos.csv", index=False)
print(f'{len(candidatos)} tramos de corredor generados (de {candidatos["calle"].nunique()} calles con >= {UMBRAL_MIN_SINIESTROS} siniestros)')
print(candidatos[['calle', 'tramo', 'tramos_totales', 'cantidad_siniestros', 'mortales', 'graves', 'contraparte_moda']].head(20).to_string(index=False))
