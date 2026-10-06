"""Genera backend/metadatos_capas.json: período de cobertura real de cada capa.

A10/A11/A15 (decisión de Rodo, 2026-10-06): la interfaz muestra el período que
cubren los datos de cada capa (lo que importa para juzgar la vigencia del
riesgo), no la fecha de generación del archivo; esa va como dato secundario.

data/ no está versionado, así que el backend no puede calcularlo en el
servidor: este script se corre donde están los datos (cada vez que se
regeneran las capas) y el JSON resultante sí se versiona en backend/.

Uso, desde la raíz del repo:
    python notebooks/generar_metadatos_capas.py
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
DATA = RAIZ / 'data'
SALIDA = RAIZ / 'backend' / 'metadatos_capas.json'
ANIOS_VENTANA_INSEGURIDAD = 3  # misma ventana que identificar_hotspots_inseguridad.py


def fecha_archivo(nombre):
    marca = (DATA / nombre).stat().st_mtime
    return datetime.fromtimestamp(marca, tz=timezone.utc).date().isoformat()


def periodo(fechas):
    fechas = pd.to_datetime(fechas, errors='coerce').dropna()
    return fechas.min().date().isoformat(), fechas.max().date().isoformat(), int(len(fechas))


def main():
    motos = pd.read_csv(DATA / 'motos_limpio.csv', usecols=['fecha_siniestro'])
    s_desde, s_hasta, s_n = periodo(motos['fecha_siniestro'])

    delitos = pd.read_csv(DATA / 'delitos_caba.csv', usecols=['fecha', 'anio_dataset', 'uso_moto'], low_memory=False)
    anio_max = int(delitos['anio_dataset'].max())
    ventana = delitos[delitos['anio_dataset'].between(anio_max - ANIOS_VENTANA_INSEGURIDAD + 1, anio_max)]
    g_desde, g_hasta, g_n = periodo(ventana['fecha'])
    m_desde, m_hasta, m_n = periodo(ventana.loc[ventana['uso_moto'] == 'SI', 'fecha'])

    fuente_siniestros = 'Siniestros viales, Buenos Aires Data (GCBA)'
    fuente_delitos = 'Delitos, Buenos Aires Data (GCBA)'
    capas = {
        'hotspots': {'descripcion': 'Siniestros con motociclistas', 'desde': s_desde, 'hasta': s_hasta,
                     'registros': s_n, 'fuente': fuente_siniestros,
                     'archivo_generado': fecha_archivo('hotspots_moto_caba.csv')},
        'corredores': {'descripcion': 'Siniestros con motociclistas por corredor', 'desde': s_desde, 'hasta': s_hasta,
                       'registros': s_n, 'fuente': fuente_siniestros,
                       'archivo_generado': fecha_archivo('corredores_riesgo.csv')},
        'inseguridad_general': {'descripcion': 'Delitos', 'desde': g_desde, 'hasta': g_hasta, 'registros': g_n,
                                'fuente': fuente_delitos,
                                'archivo_generado': fecha_archivo('hotspots_inseguridad_general.csv')},
        'inseguridad_moto': {'descripcion': 'Delitos con uso de moto', 'desde': m_desde, 'hasta': m_hasta,
                             'registros': m_n, 'fuente': fuente_delitos,
                             'archivo_generado': fecha_archivo('hotspots_inseguridad_moto.csv')},
    }
    SALIDA.write_text(json.dumps(capas, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for nombre, c in capas.items():
        print(f"{nombre:20} {c['desde']} a {c['hasta']} ({c['registros']} registros), archivo {c['archivo_generado']}")


if __name__ == '__main__':
    main()
