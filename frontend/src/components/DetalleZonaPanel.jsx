// Panel de detalle de una zona del mapa (gravedad estimada, predicción del
// modelo, ajuste por reportes recientes). A17 (BACKLOG): extraído de
// App.jsx (SES-136) -- bloque autocontenido, corte-y-pegado con props,
// sin cambio de comportamiento.

import { useState } from 'react'
import { X, ArrowUp, ChevronDown, ChevronUp } from 'lucide-react'
import { NIVELES } from '../constants'
import { formatearPeriodo } from '../utils/tiempo'

// Colores para mostrar la probabilidad cruda del modelo (LEVE/GRAVE/MORTAL) en
// este panel -- mismos tonos semánticos que los niveles de riesgo (bajo=verde,
// alto=naranja, crítico=rojo), pero mapeados a las clases reales del modelo en
// vez de al nivel ya traducido.
const COLOR_CLASE_MODELO = { LEVE: '#3DDC84', GRAVE: '#FF8C42', MORTAL: '#FF3B3B' }

export function DetalleZonaPanel({ panelDetalle, zonaMostrada, setZonaSeleccionada, coberturaCapas }) {
  // V07 (SES-162): "fuente y método ampliables sin saturar" -- el desglose
  // del modelo (prediccionModelo) y la explicación del ajuste (prensa/subió
  // por) son el "cómo se calculó", no la conclusión en sí; antes se
  // mostraban siempre, sin importar si hacía falta. La conclusión (nivel +
  // motivo) y el aviso de ajuste reciente (real, no histórico) quedan
  // siempre visibles -- no es "método", es información vigente ahora mismo.
  const [detalleAbierto, setDetalleAbierto] = useState(false)
  if (!(panelDetalle.montado && zonaMostrada)) return null
  const periodo = formatearPeriodo(coberturaCapas?.hotspots?.desde, coberturaCapas?.hotspots?.hasta)
  const hayDetalleAmpliable = !!zonaMostrada.prediccionModelo || zonaMostrada.ajuste.subio
  return (
    <div className={`detalle-panel panel-enter hazard-edge ${panelDetalle.saliendo ? 'panel-exit' : ''}`}>
      <button className="detalle-cerrar" onClick={() => setZonaSeleccionada(null)} aria-label="Cerrar detalle de zona"><X size={14} /></button>
        <span className="popup-nivel" style={{ color: NIVELES[zonaMostrada.ajuste.nivel].color }}>
        Gravedad estimada: {NIVELES[zonaMostrada.ajuste.nivel].label}
      </span>
      {/* V07: "fecha" que pide el criterio de cierre -- el período real de
          los datos de siniestros que arman este nivel, mismo texto que ya
          usa LegendStack para la misma capa (hotspots). */}
      {periodo && <p className="detalle-periodo">Datos de siniestros: {periodo}</p>}
      <strong className="detalle-nombre">{zonaMostrada.nombre}</strong>
      <p className="detalle-motivo">{zonaMostrada.motivo}</p>
      {zonaMostrada.ajustadoPorReciente && (
        <p className="popup-ajuste"><ArrowUp size={12} /> Nivel subido: {zonaMostrada.motivoAjuste}</p>
      )}
      {hayDetalleAmpliable && (
        <button type="button" className="ruta-detalle-toggle" onClick={() => setDetalleAbierto((v) => !v)} aria-expanded={detalleAbierto}>
          {detalleAbierto ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          {detalleAbierto ? 'Ocultar fuente y método' : 'Ver fuente y método'}
        </button>
      )}
      {detalleAbierto && zonaMostrada.prediccionModelo && (
        <div className="detalle-modelo">
          <span className="detalle-modelo-titulo">Gravedad estimada si ocurre un siniestro</span>
          {Object.entries(zonaMostrada.prediccionModelo).map(([clase, prob]) => (
            <div className="detalle-modelo-fila" key={clase}>
              <span className="detalle-modelo-label">{clase}</span>
              <div className="detalle-modelo-track">
                <div className="detalle-modelo-fill" style={{ width: `${prob * 100}%`, background: COLOR_CLASE_MODELO[clase] || '#8A9099' }} />
              </div>
              <span className="detalle-modelo-num">{Math.round(prob * 100)}%</span>
            </div>
          ))}
          {zonaMostrada.contextoEstimado && (
            <p className="detalle-modelo-nota">Esta zona no tiene perfil histórico propio: se usó el perfil promedio de la ciudad.</p>
          )}
          <p className="detalle-modelo-nota">No estima la probabilidad de sufrir un siniestro durante tu viaje.</p>
        </div>
      )}
      {detalleAbierto && zonaMostrada.ajuste.subio && (
        <div className="detalle-ajuste">
          <span className="detalle-ajuste-base">Base: {NIVELES[zonaMostrada.nivel].label}</span>
          <span className="detalle-ajuste-flecha">→</span>
          <span className="detalle-ajuste-ahora" style={{ color: NIVELES[zonaMostrada.ajuste.nivel].color }}>
            Ahora: {NIVELES[zonaMostrada.ajuste.nivel].label}
          </span>
          <p className="detalle-ajuste-motivo">Subió por: {zonaMostrada.ajuste.motivos.join(' + ')}</p>
        </div>
      )}
    </div>
  )
}
