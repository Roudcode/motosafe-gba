// Botón de la topbar para alternar entre las tres vistas del mapa: clusters
// (default, con detalle por zona y conexión al modelo), heatmap (vista
// panorámica de densidad) y corredores (calles completas con muchos
// siniestros, en vez de zonas puntuales). Mismo patrón que ThemeToggle: el
// estado vive en App.jsx, este componente solo dibuja el ícono correcto y
// dispara el cambio.

import { Flame, CircleDot, Route } from 'lucide-react'
import { INFO_CAPA_MAPA } from '../constants'

export function CapaMapaToggle({ capa, onCambiar }) {
  const ICONOS = { clusters: CircleDot, heatmap: Flame, corredores: Route }
  const info = INFO_CAPA_MAPA[capa] || INFO_CAPA_MAPA.clusters
  const Icon = ICONOS[capa] || CircleDot
  return (
    <button
      className="capa-toggle"
      onClick={onCambiar}
      aria-label={info.siguienteLabel}
      title={info.siguienteLabel}
    >
      <Icon size={15} />
    </button>
  )
}
