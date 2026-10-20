// Boton flotante "Reportar" + la hoja de categorias que se abre al tocarlo.
// A17 (BACKLOG): extraido de App.jsx (SES-131) -- bloque autocontenido con
// una interfaz de props chica. Corte-y-pegue con props, sin cambio de
// comportamiento.

import { X, TriangleAlert, MapPin } from 'lucide-react'
import { CATEGORIAS_REPORTE } from '../constants'

export function ReportSheet({
  paso, setPaso, setCampoActivo,
  panelRutaMontado, iniciarReporte,
  ubicacionReporte, confirmarReporte,
}) {
  return (
    <>
      <button className={`report-fab panel-enter ${paso !== 'idle' ? 'active' : ''} ${panelRutaMontado ? 'oculto-por-ruta' : ''}`} style={{ animationDelay: '0.3s' }} onClick={iniciarReporte} aria-label={paso === 'idle' ? 'Reportar' : undefined}>
        {paso === 'buscando' ? <span className="spinner" /> : paso === 'eligiendo' ? <X size={16} /> : <TriangleAlert size={16} />}
        <span>{paso === 'buscando' ? 'Ubicando...' : paso === 'eligiendo' ? 'Cancelar' : 'Reportar'}</span>
      </button>

      {paso === 'eligiendo' && (
        <div className="report-sheet hazard-edge">
          <div className="report-sheet-cabecera">
            <h3>¿Qué estás viendo en la vía?</h3>
            <button type="button" className="report-sheet-cerrar" aria-label="Cancelar reporte" onClick={() => { setPaso('idle'); setCampoActivo(null) }}><X size={16} /></button>
          </div>
          <div className={`report-options ${!ubicacionReporte ? 'deshabilitadas' : ''}`}>
            {CATEGORIAS_REPORTE.map((cat) => (
              <button key={cat.id} onClick={() => confirmarReporte(cat.id)}><cat.Icon size={15} /> {cat.label}</button>
            ))}
          </div>
          <p className="report-hint">
            <MapPin size={12} />
            {ubicacionReporte ? 'Ubicación por GPS -- tocá el mapa si no es exacta.' : 'Tocá el mapa para marcar dónde fue.'}
          </p>
        </div>
      )}
    </>
  )
}
