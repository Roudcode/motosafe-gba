"""A22 — ¿El modelo vigente predice lo mismo con otra versión de scikit-learn?

modelo_final.pkl se guardó con scikit-learn 1.7.2 (metadato `_sklearn_version`
del pickle), pero backend/requirements.txt permite cualquier 1.x y el venv
local tiene 1.9.1. Este script recorre la misma población de referencia que
notebooks/calibrar_umbrales_riesgo.py (740 hotspots y 243 corredores, cada uno
en 24 horas x 7 días x lluvia sí/no) y guarda todas las probabilidades. Se
corre una vez por entorno y después se comparan los dos resultados.

Uso (desde la raíz del repo):
    <python del entorno A> comparar_versiones_sklearn.py generar salida_A.npz
    <python del entorno B> comparar_versiones_sklearn.py generar salida_B.npz
    <cualquier python>     comparar_versiones_sklearn.py comparar salida_A.npz salida_B.npz
"""
import sys
import warnings
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[4]


def generar(destino):
    warnings.simplefilter('ignore')
    sys.path.insert(0, str(RAIZ / 'notebooks'))
    import pandas as pd
    import sklearn
    import calibrar_umbrales_riesgo as cal

    indice_por_comuna, indice_promedio = cal.cargar_indice_inseguridad()
    generico = cal._CONTEXTO_GENERICO

    hotspots = pd.read_csv(cal.BASE_DIR / 'hotspots_contexto.csv')
    hotspots['comuna_moda'] = hotspots['comuna_moda'].astype(str).fillna(generico['comuna'])
    hotspots['tipo_via_moda'] = hotspots['tipo_via_moda'].fillna(generico['tipo_via'])
    hotspots['contraparte_moda'] = hotspots['contraparte_moda'].fillna(generico['contraparte'])
    hotspots['edad_promedio'] = hotspots['edad_promedio'].fillna(generico['edad'])
    hotspots['sexo_moda'] = hotspots['sexo_moda'].fillna(generico['sexo'])

    corredores = pd.read_csv(cal.DATA_DIR / 'corredores_riesgo.csv')
    corredores['comuna_moda'] = corredores['comuna_moda'].astype(str)

    resultado = {}
    for nombre, df in (('hotspots', hotspots), ('corredores', corredores)):
        indice = cal.indice_inseguridad_de_serie(df['comuna_moda'], indice_por_comuna, indice_promedio)
        bloques = []
        for hora in cal.HORAS:
            for dia in cal.DIAS:
                for clima in cal.CLIMAS:
                    bloques.append(cal.predecir_batch(
                        df['comuna_moda'], df['tipo_via_moda'], df['contraparte_moda'],
                        df['edad_promedio'], df['sexo_moda'], indice, hora, dia, clima,
                    ))
        matriz = np.vstack(bloques)
        resultado[nombre] = matriz
        scores = cal.score_de_matriz(matriz, cal.modelo_final.classes_.tolist())
        p25, p75, p95 = np.percentile(scores, [25, 75, 95])
        print(f'{nombre}: {matriz.shape[0]} predicciones; p25={p25!r} p75={p75!r} p95={p95!r}')

    np.savez_compressed(destino, sklearn_version=sklearn.__version__, numpy_version=np.__version__,
                        clases=np.array(cal.modelo_final.classes_, dtype=str), **resultado)
    print(f'sklearn {sklearn.__version__}, numpy {np.__version__} -> {destino}')


def comparar(a, b):
    # allow_pickle: archivos generados por este mismo script, no de terceros.
    da, db = np.load(a, allow_pickle=True), np.load(b, allow_pickle=True)
    print(f'A: sklearn {da["sklearn_version"]} / B: sklearn {db["sklearn_version"]}')
    assert list(da['clases']) == list(db['clases']), 'Orden de clases distinto'
    clases = list(da['clases'])
    cortes = _cortes_de_main()
    for nombre in ('hotspots', 'corredores'):
        ma, mb = da[nombre], db[nombre]
        diff = np.abs(ma - mb)
        idx = np.argmax(ma, axis=1) != np.argmax(mb, axis=1)
        # Nivel bajo/medio/alto/critico que ve el usuario: score 2*P(MORTAL)+P(GRAVE)
        # contra los cortes fijos de backend/main.py.
        c = cortes[nombre]
        niveles = [np.digitize(2 * m[:, clases.index('MORTAL')] + m[:, clases.index('GRAVE')],
                               [c['p25'], c['p75'], c['p95']]) for m in (ma, mb)]
        print(f'{nombre}: {ma.shape[0]} filas; idénticas bit a bit: {np.array_equal(ma, mb)}; '
              f'máx |dif| = {diff.max():.3e}; filas con clase argmax distinta: {int(idx.sum())}; '
              f'filas con nivel de riesgo distinto: {int((niveles[0] != niveles[1]).sum())}')


def _cortes_de_main():
    import ast
    import re
    texto = (RAIZ / 'backend' / 'main.py').read_text(encoding='utf-8')
    return {
        nombre: ast.literal_eval(re.search(rf'^{const} = (\{{.*\}})$', texto, re.M).group(1))
        for nombre, const in (('hotspots', 'UMBRALES_HOTSPOTS'), ('corredores', 'UMBRALES_CORREDORES'))
    }


if __name__ == '__main__':
    if sys.argv[1] == 'generar':
        generar(sys.argv[2])
    elif sys.argv[1] == 'comparar':
        comparar(sys.argv[2], sys.argv[3])
    else:
        sys.exit(__doc__)
