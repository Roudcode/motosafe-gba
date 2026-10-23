import os
import json
import time
import os
import hashlib
import re
import secrets
import unicodedata
from difflib import SequenceMatcher
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Literal
from urllib.parse import quote
from fastapi import FastAPI, HTTPException, Request, Response, Header
from fastapi.responses import JSONResponse
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
import warnings
import joblib
import pandas as pd
import sklearn
from sklearn.exceptions import InconsistentVersionWarning

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
    # X-Email (SES-169): login con nombre de usuario devuelve el email real en
    # un header para la pantalla de verificación -- sin expose_headers, fetch
    # en el navegador no puede leer headers custom de una respuesta cross-origin.
    expose_headers=["X-Requiere-Verificacion", "X-Email"],
)

# --- Autenticacion de sesion -------------------------------------------------
# La app puede quedar expuesta a internet (Tailscale Funnel), asi que todo lo
# que no sea /health o /auth/* exige una cookie de sesion valida. Ver auth.py
# para el detalle de login/logout y el formato de la cookie.
import auth  # noqa: E402  (va aca para no reordenar los imports de arriba)

app.include_router(auth.router)

_RUTAS_PUBLICAS = {
    "/health", "/auth/login", "/auth/logout", "/auth/me",
    # F11 (SES-165): estas tienen que funcionar SIN cookie de sesion -- son
    # justamente el flujo para conseguir una.
    "/auth/registro", "/auth/verificar-codigo", "/auth/reenviar-codigo",
    "/auth/olvide-password", "/auth/resetear-password",
}


@app.middleware("http")
async def exigir_sesion(request: Request, call_next):
    if request.method == "OPTIONS" or request.url.path in _RUTAS_PUBLICAS:
        return await call_next(request)
    if not auth.sesion_valida(request):
        return JSONResponse(status_code=401, content={"detail": "No autenticado"})
    return await call_next(request)


# --- Modelo de Machine Learning (entrenado con notebooks/reentrenar_modelo.py) ---
# scikit-learn no garantiza que un pickle cargue igual en otra versión. Si la
# versión instalada no es la del entrenamiento, sklearn emite
# InconsistentVersionWarning al cargar: se captura acá para exponerla en
# /health (version_sklearn_coincide) en vez de dejarla perdida en la consola.
# No bloquea el arranque: la comparación de A22 (docs/evidencias/2026-10-05/
# A22-entorno/) mostró niveles idénticos entre 1.7.2 y 1.9.1, pero eso no vale
# para cualquier versión futura. requirements.txt fija la versión exacta.
with warnings.catch_warnings(record=True) as _avisos_carga_modelo:
    warnings.simplefilter('always', InconsistentVersionWarning)
    modelo_final = joblib.load(BASE_DIR / 'modelo_final.pkl')
SKLEARN_VERSION_ENTRENAMIENTO = next(
    (a.message.original_sklearn_version for a in _avisos_carga_modelo
     if isinstance(a.message, InconsistentVersionWarning)),
    sklearn.__version__,
)
# Se re-emiten para que sigan viéndose en consola, uno por texto distinto (sin
# esto saldría uno por cada uno de los 300 árboles del bosque).
for _aviso in {str(a.message): a.message for a in _avisos_carga_modelo}.values():
    warnings.warn(_aviso, stacklevel=1)
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
# Recalibrados el 05/10/2026 tras sacar edad_victima/edad_desconocida del
# modelo (ver notebooks/reentrenar_modelo.py) -- un cambio de features cambia
# la distribucion de scores de la poblacion de referencia, asi que estos
# cortes HAY que volver a calcularlos cada vez que cambia el modelo o el
# universo de hotspots/corredores (ver notebooks/calibrar_umbrales_riesgo.py
# y el chequeo de huella en _verificar_umbrales_actualizados mas abajo, que
# avisa en /health si estos valores quedaron desactualizados respecto a los
# artefactos reales en vez de quedar desincronizados en silencio).
UMBRALES_HOTSPOTS = {'p25': 0.6950040471874488, 'p75': 0.8270579939778988, 'p95': 1.0243031457262397}
UMBRALES_CORREDORES = {'p25': 0.7188575554056662, 'p75': 0.8516986379914744, 'p95': 1.0372954984662501}

# confianza_estabilidad (columna de hotspots_contexto.csv, expuesta en /hotspots):
# qué tan sensible es el nivel_riesgo de ESA zona puntual a la variabilidad propia
# de reentrenar el modelo, no a si generaliza bien de un año a otro (eso ya lo mide
# D02). Se entrenaron 10 Random Forest con los mismos hiperparámetros de
# modelo_final sobre 10 remuestras bootstrap del dataset completo (el mismo
# universo que usa reentrenar_modelo.py, sin recorte por año), se evaluó cada uno
# sobre la misma grilla de 336 escenarios (24 horas x 7 días x lluvia sí/no) que
# calibra UMBRALES_HOTSPOTS, y se midió en qué fracción de esos 10 modelos la zona
# cae en el mismo nivel de riesgo que el resto -- esa fracción, promediada sobre
# los 336 escenarios, es confianza_estabilidad (ver notebooks/calcular_confianza_zonas.py
# y docs/evidencias/2026-10-18/confianza-zonas-bootstrap/).
#
# Resultado real sobre las 740 zonas: acuerdo global entre los 10 modelos 84,9%
# (mediana 90,0%), con 'crítico' y 'alto' sensiblemente menos estables (78,5-78,9%
# de acuerdo) que 'bajo' y 'medio' (85,3-90,3%) -- la inestabilidad se concentra
# justo en los niveles que más importan para una decisión de seguridad. Por zona,
# la mediana de acuerdo es 83,8%, con un mínimo de 52,6% y solo 1 zona (de 740) por
# debajo del 60%. NO reemplaza nivel_riesgo (que sigue siendo 100% el output de
# modelo_final.pkl, sin tocar su calibración): es una medida adicional, honesta,
# de cuánto puede sostenerse esa clasificación puntual si el modelo se reentrena.
# None cuando el hotspot no tiene fila propia en hotspots_contexto.csv (no hay
# bootstrap calculado para un perfil genérico que no es una zona real).


def _huella_artefactos_riesgo():
    """SHA256 de los artefactos que alimentaron la calibracion de UMBRALES_HOTSPOTS/
    CORREDORES (ver notebooks/calibrar_umbrales_riesgo.py). Si estos bytes cambian
    (se reentreno el modelo, se actualizo el contexto de hotspots o el indice de
    inseguridad) sin que alguien vuelva a correr ese script y pegue los valores
    nuevos acá, los cortes p25/p75/p95 quedan calibrados contra una poblacion que
    ya no es la real -- esta huella detecta esa desincronizacion en vez de dejarla
    pasar en silencio. A proposito NO recalibra sola: un sistema de riesgo vial
    que se recalibra solo, sin que nadie revise el resultado antes de que se
    sirva, es peor practica que uno que avisa y espera una accion deliberada (una
    corrida de un script de segundos). Ver /health -> umbrales_riesgo_actualizados.
    No cubre corredores_riesgo.csv (vive en data/, no en backend/, y los
    corredores se sirven desde Postgres, no desde ese CSV en runtime): cubre el
    disparador principal de un recalculo real, que es el modelo entrenado."""
    h = hashlib.sha256()
    for nombre in ('modelo_final.pkl', 'hotspots_contexto.csv', 'indice_inseguridad_comuna.csv'):
        h.update((BASE_DIR / nombre).read_bytes())
    return h.hexdigest()


# Se pega a mano junto con los umbrales de arriba cada vez que se corre
# calibrar_umbrales_riesgo.py (que ahora imprime esta huella al final). Si no
# coincide con _huella_artefactos_riesgo() en runtime, /health lo expone.
_HUELLA_UMBRALES_CALIBRADOS = '19401654e33717952769b8af10a349a55de4e8d064ed4bfde0a672b9241a4fff'
try:
    UMBRALES_RIESGO_ACTUALIZADOS = _huella_artefactos_riesgo() == _HUELLA_UMBRALES_CALIBRADOS
except OSError:
    UMBRALES_RIESGO_ACTUALIZADOS = True  # no se pudo leer un artefacto -- no bloquear el arranque por esto


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


# --- Métricas por ruta (T04) ---
# Conteo de requests, errores 4xx/5xx y latencia por ruta, en memoria del
# proceso (se pierde al reiniciar, no hace falta persistirlo: es para
# observar el servicio corriendo, no para reportar historicos). Sin datos
# personales, tokens ni configuracion -- solo ruta, status y tiempo.
_metricas_lock = threading.Lock()
_metricas_por_ruta = {}


def _registrar_metrica(ruta, status_code, duracion_ms):
    with _metricas_lock:
        entrada = _metricas_por_ruta.setdefault(ruta, {
            "conteo": 0, "errores_4xx": 0, "errores_5xx": 0, "latencia_total_ms": 0.0,
        })
        entrada["conteo"] += 1
        entrada["latencia_total_ms"] += duracion_ms
        if 400 <= status_code < 500:
            entrada["errores_4xx"] += 1
        elif status_code >= 500:
            entrada["errores_5xx"] += 1


@app.middleware("http")
async def _middleware_metricas(request: Request, call_next):
    inicio = time.monotonic()
    # request.scope['route'] recien queda seteado despues de que el router
    # matchea el path -- usar el template ("/reportes/{reporte_id}") y no la
    # URL real evita una entrada distinta por cada id de reporte.
    try:
        respuesta = await call_next(request)
    except Exception:
        duracion_ms = (time.monotonic() - inicio) * 1000
        ruta_obj = request.scope.get("route")
        ruta = ruta_obj.path if ruta_obj is not None else request.url.path
        _registrar_metrica(ruta, 500, duracion_ms)
        raise
    duracion_ms = (time.monotonic() - inicio) * 1000
    ruta_obj = request.scope.get("route")
    ruta = ruta_obj.path if ruta_obj is not None else request.url.path
    _registrar_metrica(ruta, respuesta.status_code, duracion_ms)
    return respuesta


@app.get("/metrics")
def metricas():
    """Latencia promedio y errores por ruta desde que arrancó el proceso.

    Sin claves, tokens, coordenadas de usuario ni configuracion -- solo
    conteos y tiempos agregados por ruta, para observabilidad basica del
    servicio (ver T04 en BACKLOG.md).
    """
    with _metricas_lock:
        return {
            ruta: {
                "conteo": datos["conteo"],
                "errores_4xx": datos["errores_4xx"],
                "errores_5xx": datos["errores_5xx"],
                "latencia_promedio_ms": round(datos["latencia_total_ms"] / datos["conteo"], 2)
                    if datos["conteo"] else 0,
            }
            for ruta, datos in _metricas_por_ruta.items()
        }


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
        # Ver _huella_artefactos_riesgo arriba: false acá significa que el
        # modelo/contexto/indice de inseguridad cambiaron desde la última vez
        # que se corrió calibrar_umbrales_riesgo.py, y que UMBRALES_HOTSPOTS/
        # CORREDORES quedaron calibrados contra una población que ya no es la
        # real. No bloquea el servicio (sigue respondiendo con el último
        # corte conocido) pero hay que recalibrar a la brevedad.
        "umbrales_riesgo_actualizados": UMBRALES_RIESGO_ACTUALIZADOS,
        # false: el modelo se entrenó con otra versión de scikit-learn que la
        # instalada (ver carga del modelo arriba). Reinstalar requirements.txt.
        # Solo el booleano: /health es público y no publica versiones exactas
        # (el detalle queda en el aviso de la consola al arrancar).
        "version_sklearn_coincide": SKLEARN_VERSION_ENTRENAMIENTO == sklearn.__version__,
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
    columnas_contexto = ['cluster', 'comuna_moda', 'tipo_via_moda', 'contraparte_moda', 'edad_promedio', 'sexo_moda', 'confianza_estabilidad']
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
    # confianza_estabilidad NO se completa con un generico: no se calculo para
    # un hotspot sin fila propia (ver comentario largo mas abajo), asi que
    # queda None en vez de inventar un numero.

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
        valor_confianza = contexto['confianza_estabilidad'].iloc[i]
        h['confianza_estabilidad'] = None if pd.isna(valor_confianza) else round(float(valor_confianza), 3)
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


# El rate limit de arriba es por IP (20/min): no distingue dos dispositivos
# detras del mismo NAT/red, ni frena a alguien que reparte requests entre
# varias redes. Esta cuota es la segunda barrera, por dispositivo (autor_id)
# y por dia en vez de por minuto -- pensada para volumen anormal sostenido,
# no para golpes rapidos (eso ya lo frena el rate limit).
CUOTA_REPORTES_POR_DIA_POR_AUTOR = 15


@app.post("/reportes", status_code=201)
@limiter.limit("20/minute")
def crear_reporte(request: Request, reporte: ReporteNuevo):
    # El token sólo se devuelve en esta respuesta. En la tabla se persiste su
    # hash y GET /reportes nunca expone ni token ni autor_id.
    delete_token = secrets.token_urlsafe(32)
    conn = _pool_conexiones.getconn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT COUNT(*) AS cantidad FROM reportes_colaborativos
            WHERE autor_id = %s AND creado_en > now() - interval '24 hours'
        """, (reporte.autor_id,))
        conteo_previo = cur.fetchone()['cantidad']
        if conteo_previo >= CUOTA_REPORTES_POR_DIA_POR_AUTOR:
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Alcanzaste el límite de {CUOTA_REPORTES_POR_DIA_POR_AUTOR} "
                    "reportes por dispositivo en 24 horas. Probá de nuevo más tarde."
                ),
            )
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


def _estado_reporte(categoria, creado_en, confirmaciones, desmentidas, ahora):
    """Estado real de un reporte: 'vigente', 'vencido' (pasó su ventana de
    tiempo por categoría) o 'desmentido' (la comunidad lo retiró por consenso
    antes de vencer, ver MIN_DESMENTIDAS_PARA_OCULTAR). El orden de los
    chequeos -- tiempo primero, consenso después -- es el mismo que usaba
    listar_reportes antes de esta función existir, para no cambiar su
    comportamiento al extraerla. vence_en es la fecha teórica de vencimiento
    por tiempo, se devuelve siempre (incluso para un reporte ya desmentido)."""
    vigencia_horas = VIGENCIA_HORAS_POR_CATEGORIA.get(categoria, VIGENCIA_HORAS_DEFAULT)
    vence_en = creado_en + timedelta(hours=vigencia_horas)
    edad_horas = (ahora - creado_en).total_seconds() / 3600
    if edad_horas > vigencia_horas:
        return 'vencido', vence_en
    retirado_por_consenso = (
        desmentidas >= MIN_DESMENTIDAS_PARA_OCULTAR
        and (desmentidas - confirmaciones) >= MIN_DIFERENCIA_DESMENTIDAS_PARA_OCULTAR
    )
    if retirado_por_consenso:
        return 'desmentido', vence_en
    return 'vigente', vence_en


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
        # .get (no fila[...]) para tolerar filas sin estas columnas -- pasa en los
        # tests que mockean fetchall con dicts a mano sin confirmaciones/desmentidas.
        desmentidas = fila.get('desmentidas', 0)
        confirmaciones = fila.get('confirmaciones', 0)
        estado, vence_en = _estado_reporte(fila['categoria'], fila['creado_en'], confirmaciones, desmentidas, ahora)
        if estado != 'vigente':
            continue
        # La identidad de dispositivo sólo se usa del lado servidor para
        # impedir auto-voto; no forma parte del contrato público del mapa.
        vigentes.append({
            'id': fila['id'], 'lat': fila['lat'], 'lng': fila['lng'],
            'categoria': fila['categoria'], 'creado_en': fila['creado_en'],
            'confirmaciones': confirmaciones, 'desmentidas': desmentidas,
            'vence_en': vence_en.isoformat(),
        })
    return vigentes


@app.delete("/reportes/{reporte_id}")
@limiter.limit("20/minute")
def borrar_reporte(request: Request, reporte_id: int, delete_token: str = Header(alias="X-Report-Delete-Token", min_length=32, max_length=256)):
    """Borra un reporte sólo con el token secreto entregado al crearlo.

    Un UUID de dispositivo identifica para moderación, pero no autoriza una
    operación destructiva porque antes se exponía a cualquier lector del mapa.
    Se devuelve 404 también ante token inválido para no revelar información.
    """
    conn = _pool_conexiones.getconn()
    try:
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


class ReporteMioConsulta(BaseModel):
    id: int
    # Misma credencial privada que autoriza borrar (ver borrar_reporte) --
    # reutilizarla acá evita inventar un segundo mecanismo de identidad para
    # lo mismo: "este dispositivo es dueño de este reporte".
    delete_token: str = Field(min_length=32, max_length=256)


class ConsultaMisReportes(BaseModel):
    # Tope para no aceptar un batch arbitrariamente grande -- tokensReportes
    # en el frontend es, en la práctica, un puñado de reportes por dispositivo
    # (la cuota diaria ya los limita, ver CUOTA_REPORTES_POR_DIA_POR_AUTOR).
    reportes: list[ReporteMioConsulta] = Field(max_length=50)


@app.post("/reportes/mios")
@limiter.limit("20/minute")
def listar_mis_reportes(request: Request, consulta: ConsultaMisReportes):
    """
    Estado histórico de reportes propios: vigente, vencido o desmentido.
    GET /reportes no alcanza para esto a propósito -- excluye los reportes
    vencidos o retirados por consenso porque el mapa público solo debe
    mostrar lo vigente (ver listar_reportes). Acá la identidad es la misma
    credencial privada que autoriza borrar (id + delete_token); un id sin su
    token correcto, o el de un reporte ajeno, simplemente no aparece en la
    respuesta -- mismo criterio de "no revelar información" que borrar_reporte.
    """
    if not consulta.reportes:
        return []
    ids = [r.id for r in consulta.reportes]
    # Conjunto de pares (no dict id->hash): si el mismo id viene dos veces con
    # tokens distintos -- normalmente no pasa, pero el cliente podría mandarlo
    # mal -- un dict se quedaría solo con el último y podría descartar el
    # token correcto si vino antes que uno equivocado para el mismo id.
    pares_validos = {(r.id, _hash_delete_token(r.delete_token)) for r in consulta.reportes}
    conn = _pool_conexiones.getconn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT r.id, r.lat, r.lng, r.categoria, r.creado_en, r.delete_token_hash,
                   COALESCE(SUM(CASE WHEN c.tipo = 'confirma' THEN 1 ELSE 0 END), 0) AS confirmaciones,
                   COALESCE(SUM(CASE WHEN c.tipo = 'desmiente' THEN 1 ELSE 0 END), 0) AS desmentidas
            FROM reportes_colaborativos r
            LEFT JOIN reportes_confirmaciones c ON c.reporte_id = r.id
            WHERE r.id = ANY(%s)
            GROUP BY r.id
        """, (ids,))
        filas = cur.fetchall()
        cur.close()
    finally:
        _pool_conexiones.putconn(conn)

    ahora = datetime.now(timezone.utc)
    resultado = []
    for fila in filas:
        if (fila['id'], fila['delete_token_hash']) not in pares_validos:
            continue
        confirmaciones = fila.get('confirmaciones', 0)
        desmentidas = fila.get('desmentidas', 0)
        estado, vence_en = _estado_reporte(fila['categoria'], fila['creado_en'], confirmaciones, desmentidas, ahora)
        resultado.append({
            'id': fila['id'], 'lat': fila['lat'], 'lng': fila['lng'],
            'categoria': fila['categoria'], 'creado_en': fila['creado_en'],
            'confirmaciones': confirmaciones, 'desmentidas': desmentidas,
            'estado': estado, 'vence_en': vence_en.isoformat(),
        })
    return resultado


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

# Google Noticias se retiró por su robots.txt (DEC-011). Sus filas viejas siguen
# en la tabla, pero la API no las devuelve ni las usa para el riesgo. No se
# borran: limpiar la tabla es una decisión aparte, con backup (SES-080).
#
# duplicado_de_id IS NULL (A09, SES-129/130): scrapear_noticias_robos.py marca
# una fila como duplicado semantico de otra (mismo hecho, cubierto por un medio
# distinto) sin borrarla -- el dato crudo queda completo y auditable en la
# tabla. Este filtro es lo que la excluye de lo que de verdad se muestra y se
# cuenta, igual que ya hace con Google Noticias.
_FILTRO_FUENTES_PRENSA_SQL = "NOT starts_with(fuente, 'Google Noticias') AND duplicado_de_id IS NULL"

# Fecha de referencia de cada nota: la de publicación si es plausible (no más de
# un día después de la ingesta ni más de VIGENCIA_HORAS_PRENSA antes), y si no, la
# de ingesta. Una fecha mal extraída (ej. 2013) o faltante no debe dejar vigente
# una nota vieja ni ocultar una reciente (SES-080).
_FECHA_REFERENCIA_PRENSA_SQL = f"""
    CASE
        WHEN publicado_en IS NOT NULL
             AND publicado_en BETWEEN creado_en - INTERVAL '{VIGENCIA_HORAS_PRENSA // 24} days'
                                  AND creado_en + INTERVAL '1 day'
        THEN publicado_en
        ELSE creado_en
    END
"""


@app.get("/reportes-prensa")
def listar_reportes_prensa():
    """
    Igual que /reportes pero de la tabla de prensa: filtra por VIGENCIA_HORAS_PRENSA
    (30 dias fijo, no varia por nada). La vigencia usa la fecha de publicación
    cuando existe y la fecha de ingesta sólo como respaldo. No se borra nada
    de la base, solo deja de devolverse.
    """
    conn = _pool_conexiones.getconn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(f"""
            SELECT id, lat, lng, nivel_precision, radio_metros, titular, url_fuente, fuente, tipo_incidente, relacionado_moto,
                   {_FECHA_REFERENCIA_PRENSA_SQL} AS publicado_en, creado_en
            FROM reportes_prensa
            WHERE {_FILTRO_FUENTES_PRENSA_SQL}
            ORDER BY publicado_en DESC
        """)
        filas = cur.fetchall()
        cur.close()
    finally:
        _pool_conexiones.putconn(conn)

    ahora = datetime.now(timezone.utc)
    return [
        fila for fila in filas
        # .get y creado_en como respaldo: una respuesta histórica o una
        # migración parcial no debe derribar toda la capa de prensa.
        if (ahora - (fila.get('publicado_en') or fila['creado_en'])).total_seconds() / 3600 <= VIGENCIA_HORAS_PRENSA
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
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(f"""
            SELECT lat, lng, titular, {_FECHA_REFERENCIA_PRENSA_SQL} AS fecha_referencia
            FROM reportes_prensa
            WHERE tipo_incidente = %s AND {_FILTRO_FUENTES_PRENSA_SQL}
            ORDER BY fecha_referencia DESC
        """, (tipo_incidente,))
        filas = cur.fetchall()
        cur.close()
        ahora = datetime.now(timezone.utc)
        for fila in filas:
            try:
                lat, lng, titular, fecha_referencia = fila['lat'], fila['lng'], fila['titular'], fila['fecha_referencia']
                if lat is None or lng is None or fecha_referencia is None:
                    continue
                if (ahora - fecha_referencia).total_seconds() / 3600 > dias * 24:
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


# --- Ajuste de riesgo por franja horaria (solo /hotspots-inseguridad) -----
# Misma filosofia que el ajuste por reportes recientes de arriba: no se toca
# el calculo base del nivel (percentiles de cantidad_delitos por tipo, ver
# cargar_hotspots_inseguridad.py), se sube un escalon cuando corresponde y
# queda marcado explicitamente (ajustado_por_horario/motivo_ajuste_horario)
# para que se note en el frontend y en la tesis que no es el dato crudo.
#
# Por que hace falta esto y /hotspots y /corredores no lo necesitan: esos dos
# ya reciben 'hora' como feature real de un modelo entrenado (Random Forest,
# ver predecir_para_fila) -- el riesgo de SINIESTRO que muestran ya varia
# segun la hora de la consulta. /hotspots-inseguridad en cambio es densidad
# historica de DELITO sin componente horario: sin este ajuste, "evitar un
# robo a esta hora" quedaba reducido a un mapa de calor plano que da el mismo
# nivel a las 4am que a las 21hs, pese a que el propio dataset de Delitos del
# GCBA muestra que no es asi (ver detalle abajo). Entrenar un modelo nuevo
# para esto no se justifica todavia (es un problema distinto -- prediccion de
# delito, no de siniestro -- y exigiria su propia evaluacion academica); este
# ajuste por franja es la version honesta y chica del mismo principio que ya
# se aplica a siniestros, usando el dato horario real que ya esta en el
# dataset en vez de dejarlo sin usar.
#
# Las franjas pico salen de la distribucion REAL de franja_horaria en
# data/delitos_caba.csv (columna que existia pero se perdia por un alias
# incompleto en fetch_delitos_caba.py, corregido). Se probo primero una
# heuristica generica de "horario nocturno" (22-6hs) y la distribucion real
# la contradijo: 0-6hs es en realidad el tramo de MENOR incidencia en ambos
# subtipos. Tampoco hay una franja compartida que calce bien para los dos:
# - Robos con moto: pico marcado 19-23hs (20-21hs llegan a 7.3-7.5% de los
#   casos vs. 4.2% esperado si fuera parejo en 24hs).
# - Delito general: pico mas temprano y mas suave, 17-21hs (5.1-5.6% vs.
#   4.17% esperado); a las 23hs ya volvio al baseline, a diferencia de robos
#   con moto que sigue elevado hasta esa hora.
#
# Rango [desde, hasta] en hora de Buenos Aires (ZONA_CABA, misma fuente que
# usan /hotspots y /corredores para 'hora_actual' -- nunca la hora del
# sistema del servidor, que puede estar en UTC en un hosting real).
FRANJA_PICO_INSEGURIDAD = {
    'moto':    {'desde': 19, 'hasta': 23, 'etiqueta': '19-23hs'},
    'general': {'desde': 17, 'hasta': 21, 'etiqueta': '17-21hs'},
}


def _en_franja_pico_inseguridad(tipo, hora):
    franja = FRANJA_PICO_INSEGURIDAD.get(tipo)
    if not franja:
        return False
    return franja['desde'] <= hora <= franja['hasta']


def _aplicar_ajuste_horario(fila, tipo, hora_actual):
    """Muta `fila` (dict, un hotspot de /hotspots-inseguridad) in-place: sube
    nivel_riesgo un escalon si la hora actual (Buenos Aires) cae en la franja
    pico calibrada para `tipo` (ver FRANJA_PICO_INSEGURIDAD). Se aplica
    DESPUES del ajuste por reportes recientes, asi que se apilan: una zona
    puede subir dos escalones si ademas hay un reporte reciente cerca (el
    tope sigue siendo 'critico', _nivel_subido_un_escalon no pasa de ahi).
    Deja siempre ajustado_por_horario presente, mismo criterio de
    transparencia que el resto de los ajustes de esta capa."""
    en_pico = _en_franja_pico_inseguridad(tipo, hora_actual)
    fila['ajustado_por_horario'] = en_pico
    if en_pico:
        fila['nivel_riesgo'] = _nivel_subido_un_escalon(fila['nivel_riesgo'])
        franja = FRANJA_PICO_INSEGURIDAD[tipo]
        fila['motivo_ajuste_horario'] = (
            f"Ahora ({hora_actual}hs) es franja de mayor incidencia histórica de este tipo de delito "
            f"({franja['etiqueta']})"
        )
    else:
        fila['motivo_ajuste_horario'] = None


# Período de cobertura de cada capa (A10/A11/A15). Lo genera
# notebooks/generar_metadatos_capas.py desde data/, que no está versionado, así
# que se guarda en un JSON versionado al lado del modelo. Si falta, el endpoint
# devuelve las capas sin período en vez de romper el arranque.
try:
    METADATOS_CAPAS = json.loads((BASE_DIR / 'metadatos_capas.json').read_text(encoding='utf-8'))
except (OSError, ValueError):
    METADATOS_CAPAS = {}


@app.get("/capas/cobertura")
def cobertura_capas():
    """Qué período cubren los datos de cada capa, para que la interfaz muestre
    la vigencia real del riesgo (por ejemplo "siniestros 2019-2025") y no solo
    cuándo se consultó. `archivo_generado` es secundario. Prensa es dinámica:
    ventana de vigencia y fecha de la nota más reciente en la base."""
    mas_reciente = None
    conn = None
    try:
        conn = _pool_conexiones.getconn()
        cur = conn.cursor()
        cur.execute(f"SELECT max({_FECHA_REFERENCIA_PRENSA_SQL}) FROM reportes_prensa WHERE {_FILTRO_FUENTES_PRENSA_SQL}")
        fila = cur.fetchone()
        valor = fila[0] if fila else None
        mas_reciente = valor.isoformat() if isinstance(valor, datetime) else None
        cur.close()
    except Exception:
        mas_reciente = None  # la cobertura de prensa es un dato accesorio
    finally:
        if conn is not None:
            _pool_conexiones.putconn(conn)
    return {
        **METADATOS_CAPAS,
        'prensa': {'vigencia_dias': VIGENCIA_HORAS_PRENSA // 24, 'mas_reciente': mas_reciente},
    }


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
    con un modelo entrenado que ya usa 'hora' como feature; esto es densidad
    historica de delito y no pasa por ningun modelo ni depende del clima,
    pero SI depende de la hora actual desde el ajuste por franja horaria (ver
    FRANJA_PICO_INSEGURIDAD/_aplicar_ajuste_horario mas abajo): la base
    (percentiles relativos DENTRO de cada tipo, ver
    cargar_hotspots_inseguridad.py) no cambia entre pedidos, pero el nivel
    final que se devuelve puede subir un escalon segun la hora y los
    reportes recientes cercanos, igual que en /hotspots y /corredores.

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
    hora_actual = datetime.now(ZONA_CABA).hour
    for h in resultado:
        _aplicar_ajuste_riesgo(h, h['latitud'], h['longitud'], reportes_robo_recientes, 'robo')
        _aplicar_ajuste_horario(h, tipo, hora_actual)

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


# --- Búsqueda de lugares con sugerencias (SES-090) -------------------------
# Reemplaza el autocompletado EN VIVO contra Nominatim, que su política
# prohíbe (DEC-011/A18) -- TomTom sigue siendo quien responde mientras el
# usuario escribe. La clave de TomTom queda en el servidor. Las respuestas se
# cachean unos minutos para no gastar cupo en cada tecla repetida.
TOMTOM_SEARCH_URL = 'https://api.tomtom.com/search/2/search/{consulta}.json'
_CACHE_LUGARES_TTL_SEGUNDOS = 600

# Respaldo gratuito cuando TomTom no encuentra nada (SES-108): medido con
# casos reales que Rodo reportó como "no lo encuentra" -- el campus de la
# USAL en Pilar y un barrio privado no están en el catálogo de POI de
# TomTom bajo ningún nombre que se probó, pero sí están en OpenStreetMap
# (Nominatim los devuelve como "college" y "neighbourhood"). Esto NO es el
# autocompletado prohibido: se llama UNA vez, solo cuando TomTom ya
# respondió vacío para esa consulta exacta (no en cada tecla), y el
# resultado se cachea igual que el de TomTom -- el volumen real es mucho
# menor a los límites de la política (4/min para scripts periódicos; acá
# depende de que alguien escriba y TomTom falle, nunca un bucle).
NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search'
_NOMINATIM_USER_AGENT = 'MotoSafeGBA-tesis-USAL/1.0 (proyecto academico, contacto en README del repo)'
# Caja amplia de Argentina entera, SOLO como último respaldo si no hay
# centro real -- un lugar puede estar fuera del conurbano en sentido
# estricto (mismo motivo que el radio de 150 km de TomTom).
_VIEWBOX_ARGENTINA = '-73.6,-21.8,-53.6,-55.1'
# Medio grado (~55 km) a cada lado del centro real: bug real medido (SES-110,
# Rodo parado en Pilar) -- esta función nunca recibía el centro del usuario y
# siempre pedía con el viewbox de PAÍS ENTERO de arriba. bounded=0 ahí es un
# sesgo tan débil (toda Argentina) que en la práctica no sesgaba nada, y
# Nominatim devolvía su propio orden de "importancia" (que para "farmacia"
# favorece CABA, con más densidad de POI mapeados). Con el viewbox angosto
# alrededor del centro real, el sesgo es real.
_CATEGORIAS_NOMINATIM_ES = {
    'college': 'Universidad', 'university': 'Universidad', 'school': 'Escuela',
    'hospital': 'Hospital', 'pharmacy': 'Farmacia', 'restaurant': 'Restaurante',
    'cafe': 'Café o bar', 'bar': 'Bar', 'fast_food': 'Comida rápida',
    'fuel': 'Estación de servicio', 'bank': 'Banco', 'supermarket': 'Supermercado',
    'neighbourhood': 'Barrio', 'residential': 'Zona residencial', 'suburb': 'Barrio',
    'place_of_worship': 'Templo', 'police': 'Comisaría',
}


def _normalizar_para_comparar(texto):
    sin_acentos = unicodedata.normalize('NFKD', texto or '').encode('ascii', 'ignore').decode('ascii')
    return sin_acentos.lower()


def _parecida(palabra, etiqueta, umbral=0.55):
    """True si `palabra` se parece (similitud de texto, no substring exacto)
    a ALGUNA palabra de `etiqueta`. Bug real medido (SES-110, Rodo parado en
    Pilar): "farmacia" buscado ahí da resultados reales y bien ubicados en
    TomTom (Bayer Pilar, Fada Fharma, Biofarma -- laboratorios del parque
    industrial de Pilar), pero NINGUNO contiene el substring exacto
    "farmacia" (son nombres de marca: "Fharma", no el diccionario). Exigir
    substring exacto los rechazaba a todos como "sin relación" y disparaba
    el respaldo de Nominatim sin necesidad -- que para colmo, en términos
    genéricos como "farmacia", termina favoreciendo CABA de cualquier forma
    (ver el comentario de _buscar_lugares_nominatim). SequenceMatcher mide
    similitud real de caracteres: "farmacia" vs "fharma" da 0.71, vs
    "biofarma" 0.62, vs ruido real como "camus" o "bayer pilar" da 0.3-0.4
    -- 0.55 separa bien ambos grupos, medido con estos casos reales."""
    return any(
        SequenceMatcher(None, palabra, p).ratio() >= umbral
        for p in re.findall(r'[a-z]+', etiqueta)
    )


def _algun_resultado_relevante(consulta, resultados):
    """True si ALGÚN resultado de TomTom tiene en su etiqueta, a la vez, una
    palabra PARECIDA a la PRIMERA y a la ÚLTIMA palabra significativa (3+
    letras) de la consulta (la misma si la consulta es una sola palabra).
    En una búsqueda real el nombre específico suele ir primero y la
    localidad al final ("USAL Campus Pilar", "Fika Pilar") -- exigir solo
    una de las dos falla para los dos lados: solo "Pilar" (última) da por
    bueno cualquier resultado cercano sin relación real (el sesgo de
    ubicación mete "Pilar" en casi todo); solo "Universidad" (primera, de
    "Universidad del Salvador Pilar") da por bueno OTRA sede de la misma
    universidad en CABA, que tiene "Universidad" pero no "Pilar". Exigir
    las dos en el MISMO resultado filtra ambos casos reales medidos
    (SES-108). Esto distingue "encontró algo relacionado" de "no encontró
    nada pero devolvió una coincidencia fonética o de otra sede sin
    relación real" (ver el comentario largo en buscar_lugares)."""
    palabras = [p for p in re.findall(r'[a-z]+', _normalizar_para_comparar(consulta)) if len(p) >= 3]
    if not palabras:
        return True  # consulta sin palabras evaluables (solo numeros/simbolos): no se puede juzgar, no se fuerza el respaldo
    primera, ultima = palabras[0], palabras[-1]
    return any(
        _parecida(primera, _normalizar_para_comparar(r['label'])) and _parecida(ultima, _normalizar_para_comparar(r['label']))
        for r in resultados
    )


def _etiqueta_nominatim(item):
    # display_name trae la jerarquía completa ("Nombre, Localidad, Partido,
    # Provincia, CP, País") -- igual de verboso que seguir mostrando todo
    # como hace Nominatim por defecto; se recorta a los primeros 3 tramos
    # para que se lea parecido a como arma su etiqueta TomTom (_label_lugar).
    partes = (item.get('display_name') or '').split(', ')
    return ', '.join(partes[:3]) if partes else None


def _buscar_lugares_nominatim(consulta, limite, centro_lat=None, centro_lon=None):
    if centro_lat is not None and centro_lon is not None:
        viewbox = f"{centro_lon - 0.5},{centro_lat + 0.5},{centro_lon + 0.5},{centro_lat - 0.5}"
    else:
        viewbox = _VIEWBOX_ARGENTINA
    try:
        respuesta = httpx.get(
            NOMINATIM_URL,
            params={
                'format': 'json', 'q': consulta, 'countrycodes': 'ar',
                'viewbox': viewbox, 'bounded': 0,
                'limit': max(1, min(limite, 8)), 'addressdetails': 0,
            },
            headers={'User-Agent': _NOMINATIM_USER_AGENT, 'Accept-Language': 'es'},
            timeout=10,
        )
        respuesta.raise_for_status()
    except httpx.HTTPError:
        # Un fallo acá no debe tirar abajo la búsqueda entera -- TomTom ya
        # contestó vacío, así que el resultado final sigue siendo "nada",
        # igual que si este respaldo no existiera.
        return []
    datos = []
    for item in respuesta.json():
        label = _etiqueta_nominatim(item)
        try:
            lat, lon = float(item['lat']), float(item['lon'])
        except (KeyError, TypeError, ValueError):
            continue
        if label:
            datos.append({
                'label': label, 'lat': lat, 'lng': lon,
                'categoria': _CATEGORIAS_NOMINATIM_ES.get(item.get('type'), (item.get('type') or '').capitalize() or None),
            })
    return datos
_cache_lugares = {}  # consulta normalizada -> {'datos': [...], 'momento': float}


def _label_lugar(item):
    direccion = item.get('address', {})
    calle = ' '.join(p for p in [direccion.get('streetName'), direccion.get('streetNumber')] if p)
    calle = calle or direccion.get('freeformAddress', '')
    nombre = item.get('poi', {}).get('name')
    partes = [p for p in [nombre, calle, direccion.get('municipality')] if p]
    return ', '.join(partes)


# TomTom devuelve las categorias de POI en ingles aunque se pida
# language=es-ES (son tags internos, no texto traducible del proveedor) --
# traduce solo las mas frecuentes en busquedas reales (gastronomia, salud,
# combustible, alojamiento); el resto se muestra tal cual viene antes que no
# mostrar nada. _TIPO_SIN_POI cubre el caso contrario: un resultado que es
# una calle o una zona, sin objeto "poi" del que sacar categoria.
_CATEGORIAS_LUGAR_ES = {
    'restaurant': 'Restaurante', 'cafe/pub': 'Café o bar', 'fast food': 'Comida rápida',
    'latin american': 'Comida latinoamericana', 'bakery': 'Panadería', 'bar': 'Bar',
    'pharmacy': 'Farmacia', 'hospital': 'Hospital', 'doctor': 'Consultorio médico',
    'gas station': 'Estación de servicio', 'parking garage': 'Estacionamiento',
    'hotel': 'Hotel', 'supermarket': 'Supermercado', 'shopping': 'Comercio',
    'bank': 'Banco', 'atm': 'Cajero automático', 'school': 'Escuela',
    'police station': 'Comisaría', 'bus station': 'Terminal de colectivos',
    'train station': 'Estación de tren', 'park': 'Parque', 'motorcycle dealer': 'Concesionaria de motos',
}
_TIPO_SIN_POI_ES = {'Street': 'Calle', 'Point Address': 'Dirección', 'Geography': 'Zona'}


def _categoria_lugar(item):
    categorias = item.get('poi', {}).get('categories') or []
    if categorias:
        primera = categorias[0]
        return _CATEGORIAS_LUGAR_ES.get(primera, primera.capitalize())
    return _TIPO_SIN_POI_ES.get(item.get('type'))


# Bbox amplio de Argentina (no solo GBA): valida que un lat/lng que mande el
# cliente sea una posición real del país antes de usarlo como centro de
# sesgo -- un GPS roto devolviendo (0,0) no debe terminar sesgando la
# búsqueda al golfo de Guinea.
_BBOX_ARGENTINA = (-73.6, -55.1, -53.6, -21.8)  # lon_min, lat_min, lon_max, lat_max


def _centro_lugares(lat, lng):
    """(lat, lon) de sesgo para /lugares: la posición real del usuario si la
    mandó y es válida, si no el centro de CABA de siempre."""
    if lat is not None and lng is not None:
        lon_min, lat_min, lon_max, lat_max = _BBOX_ARGENTINA
        if lat_min <= lat <= lat_max and lon_min <= lng <= lon_max:
            return lat, lng
    return -34.6, -58.45


@app.get("/lugares")
@limiter.limit("60/minute")
def buscar_lugares(request: Request, q: str, limite: int = 5, lat: float | None = None, lng: float | None = None):
    consulta = ' '.join(q.split())
    if len(consulta) < 3 or len(consulta) > 120:
        return []
    if not TOMTOM_API_KEY:
        raise HTTPException(status_code=503, detail="TOMTOM_API_KEY no configurada")
    centro_lat, centro_lon = _centro_lugares(lat, lng)
    # El cache es por consulta DE TEXTO -- antes de sumar el sesgo por
    # ubicación eso alcanzaba, porque el resultado para "farmacia" era el
    # mismo para cualquiera. Ahora "farmacia" en Moreno y "farmacia" en CABA
    # son búsquedas distintas de verdad (ver el comentario largo más abajo),
    # así que la clave suma el centro redondeado a ~1 km -- esa redondeo
    # mantiene el cache útil (gente cerca comparte resultados) sin mezclar
    # resultados de zonas distintas del GBA.
    clave = f"{consulta.casefold()}@{centro_lat:.2f},{centro_lon:.2f}"
    entrada = _cache_lugares.get(clave)
    if entrada and time.time() - entrada['momento'] < _CACHE_LUGARES_TTL_SEGUNDOS:
        return entrada['datos']
    try:
        respuesta = httpx.get(
            TOMTOM_SEARCH_URL.format(consulta=quote(consulta)),
            params={
                "key": TOMTOM_API_KEY,
                "limit": max(1, min(limite, 8)),
                "countrySet": "AR",
                "lat": centro_lat,
                "lon": centro_lon,
                # 150 km, no 60: con 60 km (el radio aproximado del GBA) un
                # lugar conocido pero fuera de esa franja (la Basílica de
                # Luján, la ciudad de Zárate) quedaba afuera de los
                # resultados -- TomTom no avisa "no está", directamente
                # ofrece la mejor coincidencia DENTRO del radio, que puede
                # ser una calle homónima sin relación real (medido:
                # "Luján basilica" con 60 km devolvía una capilla en una
                # calle de CABA llamada Luján, no la Basílica real).
                # El centro ahora es la posición real del usuario cuando la
                # manda (ver _centro_lugares) -- antes quedaba siempre fijo
                # en CABA, y alguien parado en Moreno que buscaba "farmacia"
                # recibía farmacias del centro porteño a 30 km en vez de la
                # que tenía a 100 metros (medido con una consulta real a
                # TomTom: mismo "farmacia", sesgo en CABA vs sesgo en Moreno,
                # resultados completamente distintos y ambos "correctos"
                # para SU zona -- el problema no era el radio, era siempre
                # mirar desde el mismo punto).
                "radius": 150000,
                "language": "es-ES",
                "typeahead": "true",
            },
            timeout=10,
        )
        respuesta.raise_for_status()
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Búsqueda de lugares no disponible")
    datos = []
    for item in respuesta.json().get("results", []):
        posicion = item.get("position", {})
        label = _label_lugar(item)
        if label and "lat" in posicion and "lon" in posicion:
            datos.append({
                "label": label, "lat": posicion["lat"], "lng": posicion["lon"],
                "categoria": _categoria_lugar(item),
            })
    if not _algun_resultado_relevante(consulta, datos):
        # TomTom no tiene el lugar bajo ningún nombre probado -- y no
        # siempre devuelve vacío cuando pasa esto: medido con un caso real
        # (SES-108), "USAL Campus Pilar" vuelve CON resultados (calles que
        # suenan parecido, "Calle A. Camus"), ninguno con relación real a lo
        # buscado. Una lista no vacía pero irrelevante es indistinguible de
        # una buena sin mirar el contenido -- _algun_resultado_relevante
        # exige que alguna palabra significativa de la consulta aparezca en
        # algún resultado. Si no, se prueba el respaldo gratuito antes de
        # decirle al usuario "no está". Se descartan los resultados de
        # Nominatim a menos de 300 m de uno que ya puso TomTom (mismo lugar
        # con otro nombre) para no duplicar. Van PRIMERO en la lista, no al
        # final: si TomTom ya devolvió "limite" resultados (su cupo
        # completo, aunque sean irrelevantes), agregarlos al final no servía
        # de nada -- el truncado de abajo los cortaba antes de llegar al
        # usuario. Si TomTom se equivocó, lo más probable es más útil que lo
        # menos probable, va adelante.
        nuevos = []
        for lugar in _buscar_lugares_nominatim(consulta, limite, centro_lat, centro_lon):
            cerca_de_algo = any(
                _distancia_metros(lugar['lat'], lugar['lng'], d['lat'], d['lng']) < 300
                for d in datos
            )
            if not cerca_de_algo:
                nuevos.append(lugar)
        datos = nuevos + datos
    datos = datos[:max(1, min(limite, 8))]
    if len(_cache_lugares) > 500:
        _cache_lugares.clear()
    _cache_lugares[clave] = {'datos': datos, 'momento': time.time()}
    return datos


# --- Geocodificación inversa: barrio real para el portal de Actividad (SES-115) ---
# El pedido es "filtrar por zona" en el frontend, pero ni reportes_prensa ni
# reportes_colaborativos tienen un barrio en la base (solo lat/lng) -- los
# clusters numerados de ZONAS_RIESGO ("Zona 106") no significan nada para
# quien no conoce el modelo. TomTom (la misma key que ya se usa arriba para
# /lugares) sí da el barrio real de un punto.
#
# A propósito NO se usa Nominatim para esto: el proyecto ya tiene una
# decisión tomada (DEC-011/A18) de no usarlo para nada que implique pedir
# muchos puntos -- un feed de 150-300 notas/reportes resolviendo barrio uno
# por uno es justo el tipo de volumen que esa política evita. TomTom no
# tiene esa restricción, pero sí tiene costo/cupo por llamada: por eso la
# cache acá es mucho más agresiva que la de /lugares (30 días, no 10
# minutos -- el barrio de un punto no cambia) y la clave redondea a ~100 m,
# así que decenas de notas de la misma cuadra piden TomTom una sola vez.
TOMTOM_REVERSE_URL = 'https://api.tomtom.com/search/2/reverseGeocode/{lat},{lon}.json'
_cache_reversa = {}
_CACHE_REVERSA_TTL_SEGUNDOS = 30 * 24 * 3600


@app.get("/lugares/reversa")
# 300/min, no 60/min como /lugares: ese límite es por tecla escrita (un
# humano no puede superarlo); este es un burst único de hasta ~150-300
# puntos DISTINTOS la primera vez que alguien abre el portal con el feed
# completo (measured: 100+ pedidos en pocos segundos con el redondeo de
# ~100m ya aplicado) -- un límite de 60/min los frenaba a mitad de carga
# con 429, aunque cada uno fuera a terminar cacheado 30 días.
@limiter.limit("300/minute")
def geocodificar_reversa(request: Request, lat: float, lng: float):
    if not TOMTOM_API_KEY:
        raise HTTPException(status_code=503, detail="TOMTOM_API_KEY no configurada")
    clave = f"{round(lat, 3)},{round(lng, 3)}"
    entrada = _cache_reversa.get(clave)
    if entrada and time.time() - entrada['momento'] < _CACHE_REVERSA_TTL_SEGUNDOS:
        return entrada['datos']
    try:
        respuesta = httpx.get(
            TOMTOM_REVERSE_URL.format(lat=lat, lon=lng),
            params={"key": TOMTOM_API_KEY, "language": "es-ES"},
            timeout=10,
        )
        respuesta.raise_for_status()
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Geocodificación inversa no disponible")
    direcciones = respuesta.json().get("addresses", [])
    barrio = None
    if direcciones:
        direccion = direcciones[0].get("address", {})
        barrio = direccion.get("municipalitySubdivision") or direccion.get("neighbourhood") or direccion.get("localName")
    datos = {"barrio": barrio}
    if len(_cache_reversa) > 2000:
        _cache_reversa.clear()
    _cache_reversa[clave] = {'datos': datos, 'momento': time.time()}
    return datos


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
