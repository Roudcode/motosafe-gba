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
export const CLAVE_REPORTES = 'motosafe_reportes'
export const CLAVE_NIVELES = 'motosafe_niveles_activos'
export const CLAVE_FAVORITOS = 'motosafe_favoritos'
export const CLAVE_TEMA = 'motosafe_tema'
export const CLAVE_ONBOARDING = 'motosafe_onboarding_visto'

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
