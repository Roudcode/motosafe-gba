# -*- coding: utf-8 -*-
"""
A20: criterio de limpieza geografica COMUN para los dos universos de datos
reales que alimentan los algoritmos del backend -- siniestros de moto
(motos_limpio.csv, via limpiar_siniestros_motos.py) y delitos de CABA
(delitos_caba.csv, via identificar_hotspots_inseguridad.py /
construir_indice_inseguridad.py). Antes de este modulo, cada script filtraba
coordenadas por su cuenta y de forma distinta: identificar_hotspots_inseguridad.py
ya sacaba (0,0) a mano, pero ningun script sacaba coordenadas fuera de un
bounding box razonable de GBA ni duplicados exactos, y limpiar_siniestros_motos.py
no sacaba ni (0,0) ni nada de eso (ver docs/evidencias/2026-10-21/A20-limpieza-geografica/).

Cada exclusion queda contada y declarada (nunca un filtro silencioso): devuelve
el DataFrame limpio MAS un resumen {motivo: cantidad} para que quien lo llame
lo imprima o lo guarde como evidencia.

Bounding box: generoso a proposito (cubre GBA entero con margen), para sacar
solo coordenadas claramente imposibles (otra provincia, un error de exportacion
con un numero astronomico), no para recortar el area de cobertura real de
ninguna fuente -- esa es una decision de cobertura (D01), no de limpieza.
"""
import pandas as pd

GBA_BBOX = {"lat_min": -35.6, "lat_max": -34.0, "lng_min": -59.3, "lng_max": -57.8}


def limpiar_coordenadas(df, lat_col, lng_col, nombre_fuente, columnas_duplicado=None):
    """Aplica el criterio comun y devuelve (df_limpio, resumen_exclusiones).

    Orden (cada paso opera sobre lo que quedo del anterior, así los motivos
    no se pisan entre sí):
      1. sin_coordenadas: lat/lng no numéricos o vacíos.
      2. coordenada_cero: (0,0) exacto -- valor centinela de GPS inválido, no
         un null real (dropna no lo detecta).
      3. fuera_de_gba: fuera del bounding box de arriba.
      4. duplicado_exacto: fila idéntica a otra ya vista (columnas de
         `columnas_duplicado`, o todas las columnas si no se especifica),
         se conserva la primera aparición.
    """
    resumen = {"total_entrada": len(df)}
    trabajo = df.copy()
    trabajo[lat_col] = pd.to_numeric(trabajo[lat_col], errors="coerce")
    trabajo[lng_col] = pd.to_numeric(trabajo[lng_col], errors="coerce")

    sin_coords = trabajo[lat_col].isna() | trabajo[lng_col].isna()
    resumen["sin_coordenadas"] = int(sin_coords.sum())
    trabajo = trabajo[~sin_coords].copy()

    es_cero = (trabajo[lat_col] == 0) & (trabajo[lng_col] == 0)
    resumen["coordenada_cero"] = int(es_cero.sum())
    trabajo = trabajo[~es_cero].copy()

    fuera = (
        ~trabajo[lat_col].between(GBA_BBOX["lat_min"], GBA_BBOX["lat_max"])
        | ~trabajo[lng_col].between(GBA_BBOX["lng_min"], GBA_BBOX["lng_max"])
    )
    resumen["fuera_de_gba"] = int(fuera.sum())
    trabajo = trabajo[~fuera].copy()

    cols_dup = columnas_duplicado if columnas_duplicado else list(trabajo.columns)
    es_dup = trabajo.duplicated(subset=cols_dup, keep="first")
    resumen["duplicado_exacto"] = int(es_dup.sum())
    trabajo = trabajo[~es_dup].copy()

    resumen["total_salida"] = len(trabajo)
    print(f"[{nombre_fuente}] {resumen['total_entrada']} filas de entrada -> {resumen['total_salida']} filas limpias "
          f"(sin_coordenadas={resumen['sin_coordenadas']}, coordenada_cero={resumen['coordenada_cero']}, "
          f"fuera_de_gba={resumen['fuera_de_gba']}, duplicado_exacto={resumen['duplicado_exacto']})")
    return trabajo, resumen
