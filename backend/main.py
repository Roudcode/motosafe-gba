import os
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import joblib
import pandas as pd

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

# Rutas absolutas basadas en la ubicación de este archivo: el backend siempre
# encuentra sus artefactos sin importar desde qué directorio se lo ejecute
# (antes eran rutas relativas, y solo funcionaban si se corría parado en backend/).
BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Modelo de Machine Learning (entrenado en notebooks/01_eda_hotspots_moto.ipynb) ---
modelo_final = joblib.load(BASE_DIR / 'modelo_final.pkl')
columnas_modelo = joblib.load(BASE_DIR / 'columnas_modelo.pkl')
contexto_hotspots = pd.read_csv(BASE_DIR / 'hotspots_contexto.csv')
contexto_hotspots['comuna_moda'] = contexto_hotspots['comuna_moda'].astype(str)

# Contexto "genérico" de respaldo: el perfil típico de TODA la ciudad (moda de cada
# variable categórica, promedio de edad), calculado una sola vez al arrancar.
# Se usa exclusivamente cuando un hotspot no tiene fila propia en hotspots_contexto.csv,
# para que ese hotspot pase igual por el modelo entrenado en vez de quedarse con un
# nivel de riesgo calculado con una fórmula distinta (ver nota en cargar_hotspots.py).
_CONTEXTO_GENERICO = {
    'comuna': contexto_hotspots['comuna_moda'].mode().iloc[0],
    'tipo_via': contexto_hotspots['tipo_via_moda'].mode().iloc[0],
    'contraparte': contexto_hotspots['contraparte_moda'].mode().iloc[0],
    'edad': float(contexto_hotspots['edad_promedio'].mean()),
    'sexo': contexto_hotspots['sexo_moda'].mode().iloc[0],
}


def predecir_para_fila(comuna, tipo_via, hora, dia_semana, contraparte, edad, sexo):
    fila = pd.DataFrame([{
        'hora': hora,
        'edad_victima': edad,
        'edad_desconocida': 0,
        'dia_semana': dia_semana,
        'comuna': comuna,
        'tipo_de_via_siniestro': tipo_via,
        'contraparte_siniestro': contraparte,
        'sexo_victima': sexo,
    }])
    fila_codificada = pd.get_dummies(fila)
    fila_alineada = fila_codificada.reindex(columns=columnas_modelo, fill_value=0)
    probabilidades = modelo_final.predict_proba(fila_alineada)[0]
    clases = modelo_final.classes_.tolist()
    return dict(zip(clases, [round(float(p), 3) for p in probabilidades]))


def nivel_desde_probabilidades(probs):
    """
    Traduce las probabilidades del modelo a un nivel de riesgo categórico.

    Los cortes priorizan no perder casos MORTAL aun a costa de más falsos positivos
    en GRAVE (igual que ya se documenta en docs/3_Resultados: la precisión de GRAVE
    es baja en las cuatro versiones del modelo, y se acepta porque en un contexto de
    seguridad vial es preferible sobre-alertar que no alertar). Por eso el umbral de
    p_mortal es más chico (0.10-0.20) que el de p_grave (0.20-0.40): al modelo le
    cuesta más discriminar GRAVE (precisión ~0.11-0.15 en el modelo elegido) que
    detectar señal de MORTAL, así que para MORTAL alcanza con menos probabilidad
    acumulada para escalar el nivel.
    """
    p_mortal = probs.get('MORTAL', 0)
    p_grave = probs.get('GRAVE', 0)
    if p_mortal >= 0.20:
        return 'critico'
    if p_mortal >= 0.10 or p_grave >= 0.40:
        return 'alto'
    if p_grave >= 0.20:
        return 'medio'
    return 'bajo'


@app.get("/")
def raiz():
    return {"mensaje": "MotoSafe GBA API funcionando"}


@app.get("/hotspots")
def obtener_hotspots():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT id, cluster, latitud, longitud, cantidad_siniestros, mortales, graves, nivel_riesgo
        FROM hotspots_riesgo
        ORDER BY cantidad_siniestros DESC
    """)
    resultado = cur.fetchall()
    cur.close()
    conn.close()

    ahora = datetime.now()
    hora_actual = ahora.hour
    dia_actual = ahora.strftime('%A')

    for h in resultado:
        # nivel_riesgo SIEMPRE sale del modelo entrenado en este endpoint: es la única
        # fuente de verdad. El valor que trae la fila de la base (calculado con una
        # heurística simple al momento de cargar los hotspots) es solo un placeholder
        # inicial y se pisa acá en cada pedido, sin excepciones — incluso cuando el
        # hotspot no tiene fila propia en hotspots_contexto.csv, en cuyo caso se usa
        # el contexto genérico de la ciudad y se marca contexto_estimado=True para
        # que quede trazable cuáles predicciones usan datos propios del hotspot y
        # cuáles un perfil promedio.
        ctx = contexto_hotspots[contexto_hotspots['cluster'] == h['cluster']]
        if ctx.empty:
            comuna = _CONTEXTO_GENERICO['comuna']
            tipo_via = _CONTEXTO_GENERICO['tipo_via']
            contraparte = _CONTEXTO_GENERICO['contraparte']
            edad = _CONTEXTO_GENERICO['edad']
            sexo = _CONTEXTO_GENERICO['sexo']
            contexto_estimado = True
        else:
            comuna = ctx.iloc[0]['comuna_moda']
            tipo_via = ctx.iloc[0]['tipo_via_moda']
            contraparte = ctx.iloc[0]['contraparte_moda']
            edad = ctx.iloc[0]['edad_promedio']
            sexo = ctx.iloc[0]['sexo_moda']
            contexto_estimado = False

        probs = predecir_para_fila(comuna, tipo_via, hora_actual, dia_actual, contraparte, edad, sexo)
        h['nivel_riesgo'] = nivel_desde_probabilidades(probs)
        h['prediccion_modelo'] = probs
        h['contexto_estimado'] = contexto_estimado

    return resultado


class ContextoSiniestro(BaseModel):
    hora: int
    dia_semana: str
    comuna: str
    tipo_de_via: str
    contraparte: str
    edad_victima: float = 32.0
    sexo_victima: str = "SD"


@app.post("/predecir")
def predecir_gravedad(contexto: ContextoSiniestro):
    fila = pd.DataFrame([{
        'hora': contexto.hora,
        'edad_victima': contexto.edad_victima,
        'edad_desconocida': 0,
        'dia_semana': contexto.dia_semana,
        'comuna': contexto.comuna,
        'tipo_de_via_siniestro': contexto.tipo_de_via,
        'contraparte_siniestro': contexto.contraparte,
        'sexo_victima': contexto.sexo_victima,
    }])
    fila_codificada = pd.get_dummies(fila)
    fila_alineada = fila_codificada.reindex(columns=columnas_modelo, fill_value=0)

    prediccion = modelo_final.predict(fila_alineada)[0]
    probabilidades = modelo_final.predict_proba(fila_alineada)[0]
    clases = modelo_final.classes_.tolist()

    return {
        "prediccion": prediccion,
        "probabilidades": dict(zip(clases, [round(float(p), 3) for p in probabilidades]))
    }
