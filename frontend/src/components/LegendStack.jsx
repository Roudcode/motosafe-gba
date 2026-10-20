// Leyenda de nivel de riesgo (siniestros) + leyenda de inseguridad (si esa
// capa está activa), con filtro por nivel y por tipo de hexágono. A17
// (BACKLOG): extraído de App.jsx (SES-136) -- bloque autocontenido,
// corte-y-pegado con props, sin cambio de comportamiento.

import {
  NIVELES, OPCIONES_FILTRO_HEXAGONO, OPCIONES_CAPA_INSEGURIDAD, NIVELES_INSEGURIDAD_COLOR,
} from '../constants'
import { formatearPeriodo } from '../utils/tiempo'

// Línea de cobertura bajo el título de una leyenda: el período de los datos es
// lo principal (con eso se juzga la vigencia del riesgo); la fecha en que se
// generó el archivo de la capa va solo en el tooltip.
function TextoCobertura({ meta, prefijo }) {
  const periodo = formatearPeriodo(meta?.desde, meta?.hasta)
  if (!periodo) return null
  const detalle = `${meta.descripcion}: ${meta.desde} a ${meta.hasta} (${meta.registros.toLocaleString('es-AR')} registros). ${meta.fuente}.`
    + (meta.archivo_generado ? ` Archivo de la capa generado el ${meta.archivo_generado}.` : '')
  return (
    <p className="legend-cobertura" title={detalle}>
      {prefijo} {periodo} · GCBA
    </p>
  )
}

export function LegendStack({
  vistaNavegacion, panelRutaMontado, capaMapa, filtroHexagono, setFiltroHexagono,
  coberturaCapas, nivelesActivos, toggleNivel, conteos, hayFiltrosApagados, restablecerFiltros,
  capaInseguridad, conteosInseguridad,
}) {
  // La leyenda se esconde mientras está abierto "Opciones de ruta": ahí
  // el riesgo ya se lee en cada tarjeta de ruta (bajo/medio/alto/
  // crítico) y en las burbujas de hotspot del mapa, así que la leyenda
  // + filtro por nivel no suma nada en ese momento y sí compite por el
  // mismo espacio de pantalla en celular (a pedido de Rodo: que
  // "Opciones de ruta" pueda usar ese lugar en vez de compartirlo).
  if (vistaNavegacion || panelRutaMontado) return null
  return (
    <div className="legend-stack">
      <div className="legend panel-enter hazard-edge" style={{ animationDelay: '0.2s' }}>
        <div className="legend-header">
          <span className="legend-title">Nivel de riesgo <em>(tocá para filtrar)</em></span>
          {hayFiltrosApagados && <button className="legend-reset" onClick={restablecerFiltros}>Restablecer</button>}
        </div>
        {capaMapa === 'hexagonos' && (
          <div className="portal-actividad-filtros-fila legend-filtro-hexagono">
            {OPCIONES_FILTRO_HEXAGONO.map((f) => (
              <button key={f.id} className={filtroHexagono === f.id ? 'activo' : ''} onClick={() => setFiltroHexagono(f.id)}>{f.label}</button>
            ))}
          </div>
        )}
        <TextoCobertura meta={coberturaCapas?.[capaMapa === 'corredores' ? 'corredores' : 'hotspots']} prefijo="Siniestros" />
        {Object.entries(NIVELES).map(([key, val]) => (
          <button key={key} className={`legend-item ${nivelesActivos.has(key) ? '' : 'inactive'}`} onClick={() => toggleNivel(key)}>
            <span className="legend-swatch" style={{ background: val.color }} />
            {val.label}
            <span className="legend-count">{conteos[key]}</span>
          </button>
        ))}
      </div>

      {capaInseguridad !== 'apagado' && (
        <div className="legend legend-inseguridad panel-enter hazard-edge" style={{ animationDelay: '0.22s' }}>
          <div className="legend-header">
            <span className="legend-title">{OPCIONES_CAPA_INSEGURIDAD.find((o) => o.id === capaInseguridad)?.label} <em>(datos GCBA)</em></span>
          </div>
          <TextoCobertura meta={coberturaCapas?.[`inseguridad_${capaInseguridad}`]} prefijo="Delitos" />
          {Object.entries(NIVELES).map(([key, val]) => (
            <button key={key} className={`legend-item ${nivelesActivos.has(key) ? '' : 'inactive'}`} onClick={() => toggleNivel(key)}>
              <span className="legend-swatch" style={{ background: NIVELES_INSEGURIDAD_COLOR[key] }} />
              {val.label}
              <span className="legend-count">{conteosInseguridad[key]}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
