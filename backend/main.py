import os
import json
import time
import os
import hashlib
import secrets
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, HTTPException, Request, Response, Header
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, Field, field_validator
import uuid
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import psycopg2.extras
import queue
import threading
from dotenv import load_dotenv
import httpx
import joblib
import pandas as pd

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

# Pool de conexiones a Postgres: antes cada endpoint abria y cerraba su propia
# conexion (psycopg2.connect por pedido), que funciona pero no escala -- cada
# conexion nueva implica un handshake TCP + auth completo. Este pool reutiliza
# conexiones ya abiertas en vez de una nueva por pedido (hasta 10 en simultaneo,
# de sobra para el volumen esperado de este proyecto).
#
# Implementacion propia en vez de psycopg2.pool.SimpleConnectionPool a proposito:
# llama a psycopg2.connect() de la misma forma que antes (no a un metodo interno
# de otra clase), asi los tests que mockean main.psycopg2.connect (ver
# tests/test_main.py) siguen funcionando sin cambios. Ademas es lazy (no abre
# ninguna conexion real al importar el modulo), lo que mantiene valido correr
# pytest sin la base de datos levantada.
class _PoolConexiones:
    """Pool lazy con límite de conexiones físicas y transacciones limpias."""
    def __init__(self, maxsize=10, timeout=5):
        self._libres = queue.LifoQueue(maxsize=maxsize)
        self._maxsize = maxsize
        self._timeout = timeout
        self._creadas = 0
        self._lock = threading.Lock()

    @staticmethod
    def _cerrada(conn):
        # Los tests usan MagicMock como conexión aislada. No se los reutiliza
        # entre requests para que cada fixture conserve su cursor esperado.
        if type(conn).__module__.startswith('unittest.mock'):
            return True
        estado = getattr(conn, 'closed', True)
        # psycopg2 usa 0 para abierta. Los mocks no deben parecer cerrados.
        return isinstance(estado, (bool, int)) and estado != 0

    def _olvidar_conexion(self):
        with self._lock:
            self._creadas = max(0, self._creadas - 1)

    def getconn(self):
        while True:
            try:
                conn = self._libres.get_nowait()
                if not self._cerrada(conn):
                    return conn
                self._olvidar_conexion()
                continue
            except queue.Empty:
                pass

            with self._lock:
                crear = self._creadas < self._maxsize
                if crear:
                    self._creadas += 1
            if crear:
                try:
                    return psycopg2.connect(DATABASE_URL)
                except Exception:
                    self._olvidar_conexion()
                    raise

            try:
                conn = self._libres.get(timeout=self._timeout)
            except queue.Empty as exc:
                raise RuntimeError('Pool de conexiones agotado') from exc
            if not self._cerrada(conn):
                return conn
            self._olvidar_conexion()

    def putconn(self, conn):
        if conn is None:
            return
        try:
            if self._cerrada(conn):
                self._olvidar_conexion()
                return
            # Un SELECT también abre una transacción en psycopg2. Siempre se
            # devuelve limpia para que el siguiente endpoint no herede estado.
            conn.rollback()
            self._libres.put_nowait(conn)
        except Exception:
            try:
                conn.close()
            finally:
                self._olvidar_conexion()


_pool_conexiones = _PoolConexiones()

# Rutas absolutas basadas en la ubicación de este archivo: el backend siempre
# encuentra sus artefactos sin importar desde qué directorio se lo ejecute
# (antes eran rutas relativas, y solo funcionaban si se corría parado en backend/).
BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()

# Rate limiting por IP en los endpoints con costo real: computo del modelo para
# los 740 hotspots en cada pedido (/hotspots) o para un solo escenario
# (/predecir), escritura en base (/reportes POST) y llamada a un servicio
# externo pago (/rutas, via TomTom). Limite conservador pensado para no afectar
# el uso normal de una sola persona navegando el mapa, solo cortar abuso obvio
# (scripts, refresh en loop) antes de que impacte la cuota de TomTom o la base
# de datos. /hotspots es, en volumen de computo, el mas caro de los cinco (un
# predict_proba de lote sobre 740 filas en cada llamada, sin cache propia mas
# alla del clima) y no tenia limite -- se lo agrega con el mismo criterio.
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Origenes permitidos por CORS, separados por coma en la variable de entorno
# CORS_ALLOWED_ORIGINS (ver .env.example). Sin esa variable, quedan los dos
# puertos de desarrollo local de Vite -- en un deploy real hay que definirla
# con el dominio publico real del frontend, o el navegador bloquea los
# pedidos aunque el backend responda bien.
_origenes_default = "http://localhost:5173,http://localhost:5174"
CORS_ALLOWED_ORIGINS = [
    origen.strip() for origen in os.getenv("CORS_ALLOWED_ORIGINS", _origenes_default).split(",") if origen.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
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
# La hora y el dia de la semana son features del modelo (franjas pico de
# siniestralidad, ver constants.js del frontend): tienen que ser la hora real
# de Buenos Aires, no la hora local del servidor. datetime.now() sin tz da la
# hora del sistema operativo del proceso -- en desarrollo coincide con la de
# CABA porque la PC esta configurada asi, pero en un deploy real (contenedor
# en UTC, tipico de la mayoria de los hostings) el modelo recibiria una hora
# desfasada 3hs y clasificaria mal el riesgo horario sin ningun error visible.
ZONA_CABA = ZoneInfo('America/Argentina/Buenos_Aires')
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
#
# "robo" se separo de "inseguro" (antes una sola categoria "Zona insegura") porque
# son cosas distintas: robo es un hecho puntual (arrebato, robo en curso o recien
# pasado), con vigencia corta y que dispara una alerta de proximidad en vivo en el
# frontend si sucedio hace poco (ver MINUTOS_ALERTA_REPORTE_RECIENTE en
# frontend/src/constants.js); inseguro es una percepcion de zona (poca luz, sin
# gente) que no es un evento puntual y no amerita esa alerta.
CATEGORIAS_REPORTE_VALIDAS = ('robo', 'inseguro', 'pavimento', 'corte', 'iluminacion')
VIGENCIA_HORAS_POR_CATEGORIA = {
    'corte': 12,           # cortes/desvios: casi siempre se resuelven en el dia
    'robo': 48,            # hecho puntual: sirve de advertencia un par de dias, despues es ruido viejo
    'inseguro': 24 * 7,    # percepcion de inseguridad: vale refrescarla cada semana
    'pavimento': 24 * 30,  # pozos/pavimento roto: tarda semanas o meses en arreglarse
    'iluminacion': 24 * 30,
}

# Umbral de retiro anticipado por consenso (ver listar_reportes): si suficientes
# usuarios distintos dicen "ya no esta", el reporte se oculta del mapa antes de
# que venza su timer de vigencia normal. Exige tanto un piso absoluto de
# desmentidas (para que un solo voto malintencionado no tire abajo un reporte
# real) como que le ganen claramente a las confirmaciones (para que un reporte
# activamente confirmado no se caiga por un par de desmentidas sueltas).
MIN_DESMENTIDAS_PARA_OCULTAR = 2
MIN_DIFERENCIA_DESMENTIDAS_PARA_OCULTAR = 2
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


# Cortes de percentil (p25/p75/p95) que separan bajo/medio/alto/critico, calibrados
# UNA SOLA VEZ offline sobre una poblacion de referencia amplia -- ver
# notebooks/calibrar_umbrales_riesgo.py -- en vez de recalcularse en cada pedido
# HTTP sobre el lote de ese momento.
#
# Por que un corte fijo y no percentiles del lote de cada pedido (que es lo que
# habia antes, ver historial de niveles_relativos_desde_matriz): 'hora' es el
# feature mas influyente del modelo con bastante diferencia sobre el resto (ver
# docs/3_Resultados_DETALLADO.md) y se le pasa el MISMO valor a las 740 filas de
# un pedido (la hora real del momento de la consulta). El Random Forest generaliza
# fuerte sobre esa variable, asi que a ciertas horas la probabilidad predicha para
# las 740 zonas se comprime (terminan pareciendose mucho entre si). Calcular
# percentiles DESDE CERO sobre esa distribucion ya comprimida hacia que "alto"
# significara cosas distintas segun la hora de la consulta -- a las 3am salia
# "casi todo alto" y a las 11am "bastante repartido", no porque el mapa cambiara
# de contenido sino porque la vara de medir se recalibraba sola en cada pedido.
#
# La correccion: los percentiles se calculan una sola vez sobre una poblacion de
# referencia que cubre las 24 horas x 7 dias x lluvia si/no para las 740 zonas (o
# los 243 corredores), y esos cortes quedan fijos. La probabilidad en si se sigue
# calculando en vivo con la hora/clima reales de cada pedido -- lo que cambia es
# contra que se la compara. Consecuencia esperada y correcta: de madrugada mas
# zonas caen en alto/critico que a media mañana (verificado: hora 3am da
# aproximadamente bajo=122 medio=96 alto=346 critico=176 sobre 740, mientras que
# hora 11am da aproximadamente bajo=223 medio=500 alto=16 critico=1) -- eso es la
# señal real que el modelo aprendio (de noche es mas grave), no un artefacto de
# calculo, y ahora 'alto' significa lo mismo sin importar cuando se consulte.
UMBRALES_HOTSPOTS = {'p25': 0.7097281275573558, 'p75': 0.8510277233152828, 'p95': 1.0168910028314664}
UMBRALES_CORREDORES = {'p25': 0.7366849020697045, 'p75': 0.8824753817295781, 'p95': 1.0313856422589212}


def niveles_relativos_desde_matriz(matriz_probabilidades, clases, cortes):
    """
    Traduce probabilidades del modelo a nivel de riesgo categórico, contra
    cortes de percentil fijos (cortes: dict con 'p25'/'p75'/'p95', ver
    UMBRALES_HOTSPOTS / UMBRALES_CORREDORES y el comentario que las calibra),
    no con un corte absoluto arbitrario ni con percentiles recalculados sobre
    el lote de este pedido puntual.

    Es la tercera version de esta funcion, cada una resolviendo el problema de
    la anterior:
    1. Corte absoluto fijo (p_mortal >= 0.20 -> critico, etc.): el modelo
       aprende que CABA en su conjunto es zona de riesgo vial relativamente
       alto, asi que la probabilidad de GRAVE/MORTAL viene alta en la enorme
       mayoria de los 740 hotspots -- ~86% terminaba en 'alto'/'critico'
       (confirmado en producción: Bajo 6, Medio 98, Alto 568, Crítico 68).
    2. Percentiles calculados sobre el lote de CADA pedido: resolvia la
       comparacion entre zonas en un mismo momento, pero 'hora' (el feature
       mas influyente del modelo) es igual para todo el lote y cambia entre
       pedidos, asi que la vara de medir se recalibraba sola en cada
       consulta -- 'alto' dejaba de significar lo mismo de una hora a otra.
    3. (esta version) Percentiles calculados UNA SOLA VEZ sobre una poblacion
       de referencia que cubre todas las horas/dias/climas posibles: la
       probabilidad se sigue calculando en vivo, pero se compara contra una
       vara fija, asi que el significado de cada nivel es estable en el
       tiempo y las diferencias reales (de noche es mas grave) siguen
       reflejandose sin distorsionar la escala.

    p_mortal pesa el doble que p_grave en el score (mismo criterio que las
    versiones anteriores: preferible sobre-alertar en MORTAL antes que en
    GRAVE, que el modelo discrimina peor -- ver docs/3_Resultados). Sigue
    siendo 100% la probabilidad real del modelo: cambia únicamente contra qué
    vara fija se comparan esas probabilidades.
    """
    idx_mortal = clases.index('MORTAL')
    idx_grave = clases.index('GRAVE')
    score = 2 * matriz_probabilidades[:, idx_mortal] + matriz_probabilidades[:, idx_grave]

    def nivel_relativo(s):
        if s >= cortes['p95']:
            return 'critico'
        if s >= cortes['p75']:
            return 'alto'
        if s >= cortes['p25']:
            return 'medio'
        return 'bajo'

    return [nivel_relativo(s) for s in score]


@app.get("/")
def raiz():
    return {"mensaje": "MotoSafe GBA API funcionando"}


@app.get("/health")
def estado_salud():
    """Sonda mínima para despliegue: no devuelve configuración ni datos de usuarios."""
    estado_db = "no_verificada"
    try:
        conn = _pool_conexiones.getconn()
        try:
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.close()
            estado_db = "ok"
        finally:
            _pool_conexiones.putconn(conn)
    except Exception:
        estado_db = "no_disponible"
    return {
        "estado": "ok" if estado_db == "ok" else "degradado",
        "base_datos": estado_db,
        "servidor_utc": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/hotspots")
@limiter.limit("30/minute")
def obtener_hotspots(request: Request):
    conn = _pool_conexiones.getconn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT id, cluster, latitud, longitud, cantidad_siniestros, mortales, graves, nivel_riesgo
            FROM hotspots_riesgo
            ORDER BY cantidad_siniestros DESC
        """)
        resultado = cur.fetchall()
        cur.close()
    finally:
        _pool_conexiones.putconn(conn)

    # Una instalación recién creada puede no tener hotspots todavía. Es un
    # estado válido de la aplicación, no una entrada válida para sklearn.
    if not resultado:
        return []

    ahora = datetime.now(ZONA_CABA)
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
    niveles = niveles_relativos_desde_matriz(matriz_probabilidades, clases, UMBRALES_HOTSPOTS)

    # Ver "Ajuste de riesgo por reportes de prensa recientes" mas abajo: un
    # choque reportado en prensa hace poco y cerca de un hotspot le sube el
    # nivel un escalon, sin tocar la calibracion del modelo (nivel_riesgo
    # sigue saliendo 100% del modelo antes de este ajuste).
    reportes_choque_recientes = _obtener_reportes_recientes_por_tipo('choque')

    for i, h in enumerate(resultado):
        probs = dict(zip(clases, [round(float(p), 3) for p in matriz_probabilidades[i]]))
        h['nivel_riesgo'] = niveles[i]
        h['prediccion_modelo'] = probs
        h['contexto_estimado'] = bool(contexto_estimado.iloc[i])
        h['clima'] = clima_actual
        _aplicar_ajuste_riesgo(h, h['latitud'], h['longitud'], reportes_choque_recientes, 'choque')

    return resultado


class ContextoSiniestro(BaseModel):
    hora: int = Field(ge=0, le=23)
    dia_semana: str
    comuna: str
    tipo_de_via: str
    contraparte: str
    edad_victima: float = Field(default=32.0, ge=14, le=95)
    sexo_victima: str = "SD"
    # Si no se pasan, se usa el clima en vivo actual de CABA (ver obtener_clima_actual).
    # Se pueden pasar explícitos para simular un escenario ("¿y si llueve?").
    lluvia: str | None = None
    temperatura: float | None = Field(default=None, ge=-30, le=60)
    humedad: float | None = Field(default=None, ge=0, le=100)


@app.post("/predecir")
@limiter.limit("30/minute")
def predecir_gravedad(request: Request, contexto: ContextoSiniestro):
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
    Compatibilidad para instalaciones existentes. Las instalaciones nuevas se
    inicializan con ``backend/migrar.py`` y las migraciones versionadas; este
    guard evita romper una instancia aún no migrada durante la transición.
    """
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reportes_colaborativos (
            id SERIAL PRIMARY KEY,
            lat DOUBLE PRECISION NOT NULL,
            lng DOUBLE PRECISION NOT NULL,
            categoria VARCHAR(30) NOT NULL,
            autor_id VARCHAR(50) NOT NULL,
            delete_token_hash VARCHAR(64),
            creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    # Las filas creadas antes de la corrección no tienen token. Siguen siendo
    # visibles hasta vencer, pero no se pueden borrar con un UUID público.
    cur.execute("ALTER TABLE reportes_colaborativos ADD COLUMN IF NOT EXISTS delete_token_hash VARCHAR(64)")
    conn.commit()
    cur.close()


def _asegurar_tabla_confirmaciones(conn):
    """
    Compatibilidad para instalaciones existentes. Un voto ("confirma" / "desmiente") por dispositivo y por reporte -- el UNIQUE
    de mas abajo es lo que hace que votar de nuevo actualice el voto propio en vez
    de sumar otro (ver confirmar_reporte, INSERT ... ON CONFLICT). ON DELETE CASCADE
    porque una confirmacion sin su reporte no significa nada.
    """
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reportes_confirmaciones (
            id SERIAL PRIMARY KEY,
            reporte_id INTEGER NOT NULL REFERENCES reportes_colaborativos(id) ON DELETE CASCADE,
            autor_id VARCHAR(50) NOT NULL,
            tipo VARCHAR(10) NOT NULL,
            creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (reporte_id, autor_id)
        )
    """)
    conn.commit()
    cur.close()


_esquema_reportes_listo = False
_lock_esquema_reportes = threading.Lock()


def _asegurar_esquema_reportes_una_vez(conn):
    """Compatibilidad transitoria sin ejecutar DDL en cada request."""
    global _esquema_reportes_listo
    if _esquema_reportes_listo:
        return
    with _lock_esquema_reportes:
        if _esquema_reportes_listo:
            return
        _asegurar_tabla_reportes(conn)
        _asegurar_tabla_confirmaciones(conn)
        _esquema_reportes_listo = True


class ReporteNuevo(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    categoria: Literal['robo', 'inseguro', 'pavimento', 'corte', 'iluminacion']
    # No es autenticacion de usuario -- es un identificador de dispositivo (UUID v4
    # generado por el frontend la primera vez que se abre la app y persistido en
    # localStorage, ver frontend/src/App.jsx -- estado autorId). Sirve para que 'borrar mis
    # reportes' borre los del dispositivo que los creo y no los de otro. Se valida el
    # formato UUID para que no sirva mandar un valor corto y adivinable a mano.
    autor_id: str

    @field_validator('autor_id')
    @classmethod
    def validar_autor_id(cls, valor):
        try:
            uuid.UUID(valor)
        except (ValueError, AttributeError, TypeError):
            raise ValueError('autor_id debe ser un UUID valido')
        return str(uuid.UUID(valor))


def _hash_delete_token(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


@app.post("/reportes", status_code=201)
@limiter.limit("20/minute")
def crear_reporte(request: Request, reporte: ReporteNuevo):
    # El token sólo se devuelve en esta respuesta. En la tabla se persiste su
    # hash y GET /reportes nunca expone ni token ni autor_id.
    delete_token = secrets.token_urlsafe(32)
    conn = _pool_conexiones.getconn()
    try:
        _asegurar_tabla_reportes(conn)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            INSERT INTO reportes_colaborativos (lat, lng, categoria, autor_id, delete_token_hash)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, lat, lng, categoria, creado_en
        """, (reporte.lat, reporte.lng, reporte.categoria, reporte.autor_id, _hash_delete_token(delete_token)))
        fila = cur.fetchone()
        conn.commit()
        cur.close()
    except Exception:
        # Si algo revienta a mitad de la transaccion, hay que devolver la
        # conexion limpia al pool -- sin este rollback, la proxima request
        # que la reciba del pool hereda una transaccion abortada y falla con
        # "current transaction is aborted" aunque su propia query sea valida.
        conn.rollback()
        raise
    finally:
        _pool_conexiones.putconn(conn)
    return {**fila, "delete_token": delete_token}


class ConfirmacionNueva(BaseModel):
    # Mismo autor_id de dispositivo que ReporteNuevo (ver nota mas arriba): no es
    # autenticacion real, solo lo minimo para que un dispositivo no pueda votar dos
    # veces el mismo reporte (UNIQUE en reportes_confirmaciones) ni confirmar/desmentir
    # su propio reporte (chequeado en confirmar_reporte).
    autor_id: str
    tipo: Literal['confirma', 'desmiente']

    @field_validator('autor_id')
    @classmethod
    def validar_autor_id(cls, valor):
        try:
            uuid.UUID(valor)
        except (ValueError, AttributeError, TypeError):
            raise ValueError('autor_id debe ser un UUID valido')
        return str(uuid.UUID(valor))


@app.post("/reportes/{reporte_id}/confirmar", status_code=201)
@limiter.limit("30/minute")
def confirmar_reporte(request: Request, reporte_id: int, confirmacion: ConfirmacionNueva):
    """
    Verificacion social sobre un reporte ya existente: cualquier dispositivo que no
    sea el autor original puede marcar "sigue ahi" o "ya no esta". Un segundo voto
    del mismo dispositivo sobre el mismo reporte actualiza su voto anterior (no lo
    duplica), via el UNIQUE(reporte_id, autor_id) + ON CONFLICT de mas abajo.
    """
    conn = _pool_conexiones.getconn()
    try:
        _asegurar_esquema_reportes_una_vez(conn)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT autor_id FROM reportes_colaborativos WHERE id = %s", (reporte_id,))
        reporte = cur.fetchone()
        if reporte is None:
            raise HTTPException(status_code=404, detail="Reporte no encontrado")
        if reporte['autor_id'] == confirmacion.autor_id:
            raise HTTPException(status_code=400, detail="No podes confirmar o desmentir tu propio reporte")
        cur.execute("""
            INSERT INTO reportes_confirmaciones (reporte_id, autor_id, tipo)
            VALUES (%s, %s, %s)
            ON CONFLICT (reporte_id, autor_id) DO UPDATE SET tipo = EXCLUDED.tipo, creado_en = now()
            RETURNING reporte_id, autor_id, tipo
        """, (reporte_id, confirmacion.autor_id, confirmacion.tipo))
        fila = cur.fetchone()
        conn.commit()
        cur.close()
    except Exception:
        conn.rollback()
        raise
    finally:
        _pool_conexiones.putconn(conn)
    return fila


@app.get("/reportes")
def listar_reportes():
    """
    Devuelve los reportes de TODOS los usuarios (esto es lo colaborativo), filtrados
    por vigencia segun su categoria: un reporte vencido no se borra de la base (queda
    como historico), simplemente deja de aparecer en el mapa y de sumar al ajuste de
    riesgo de su zona. Ademas de la vigencia por tiempo, un reporte se retira antes de
    tiempo si la comunidad lo desmiente lo suficiente (ver MIN_DESMENTIDAS_PARA_OCULTAR).
    """
    conn = _pool_conexiones.getconn()
    try:
        _asegurar_esquema_reportes_una_vez(conn)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT r.id, r.lat, r.lng, r.categoria, r.creado_en,
                   COALESCE(SUM(CASE WHEN c.tipo = 'confirma' THEN 1 ELSE 0 END), 0) AS confirmaciones,
                   COALESCE(SUM(CASE WHEN c.tipo = 'desmiente' THEN 1 ELSE 0 END), 0) AS desmentidas
            FROM reportes_colaborativos r
            LEFT JOIN reportes_confirmaciones c ON c.reporte_id = r.id
            GROUP BY r.id
            ORDER BY r.creado_en DESC
        """)
        filas = cur.fetchall()
        cur.close()
    finally:
        _pool_conexiones.putconn(conn)

    ahora = datetime.now(timezone.utc)
    vigentes = []
    for fila in filas:
        vigencia_horas = VIGENCIA_HORAS_POR_CATEGORIA.get(fila['categoria'], VIGENCIA_HORAS_DEFAULT)
        edad_horas = (ahora - fila['creado_en']).total_seconds() / 3600
        if edad_horas > vigencia_horas:
            continue
        # .get (no fila[...]) para tolerar filas sin estas columnas -- pasa en los
        # tests que mockean fetchall con dicts a mano sin confirmaciones/desmentidas.
        desmentidas = fila.get('desmentidas', 0)
        confirmaciones = fila.get('confirmaciones', 0)
        retirado_por_consenso = (
            desmentidas >= MIN_DESMENTIDAS_PARA_OCULTAR
            and (desmentidas - confirmaciones) >= MIN_DIFERENCIA_DESMENTIDAS_PARA_OCULTAR
        )
        if retirado_por_consenso:
            continue
        # La identidad de dispositivo sólo se usa del lado servidor para
        # impedir auto-voto; no forma parte del contrato público del mapa.
        vigentes.append({
            'id': fila['id'], 'lat': fila['lat'], 'lng': fila['lng'],
            'categoria': fila['categoria'], 'creado_en': fila['creado_en'],
            'confirmaciones': confirmaciones, 'desmentidas': desmentidas,
        })
    return vigentes


@app.delete("/reportes/{reporte_id}")
def borrar_reporte(reporte_id: int, delete_token: str = Header(alias="X-Report-Delete-Token", min_length=32, max_length=256)):
    """Borra un reporte sólo con el token secreto entregado al crearlo.

    Un UUID de dispositivo identifica para moderación, pero no autoriza una
    operación destructiva porque antes se exponía a cualquier lector del mapa.
    Se devuelve 404 también ante token inválido para no revelar información.
    """
    conn = _pool_conexiones.getconn()
    try:
        _asegurar_tabla_reportes(conn)
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM reportes_colaborativos WHERE id = %s AND delete_token_hash = %s",
            (reporte_id, _hash_delete_token(delete_token)),
        )
        eliminado = cur.rowcount
        if not eliminado:
            raise HTTPException(status_code=404, detail="Reporte no encontrado")
        conn.commit()
        cur.close()
    except Exception:
        conn.rollback()
        raise
    finally:
        _pool_conexiones.putconn(conn)
    return {"eliminado": True}


# --- Reportes de prensa (corroborados por medios, no por usuarios) ---
# Distintos de reportes_colaborativos a proposito: esto no lo escribe un usuario
# desde la app sino un scraper offline (ver notebooks/scrapear_noticias_robos.py,
# corre unas pocas veces por dia, no en cada request) que junta noticias de robos
# de portales (La Nacion, Infobae) en el GBA. No pasa por el sistema de
# confirmar/desmentir (no tiene sentido "desmentir" una nota publicada) ni
# alimenta la alerta de proximidad en vivo del frontend (una noticia sale horas
# o un dia despues del hecho, nunca es "esto esta pasando ahora"). Su valor es
# otro: cubrir el arranque en frio del mapa colaborativo (recien lanzada la app,
# sin usuarios reportando todavia, esto ya pone datos reales) y darle mas peso a
# la tesis con una fuente verificable ademas de la autoreportada.
#
# nivel_precision indica que tan exacta es la ubicacion extraida del texto de la
# noticia (nunca viene con coordenadas, hay que inferirlas -- ver el scraper):
# 'interseccion' (calle y calle, la mas precisa), 'calle' (calle + altura) o
# 'barrio'/'partido' (la nota solo menciona la zona, sin calle). radio_metros
# viene de la mano: cuanto mas vago el texto, mas grande el radio que se pinta
# en el mapa, para no mostrar como pin exacto algo que en realidad es "en algun
# lugar de este barrio". Ver renderizado en el frontend (radio > 0 = circulo,
# no marcador puntual).
VIGENCIA_HORAS_PRENSA = 24 * 30  # "ultimo mes", pedido explicito de Rodo -- no es
                                 # vivo, sirve como contexto/historico reciente


def _asegurar_tabla_prensa(conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reportes_prensa (
            id SERIAL PRIMARY KEY,
            lat DOUBLE PRECISION NOT NULL,
            lng DOUBLE PRECISION NOT NULL,
            nivel_precision VARCHAR(20) NOT NULL,
            radio_metros INTEGER NOT NULL,
            titular TEXT NOT NULL,
            url_fuente VARCHAR(500) NOT NULL UNIQUE,
            fuente VARCHAR(50) NOT NULL,
            tipo_incidente VARCHAR(20) NOT NULL DEFAULT 'robo',
            relacionado_moto BOOLEAN NOT NULL DEFAULT FALSE,
            publicado_en TIMESTAMPTZ,
            creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    # Para bases que ya tenian la tabla creada antes de que existiera esta
    # columna (CREATE TABLE IF NOT EXISTS no la agrega si la tabla ya
    # existe) -- ver la misma alteracion del lado del scraper
    # (scrapear_noticias_robos.py:_asegurar_tabla), asi que corra primero
    # cualquiera de los dos dos la tabla termina igual.
    cur.execute("ALTER TABLE reportes_prensa ADD COLUMN IF NOT EXISTS tipo_incidente VARCHAR(20) NOT NULL DEFAULT 'robo'")
    cur.execute("ALTER TABLE reportes_prensa ADD COLUMN IF NOT EXISTS relacionado_moto BOOLEAN NOT NULL DEFAULT FALSE")
    conn.commit()
    cur.close()


@app.get("/reportes-prensa")
def listar_reportes_prensa():
    """
    Igual que /reportes pero de la tabla de prensa: filtra por VIGENCIA_HORAS_PRENSA
    (30 dias fijo, no varia por nada). Desde v5 hay dos tipo_incidente posibles
    ('robo', 'choque' -- ver scrapear_noticias_robos.py), cada uno con su
    propio icono en el frontend. No se borra nada de la base, solo deja de
    devolverse.
    """
    conn = _pool_conexiones.getconn()
    try:
        _asegurar_tabla_prensa(conn)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT id, lat, lng, nivel_precision, radio_metros, titular, url_fuente, fuente, tipo_incidente, relacionado_moto, creado_en
            FROM reportes_prensa
            ORDER BY creado_en DESC
        """)
        filas = cur.fetchall()
        cur.close()
    finally:
        _pool_conexiones.putconn(conn)

    ahora = datetime.now(timezone.utc)
    return [
        fila for fila in filas
        if (ahora - fila['creado_en']).total_seconds() / 3600 <= VIGENCIA_HORAS_PRENSA
    ]


# --- Ajuste de riesgo por reportes de prensa recientes ---
# Pedido explicito de Rodo: los reportes recientes de prensa (robos, choques)
# tienen que "contemplarse en el riesgo", no ser solo una capa visual aparte.
# Decision de diseño (confirmada con Rodo antes de implementar): el modelo
# entrenado NO se toca -- sus umbrales de percentil (UMBRALES_HOTSPOTS/
# UMBRALES_CORREDORES) estan calibrados una sola vez offline para que
# "alto"/"critico" signifique siempre lo mismo, y meter esto como feature
# nueva del Random Forest exigiria reentrenar y recalibrar, sin sentido
# todavia con pocas semanas de reportes acumulados. En cambio, el nivel que
# YA calculo el modelo se sube un escalon (bajo->medio->alto->critico,
# nunca mas alla de critico) cuando hay un reporte del tipo correspondiente
# a poca distancia y reciente de verdad -- y queda marcado explicitamente
# (ajustado_por_reciente + motivo_ajuste) para que se note en el frontend y
# en la tesis que ese nivel no es 100% el output crudo del modelo.
#
# Que tipo de reporte ajusta que capa es semantico, no arbitrario: 'choque'
# ajusta /hotspots y /corredores (predicen severidad de SINIESTRO VIAL, un
# choque de prensa es literalmente un dato de esa misma naturaleza); 'robo'
# ajusta /hotspots-inseguridad (densidad de DELITO, no de siniestro).
RADIO_AJUSTE_RECIENTE_METROS = 600
DIAS_AJUSTE_RECIENTE = 7
CACHE_REPORTES_RECIENTES_TTL_SEGUNDOS = 180
_cache_reportes_recientes = {}  # tipo_incidente -> {'datos': [...], 'timestamp': float}
_NIVELES_EN_ORDEN = ('bajo', 'medio', 'alto', 'critico')


def _obtener_reportes_recientes_por_tipo(tipo_incidente, dias=DIAS_AJUSTE_RECIENTE):
    """Lista de {'lat', 'lng', 'titular'} de reportes_prensa de ese tipo
    dentro de los ultimos `dias` dias, cacheada un rato corto (ver
    CACHE_REPORTES_RECIENTES_TTL_SEGUNDOS -- el scraper corre a lo sumo unas
    pocas veces por dia, no hace falta ir a la base en cada pedido de
    /hotspots). Nunca rompe el endpoint que la llama: si la tabla no existe
    todavia, la conexion falla, o una fila viene con datos raros, se la
    ignora y sigue -- este ajuste es un plus visible, no una dependencia
    dura (mismo criterio que ya se usa para TomTom/clima)."""
    entrada = _cache_reportes_recientes.get(tipo_incidente)
    ahora_ts = time.time()
    if entrada and (ahora_ts - entrada['timestamp']) < CACHE_REPORTES_RECIENTES_TTL_SEGUNDOS:
        return entrada['datos']

    reportes = []
    conn = None
    try:
        conn = _pool_conexiones.getconn()
        _asegurar_tabla_prensa(conn)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT lat, lng, titular, creado_en
            FROM reportes_prensa
            WHERE tipo_incidente = %s
            ORDER BY creado_en DESC
        """, (tipo_incidente,))
        filas = cur.fetchall()
        cur.close()
        ahora = datetime.now(timezone.utc)
        for fila in filas:
            try:
                lat, lng, titular, creado_en = fila['lat'], fila['lng'], fila['titular'], fila['creado_en']
                if lat is None or lng is None or creado_en is None:
                    continue
                if (ahora - creado_en).total_seconds() / 3600 > dias * 24:
                    continue
                reportes.append({'lat': float(lat), 'lng': float(lng), 'titular': titular})
            except (KeyError, TypeError, ValueError):
                continue
    except Exception:
        reportes = []
    finally:
        if conn is not None:
            _pool_conexiones.putconn(conn)

    _cache_reportes_recientes[tipo_incidente] = {'datos': reportes, 'timestamp': ahora_ts}
    return reportes


def _distancia_metros(lat1, lng1, lat2, lng2):
    """Haversine simple -- de sobra de precision para un radio de a lo sumo
    unos cientos de metros, no hace falta nada mas fino (ni una extension de
    Postgres) para este uso."""
    import math
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _nivel_subido_un_escalon(nivel):
    if nivel not in _NIVELES_EN_ORDEN:
        return nivel
    idx = _NIVELES_EN_ORDEN.index(nivel)
    return _NIVELES_EN_ORDEN[min(idx + 1, len(_NIVELES_EN_ORDEN) - 1)]


def _ajuste_por_reportes_recientes(lat, lng, reportes, radio_m=RADIO_AJUSTE_RECIENTE_METROS):
    """Devuelve (hay_ajuste, cantidad, titular_mas_reciente) segun cuantos de
    `reportes` (ya prefiltrados por tipo y por antigüedad, ver
    _obtener_reportes_recientes_por_tipo) caen a `radio_m` o menos de
    (lat, lng). `reportes` viene ordenado por creado_en DESC, asi que el
    primer match en el loop ya es el mas reciente."""
    cercanos = [r for r in reportes if _distancia_metros(lat, lng, r['lat'], r['lng']) <= radio_m]
    if not cercanos:
        return False, 0, None
    return True, len(cercanos), cercanos[0]['titular']


def _aplicar_ajuste_riesgo(fila, lat, lng, reportes, tipo_label):
    """Muta `fila` (dict) in-place: sube nivel_riesgo un escalon si hay un
    reporte reciente cerca, y deja siempre presentes ajustado_por_reciente/
    motivo_ajuste (True/mensaje o False/None) para que el frontend pueda
    mostrarlo sin adivinar si la clave existe."""
    hay_ajuste, cantidad, titular = _ajuste_por_reportes_recientes(lat, lng, reportes)
    fila['ajustado_por_reciente'] = hay_ajuste
    if hay_ajuste:
        fila['nivel_riesgo'] = _nivel_subido_un_escalon(fila['nivel_riesgo'])
        plural = 's' if cantidad != 1 else ''
        fila['motivo_ajuste'] = (
            f"{cantidad} {tipo_label}{plural} reportado{plural} en prensa en los últimos "
            f"{DIAS_AJUSTE_RECIENTE} días cerca de esta zona (más reciente: \"{titular}\")"
        )
    else:
        fila['motivo_ajuste'] = None


def _vertices_de_geometria(geometria):
    """Extrae los vertices (lat, lng) de corredores_riesgo.geometria ya
    parseada (json.loads de la columna) -- una lista plana de pares
    [lat, lng] (ver test_corredores_devuelve_nivel_de_riesgo_y_geometria_parseada
    en tests/test_main.py, que documenta el formato real). Devuelve [] ante
    cualquier formato inesperado en vez de romper el endpoint."""
    try:
        return [(float(lat), float(lng)) for lat, lng in geometria]
    except (TypeError, ValueError):
        return []


def _aplicar_ajuste_por_corredor(corredor, reportes, tipo_label):
    """Como _aplicar_ajuste_riesgo, pero para un corredor (calle entera, no
    un punto): "cerca" es cerca de CUALQUIER vertice de su trazado. Entre
    todos los reportes que caen cerca de algun vertice, se usa el mas
    reciente para el mensaje."""
    vertices = _vertices_de_geometria(corredor.get('geometria', {}))
    mejor = (False, 0, None)
    for lat, lng in vertices:
        hay, cantidad, titular = _ajuste_por_reportes_recientes(lat, lng, reportes)
        if hay and cantidad > mejor[1]:
            mejor = (hay, cantidad, titular)
    corredor['ajustado_por_reciente'] = mejor[0]
    if mejor[0]:
        corredor['nivel_riesgo'] = _nivel_subido_un_escalon(corredor['nivel_riesgo'])
        cantidad, titular = mejor[1], mejor[2]
        plural = 's' if cantidad != 1 else ''
        corredor['motivo_ajuste'] = (
            f"{cantidad} {tipo_label}{plural} reportado{plural} en prensa en los últimos "
            f"{DIAS_AJUSTE_RECIENTE} días cerca de este corredor (más reciente: \"{titular}\")"
        )
    else:
        corredor['motivo_ajuste'] = None


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
    conn = _pool_conexiones.getconn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT id, calle, tramo, tramos_totales, geometria, cantidad_siniestros, mortales, graves,
                   comuna_moda, tipo_via_moda, contraparte_moda, edad_promedio, sexo_moda
            FROM corredores_riesgo
            ORDER BY cantidad_siniestros DESC
        """)
        resultado = cur.fetchall()
        cur.close()
    finally:
        _pool_conexiones.putconn(conn)

    if not resultado:
        return []

    ahora = datetime.now(ZONA_CABA)
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
    # (ya se filtraron a partir de 30 en notebooks/identificar_corredores.py),
    # asi que su riesgo absoluto cae en un rango distinto al de los 740
    # hotspots puntuales -- por eso tienen su propia poblacion de referencia
    # calibrada por separado (UMBRALES_CORREDORES, ver
    # notebooks/calibrar_umbrales_riesgo.py), no los mismos cortes que
    # /hotspots, aunque la funcion de clasificacion es la misma.
    niveles = niveles_relativos_desde_matriz(matriz_probabilidades, clases, UMBRALES_CORREDORES)

    reportes_choque_recientes = _obtener_reportes_recientes_por_tipo('choque')

    for i, c in enumerate(resultado):
        probs = dict(zip(clases, [round(float(p), 3) for p in matriz_probabilidades[i]]))
        c['nivel_riesgo'] = niveles[i]
        c['prediccion_modelo'] = probs
        c['geometria'] = json.loads(c['geometria'])
        # Un corredor es una calle entera, no un punto -- se toma "cerca" como
        # "cerca de CUALQUIER vertice de su trazado" (ver _vertices_de_geometria),
        # no del centro ni de un extremo solo.
        _aplicar_ajuste_por_corredor(c, reportes_choque_recientes, 'choque')

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
    conn = _pool_conexiones.getconn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT id, cluster, latitud, longitud, cantidad_delitos, comuna_moda, tipo_delito_moda, nivel_riesgo
            FROM hotspots_inseguridad
            WHERE tipo = %s
            ORDER BY cantidad_delitos DESC
        """, (tipo,))
        resultado = cur.fetchall()
        cur.close()
    finally:
        _pool_conexiones.putconn(conn)

    # A diferencia de /hotspots y /corredores (siniestros viales), esta capa
    # Es densidad de delito: robos y otros hechos explícitos de inseguridad
    # pueden ajustar esta capa; los choques continúan separados porque sólo
    # aportan contexto a la capa vial.
    reportes_robo_recientes = (
        _obtener_reportes_recientes_por_tipo('robo')
        + _obtener_reportes_recientes_por_tipo('inseguridad')
    )
    for h in resultado:
        _aplicar_ajuste_riesgo(h, h['latitud'], h['longitud'], reportes_robo_recientes, 'robo')

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

# Traduccion de codigos de maniobra de TomTom Routing API al formato que ya
# espera el frontend (heredado del contrato de OSRM: tipo + modificador, ver
# frontend/src/utils/ui.js -- textoManiobra/iconoManiobra). Se traduce en el
# backend para no tocar nada de esa logica de UI, que ya esta probada.
TOMTOM_MANIOBRA_A_OSRM = {
    "ARRIVE": ("arrive", None),
    "ARRIVE_LEFT": ("arrive", "left"),
    "ARRIVE_RIGHT": ("arrive", "right"),
    "DEPART": ("depart", None),
    "STRAIGHT": ("turn", "straight"),
    "KEEP_RIGHT": ("fork", "slight right"),
    "BEAR_RIGHT": ("turn", "slight right"),
    "TURN_RIGHT": ("turn", "right"),
    "SHARP_RIGHT": ("turn", "sharp right"),
    "KEEP_LEFT": ("fork", "slight left"),
    "BEAR_LEFT": ("turn", "slight left"),
    "TURN_LEFT": ("turn", "left"),
    "SHARP_LEFT": ("turn", "sharp left"),
    "MAKE_UTURN": ("turn", "uturn"),
    "TRY_MAKE_UTURN": ("turn", "uturn"),
    "ENTER_MOTORWAY": ("merge", "straight"),
    "ENTER_FREEWAY": ("merge", "straight"),
    "ENTER_HIGHWAY": ("merge", "straight"),
    "TAKE_EXIT": ("end of road", "right"),
    "MOTORWAY_EXIT_LEFT": ("end of road", "left"),
    "MOTORWAY_EXIT_RIGHT": ("end of road", "right"),
    "TAKE_FERRY": ("merge", "straight"),
    "ROUNDABOUT_CROSS": ("roundabout", "straight"),
    "ROUNDABOUT_RIGHT": ("roundabout", "right"),
    "ROUNDABOUT_LEFT": ("roundabout", "left"),
    "ROUNDABOUT_BACK": ("roundabout", "uturn"),
    "FOLLOW": ("turn", "straight"),
    "SWITCH_PARALLEL_ROAD": ("turn", "straight"),
    "SWITCH_MAIN_ROAD": ("turn", "straight"),
    "ENTRANCE_RAMP": ("merge", "straight"),
    "WAYPOINT_LEFT": ("turn", "left"),
    "WAYPOINT_RIGHT": ("turn", "right"),
    "WAYPOINT_REACHED": ("turn", "straight"),
    "WAYPOINT_APPROACH": ("turn", "straight"),
    "AHEAD_KEEP_RIGHT": ("fork", "slight right"),
    "AHEAD_RIGHT_TURN": ("turn", "right"),
    "AHEAD_KEEP_LEFT": ("fork", "slight left"),
    "AHEAD_LEFT_TURN": ("turn", "left"),
    "AHEAD_UTURN": ("turn", "uturn"),
    "AHEAD_EXIT": ("end of road", "right"),
    "AHEAD_EXIT_RIGHT": ("end of road", "right"),
    "AHEAD_EXIT_LEFT": ("end of road", "left"),
    "AHEAD_TAKE_FERRY": ("merge", "straight"),
}


class PasoRutaOut(BaseModel):
    tipo: str
    modificador: str | None = None
    calle: str | None = None
    lat: float
    lng: float


class EtaTraficoOut(BaseModel):
    con_trafico_min: int
    sin_trafico_min: int
    diferencia_min: int


class RutaOut(BaseModel):
    coords: list[list[float]]
    km: float
    min: int
    eta_trafico: EtaTraficoOut | None = None
    pasos: list[PasoRutaOut]


@app.get("/rutas", response_model=list[RutaOut])
@limiter.limit("20/minute")
def calcular_rutas(
    request: Request, origen_lat: float, origen_lng: float, destino_lat: float, destino_lng: float,
    alternativas: int = 2
):
    """
    Reemplaza al servidor de demo publico de OSRM (router.project-osrm.org):
    ese servidor esta pensado solo para pruebas, sin garantia de
    disponibilidad ni limite de uso documentado, no apto para produccion.

    Usa la Routing API de TomTom (la misma cuenta/key que ya se usa para el
    trafico en vivo) para calcular la ruta, sus alternativas, la guia
    turn-by-turn y el tiempo real con trafico en vivo, todo en un solo
    pedido -- lo que de paso resuelve el problema que tenia el diseño anterior
    de mezclar el trazado de OSRM con el tiempo de TomTom (dos rutas
    calculadas por separado, no necesariamente identicas). Ahora el trazado y
    el tiempo con trafico salen de la misma ruta.

    "min" se completa con noTrafficTravelTimeInSeconds (tiempo de referencia,
    sin trafico) para no romper la logica existente de comparacion entre
    rutas (rapida/corta) que ya usa ese campo. El tiempo con trafico en vivo
    va aparte en eta_trafico, igual que antes.
    """
    if not TOMTOM_API_KEY:
        raise HTTPException(status_code=503, detail="TOMTOM_API_KEY no configurada")

    try:
        respuesta = httpx.get(
            TOMTOM_ROUTING_URL.format(
                origen=f"{origen_lat},{origen_lng}", destino=f"{destino_lat},{destino_lng}"
            ),
            params={
                "key": TOMTOM_API_KEY,
                "traffic": "true",
                "computeTravelTimeFor": "all",
                "maxAlternatives": max(0, min(alternativas, 5)),
                "routeRepresentation": "polyline",
                "instructionsType": "tagged",
            },
            timeout=8.0,
        )
        respuesta.raise_for_status()
        rutas_tomtom = respuesta.json()["routes"]
    except (httpx.HTTPError, KeyError, IndexError, ValueError):
        raise HTTPException(status_code=502, detail="No se pudo calcular la ruta con TomTom")

    if not rutas_tomtom:
        raise HTTPException(status_code=404, detail="TomTom no encontro una ruta entre esos puntos")

    salida = []
    for ruta in rutas_tomtom:
        pierna = ruta["legs"][0]
        coords = [[p["latitude"], p["longitude"]] for p in pierna["points"]]
        resumen = ruta["summary"]

        con_trafico_min = round(resumen["travelTimeInSeconds"] / 60)
        sin_trafico_seg = resumen.get("noTrafficTravelTimeInSeconds", resumen["travelTimeInSeconds"])
        sin_trafico_min = round(sin_trafico_seg / 60)

        pasos = []
        for instr in ruta.get("guidance", {}).get("instructions", []):
            tipo, modificador = TOMTOM_MANIOBRA_A_OSRM.get(instr.get("maneuver", ""), ("turn", "straight"))
            pasos.append(
                PasoRutaOut(
                    tipo=tipo,
                    modificador=modificador,
                    calle=instr.get("street") or None,
                    lat=instr["point"]["latitude"],
                    lng=instr["point"]["longitude"],
                )
            )

        salida.append(
            RutaOut(
                coords=coords,
                km=round(resumen["lengthInMeters"] / 1000, 1),
                min=sin_trafico_min,
                eta_trafico=EtaTraficoOut(
                    con_trafico_min=con_trafico_min,
                    sin_trafico_min=sin_trafico_min,
                    diferencia_min=con_trafico_min - sin_trafico_min,
                ),
                pasos=pasos,
            )
        )

    return salida
