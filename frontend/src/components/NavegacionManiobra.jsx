// Tarjeta de "doblá acá" durante la navegación activa (próximo giro + preview
// del siguiente). A17 (BACKLOG): extraído de App.jsx (SES-136) -- bloque
// autocontenido, corte-y-pegado con props, sin cambio de comportamiento.

import { CornerDownRight } from 'lucide-react'

export function NavegacionManiobra({
  modoViaje, rutasCalculadas, rutaSeleccionada, pasoActual,
  miUbicacion, distanciaManiobraKm, formatearDistancia, textoManiobra, iconoManiobra,
}) {
  if (!(modoViaje && rutasCalculadas.length > 0 && rutasCalculadas[rutaSeleccionada]?.pasos?.[pasoActual])) {
    return null
  }
  const pasos = rutasCalculadas[rutaSeleccionada].pasos
  const pasoActivo = pasos[pasoActual]
  const pasoSiguiente = pasos[pasoActual + 1]
  const maniobra = { Icon: iconoManiobra(pasoActivo) }
  return (
    <div className="navegacion-panel panel-enter">
      <span className="navegacion-icono-chip"><maniobra.Icon size={26} /></span>
      <div className="navegacion-texto">
        {miUbicacion && (
          <span className="navegacion-distancia">
            {formatearDistancia(distanciaManiobraKm(pasoActivo))}
          </span>
        )}
        <strong>{textoManiobra(pasoActivo)}</strong>
        {/* Preview del giro siguiente, más chico -- ayuda en cruces
            seguidos a no quedar "ciego" un paso adelante, que era el
            caso hasta ahora (solo se veía el giro inmediato). Separado
            del resto con su propio borde superior en vez de solo ser
            texto más chico, para que se lea como un dato secundario y
            no como continuación del mismo mensaje. */}
        {pasoSiguiente && (
          <div className="navegacion-luego">
            <span className="navegacion-luego-etiqueta">Luego</span>
            <CornerDownRight size={13} />
            <span className="navegacion-luego-texto">{textoManiobra(pasoSiguiente)}</span>
          </div>
        )}
      </div>
    </div>
  )
}
