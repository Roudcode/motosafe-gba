// Pantalla de carga con marca, mostrada mientras el backend calcula las 740
// predicciones en vivo (la primera vez que se abre la app, o al reconectar).
// Reemplaza el mapa vacío con solo un texto chico en la topbar: ahora hay un
// momento de marca explícito en vez de un vacío mientras carga.

import { Bike } from 'lucide-react'

export function LoadingScreen({ visible }) {
  return (
    <div className={`loading-screen ${visible ? '' : 'oculta'}`} aria-hidden={!visible}>
      <div className="loading-screen-marca">
        <Bike size={40} strokeWidth={1.6} className="loading-screen-icono" />
        <span className="loading-screen-nombre">MotoSafe <em>GBA</em></span>
      </div>
      <p className="loading-screen-texto">Calculando riesgo en vivo para 740 zonas de CABA...</p>
      <div className="loading-screen-barra"><div className="loading-screen-barra-fill" /></div>
    </div>
  )
}
