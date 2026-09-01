// Card de bienvenida, se muestra una sola vez (flag en localStorage) la primera
// vez que alguien abre la app, para dar contexto rápido de qué está mirando antes
// de tener que descubrirlo solo tocando botones.

import { Bike, X } from 'lucide-react'

export function Onboarding({ onCerrar }) {
  return (
    <div className="onboarding-scrim">
      <div className="onboarding-card panel-enter hazard-edge">
        <button className="detalle-cerrar onboarding-cerrar" onClick={onCerrar} aria-label="Cerrar bienvenida">
          <X size={14} />
        </button>
        <Bike size={28} strokeWidth={1.6} />
        <h2>Así funciona MotoSafe</h2>
        <p>
          Cada punto del mapa es una zona con historial real de siniestros de motociclistas en CABA.
          El color no es fijo: se recalcula ahora mismo con un modelo de Machine Learning entrenado
          con 23.343 casos reales, según la hora y el perfil histórico de cada zona.
        </p>
        <button className="onboarding-entendido" onClick={onCerrar}>Entendido</button>
      </div>
    </div>
  )
}
