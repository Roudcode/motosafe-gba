// Constantes de la app: umbrales de distancia, claves de localStorage,
// definiciones de niveles de riesgo y catálogos fijos (categorías de reporte).
// Se separan de App.jsx para que estén en un solo lugar y no mezcladas con lógica de UI.

import { Construction, TrafficCone, LightbulbOff, ShieldAlert, ShieldOff, Shield, CircleDot, Flame, Route, EyeOff, Siren, Hexagon } from 'lucide-react'

export const CENTRO_GBA = { lat: -34.62, lng: -58.44 }
export const UMBRAL_CRUCE_KM = 0.6
export const UMBRAL_REPORTE_KM = 0.5
export const UMBRAL_ALERTA_KM = 0.25
// Alerta de proximidad a un reporte de "robo" reciente (no de zona insegura
// generica -- ver CATEGORIAS_ALERTA_PROXIMIDAD): distinta de UMBRAL_ALERTA_KM
// porque esa es contra zonas de riesgo historico, esta es contra un hecho
// puntual que alguien reporto hace poco. Un reporte de robo de hace 3 dias ya
// no sirve como alerta "esto esta pasando ahora", aunque siga vigente en el
// mapa (ver VIGENCIA_HORAS_POR_CATEGORIA) como advertencia historica de la zona.
export const RADIO_ALERTA_REPORTE_KM = 0.3
export const MINUTOS_ALERTA_REPORTE_RECIENTE = 45
export const CATEGORIAS_ALERTA_PROXIMIDAD = ['robo']
export const ORDEN_NIVELES = ['bajo', 'medio', 'alto', 'critico']
export const PESO_RIESGO = { bajo: 1, medio: 2, alto: 3, critico: 5 }

// El ajuste por franja horaria de /hotspots-inseguridad (antes, esta capa
// NO dependia de la hora, a diferencia de /hotspots y /corredores que ya
// usan 'hora' como feature del modelo) vive entero en el backend --
// FRANJA_PICO_INSEGURIDAD y _aplicar_ajuste_horario en backend/main.py,
// con la calibracion real contra franja_horaria del dataset de Delitos del
// GCBA documentada ahi. El frontend no necesita las franjas: cada hotspot
// que devuelve /hotspots-inseguridad ya viene con ajustado_por_horario y
// motivo_ajuste_horario (mismo patron que ajustado_por_reciente/
// motivo_ajuste para reportes de prensa), listo para mostrar sin
// recalcular nada de este lado.

// Debe reflejar exactamente VIGENCIA_HORAS_POR_CATEGORIA de backend/main.py: el
// front la usa solo para el efecto visual de "se va apagando con el tiempo" en el
// mapa (mas fresco = mas solido, cerca de vencer = mas transparente). El backend
// sigue siendo la unica fuente de verdad de cuando un reporte deja de mostrarse;
// si estos valores quedaran desincronizados, en el peor caso un reporte se ve mas
// o menos opaco de lo que deberia, nunca aparece uno ya vencido.
export const VIGENCIA_HORAS_POR_CATEGORIA = {
  corte: 12,
  robo: 48,           // hecho puntual: sirve de advertencia un par de dias, despues es ruido viejo
  inseguro: 24 * 7,
  pavimento: 24 * 30,
  iluminacion: 24 * 30,
}
export const VIGENCIA_HORAS_DEFAULT = 24 * 7
export const BBOX_GBA = '-59.5,-33.9,-57.8,-35.3'
// En desarrollo local, sin VITE_API_URL definida, usa una ruta relativa
// ('/api') que el dev server de Vite reescribe hacia el backend
// (ver server.proxy en vite.config.js). Esto hace que funcione igual desde
// localhost o desde el celular en la misma red: el navegador siempre le
// pega a su propio origen, nunca a un host hardcodeado. En un deploy real,
// se define VITE_API_URL como variable de entorno del hosting apuntando a
// la URL publica del backend -- Vite la inyecta en build time, no en
// runtime, asi que un cambio de esta variable requiere un rebuild del
// frontend.
export const API_URL = import.meta.env.VITE_API_URL || '/api'
export const CLAVE_NIVELES = 'motosafe_niveles_activos'
export const CLAVE_FAVORITOS = 'motosafe_favoritos'
export const CLAVE_TEMA = 'motosafe_tema'
export const CLAVE_ONBOARDING = 'motosafe_onboarding_visto'
export const CLAVE_CAPA_MAPA = 'motosafe_capa_mapa'
export const CLAVE_CAPA_INSEGURIDAD = 'motosafe_capa_inseguridad'
export const CLAVE_CAPA_TRAFICO = 'motosafe_capa_trafico'
// Prensa (noticias de robos scrapeadas, ver backend/scrapear_noticias_robos.py):
// prendida por default -- a diferencia de tráfico (costo de API) o inseguridad
// (overlay denso que puede saturar el mapa), esta capa son pocos puntos por
// corrida y es justamente el diferencial que se quiere mostrar de entrada.
export const CLAVE_CAPA_PRENSA = 'motosafe_capa_prensa'
// TomTom (como Google Maps y Waze) no pinta el color de congestion por calle
// a niveles de zoom muy alejados -- a esa escala seria ruido visual ilegible,
// asi que recien se ve algo util a partir de este zoom (nivel de barrio/calle).
export const UMBRAL_ZOOM_TRAFICO = 13
export const CLAVE_AUTOR_ID = 'motosafe_autor_id'
// Token privado por reporte: se recibe una única vez al crear el reporte y se
// usa para borrarlo. Nunca se manda en GET ni se confunde con autor_id.
export const CLAVE_TOKENS_REPORTES = 'motosafe_tokens_reportes'
// Última respuesta buena de cada capa de riesgo, para tener algo que mostrar
// si el celular se queda sin señal antes de que el backend responda (ver
// cargarHotspots/cargarCorredores/cargarInseguridad en App.jsx) -- en vez de
// una pantalla de "Conectando..." infinita cuando no hay con qué conectarse.
export const CLAVE_CACHE_HOTSPOTS = 'motosafe_cache_hotspots'
export const CLAVE_CACHE_CORREDORES = 'motosafe_cache_corredores'
export const CLAVE_CACHE_INSEGURIDAD_GENERAL = 'motosafe_cache_inseguridad_general'
export const CLAVE_CACHE_INSEGURIDAD_MOTO = 'motosafe_cache_inseguridad_moto'

export const NIVELES = {
  bajo:    { label: 'Bajo',    color: '#3DDC84' },
  medio:   { label: 'Medio',   color: '#FFD23F' },
  alto:    { label: 'Alto',    color: '#FF8C42' },
  critico: { label: 'Crítico', color: '#FF3B3B' },
}

// Paleta propia para la capa de inseguridad (delitos), deliberadamente distinta
// de NIVELES (verde/amarillo/naranja/rojo, que ya es "el color de siniestros" en
// toda la app): violeta -> magenta, mismo orden ordinal de severidad, para que
// se lea como otra fuente de datos de un vistazo y no se confunda con clusters
// o corredores cuando estan las dos capas prendidas a la vez.
export const NIVELES_INSEGURIDAD_COLOR = {
  bajo: '#D9A6FF',
  medio: '#B266FF',
  alto: '#9B30FF',
  critico: '#FF2E92',
}

export const CODIGOS_LLUVIA = [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99]

// "robo" e "inseguro" se separan porque son cosas distintas: robo es un hecho
// puntual (arrebato, robo en curso o recien pasado) con vigencia corta y que
// dispara la alerta de proximidad en vivo (ver CATEGORIAS_ALERTA_PROXIMIDAD);
// inseguro es una percepcion de zona (poca luz, sin gente, sensacion de
// inseguridad) que no es un evento puntual y no amerita esa alerta.
export const CATEGORIAS_REPORTE = [
  { id: 'robo', label: 'Robo o arrebato', Icon: Siren },
  { id: 'inseguro', label: 'Zona insegura', Icon: ShieldAlert },
  { id: 'pavimento', label: 'Pavimento en mal estado', Icon: Construction },
  { id: 'corte', label: 'Corte o desvío', Icon: TrafficCone },
  { id: 'iluminacion', label: 'Falta de iluminación', Icon: LightbulbOff },
]

// Panel unico de capas: reemplaza los dos botones que ciclaban estados (uno
// para vista de fondo, otro para inseguridad) por un panel con todas las
// opciones visibles de entrada, con label y descripcion en vez de solo un
// icono. Vive aca, no en el componente del panel, porque react-refresh exige
// que un archivo de componente solo exporte componentes.
//
// Vista de fondo: excluyente (una sola a la vez, por eso son radio buttons
// en el panel). Clusters es el default.
export const OPCIONES_CAPA_MAPA = [
  { id: 'apagado', label: 'Apagada', desc: 'No se dibuja en el mapa (la ruta y las alertas la siguen usando igual)', Icon: EyeOff },
  { id: 'hexagonos', label: 'Hexágonos de cobertura', desc: 'Celdas con borde nítido · se entiende la zona de un vistazo', Icon: Hexagon },
  { id: 'clusters', label: 'Clusters de siniestros', desc: 'Zonas puntuales · predicción del modelo en vivo', Icon: CircleDot },
  { id: 'heatmap', label: 'Mapa de calor', desc: 'Densidad de siniestros de moto', Icon: Flame },
  { id: 'corredores', label: 'Corredores de riesgo', desc: 'Avenidas completas con score de riesgo', Icon: Route },
]

// Inseguridad (delitos reales del GCBA -- robos, hurtos, lesiones -- no
// siniestros de moto): tambien excluyente entre si (general y moto se
// superponen bastante, mostrar las dos juntas solo duplica puntos sobre el
// mismo hecho), pero es un grupo aparte porque se apaga por default y es un
// overlay sobre la vista de fondo, no la reemplaza. Aclaramos "historico" en
// la descripcion porque, a diferencia de los siniestros, esto no se
// actualiza en vivo -- ver construir_indice_inseguridad.py.
export const OPCIONES_CAPA_INSEGURIDAD = [
  { id: 'apagado', label: 'Apagada', desc: 'No se dibuja en el mapa', Icon: ShieldOff },
  { id: 'general', label: 'Todo delito', desc: 'Histórico GCBA · se actualiza una vez al año', Icon: Shield },
  { id: 'moto', label: 'Robos con moto', desc: 'Histórico GCBA · se actualiza una vez al año', Icon: ShieldAlert },
]
