// Panel chico de "Actividad reciente": el historial de TUS reportes (no el
// feed de toda la ciudad, eso es ActividadPortal). A17 (BACKLOG): extraído
// de App.jsx -- corte-y-pegado con props, sin cambio de comportamiento.
//
// F08: mientras el historial no cargó (o si falló), se ve lo vigente --
// que ya se tenía antes, sin esperar a la red -- para no mostrar el panel
// vacío. Una vez que historialReportes trae algo, manda eso: incluye
// además lo vencido y lo retirado por consenso, que misReportes nunca
// tiene porque sale de GET /reportes (solo vigente, a propósito).

import { X } from 'lucide-react'
import { CATEGORIAS_REPORTE } from '../constants'
import { formatearAntiguedad } from '../utils/tiempo'

export function ActividadReciente({
  panelActividad, setActividadAbierta,
  cargandoHistorial, errorHistorial, historialReportes, misReportes,
  horaActual, setVuelo, borrarReportes,
}) {
  const items = historialReportes.length > 0
    ? historialReportes
    : misReportes.map((r) => ({ id: r.id, lat: r.lat, lng: r.lng, categoria: r.categoria, creadoEn: r.creadoEn, estado: 'vigente' }))

  return (
    <div className={`actividad-panel panel-enter hazard-edge ${panelActividad.saliendo ? 'panel-exit' : ''}`}>
      <div className="actividad-header">
        <span className="cercanas-title">Actividad reciente</span>
        <button className="detalle-cerrar" onClick={() => setActividadAbierta(false)} aria-label="Cerrar panel de actividad"><X size={14} /></button>
      </div>
      {cargandoHistorial && historialReportes.length === 0 && <p className="actividad-estado-carga">Cargando historial…</p>}
      {errorHistorial && <p className="actividad-estado-carga">No se pudo cargar el historial completo; se muestra lo vigente.</p>}
      {items.map((rep) => {
        const cat = CATEGORIAS_REPORTE.find((c) => c.id === rep.categoria)
        const textoEstado = rep.estado === 'vencido' ? `Venció · ${formatearAntiguedad(rep.creadoEn, horaActual)}`
          : rep.estado === 'desmentido' ? `Retirado por la comunidad · ${formatearAntiguedad(rep.creadoEn, horaActual)}`
          : `Vigente · ${formatearAntiguedad(rep.creadoEn, horaActual)}`
        return (
          <button
            key={rep.id}
            className={`actividad-item ${rep.estado !== 'vigente' ? 'actividad-item-historico' : ''}`}
            onClick={() => { setVuelo({ lat: rep.lat, lng: rep.lng, zoom: 16 }); setActividadAbierta(false) }}
          >
            <span className="actividad-icon">{cat?.Icon && <cat.Icon size={15} />}</span>
            <span className="actividad-texto">
              <span className="actividad-label">{cat?.label}</span>
              <span className="actividad-hora">{textoEstado}</span>
            </span>
          </button>
        )
      })}
      {misReportes.length > 0 && <button className="actividad-borrar" onClick={borrarReportes}>Borrar mis reportes</button>}
    </div>
  )
}
