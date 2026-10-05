"""
Calibra los umbrales de percentil (p25/p75/p95) que separan bajo/medio/alto/critico,
usando una poblacion de REFERENCIA fija en vez de recalcular percentiles en cada
pedido HTTP.

Por que hace falta esto (contexto del hallazgo, sesion de calibracion de nivel_riesgo):

niveles_relativos_desde_matriz ya habia sido corregida una vez: paso de un corte de
probabilidad absoluto (que dejaba ~86% de los hotspots en alto/critico, siempre) a un
corte por percentiles DENTRO DE CADA PEDIDO. Eso resolvio la comparacion entre zonas
en un mismo momento, pero genero un problema nuevo: el modelo recibe 'hora' como
feature (la mas influyente del modelo, ver docs/3_Resultados_DETALLADO.md linea 134,
con bastante diferencia sobre el resto) y ese valor es EL MISMO para las 740 filas de
un pedido (siempre la hora real del momento de la consulta). Como el Random Forest
generaliza fuerte sobre esa variable, a ciertas horas la distribucion de probabilidad
predicha para las 740 zonas se comprime (muchas zonas terminan con probabilidad
parecida entre si). Si los percentiles se recalculan DESDE CERO en cada pedido sobre
esa distribucion ya comprimida, el resultado visual es "casi todo alto" a esa hora, y
"bastante repartido" a otra -- el significado de 'alto' dejaba de ser estable en el
tiempo, cambiaba segun a que hora se consultaba, no solo el CONTENIDO del mapa.

La solucion: los percentiles se calculan UNA SOLA VEZ, offline, sobre una poblacion de
referencia que cubre TODAS las combinaciones de hora (0-23) x dia de la semana (7) x
lluvia (si/no) para las 740 hotspots (o los 243 corredores) -- 336 escenarios x zona.
Esos p25/p75/p95 quedan fijos como constantes en main.py. En cada pedido real se sigue
calculando la probabilidad EN VIVO (con la hora/clima actuales), pero se clasifica
contra esos cortes fijos, no contra los de la fotografia del momento. Consecuencia
esperada y correcta: a las 3am, mas zonas van a caer en alto/critico que a las 11am
-- eso es señal real (el modelo aprendio que de noche es mas grave, ver docs), no un
artefacto de calculo. Lo que cambia es que 'alto' ahora significa lo mismo (esta en el
25% mas riesgoso de TODO lo que el modelo puede predecir, a cualquier hora/clima/dia)
sin importar cuando se consulta, en vez de recalibrarse cada vez.

Uso: python3 calibrar_umbrales_riesgo.py
Corre una sola vez cuando se re-entrena el modelo o cambia el universo de hotspots/
corredores; los resultados se pegan a mano como constantes en backend/main.py.

Ademas imprime la huella SHA256 de los artefactos usados (modelo_final.pkl +
hotspots_contexto.csv + indice_inseguridad_comuna.csv), que tambien hay que
pegar en _HUELLA_UMBRALES_CALIBRADOS en backend/main.py -- es lo que permite
que /health avise cuando estos cortes quedaron desincronizados del modelo real
en vez de recalibrarse solos sin que nadie lo revise (ver
_huella_artefactos_riesgo en backend/main.py).
"""
import hashlib
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent / 'backend'
DATA_DIR = Path(__file__).resolve().parent.parent / 'data'

modelo_final = joblib.load(BASE_DIR / 'modelo_final.pkl')
columnas_modelo = joblib.load(BASE_DIR / 'columnas_modelo.pkl')

HORAS = list(range(24))
DIAS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
# temperatura/humedad promedio historica (mismo fallback que usa main.py cuando no
# hay clima en vivo, ver _CLIMA_FALLBACK) para los dos estados de lluvia -- el clima
# pesa mucho menos que la hora (ver docs/3_Resultados), asi que dos escenarios de
# lluvia con la temperatura/humedad promedio alcanzan para cubrir su efecto sin
# necesitar un grid de temperaturas.
CLIMAS = [
    {'lluvia': 'NO', 'temperatura': 17.6, 'humedad': 72.1},
    {'lluvia': 'SI', 'temperatura': 17.6, 'humedad': 72.1},
]

_CONTEXTO_GENERICO = {'comuna': '1', 'tipo_via': 'CALLE', 'contraparte': 'AUTO', 'edad': 35.0, 'sexo': 'M'}


def indice_inseguridad_de_serie(comunas, indice_por_comuna, promedio):
    return comunas.map(indice_por_comuna).fillna(promedio)


def cargar_indice_inseguridad():
    df = pd.read_csv(BASE_DIR / 'indice_inseguridad_comuna.csv')
    df['comuna'] = df['comuna'].astype(str)
    mapa = df.set_index('comuna')['indice_inseguridad'].to_dict()
    return mapa, float(df['indice_inseguridad'].mean())


def score_de_matriz(matriz_probabilidades, clases):
    idx_mortal = clases.index('MORTAL')
    idx_grave = clases.index('GRAVE')
    return 2 * matriz_probabilidades[:, idx_mortal] + matriz_probabilidades[:, idx_grave]


def predecir_batch(comunas, tipos_via, contrapartes, edades, sexos, indice_inseguridad, hora, dia, clima):
    n = len(comunas)
    filas = pd.DataFrame({
        'hora': hora,
        'edad_victima': edades,
        'edad_desconocida': 0,
        'temperatura': clima['temperatura'],
        'humedad': clima['humedad'],
        'dia_semana': dia,
        'comuna': comunas,
        'tipo_de_via_siniestro': tipos_via,
        'contraparte_siniestro': contrapartes,
        'sexo_victima': sexos,
        'lluvia': clima['lluvia'],
        'indice_inseguridad': indice_inseguridad,
    })
    fila_codificada = pd.get_dummies(filas)
    fila_alineada = fila_codificada.reindex(columns=columnas_modelo, fill_value=0)
    matriz = modelo_final.predict_proba(fila_alineada)
    return matriz


def calibrar(nombre, comunas, tipos_via, contrapartes, edades, sexos, indice_inseguridad):
    clases = modelo_final.classes_.tolist()
    scores = []
    total_escenarios = len(HORAS) * len(DIAS) * len(CLIMAS)
    hecho = 0
    for hora in HORAS:
        for dia in DIAS:
            for clima in CLIMAS:
                matriz = predecir_batch(comunas, tipos_via, contrapartes, edades, sexos, indice_inseguridad, hora, dia, clima)
                scores.append(score_de_matriz(matriz, clases))
                hecho += 1
        print(f'  {nombre}: hora {hora:02d} lista ({hecho}/{total_escenarios} escenarios)', file=sys.stderr)
    scores = np.concatenate(scores)
    p25, p75, p95 = np.percentile(scores, [25, 75, 95])
    print(f'\n=== {nombre} ===')
    print(f'  poblacion de referencia: {len(scores)} predicciones ({total_escenarios} escenarios x {len(comunas)} zonas)')
    print(f'  score minimo: {scores.min():.4f}  maximo: {scores.max():.4f}  mediana: {np.median(scores):.4f}')
    print(f'  p25={p25:.4f}  p75={p75:.4f}  p95={p95:.4f}')
    return {'p25': float(p25), 'p75': float(p75), 'p95': float(p95)}


def main():
    indice_por_comuna, indice_promedio = cargar_indice_inseguridad()

    # --- Hotspots (740 zonas puntuales) ---
    contexto_hotspots = pd.read_csv(BASE_DIR / 'hotspots_contexto.csv')
    contexto_hotspots['comuna_moda'] = contexto_hotspots['comuna_moda'].astype(str).fillna(_CONTEXTO_GENERICO['comuna'])
    contexto_hotspots['tipo_via_moda'] = contexto_hotspots['tipo_via_moda'].fillna(_CONTEXTO_GENERICO['tipo_via'])
    contexto_hotspots['contraparte_moda'] = contexto_hotspots['contraparte_moda'].fillna(_CONTEXTO_GENERICO['contraparte'])
    contexto_hotspots['edad_promedio'] = contexto_hotspots['edad_promedio'].fillna(_CONTEXTO_GENERICO['edad'])
    contexto_hotspots['sexo_moda'] = contexto_hotspots['sexo_moda'].fillna(_CONTEXTO_GENERICO['sexo'])
    indice_hotspots = indice_inseguridad_de_serie(contexto_hotspots['comuna_moda'], indice_por_comuna, indice_promedio)

    umbrales_hotspots = calibrar(
        'HOTSPOTS',
        contexto_hotspots['comuna_moda'], contexto_hotspots['tipo_via_moda'],
        contexto_hotspots['contraparte_moda'], contexto_hotspots['edad_promedio'],
        contexto_hotspots['sexo_moda'], indice_hotspots,
    )

    # --- Corredores (243 avenidas/tramos) ---
    corredores = pd.read_csv(DATA_DIR / 'corredores_riesgo.csv')
    corredores['comuna_moda'] = corredores['comuna_moda'].astype(str)
    indice_corredores = indice_inseguridad_de_serie(corredores['comuna_moda'], indice_por_comuna, indice_promedio)

    umbrales_corredores = calibrar(
        'CORREDORES',
        corredores['comuna_moda'], corredores['tipo_via_moda'],
        corredores['contraparte_moda'], corredores['edad_promedio'],
        corredores['sexo_moda'], indice_corredores,
    )

    h = hashlib.sha256()
    for nombre in ('modelo_final.pkl', 'hotspots_contexto.csv', 'indice_inseguridad_comuna.csv'):
        h.update((BASE_DIR / nombre).read_bytes())

    print('\n--- Para pegar en backend/main.py ---')
    print(f"UMBRALES_HOTSPOTS = {umbrales_hotspots}")
    print(f"UMBRALES_CORREDORES = {umbrales_corredores}")
    print(f"_HUELLA_UMBRALES_CALIBRADOS = '{h.hexdigest()}'")


if __name__ == '__main__':
    main()
