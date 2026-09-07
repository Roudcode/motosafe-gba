import os
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import httpx
import joblib
import numpy as np
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

# --- Indice de inseguridad por comuna (data/delitos_caba.csv del GCBA, ver
# notebooks/construir_indice_inseguridad.py) — variable numerica del modelo desde
# el reentreno que lo incorporo (ver notebooks/reentrenar_modelo.py). Es estatico
# (se actualiza a mano una vez por anio, cuando el GCBA publica el siguiente), no
# hace falta consultarlo en vivo por request como el clima: se carga una sola vez
# al arrancar y se busca por comuna en cada prediccion.
_indice_inseguridad_df = pd.read_csv(BASE_DIR / 'indice_inseguridad_comuna.csv')
_indice_inseguridad_df['comuna'] = _indice_inseguridad_df['comuna'].astype(str)
INDICE_INSEGURIDAD_POR_COMUNA = _indice_inseguridad_df.set_index('comuna')['indice_inseguridad'].to_dict()
_INDICE_INSEGURIDAD_PROMEDIO = float(_indice_inseguridad_df['indice_inseguridad'].mean())


def indice_inseguridad_de(comuna):
    return INDICE_INSEGURIDAD_POR_COMUNA.get(str(comuna), _INDICE_INSEGURIDAD_PROMEDIO)

# --- Clima en vivo (Open-Meteo) ---
# El modelo se reentrenó con clima real como variable (ver notebooks/01_eda_hotspots_moto.ipynb,
# sección 5.1): lluvia, temperatura y humedad. En producción esos tres valores salen de
# la API de pronóstico de Open-Meteo para CABA, no del histórico usado para entrenar.
OPEN_METEO_URL = os.getenv('OPEN_METEO_BASE_URL', 'https://api.open-meteo.com/v1/forecast')
LATITUD_CABA = -34.61
LONGITUD_CABA = -58.44
CACHE_CLIMA_TTL_SEGUNDOS = 600  # 10 minutos: evita repetir la llamada externa en cada
                                 # pedido a /hotspots (que ya procesa 740 hotspots por request)

# Promedio histórico 2019-2026 usado en el entrenamiento (ver clima_historico.csv):
# último respaldo si la API en vivo no responde y todavía no hay nada en cache.
_CLIMA_FALLBACK = {'lluvia': 'NO', 'temperatura': 17.6, 'humedad': 72.1}
_cache_clima = {'datos': None, 'timestamp': 0.0}


# --- Reportes colaborativos ---
# Antes vivian solo en el localStorage de cada navegador (ver docs/1_Guia_RESUMEN.md):
# cada usuario veia unicamente sus propios reportes, sin componente colaborativo real.
# Ahora se guardan en la base y se comparten entre todos los usuarios; calcularAjuste
# en el frontend ya sumaba reportes cercanos al nivel de riesgo de una zona, y ese
# calculo gana sentido real recien cuando "cercanos" incluye reportes de otra gente,
# no solo los propios.
#
# No hay autenticacion en el sistema, asi que la nocion de "mio" es un id aleatorio
# que el frontend genera una vez y guarda en su propio localStorage (autor_id). No es
# una identidad real ni evita que alguien mande reportes con cualquier autor_id: solo
# alcanza para que el boton "Borrar mis reportes" borre los del dispositivo que los
# creo, sin pedirle al usuario que se registre para algo tan simple como marcar un
# pozo en la calle.
#
# La vigencia es distinta por categoria porque no todos los reportes envejecen igual:
# un corte de calle deja de ser cierto en horas, un pozo en el pavimento sigue ahi
# semanas.
CATEGORIAS_REPORTE_VALIDAS = ('pavimento', 'corte', 'iluminacion', 'inseguro')
VIGENCIA_HORAS_POR_CATEGORIA = {
    'corte': 12,           # cortes/desvios: casi siempre se resuelven en el dia
    'inseguro': 24 * 7,    # percepcion de inseguridad: vale refrescarla cada semana
    'pavimento': 24 * 30,  # pozos/pavimento roto: tarda semanas o meses en arreglarse
    'iluminacion': 24 * 30,
}
VIGENCIA_HORAS_DEFAULT = 24 * 7


def obtener_clima_actual():
    """
    Clima en vivo para CABA, con cache de 10 minutos y degradación controlada si la
    API de Open-Meteo falla: se devuelve el último valor cacheado si existe (aunque
    esté vencido, sigue siendo más real que un promedio de 8 años), y si todavía no
    hay ningún dato en cache, el promedio histórico usado en el entrenamiento. Nunca
    tira una excepción hacia el caller: /hotspots y /predecir tienen que poder
    responder aunque el clima en vivo no esté disponible.
    """
    ahora = time.monotonic()
    if _cache_clima['datos'] is not None and (ahora - _cache_clima['timestamp']) < CACHE_CLIMA_TTL_SEGUNDOS:
        return _cache_clima['datos']

    try:
        respuesta = httpx.get(
            OPEN_METEO_URL,
            params={
                'latitude': LATITUD_CABA,
                'longitude': LONGITUD_CABA,
                'current': 'precipitation,temperature_2m,relative_humidity_2m',
                'timezone': 'America/Argentina/Buenos_Aires',
            },
            timeout=5.0,
        )
        respuesta.raise_for_status()
        actual = respuesta.json()['current']
        datos = {
            'lluvia': 'SI' if actual['precipitation'] > 0.1 else 'NO',
            'temperatura': float(actual['temperature_2m']),
            'humedad': float(actual['relative_humidity_2m']),
        }
        _cache_clima['datos'] = datos
        _cache_clima['timestamp'] = ahora
        return datos
    except Exception:
        if _cache_clima['datos'] is not None:
            return _cache_clima['datos']
        return _CLIMA_FALLBACK


def predecir_para_fila(comuna, tipo_via, hora, dia_semana, contraparte, edad, sexo, clima):
    fila = pd.DataFrame([{
        'hora': hora,
        'edad_victima': edad,
        'edad_desconocida': 0,
        'temperatura': clima['temperatura'],
        'humedad': clima['humedad'],
        'dia_semana': dia_semana,
        'comuna': comuna,
        'tipo_de_via_siniestro': tipo_via,
        'contraparte_siniestro': contraparte,
        'sexo_victima': sexo,
        'lluvia': clima['lluvia'],
        'indice_inseguridad': indice_inseguridad_de(comuna),
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
    clima_actual = obtener_clima_actual()

    # Vectorizado: se arman las filas de los 740 hotspots de una sola vez y se
    # predice todo el lote junto (un solo pd.get_dummies + un solo predict_proba),
    # en vez de un loop en Python armando un DataFrame de una fila por hotspot.
    # Esto es lo que hacía que el endpoint tardara 15-20 segundos: no era el modelo
    # en si (un RandomForest predice un lote de 740 filas en milisegundos), era el
    # overhead de pandas (crear DataFrame, get_dummies, reindex) repetido 740 veces
    # en Python puro, mas el filtro lineal sobre contexto_hotspots en cada vuelta.
    # El clima es el mismo para las 740 filas (una sola ciudad, un solo momento),
    # así que se pide una vez (con cache) y no por hotspot.
    columnas_contexto = ['cluster', 'comuna_moda', 'tipo_via_moda', 'contraparte_moda', 'edad_promedio', 'sexo_moda']
    contexto = pd.DataFrame({'cluster': [h['cluster'] for h in resultado]}).merge(
        contexto_hotspots[columnas_contexto], on='cluster', how='left',
    )
    # nivel_riesgo SIEMPRE sale del modelo entrenado en este endpoint: es la única
    # fuente de verdad. El valor que trae la fila de la base (calculado con una
    # heurística simple al momento de cargar los hotspots) es solo un placeholder
    # inicial y se pisa acá en cada pedido, sin excepciones — incluso cuando el
    # hotspot no tiene fila propia en hotspots_contexto.csv, en cuyo caso se usa
    # el contexto genérico de la ciudad y se marca contexto_estimado=True para
    # que quede trazable cuáles predicciones usan datos propios del hotspot y
    # cuáles un perfil promedio.
    contexto_estimado = contexto['comuna_moda'].isna()
    contexto['comuna_moda'] = contexto['comuna_moda'].fillna(_CONTEXTO_GENERICO['comuna'])
    contexto['tipo_via_moda'] = contexto['tipo_via_moda'].fillna(_CONTEXTO_GENERICO['tipo_via'])
    contexto['contraparte_moda'] = contexto['contraparte_moda'].fillna(_CONTEXTO_GENERICO['contraparte'])
    contexto['edad_promedio'] = contexto['edad_promedio'].fillna(_CONTEXTO_GENERICO['edad'])
    contexto['sexo_moda'] = contexto['sexo_moda'].fillna(_CONTEXTO_GENERICO['sexo'])

    filas = pd.DataFrame({
        'hora': hora_actual,
        'edad_victima': contexto['edad_promedio'],
        'edad_desconocida': 0,
        'temperatura': clima_actual['temperatura'],
        'humedad': clima_actual['humedad'],
        'dia_semana': dia_actual,
        'comuna': contexto['comuna_moda'],
        'tipo_de_via_siniestro': contexto['tipo_via_moda'],
        'contraparte_siniestro': contexto['contraparte_moda'],
        'sexo_victima': contexto['sexo_moda'],
        'lluvia': clima_actual['lluvia'],
        'indice_inseguridad': contexto['comuna_moda'].map(INDICE_INSEGURIDAD_POR_COMUNA).fillna(_INDICE_INSEGURIDAD_PROMEDIO),
    })
    fila_codificada = pd.get_dummies(filas)
    fila_alineada = fila_codificada.reindex(columns=columnas_modelo, fill_value=0)
    matriz_probabilidades = modelo_final.predict_proba(fila_alineada)
    clases = modelo_final.classes_.tolist()

    for i, h in enumerate(resultado):
        probs = dict(zip(clases, [round(float(p), 3) for p in matriz_probabilidades[i]]))
        h['nivel_riesgo'] = nivel_desde_probabilidades(probs)
        h['prediccion_modelo'] = probs
        h['contexto_estimado'] = bool(contexto_estimado.iloc[i])
        h['clima'] = clima_actual

    return resultado


class ContextoSiniestro(BaseModel):
    hora: int
    dia_semana: str
    comuna: str
    tipo_de_via: str
    contraparte: str
    edad_victima: float = 32.0
    sexo_victima: str = "SD"
    # Si no se pasan, se usa el clima en vivo actual de CABA (ver obtener_clima_actual).
    # Se pueden pasar explícitos para simular un escenario ("¿y si llueve?").
    lluvia: str | None = None
    temperatura: float | None = None
    humedad: float | None = None


@app.post("/predecir")
def predecir_gravedad(contexto: ContextoSiniestro):
    if contexto.lluvia is not None and contexto.temperatura is not None and contexto.humedad is not None:
        clima = {'lluvia': contexto.lluvia, 'temperatura': contexto.temperatura, 'humedad': contexto.humedad}
    else:
        clima = obtener_clima_actual()

    fila = pd.DataFrame([{
        'hora': contexto.hora,
        'edad_victima': contexto.edad_victima,
        'edad_desconocida': 0,
        'temperatura': clima['temperatura'],
        'humedad': clima['humedad'],
        'dia_semana': contexto.dia_semana,
        'comuna': contexto.comuna,
        'tipo_de_via_siniestro': contexto.tipo_de_via,
        'contraparte_siniestro': contexto.contraparte,
        'sexo_victima': contexto.sexo_victima,
        'lluvia': clima['lluvia'],
        'indice_inseguridad': indice_inseguridad_de(contexto.comuna),
    }])
    fila_codificada = pd.get_dummies(fila)
    fila_alineada = fila_codificada.reindex(columns=columnas_modelo, fill_value=0)

    prediccion = modelo_final.predict(fila_alineada)[0]
    probabilidades = modelo_final.predict_proba(fila_alineada)[0]
    clases = modelo_final.classes_.tolist()

    return {
        "prediccion": prediccion,
        "probabilidades": dict(zip(clases, [round(float(p), 3) for p in probabilidades])),
        "clima_usado": clima,
    }


def _asegurar_tabla_reportes(conn):
    """
    CREATE TABLE IF NOT EXISTS en vez de una migracion aparte: el proyecto no tiene
    herramienta de migraciones (ver cargar_hotspots.py, que asume la tabla de
    hotspots ya creada a mano), y para una tabla tan simple agregar una es mas
    ceremonia que valor. Se ejecuta al principio de cada endpoint que toca la
    tabla, es barato en Postgres cuando ya existe, y el sistema funciona igual
    en un clone limpio sin pasos manuales de setup adicionales.
    """
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reportes_colaborativos (
            id SERIAL PRIMARY KEY,
            lat DOUBLE PRECISION NOT NULL,
            lng DOUBLE PRECISION NOT NULL,
            categoria VARCHAR(30) NOT NULL,
            autor_id VARCHAR(50) NOT NULL,
            creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    conn.commit()
    cur.close()


class ReporteNuevo(BaseModel):
    lat: float
    lng: float
    categoria: Literal['pavimento', 'corte', 'iluminacion', 'inseguro']
    autor_id: str


@app.post("/reportes", status_code=201)
def crear_reporte(reporte: ReporteNuevo):
    conn = psycopg2.connect(DATABASE_URL)
    _asegurar_tabla_reportes(conn)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        INSERT INTO reportes_colaborativos (lat, lng, categoria, autor_id)
        VALUES (%s, %s, %s, %s)
        RETURNING id, lat, lng, categoria, autor_id, creado_en
    """, (reporte.lat, reporte.lng, reporte.categoria, reporte.autor_id))
    fila = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return fila


@app.get("/reportes")
def listar_reportes():
    """
    Devuelve los reportes de TODOS los usuarios (esto es lo colaborativo), filtrados
    por vigencia segun su categoria: un reporte vencido no se borra de la base (queda
    como historico), simplemente deja de aparecer en el mapa y de sumar al ajuste de
    riesgo de su zona.
    """
    conn = psycopg2.connect(DATABASE_URL)
    _asegurar_tabla_reportes(conn)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT id, lat, lng, categoria, autor_id, creado_en FROM reportes_colaborativos ORDER BY creado_en DESC")
    filas = cur.fetchall()
    cur.close()
    conn.close()

    ahora = datetime.now(timezone.utc)
    vigentes = []
    for fila in filas:
        vigencia_horas = VIGENCIA_HORAS_POR_CATEGORIA.get(fila['categoria'], VIGENCIA_HORAS_DEFAULT)
        edad_horas = (ahora - fila['creado_en']).total_seconds() / 3600
        if edad_horas <= vigencia_horas:
            vigentes.append(fila)
    return vigentes


@app.delete("/reportes")
def borrar_mis_reportes(autor_id: str):
    """Borra solo los reportes de ese autor_id (ver nota sobre autor_id mas arriba:
    no es autenticacion real, es lo minimo para que 'borrar mis reportes' borre los
    del dispositivo que los creo y no los de otro usuario)."""
    conn = psycopg2.connect(DATABASE_URL)
    _asegurar_tabla_reportes(conn)
    cur = conn.cursor()
    cur.execute("DELETE FROM reportes_colaborativos WHERE autor_id = %s", (autor_id,))
    eliminados = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return {"eliminados": eliminados}


@app.get("/corredores")
def obtener_corredores():
    """
    Corredores de riesgo: calles completas (no zonas puntuales) con muchos
    siniestros a lo largo de su extension, como Av. Gral. Paz o Av. Rivadavia.
    Se precalcularon una sola vez offline (notebooks/identificar_corredores.py +
    fetch_corredores_geometria.py, que le pide a OSRM la geometria real de cada
    avenida) — la tabla trae calle, geometria y el perfil tipico de esa calle
    (comuna/tipo de via/contraparte mas frecuente, edad promedio, sexo mas
    frecuente); el nivel de riesgo, como en /hotspots, se calcula en vivo con
    el modelo entrenado, no se guarda precalculado.
    """
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT id, calle, tramo, tramos_totales, geometria, cantidad_siniestros, mortales, graves,
               comuna_moda, tipo_via_moda, contraparte_moda, edad_promedio, sexo_moda
        FROM corredores_riesgo
        ORDER BY cantidad_siniestros DESC
    """)
    resultado = cur.fetchall()
    cur.close()
    conn.close()

    if not resultado:
        return []

    ahora = datetime.now()
    hora_actual = ahora.hour
    dia_actual = ahora.strftime('%A')
    clima_actual = obtener_clima_actual()

    filas = pd.DataFrame({
        'hora': hora_actual,
        'edad_victima': [c['edad_promedio'] for c in resultado],
        'edad_desconocida': 0,
        'temperatura': clima_actual['temperatura'],
        'humedad': clima_actual['humedad'],
        'dia_semana': dia_actual,
        'comuna': [c['comuna_moda'] for c in resultado],
        'tipo_de_via_siniestro': [c['tipo_via_moda'] for c in resultado],
        'contraparte_siniestro': [c['contraparte_moda'] for c in resultado],
        'sexo_victima': [c['sexo_moda'] for c in resultado],
        'lluvia': clima_actual['lluvia'],
        'indice_inseguridad': [indice_inseguridad_de(c['comuna_moda']) for c in resultado],
    })
    fila_codificada = pd.get_dummies(filas)
    fila_alineada = fila_codificada.reindex(columns=columnas_modelo, fill_value=0)
    matriz_probabilidades = modelo_final.predict_proba(fila_alineada)
    clases = modelo_final.classes_.tolist()

    # Los corredores son, por construccion, solo avenidas con muchos siniestros
    # (ya se filtraron a partir de 30 en notebooks/identificar_corredores.py), asi
    # que su riesgo absoluto cae en un rango mucho mas angosto que el de los 740
    # hotspots (que incluyen tambien esquinas tranquilas con pocos casos). Usar
    # los mismos cortes absolutos de nivel_desde_probabilidades ahi casi todo cae
    # en "alto" — se probo (ver commit) y con eso el 95% de los corredores
    # quedaba en el mismo nivel, sin distinguir ninguno de otro. Por eso el nivel
    # de un corredor es relativo a los demas corredores de este mismo pedido
    # (percentiles), no un corte absoluto: sigue siendo 100% la probabilidad real
    # del modelo, solo cambia como se traduce a las 4 categorias visuales.
    idx_mortal = clases.index('MORTAL')
    idx_grave = clases.index('GRAVE')
    score = 2 * matriz_probabilidades[:, idx_mortal] + matriz_probabilidades[:, idx_grave]
    p25, p75, p95 = np.percentile(score, [25, 75, 95])

    def nivel_relativo(s):
        if s >= p95:
            return 'critico'
        if s >= p75:
            return 'alto'
        if s >= p25:
            return 'medio'
        return 'bajo'

    for i, c in enumerate(resultado):
        probs = dict(zip(clases, [round(float(p), 3) for p in matriz_probabilidades[i]]))
        c['nivel_riesgo'] = nivel_relativo(score[i])
        c['prediccion_modelo'] = probs
        c['geometria'] = json.loads(c['geometria'])

    return resultado


@app.get("/hotspots-inseguridad")
def obtener_hotspots_inseguridad(tipo: Literal["general", "moto"] = "general"):
    """
    Zonas con mayor densidad de delitos reales (robos, hurtos, lesiones,
    amenazas, homicidios — no siniestros de moto), segun el dataset de Delitos
    del GCBA (ver notebooks/identificar_hotspots_inseguridad.py). Es una capa
    aparte de /hotspots y /corredores: esos predicen severidad de un siniestro
    con el modelo entrenado; esto es densidad historica de inseguridad, no
    pasa por el modelo ni depende del clima o la hora actual — el nivel de
    riesgo ya viene calculado (percentiles relativos DENTRO de cada tipo, ver
    cargar_hotspots_inseguridad.py) y no cambia entre un pedido y el siguiente.

    tipo=general: todo delito salvo infracciones de transito.
    tipo=moto: delitos con uso de moto (en la practica, robos).
    """
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT id, cluster, latitud, longitud, cantidad_delitos, comuna_moda, tipo_delito_moda, nivel_riesgo
        FROM hotspots_inseguridad
        WHERE tipo = %s
        ORDER BY cantidad_delitos DESC
    """, (tipo,))
    resultado = cur.fetchall()
    cur.close()
    conn.close()
    return resultado


# --- Trafico en vivo (TomTom) ---
# Dos features distintas, ambas opcionales: si no hay TOMTOM_API_KEY configurada
# (variable de entorno, ver .env.example), los endpoints devuelven 503 y el
# frontend simplemente no ofrece la capa/dato -- el resto de la app funciona
# igual, esto nunca es una dependencia dura.
#
# Todo pasa por el backend (nunca se llama a TomTom directo desde el navegador):
# si la key viajara al frontend, cualquiera podria copiarsela desde las devtools
# y gastar la cuota gratuita del proyecto en minutos. El backend es quien la usa
# y la mantiene fuera de git (.env esta en .gitignore).
TOMTOM_API_KEY = os.getenv('TOMTOM_API_KEY')
TOMTOM_TRAFFIC_TILE_URL = 'https://api.tomtom.com/traffic/map/4/tile/flow/{style}/{z}/{x}/{y}.png'
TOMTOM_ROUTING_URL = 'https://api.tomtom.com/routing/1/calculateRoute/{origen}:{destino}/json'

# Cache en memoria simple (no Redis: un solo proceso, volumen de proyecto de
# tesis, no hace falta mas). El limite de entradas es una salvaguarda contra
# crecimiento sin fin en un server de larga duracion, no una necesidad real al
# volumen esperado de uso.
CACHE_TILES_TTL_SEGUNDOS = 120  # el trafico real no cambia mas rapido que esto
CACHE_TILES_MAX_ENTRADAS = 500
_cache_tiles_trafico = {}

CACHE_ETA_TTL_SEGUNDOS = 60
CACHE_ETA_MAX_ENTRADAS = 200
_cache_eta_trafico = {}


@app.get("/trafico/tiles/{z}/{x}/{y}.png")
def tile_trafico(z: int, x: int, y: int):
    """
    Proxy de los tiles raster de flujo de trafico en vivo de TomTom (estilo
    relative0-dark, pensado para el mapa oscuro de la app: colorea cada calle
    segun que tan lenta esta respecto a su velocidad libre, no la velocidad
    absoluta). Se usa igual que cualquier tile de OpenStreetMap, con el mismo
    esquema z/x/y, asi que del lado del frontend es un TileLayer mas.

    Cache de 120s por tile: varios usuarios mirando la misma zona de CABA en la
    misma ventana de 2 minutos comparten el mismo pedido a TomTom en vez de
    generar uno nuevo por persona/reload -- protege la cuota gratuita mensual
    (200.000 tiles) de un uso descuidado, no porque haga falta para el volumen
    real esperado de este proyecto.
    """
    if not TOMTOM_API_KEY:
        raise HTTPException(status_code=503, detail="TOMTOM_API_KEY no configurada")

    clave = (z, x, y)
    ahora = time.monotonic()
    cacheado = _cache_tiles_trafico.get(clave)
    if cacheado and (ahora - cacheado[1]) < CACHE_TILES_TTL_SEGUNDOS:
        return Response(content=cacheado[0], media_type="image/png")

    try:
        respuesta = httpx.get(
            TOMTOM_TRAFFIC_TILE_URL.format(style="relative0-dark", z=z, x=x, y=y),
            params={"key": TOMTOM_API_KEY},
            timeout=5.0,
        )
        respuesta.raise_for_status()
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="No se pudo obtener el tile de trafico de TomTom")

    if len(_cache_tiles_trafico) > CACHE_TILES_MAX_ENTRADAS:
        _cache_tiles_trafico.clear()
    _cache_tiles_trafico[clave] = (respuesta.content, ahora)
    return Response(content=respuesta.content, media_type="image/png")


class EtaTraficoOut(BaseModel):
    con_trafico_min: int
    sin_trafico_min: int
    diferencia_min: int


@app.get("/trafico/eta", response_model=EtaTraficoOut)
def eta_con_trafico(origen_lat: float, origen_lng: float, destino_lat: float, destino_lng: float):
    """
    Tiempo de viaje real con trafico en vivo (TomTom Routing API) entre dos
    puntos, para mostrar como dato complementario junto al tiempo que ya
    calcula OSRM sobre la ruta que se dibuja en el mapa.

    Importante -- por que es un dato aparte y no un reemplazo: TomTom calcula
    su propia ruta puertas adentro para estimar este tiempo, y esa ruta no es
    necesariamente identica a la que traza OSRM (pueden variar en que calles
    eligen). Mezclar "el tiempo de la ruta de TomTom" con "el trazado de OSRM"
    seria mostrar un dato que no corresponde exactamente a lo que se ve
    dibujado. Por eso el frontend lo etiqueta explicitamente como "con trafico
    en vivo (TomTom)", nunca pisa el tiempo de la ruta trazada.

    Cache de 60s por par origen/destino (redondeado a ~11m de precision) como
    salvaguarda basica contra clicks repetidos accidentales, no por necesidad
    real de volumen.
    """
    if not TOMTOM_API_KEY:
        raise HTTPException(status_code=503, detail="TOMTOM_API_KEY no configurada")

    clave = (round(origen_lat, 4), round(origen_lng, 4), round(destino_lat, 4), round(destino_lng, 4))
    ahora = time.monotonic()
    cacheado = _cache_eta_trafico.get(clave)
    if cacheado and (ahora - cacheado[1]) < CACHE_ETA_TTL_SEGUNDOS:
        return cacheado[0]

    try:
        respuesta = httpx.get(
            TOMTOM_ROUTING_URL.format(origen=f"{origen_lat},{origen_lng}", destino=f"{destino_lat},{destino_lng}"),
            params={"key": TOMTOM_API_KEY, "traffic": "true", "computeTravelTimeFor": "all"},
            timeout=6.0,
        )
        respuesta.raise_for_status()
        resumen = respuesta.json()["routes"][0]["summary"]
    except (httpx.HTTPError, KeyError, IndexError, ValueError):
        raise HTTPException(status_code=502, detail="No se pudo calcular el tiempo con trafico de TomTom")

    con_trafico_min = round(resumen["travelTimeInSeconds"] / 60)
    sin_trafico_min = round(resumen.get("noTrafficTravelTimeInSeconds", resumen["travelTimeInSeconds"]) / 60)
    salida = EtaTraficoOut(
        con_trafico_min=con_trafico_min,
        sin_trafico_min=sin_trafico_min,
        diferencia_min=con_trafico_min - sin_trafico_min,
    )

    if len(_cache_eta_trafico) > CACHE_ETA_MAX_ENTRADAS:
        _cache_eta_trafico.clear()
    _cache_eta_trafico[clave] = (salida, ahora)
    return salida
