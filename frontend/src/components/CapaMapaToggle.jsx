// Botón de la topbar para alternar entre la vista de clusters (default, con
// detalle por zona y conexión al modelo) y el heatmap (vista panorámica de
// densidad). Mismo patrón que ThemeToggle: el estado vive en App.jsx, este
// componente solo dibuja el ícono correcto y dispara el cambio.

import { Flame, CircleDot } from 'lucide-react'

export function CapaMapaToggle({ capa, onCambiar }) {
  const esHeatmap = capa === 'heatmap'
  return (
    <button
      className="capa-toggle"
      onClick={onCambiar}
      aria-label={esHeatmap ? 'Cambiar a vista de zonas' : 'Cambiar a mapa de calor'}
      title={esHeatmap ? 'Vista de zonas' : 'Mapa de calor'}
    >
      {esHeatmap ? <CircleDot size={15} /> : <Flame size={15} />}
    </button>
  )
}
