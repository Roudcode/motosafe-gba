// Constantes de la app: umbrales de distancia, claves de localStorage,
// definiciones de niveles de riesgo y catálogos fijos (categorías de reporte).
// Se separan de App.jsx para que estén en un solo lugar y no mezcladas con lógica de UI.

import { Construction, TrafficCone, LightbulbOff, ShieldAlert } from 'lucide-react'

export const CENTRO_GBA = { lat: -34.62, lng: -58.44 }
export const UMBRAL_CRUCE_KM = 0.6
export const UMBRAL_REPORTE_KM = 0.5
export const UMBRAL_ALERTA_KM = 0.25
export const ORDEN_NIVELES = ['bajo', 'medio', 'alto', 'critico']
export const PESO_RIESGO = { bajo: 1, medio: 2, alto: 3, critico: 5 }
export const BBOX_GBA = '-59.5,-33.9,-57.8,-35.3'
export const API_URL = 'http://localhost:8000'
export const CLAVE_NIVELES = 'motosafe_niveles_activos'
export const CLAVE_FAVORITOS = 'motosafe_favoritos'
export const CLAVE_TEMA = 'motosafe_tema'
export const CLAVE_ONBOARDING = 'motosafe_onboarding_visto'
export const CLAVE_CAPA_MAPA = 'motosafe_capa_mapa'
export const CLAVE_AUTOR_ID = 'motosafe_autor_id'

export const NIVELES = {
  bajo:    { label: 'Bajo',    color: '#3DDC84' },
  medio:   { label: 'Medio',   color: '#FFD23F' },
  alto:    { label: 'Alto',    color: '#FF8C42' },
  critico: { label: 'Crítico', color: '#FF3B3B' },
}

export const CODIGOS_LLUVIA = [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99]

export const CATEGORIAS_REPORTE = [
  { id: 'pavimento', label: 'Pavimento en mal estado', Icon: Construction },
  { id: 'corte', label: 'Corte o desvío', Icon: TrafficCone },
  { id: 'iluminacion', label: 'Falta de iluminación', Icon: LightbulbOff },
  { id: 'inseguro', label: 'Zona insegura', Icon: ShieldAlert },
]

// Ciclo de vistas del mapa: clusters (zonas puntuales, default) -> heatmap
// (densidad) -> corredores (calles completas). Vive acá, no en el componente
// del botón, porque react-refresh exige que un archivo de componente solo
// exporte componentes.
export const ORDEN_CAPAS_MAPA = ['clusters', 'heatmap', 'corredores', 'inseguridad_general', 'inseguridad_moto']
export const INFO_CAPA_MAPA = {
  clusters: { siguienteLabel: 'Cambiar a mapa de calor' },
  heatmap: { siguienteLabel: 'Cambiar a corredores de riesgo' },
  corredores: { siguienteLabel: 'Cambiar a inseguridad (robos, hurtos)' },
  inseguridad_general: { siguienteLabel: 'Cambiar a inseguridad con moto' },
  inseguridad_moto: { siguienteLabel: 'Cambiar a vista de zonas' },
}

// Etiquetas y color base de cada capa, para el indicador de capa activa y las
// leyendas. Las dos de inseguridad usan datos reales de delitos del GCBA
// (no siniestros de moto), por eso tienen su propio label explicativo.
export const ETIQUETA_CAPA_MAPA = {
  clusters: 'Zonas de riesgo (siniestros de moto)',
  heatmap: 'Mapa de calor (siniestros de moto)',
  corredores: 'Corredores de riesgo (siniestros de moto)',
  inseguridad_general: 'Inseguridad (robos, hurtos, lesiones)',
  inseguridad_moto: 'Inseguridad con moto (robos)',
}

export function siguienteCapaMapa(capa) {
  const idx = ORDEN_CAPAS_MAPA.indexOf(capa)
  return ORDEN_CAPAS_MAPA[(idx + 1) % ORDEN_CAPAS_MAPA.length]
}
