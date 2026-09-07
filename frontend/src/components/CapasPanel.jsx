// Panel único de capas del mapa: reemplaza los dos botones que ciclaban
// estados (vista de fondo / inseguridad) por un panel con todas las opciones
// visibles de entrada. Vista de fondo e inseguridad son dos grupos de radio
// separados (cada uno excluyente puertas adentro, pero independientes entre
// sí: podés tener corredores + inseguridad con moto al mismo tiempo).

import { X } from 'lucide-react'
import { OPCIONES_CAPA_MAPA, OPCIONES_CAPA_INSEGURIDAD } from '../constants'

export function CapasPanel({ capaMapa, onCambiarCapaMapa, capaInseguridad, onCambiarCapaInseguridad, onCerrar }) {
  return (
    <div className="capas-panel panel-enter hazard-edge">
      <div className="capas-panel-header">
        <span className="cercanas-title">Capas del mapa</span>
        <button className="detalle-cerrar" onClick={onCerrar} aria-label="Cerrar capas"><X size={14} /></button>
      </div>

      <span className="capas-grupo-titulo">Vista de fondo</span>
      {OPCIONES_CAPA_MAPA.map((op) => (
        <button
          key={op.id}
          className={`capas-opcion ${capaMapa === op.id ? 'activa' : ''}`}
          onClick={() => onCambiarCapaMapa(op.id)}
        >
          <span className="capas-opcion-radio" />
          <op.Icon size={15} className="capas-opcion-icono" />
          <span className="capas-opcion-texto">
            <span className="capas-opcion-label">{op.label}</span>
            <span className="capas-opcion-desc">{op.desc}</span>
          </span>
        </button>
      ))}

      <span className="capas-grupo-titulo">Inseguridad (delitos)</span>
      {OPCIONES_CAPA_INSEGURIDAD.map((op) => (
        <button
          key={op.id}
          className={`capas-opcion ${capaInseguridad === op.id ? 'activa' : ''}`}
          onClick={() => onCambiarCapaInseguridad(op.id)}
        >
          <span className="capas-opcion-radio" />
          <op.Icon size={15} className="capas-opcion-icono" />
          <span className="capas-opcion-texto">
            <span className="capas-opcion-label">{op.label}</span>
            <span className="capas-opcion-desc">{op.desc}</span>
          </span>
        </button>
      ))}

      <p className="capas-panel-nota">
        Tu ruta y las alertas en viaje ya tienen en cuenta la inseguridad esté o no prendida esta capa: esto solo cambia lo que ves dibujado en el mapa.
      </p>
    </div>
  )
}
