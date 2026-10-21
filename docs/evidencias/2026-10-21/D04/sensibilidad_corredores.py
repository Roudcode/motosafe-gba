"""
D04 -- sensibilidad real de clustering de corredores (notebooks/identificar_corredores.py).
Misma logica EXACTA del script canonico (lectura de data/motos_limpio.csv +
data/siniestros_viales_victimas.csv reales, agrupacion por calle, particion en
tramos), parametrizada para variar UMBRAL_MIN_SINIESTROS, SINIESTROS_POR_TRAMO_OBJETIVO
y MAX_TRAMOS_POR_CALLE sin tocar data/corredores_candidatos.csv real.
No usa red (el agrupamiento es offline; el script original ya lo documenta asi).
"""
import re
from pathlib import Path

import pandas as pd
import numpy as np

BASE = Path(__file__).resolve().parent.parent.parent.parent.parent

motos = pd.read_csv(BASE / "data/motos_limpio.csv")
motos['contraparte_siniestro'] = motos['contraparte_siniestro'].str.strip().str.upper()
motos['tipo_de_via_siniestro'] = motos['tipo_de_via_siniestro'].str.strip().str.upper()


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


def generar_candidatos(umbral_min_siniestros, siniestros_por_tramo_objetivo, max_tramos_por_calle):
    filas = []
    for calle, grupo in con_calle.groupby('calle'):
        cantidad = len(grupo)
        if cantidad < umbral_min_siniestros:
            continue
        n_tramos = max(1, min(max_tramos_por_calle, cantidad // siniestros_por_tramo_objetivo))
        filas.append({'calle': calle, 'cantidad_siniestros': cantidad, 'n_tramos': n_tramos})
    return pd.DataFrame(filas).sort_values('cantidad_siniestros', ascending=False)


CONFIGURACIONES = {
    "base (30 / 40 / 8, la vigente en el repo)": (30, 40, 8),
    "umbral_mas_bajo (20 / 40 / 8)": (20, 40, 8),
    "umbral_mas_alto (50 / 40 / 8)": (50, 40, 8),
    "tramos_mas_finos (30 / 25 / 8)": (30, 25, 8),
    "tramos_mas_gruesos (30 / 60 / 8)": (30, 60, 8),
}

resultados = {}
for nombre, (umin, obj, maxt) in CONFIGURACIONES.items():
    df = generar_candidatos(umin, obj, maxt)
    resultados[nombre] = df

base_calles = set(resultados["base (30 / 40 / 8, la vigente en el repo)"]['calle'])

print(f"Total siniestros de moto con calle identificable: {len(con_calle)}\n")
for nombre, df in resultados.items():
    calles = set(df['calle'])
    tramos_totales = int(df['n_tramos'].sum())
    entran = calles - base_calles
    salen = base_calles - calles
    print(f"-- {nombre} --")
    print(f"   {len(df)} calles candidatas, {tramos_totales} tramos totales generados")
    if nombre != "base (30 / 40 / 8, la vigente en el repo)":
        print(f"   vs base: +{len(entran)} calles nuevas, -{len(salen)} calles que salen")
        if entran:
            print(f"   nuevas: {sorted(entran)[:10]}{'...' if len(entran) > 10 else ''}")
        if salen:
            print(f"   salen: {sorted(salen)[:10]}{'...' if len(salen) > 10 else ''}")
    print()

print("Top 10 calles por cantidad de siniestros (igual en todas las configuraciones, no cambia el orden, solo el corte):")
print(resultados["base (30 / 40 / 8, la vigente en el repo)"].head(10).to_string(index=False))
