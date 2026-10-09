// Card de bienvenida, se muestra una sola vez (flag en localStorage) la primera
// vez que alguien abre la app, para dar contexto rápido de qué está mirando antes
// de tener que descubrirlo solo tocando botones.

import { useEffect, useRef } from 'react'
import { Bike, X } from 'lucide-react'

// Único overlay de pantalla completa de la app (ver SES-112): sin trampa de
// foco, Tab se escapaba del modal hacia controles tapados por el scrim (el
// botón de tema quedaba enfocado sin verse y Enter lo activaba a ciegas).
// Captura Tab/Shift+Tab para quedarse entre cerrar y "Entendido", Escape
// cierra igual que los botones, y el foco arranca en "Entendido" (acción
// principal) al montar.
export function Onboarding({ onCerrar }) {
  const cardRef = useRef(null)
  const entendidoRef = useRef(null)

  useEffect(() => {
    entendidoRef.current?.focus()
    const alKeyDown = (e) => {
      if (e.key === 'Escape') {
        onCerrar()
        return
      }
      if (e.key !== 'Tab') return
      const focables = cardRef.current.querySelectorAll('button')
      const primero = focables[0]
      const ultimo = focables[focables.length - 1]
      if (e.shiftKey && document.activeElement === primero) {
        e.preventDefault()
        ultimo.focus()
      } else if (!e.shiftKey && document.activeElement === ultimo) {
        e.preventDefault()
        primero.focus()
      }
    }
    document.addEventListener('keydown', alKeyDown)
    return () => document.removeEventListener('keydown', alKeyDown)
  }, [onCerrar])

  return (
    <div className="onboarding-scrim">
      <div className="onboarding-card panel-enter hazard-edge" ref={cardRef} role="dialog" aria-modal="true" aria-label="Así funciona MotoSafe">
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
        <button className="onboarding-entendido" onClick={onCerrar} ref={entendidoRef}>Entendido</button>
      </div>
    </div>
  )
}
