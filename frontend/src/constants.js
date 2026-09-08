// Constantes de la app: umbrales de distancia, claves de localStorage,
// definiciones de niveles de riesgo y catálogos fijos (categorías de reporte).
// Se separan de App.jsx para que estén en un solo lugar y no mezcladas con lógica de UI.

import { Construction, TrafficCone, LightbulbOff, ShieldAlert, ShieldOff, Shield, CircleDot, Flame, Route, Zap, EyeOff } from 'lucide-react'

export const CENTRO_GBA = { lat: -34.62, lng: -58.44 }
export const UMBRAL_CRUCE_KM = 0.6
export const UMBRAL_REPORTE_KM = 0.5
export const UMBRAL_ALERTA_KM = 0.25
export const ORDEN_NIVELES = ['bajo', 'medio', 'alto', 'critico']
export const PESO_RIESGO = { bajo: 1, medio: 2, alto: 3, critico: 5 }

// Franja horaria de mayor riesgo de inseguridad, calibrada con el dato REAL
// de franja_horaria del dataset de Delitos del GCBA (columna que existia
// pero se perdia en la carga por un alias incompleto en fetch_delitos_caba.py,
// corregido). Se probo primero una heuristica generica de "horario nocturno"
// (22-6hs, criterio criminologico sin verificar contra el dato) y la
// distribucion real la contradijo: robos con moto tiene su pico real entre
// las 19 y las 23hs (20-21hs llegan a 7.3-7.5% de los casos, contra un 4.2%
// esperado si la distribucion fuera pareja en 24hs), mientras que 0-6hs es
// en realidad el tramo de MENOR incidencia (1.4-2.5%), lo opuesto a lo que
// asumia la heuristica anterior. No se aplica a siniestros de moto porque
// esa capa ya recibe hora real como feature del modelo entrenado (ver
// backend/main.py, predecir_para_fila).
export const FRANJA_PICO_INSEGURIDAD = { desde: 19, hasta: 24 }

// Debe reflejar exactamente VIGENCIA_HORAS_POR_CATEGORIA de backend/main.py: el
// front la usa solo para el efecto visual de "se va apagando con el tiempo" en el
// mapa (mas fresco = mas solido, cerca de vencer = mas transparente). El backend
// sigue siendo la unica fuente de verdad de cuando un reporte deja de mostrarse;
// si estos valores quedaran desincronizados, en el peor caso un reporte se ve mas
// o menos opaco de lo que deberia, nunca aparece uno ya vencido.
export const VIGENCIA_HORAS_POR_CATEGORIA = {
  corte: 12,
  inseguro: 24 * 7,
  pavimento: 24 * 30,
  iluminacion: 24 * 30,
}
export const VIGENCIA_HORAS_DEFAULT = 24 * 7
export const BBOX_GBA = '-59.5,-33.9,-57.8,-35.3'
// En desarrollo local, sin VITE_API_URL definida, apunta a localhost:8000
// (el backend corriendo en tu maquina). En un deploy real, se define
// VITE_API_URL como variable de entorno del hosting apuntando a la URL
// publica del backend -- Vite la inyecta en build time, no en runtime, asi
// que un cambio de esta variable requiere un rebuild del frontend.
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
export const CLAVE_NIVELES = 'motosafe_niveles_activos'
export const CLAVE_FAVORITOS = 'motosafe_favoritos'
export const CLAVE_TEMA = 'motosafe_tema'
export const CLAVE_ONBOARDING = 'motosafe_onboarding_visto'
export const CLAVE_CAPA_MAPA = 'motosafe_capa_mapa'
export const CLAVE_CAPA_INSEGURIDAD = 'motosafe_capa_inseguridad'
export const CLAVE_CAPA_TRAFICO = 'motosafe_capa_trafico'
// TomTom (como Google Maps y Waze) no pinta el color de congestion por calle
// a niveles de zoom muy alejados -- a esa escala seria ruido visual ilegible,
// asi que recien se ve algo util a partir de este zoom (nivel de barrio/calle).
export const UMBRAL_ZOOM_TRAFICO = 13
export const CLAVE_AUTOR_ID = 'motosafe_autor_id'

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

export const CATEGORIAS_REPORTE = [
  { id: 'pavimento', label: 'Pavimento en mal estado', Icon: Construction },
  { id: 'corte', label: 'Corte o desvío', Icon: TrafficCone },
  { id: 'iluminacion', label: 'Falta de iluminación', Icon: LightbulbOff },
  { id: 'inseguro', label: 'Zona insegura', Icon: ShieldAlert },
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
