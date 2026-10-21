# -*- coding: utf-8 -*-
"""
D05 -- monitor de cambios en calidad de datos. Corre ANTES de
`promover_artefactos.py --confirmar` (depende de A20/A22, ya cerrados) y
compara el candidato nuevo (normalmente `data/`, recien generado por el
pipeline) contra lo vigente (normalmente `backend/`, lo que ya sirve
produccion), buscando tres cosas, con numeros reales, nunca en silencio:

  1. Cambios de esquema: columnas nuevas/desaparecidas o de tipo distinto en
     cada CSV, y columnas nuevas/desaparecidas en `columnas_modelo.pkl` (el
     esquema de features que espera el modelo).
  2. Cambios relevantes en la proporcion de faltantes por columna (umbral
     configurable, UMBRAL_FALTANTES_PP puntos porcentuales por defecto).
  3. Un salto fuerte en lo que mide `limpieza_geografica_comun.py`
     (coordenada_cero / fuera_de_gba / duplicado_exacto como proporcion del
     total) en los archivos con coordenadas reales (motos_limpio.csv,
     delitos_caba.csv).

Es SOLO un reporte: nunca bloquea nada ni decide por su cuenta. La decision
de correr `--confirmar` sigue siendo de Rodo -- este script no se invoca
desde `promover_artefactos.py` ni desde ningun otro paso automatico.

Uso (desde la raiz del repo):
    python notebooks/monitor_calidad_datos.py --vigente backend --candidato data
    python notebooks/monitor_calidad_datos.py --vigente data --candidato /ruta/a/copia/alterada

`--vigente`/`--candidato` son carpetas: el script busca en cada una los
mismos nombres de archivo conocidos (CSV_CONOCIDOS, PKL_CONOCIDOS) y compara
los que existan en ambas. Un archivo que solo existe en una de las dos
carpetas se reporta aparte (no es un error, pero es un cambio real).
"""
import argparse
import pickle
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from limpieza_geografica_comun import limpiar_coordenadas  # noqa: E402

UMBRAL_FALTANTES_PP = 5.0  # puntos porcentuales de faltantes para marcar un cambio como relevante
UMBRAL_GEO_PP = 1.0  # puntos porcentuales de (0,0)/fuera_de_gba/duplicado para marcar un salto como relevante
UMBRAL_GEO_FILAS = 100  # ademas del umbral porcentual: un salto en CANTIDAD de filas tambien cuenta,
# para no perder un problema real en un dataset grande (ej. 3000 filas nuevas en (0,0) es solo +0,2 pp
# sobre 1,4 millones de delitos, pero son 3000 filas reales con un problema real -- medido de verdad en
# esta sesion, no un umbral teorico).

CSV_CONOCIDOS = [
    "hotspots_contexto.csv",
    "indice_inseguridad_comuna.csv",
    "motos_limpio.csv",
    "delitos_caba.csv",
]
PKL_CONOCIDOS = ["columnas_modelo.pkl"]

# (archivo, columna_lat, columna_lng): donde aplica el chequeo geografico de A20.
ARCHIVOS_CON_COORDENADAS = [
    ("motos_limpio.csv", "latitud_siniestro", "longitud_siniestro"),
    ("delitos_caba.csv", "latitud", "longitud"),
]


def _leer_csv(ruta):
    return pd.read_csv(ruta, low_memory=False) if ruta.is_file() else None


def comparar_esquema_csv(nombre, df_vigente, df_candidato):
    cols_v, cols_c = set(df_vigente.columns), set(df_candidato.columns)
    nuevas = sorted(cols_c - cols_v)
    desaparecidas = sorted(cols_v - cols_c)
    tipos_distintos = [
        (c, str(df_vigente[c].dtype), str(df_candidato[c].dtype))
        for c in sorted(cols_v & cols_c)
        if df_vigente[c].dtype != df_candidato[c].dtype
    ]
    return {"nuevas": nuevas, "desaparecidas": desaparecidas, "tipos_distintos": tipos_distintos}


def comparar_faltantes(df_vigente, df_candidato):
    cambios = []
    for c in sorted(set(df_vigente.columns) & set(df_candidato.columns)):
        pct_v = df_vigente[c].isna().mean() * 100
        pct_c = df_candidato[c].isna().mean() * 100
        delta = pct_c - pct_v
        if abs(delta) >= UMBRAL_FALTANTES_PP:
            cambios.append((c, round(pct_v, 2), round(pct_c, 2), round(delta, 2)))
    return cambios


def comparar_geo(nombre, lat_col, lng_col, df_vigente, df_candidato):
    if lat_col not in df_vigente.columns or lat_col not in df_candidato.columns:
        return None
    _, resumen_v = limpiar_coordenadas(df_vigente, lat_col, lng_col, f"{nombre} (vigente)")
    _, resumen_c = limpiar_coordenadas(df_candidato, lat_col, lng_col, f"{nombre} (candidato)")
    saltos = []
    for motivo in ("coordenada_cero", "fuera_de_gba", "duplicado_exacto"):
        pct_v = resumen_v[motivo] / resumen_v["total_entrada"] * 100 if resumen_v["total_entrada"] else 0
        pct_c = resumen_c[motivo] / resumen_c["total_entrada"] * 100 if resumen_c["total_entrada"] else 0
        delta_pct = pct_c - pct_v
        delta_filas = resumen_c[motivo] - resumen_v[motivo]
        if abs(delta_pct) >= UMBRAL_GEO_PP or abs(delta_filas) >= UMBRAL_GEO_FILAS:
            saltos.append((motivo, round(pct_v, 3), round(pct_c, 3), round(delta_pct, 3), delta_filas))
    return {"resumen_vigente": resumen_v, "resumen_candidato": resumen_c, "saltos": saltos}


def comparar_pkl_columnas(df_v_cols, df_c_cols):
    set_v, set_c = set(df_v_cols), set(df_c_cols)
    return {"nuevas": sorted(set_c - set_v), "desaparecidas": sorted(set_v - set_c)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vigente", required=True, help="Carpeta con los archivos vigentes (ej. backend/ o data/)")
    ap.add_argument("--candidato", required=True, help="Carpeta con los archivos candidatos a comparar")
    args = ap.parse_args()

    dir_v, dir_c = Path(args.vigente), Path(args.candidato)
    hubo_hallazgos = False

    print(f"Comparando vigente={dir_v} vs candidato={dir_c}\n")

    for nombre in CSV_CONOCIDOS:
        ruta_v, ruta_c = dir_v / nombre, dir_c / nombre
        df_v, df_c = _leer_csv(ruta_v), _leer_csv(ruta_c)
        if df_v is None and df_c is None:
            continue
        if df_v is None or df_c is None:
            hubo_hallazgos = True
            print(f"[{nombre}] solo existe en {'candidato' if df_v is None else 'vigente'} -- cambio real, revisar a mano.")
            continue

        esquema = comparar_esquema_csv(nombre, df_v, df_c)
        if esquema["nuevas"] or esquema["desaparecidas"] or esquema["tipos_distintos"]:
            hubo_hallazgos = True
            print(f"[{nombre}] ESQUEMA distinto:")
            if esquema["nuevas"]:
                print(f"  columnas nuevas: {esquema['nuevas']}")
            if esquema["desaparecidas"]:
                print(f"  columnas desaparecidas: {esquema['desaparecidas']}")
            for c, tv, tc in esquema["tipos_distintos"]:
                print(f"  tipo distinto en '{c}': vigente={tv} -> candidato={tc}")

        faltantes = comparar_faltantes(df_v, df_c)
        if faltantes:
            hubo_hallazgos = True
            print(f"[{nombre}] FALTANTES cambiaron >= {UMBRAL_FALTANTES_PP} pp:")
            for c, pv, pc, d in faltantes:
                signo = "+" if d > 0 else ""
                print(f"  '{c}': {pv}% -> {pc}% ({signo}{d} pp)")

        for arch, lat_col, lng_col in ARCHIVOS_CON_COORDENADAS:
            if arch != nombre:
                continue
            geo = comparar_geo(nombre, lat_col, lng_col, df_v, df_c)
            if geo and geo["saltos"]:
                hubo_hallazgos = True
                print(f"[{nombre}] LIMPIEZA GEOGRAFICA, saltos >= {UMBRAL_GEO_PP} pp o >= {UMBRAL_GEO_FILAS} filas:")
                for motivo, pv, pc, d, df in geo["saltos"]:
                    signo = "+" if d > 0 else ""
                    signo_f = "+" if df > 0 else ""
                    print(f"  {motivo}: {pv}% -> {pc}% ({signo}{d} pp, {signo_f}{df} filas)")

    for nombre in PKL_CONOCIDOS:
        ruta_v, ruta_c = dir_v / nombre, dir_c / nombre
        if not ruta_v.is_file() or not ruta_c.is_file():
            continue
        cols_v = pickle.loads(ruta_v.read_bytes())
        cols_c = pickle.loads(ruta_c.read_bytes())
        cambio = comparar_pkl_columnas(cols_v, cols_c)
        if cambio["nuevas"] or cambio["desaparecidas"]:
            hubo_hallazgos = True
            print(f"[{nombre}] ESQUEMA DEL MODELO distinto:")
            if cambio["nuevas"]:
                print(f"  features nuevas: {cambio['nuevas']}")
            if cambio["desaparecidas"]:
                print(f"  features desaparecidas: {cambio['desaparecidas']}")

    print()
    if hubo_hallazgos:
        print("Hay cambios para revisar antes de promover (ver arriba). Este reporte no bloquea nada -- la decision de correr --confirmar es de Rodo.")
    else:
        print("Sin cambios relevantes.")


if __name__ == "__main__":
    main()
