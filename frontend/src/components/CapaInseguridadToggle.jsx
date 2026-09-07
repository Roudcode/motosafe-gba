// Botón propio para la capa de inseguridad (delitos reales del GCBA), separado
// del selector de vista de siniestros de moto (CapaMapaToggle). Cicla
// apagado -> general -> con moto -> apagado. Cuando está prendido se marca
// visualmente distinto (clase "activa") para que se note de un vistazo que
// hay una capa extra sobre el mapa, no solo por el tooltip.

import { ShieldAlert } from 'lucide-react'
import { INFO_CAPA_INSEGURIDAD } from '../constants'

export function CapaInseguridadToggle({ capa, onCambiar }) {
  const info = INFO_CAPA_INSEGURIDAD[capa] || INFO_CAPA_INSEGURIDAD.apagado
  const activa = capa !== 'apagado'
  return (
    <button
      className={`capa-toggle capa-inseguridad-toggle ${activa ? 'activa' : ''}`}
      onClick={onCambiar}
      aria-label={info.siguienteLabel}
      title={info.siguienteLabel}
    >
      <ShieldAlert size={15} />
    </button>
  )
}
