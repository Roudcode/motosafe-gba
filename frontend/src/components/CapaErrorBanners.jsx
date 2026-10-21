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

// V10 (SES-153): "sin datos" no es lo mismo que "fallo, reintentando". Las
// tres capas de arriba (corredores, hotspots-inseguridad general/moto) tienen
// un camino real en el backend para devolver 200 con una lista vacia --
// /corredores incluso lo comenta explicito ("if not resultado: return []").
// /hotspots queda afuera a proposito: hoy siempre trae las 740 filas reales,
// una lista vacia ahi seria un bug real, no un estado vacio legitimo. Este
// aviso es nada mas informativo: sin icono de alerta, sin boton de
// reintento (no tiene sentido reintentar algo que no fallo).
export function CapaErrorBanners({
  backendError, cargarHotspots,
  erroresCapas, ultimaConsultaCapas, setRecargaCapas,
  capaTrafico, traficoNoDisponible, setCapaTrafico,
  capasVacias = {},
}) {
  const capasSinDatos = Object.entries(capasVacias)
    .filter(([capa, vacia]) => vacia && !erroresCapas[capa])
    .map(([capa]) => NOMBRE_CAPA[capa] || capa)
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
      {!backendError && capasSinDatos.length > 0 && (
        <div className="ruta-banner panel-enter" role="status" aria-live="polite">
          Sin datos registrados todavía en esta zona: {capasSinDatos.join(', ')}. No es un fallo -- el mapa sigue funcionando con el resto de las capas.
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
