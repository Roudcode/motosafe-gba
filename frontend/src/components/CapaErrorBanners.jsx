// Banners de error de capas: backend caído, capas que no se actualizaron
// (corredores/inseguridad) y tráfico en vivo no disponible. A17 (BACKLOG):
// extraído de App.jsx -- tres bloques adyacentes, corte-y-pegado con props,
// sin cambio de comportamiento.
//
// SES-112: con el backend caído, activar tráfico quedaba sin ningún aviso
// -- las fichas de calle (tiles PNG de TomTom vía backend) fallan en
// silencio, MapLibre no dispara un error que el usuario vea, y el panel de
// capas seguía marcando la opción como activa. El toast de App.jsx solo
// avisaba en un SEGUNDO intento de activarla (si traficoNoDisponible ya
// era true). El banner de tráfico cubre el primer intento, con la misma
// fuente/reintento que el resto de las capas.

import { WifiOff } from 'lucide-react'

const NOMBRE_CAPA = { corredores: 'corredores', inseguridadGeneral: 'inseguridad general', inseguridadMoto: 'inseguridad con moto' }

export function CapaErrorBanners({
  backendError, cargarHotspots,
  erroresCapas, ultimaConsultaCapas, setRecargaCapas,
  capaTrafico, traficoNoDisponible, setCapaTrafico,
}) {
  return (
    <>
      {backendError && (
        <div className="ruta-banner ruta-banner-error panel-enter backend-banner" role="alert">
          <WifiOff size={14} /> Sin conexión con el backend. Reintentando cada 5s.
          <button onClick={cargarHotspots}>Reintentar ahora</button>
        </div>
      )}
      {!backendError && Object.values(erroresCapas).some(Boolean) && (
        <div className="ruta-banner ruta-banner-error panel-enter backend-banner" role="status" aria-live="polite">
          <WifiOff size={14} /> No se actualizaron: {Object.entries(erroresCapas).filter(([, fallo]) => fallo).map(([capa]) => NOMBRE_CAPA[capa] || capa).join(', ')}. Se mantiene la última información disponible.
          {ultimaConsultaCapas && <span className="backend-banner-fecha">Última consulta: {ultimaConsultaCapas}</span>}
          <button onClick={() => setRecargaCapas((v) => v + 1)}>Reintentar capas</button>
        </div>
      )}
      {!backendError && capaTrafico && traficoNoDisponible && (
        <div className="ruta-banner ruta-banner-error panel-enter backend-banner" role="status" aria-live="polite">
          <WifiOff size={14} /> Tráfico en vivo (TomTom) no disponible ahora. Se mantiene el mapa sin esa capa.
          <button onClick={() => { setCapaTrafico(false); setTimeout(() => setCapaTrafico(true), 50) }}>Reintentar tráfico</button>
        </div>
      )}
    </>
  )
}
