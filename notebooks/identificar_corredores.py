# -*- coding: utf-8 -*-
"""
Identifica "corredores de riesgo": calles con muchos siniestros a lo largo de su
extension, en vez de zonas puntuales (los 430 hotspots de DBSCAN). Se corre una
sola vez (analogo a como se generan los hotspots), sin red: solo agrupa datos
que ya estan en el repo. El resultado (data/corredores_candidatos.csv) despues
se le pasa a notebooks/fetch_corredores_geometria.py, que si necesita red (pega
a OSRM) y por eso lo corre el usuario en su propia maquina.
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

def punto_extremo(grupo):
    """Los dos puntos mas alejados entre si del grupo (aproximacion planar,
    suficiente para elegir extremos de una avenida dentro de CABA)."""
    lat = grupo['latitud_siniestro'].to_numpy()
    lon = grupo['longitud_siniestro'].to_numpy()
    if len(lat) == 1:
        return lat[0], lon[0], lat[0], lon[0]
    # distancias en grados (no hace falta haversine exacto solo para elegir el par mas lejano)
    dlat = lat[:, None] - lat[None, :]
    dlon = (lon[:, None] - lon[None, :]) * np.cos(np.radians(lat.mean()))
    dist2 = dlat ** 2 + dlon ** 2
    i, j = np.unravel_index(np.argmax(dist2), dist2.shape)
    return lat[i], lon[i], lat[j], lon[j]

filas = []
for calle, grupo in con_calle.groupby('calle'):
    cantidad = len(grupo)
    if cantidad < UMBRAL_MIN_SINIESTROS:
        continue
    mortales = int((grupo['gravedad_siniestro'] == 'MORTAL').sum())
    graves = int((grupo['gravedad_siniestro'] == 'GRAVE').sum())
    lat_a, lng_a, lat_b, lng_b = punto_extremo(grupo)
    filas.append({
        'calle': calle,
        'cantidad_siniestros': cantidad,
        'mortales': mortales,
        'graves': graves,
        'comuna_moda': grupo['comuna'].mode().iloc[0] if not grupo['comuna'].mode().empty else None,
        'tipo_via_moda': grupo['tipo_de_via_siniestro'].mode().iloc[0] if not grupo['tipo_de_via_siniestro'].mode().empty else 'AVENIDA',
        'contraparte_moda': grupo['contraparte_siniestro'].mode().iloc[0] if not grupo['contraparte_siniestro'].mode().empty else 'AUTO',
        'edad_promedio': round(float(grupo['edad_victima'].mean()), 1),
        'sexo_moda': grupo['sexo_victima'].mode().iloc[0] if not grupo['sexo_victima'].mode().empty else 'SD',
        'lat_a': lat_a, 'lng_a': lng_a, 'lat_b': lat_b, 'lng_b': lng_b,
    })

candidatos = pd.DataFrame(filas).sort_values('cantidad_siniestros', ascending=False)
candidatos.to_csv(f"{BASE}/data/corredores_candidatos.csv", index=False)
print(f'{len(candidatos)} calles candidatas a corredor (>= {UMBRAL_MIN_SINIESTROS} siniestros), guardadas en data/corredores_candidatos.csv')
print(candidatos[['calle', 'cantidad_siniestros', 'mortales', 'graves']].head(15).to_string(index=False))
