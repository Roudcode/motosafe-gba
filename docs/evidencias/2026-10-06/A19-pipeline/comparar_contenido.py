"""A19: compara por contenido los artefactos regenerados en una copia de trabajo
contra los vigentes. El hash de bytes no alcanza: en Windows pandas escribe CSV
con CRLF y Git convierte fines de línea (core.autocrlf), así que dos CSV con los
mismos datos pueden tener distinto SHA256.

  CSV    -> mismas columnas, filas y valores (numéricos con tolerancia 1e-9).
  modelo -> mismos árboles: feature, umbral, hijos y valores de cada nodo,
            y misma lista de columnas.

Uso:  python comparar_contenido.py <dir_copia_data> <dir_vigente_data>
"""
import sys
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

warnings.simplefilter('ignore')
COPIA, VIGENTE = Path(sys.argv[1]), Path(sys.argv[2])
CSV = ['indice_inseguridad_comuna.csv', 'motos_con_clusters.csv', 'hotspots_moto_caba.csv',
       'hotspots_contexto.csv', 'corredores_candidatos.csv',
       'hotspots_inseguridad_general.csv', 'hotspots_inseguridad_moto.csv']


def comparar_csv(nombre):
    if not (COPIA / nombre).is_file():
        return 'sin regenerar'
    a, b = pd.read_csv(COPIA / nombre, low_memory=False), pd.read_csv(VIGENTE / nombre, low_memory=False)
    if list(a.columns) != list(b.columns):
        return f'columnas distintas: {set(a.columns) ^ set(b.columns)}'
    if len(a) != len(b):
        return f'filas distintas: {len(a)} contra {len(b)}'
    distintas = []
    for col in a.columns:
        if pd.api.types.is_numeric_dtype(a[col]) and pd.api.types.is_numeric_dtype(b[col]):
            iguales = np.isclose(a[col].to_numpy(float), b[col].to_numpy(float), rtol=0, atol=1e-9, equal_nan=True)
        else:
            iguales = (a[col].astype(str) == b[col].astype(str)).to_numpy()
        if not iguales.all():
            distintas.append(f'{col} ({(~iguales).sum()} celdas)')
    return 'mismo contenido' if not distintas else 'difiere en ' + ', '.join(distintas)


def comparar_modelo():
    a, b = joblib.load(COPIA / 'modelo_final.pkl'), joblib.load(VIGENTE / 'modelo_final.pkl')
    if joblib.load(COPIA / 'columnas_modelo.pkl') != joblib.load(VIGENTE / 'columnas_modelo.pkl'):
        return 'columnas del modelo distintas'
    if len(a.estimators_) != len(b.estimators_):
        return 'distinta cantidad de árboles'
    distintos = 0
    for ta, tb in zip(a.estimators_, b.estimators_):
        x, y = ta.tree_, tb.tree_
        if not (x.node_count == y.node_count and np.array_equal(x.feature, y.feature)
                and np.array_equal(x.children_left, y.children_left)
                and np.allclose(x.threshold, y.threshold, rtol=0, atol=1e-12)
                and np.allclose(x.value, y.value, rtol=0, atol=1e-12)):
            distintos += 1
    return f'{len(a.estimators_)} árboles, {distintos} distintos' + (' (mismo modelo)' if distintos == 0 else '')


for nombre in CSV:
    print(f'{nombre:36} {comparar_csv(nombre)}')
print(f"{'modelo_final.pkl':36} {comparar_modelo()}")
