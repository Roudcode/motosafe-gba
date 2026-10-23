// Portal de "Actividad": prensa + reportes de usuarios combinados en un solo
// feed, estilo noticias, con filtros de categoría/fecha/barrio. Pedido
// explícito de Rodo -- no reemplaza el panel chico de "Actividad reciente"
// (ese es solo el historial de TUS reportes, con su propio criterio de
// vigencia/estado); esto es la ciudad entera.
//
// El filtro de barrio usa geocodificación inversa real (TomTom, vía
// utils/barrio.js -> backend /lugares/reversa) -- la primera versión de
// esta pantalla filtraba contra el cluster de ZONAS_RIESGO más cercano
// ("Zona 106"), que no significa nada para quien no conoce el modelo. Ver
// backend/main.py para por qué esto usa TomTom y no Nominatim (DEC-011).
// El lector de notas vive en App.jsx (onAbrirLector), no acá: también se
// abre desde los marcadores de prensa del mapa, no solo desde este portal.
import { useEffect, useMemo, useRef, useState } from 'react'
import { X, Newspaper, Siren, ShieldAlert, Construction, TrafficCone, LightbulbOff, CarFront, Bike, MapPin, ThumbsUp, ThumbsDown, BookOpen } from 'lucide-react'
import { CATEGORIAS_REPORTE } from '../constants'
import { resolverBarrio } from '../utils/barrio'
import { formatearAntiguedad } from '../utils/tiempo'

const ICONOS_CATEGORIA = {
  robo: Siren,
  choque: CarFront,
  moto: Bike,
  inseguro: ShieldAlert,
  pavimento: Construction,
  corte: TrafficCone,
  iluminacion: LightbulbOff,
}

// Un color por categoría (de la misma paleta de riesgo que ya usa el resto
// de la app, no colores nuevos) -- antes todos los ítems tenían el mismo
// ícono gris plano sin ninguna jerarquía visual entre una urgencia y un
// aviso menor.
const COLOR_CATEGORIA = {
  robo: 'rojo',
  choque: 'naranja',
  moto: 'azul',
  inseguro: 'magenta',
  pavimento: 'amarillo',
  corte: 'amarillo',
  iluminacion: 'gris',
}

// Etiquetas cortas a mano, no la primera palabra de CATEGORIAS_REPORTE.label:
// "Zona insegura" truncada a "Zona" se confundía con el selector de barrio
// que va debajo (dos cosas distintas con la misma palabra).
const ETIQUETA_CORTA_REPORTE = { inseguro: 'Inseguridad', pavimento: 'Pavimento', corte: 'Cortes', iluminacion: 'Iluminación' }
const FILTROS_CATEGORIA = [
  { id: 'todas', label: 'Todas' },
  { id: 'moto', label: 'Motos' },
  { id: 'robo', label: 'Robos' },
  { id: 'choque', label: 'Choques' },
  ...CATEGORIAS_REPORTE.filter((c) => c.id !== 'robo').map((c) => ({ id: c.id, label: ETIQUETA_CORTA_REPORTE[c.id] || c.label })),
]

const FILTROS_FECHA = [
  { id: '24h', label: 'Últimas 24 h', horas: 24 },
  { id: '7d', label: 'Últimos 7 días', horas: 24 * 7 },
  { id: '30d', label: 'Últimos 30 días', horas: 24 * 30 },
  { id: 'todo', label: 'Todo', horas: Infinity },
]

function claveBarrio(lat, lng) {
  return `${lat.toFixed(3)},${lng.toFixed(3)}`
}

export function ActividadPortal({ reportesPrensa, reportes, horaActual, onCerrar, onVerEnMapa, onAbrirLector, saliendo }) {
  const [filtroCategoria, setFiltroCategoria] = useState('todas')
  const [filtroFecha, setFiltroFecha] = useState('7d')
  const [filtroBarrio, setFiltroBarrio] = useState('todas')
  // barrio resuelto por clave "lat,lng" (redondeada) -- undefined = todavía
  // no se pidió, null = se pidió y TomTom no devolvió nada, string = listo.
  const [barrios, setBarrios] = useState({})
  const barriosPedidosRef = useRef(new Set())

  const items = useMemo(() => {
    const dePrensa = reportesPrensa.map((r) => {
      const categoria = r.tipoIncidente === 'choque'
        ? 'choque'
        : (r.relacionadoMoto || /\bmoto(?:s|cicleta|cicletas)?\b/i.test(r.titular || ''))
          ? 'moto'
          : 'robo'
      return {
        id: `prensa-${r.id}`, tipo: 'prensa', categoria,
        titulo: r.titular, fecha: r.fechaReferencia,
        lat: r.lat, lng: r.lng,
        fuente: r.fuente, url: r.urlFuente,
      }
    })
    const deReportes = reportes.map((r) => ({
      id: `reporte-${r.id}`, tipo: 'reporte', categoria: r.categoria,
      titulo: CATEGORIAS_REPORTE.find((c) => c.id === r.categoria)?.label || r.categoria,
      fecha: r.creadoEn, lat: r.lat, lng: r.lng,
      confirmaciones: r.confirmaciones, desmentidas: r.desmentidas,
    }))
    return [...dePrensa, ...deReportes].sort((a, b) => new Date(b.fecha) - new Date(a.fecha))
  }, [reportesPrensa, reportes])

  // Items según categoría/fecha, SIN aplicar todavía el filtro de barrio --
  // es a partir de este conjunto (no de `items` entero) que se resuelve el
  // barrio real contra TomTom: acotado a lo que de verdad se está mirando
  // con los filtros actuales, no el feed completo de una sola vez.
  const itemsParaBarrio = useMemo(() => {
    const horasMax = FILTROS_FECHA.find((f) => f.id === filtroFecha)?.horas ?? Infinity
    return items.filter((item) => {
      if (filtroCategoria !== 'todas' && item.categoria !== filtroCategoria) return false
      if (horasMax !== Infinity) {
        const edadHoras = (horaActual - new Date(item.fecha).getTime()) / 3600000
        if (edadHoras > horasMax) return false
      }
      return true
    })
  }, [items, filtroCategoria, filtroFecha, horaActual])

  useEffect(() => {
    // Sin bandera de "desmontado": el dedupe real es barriosPedidosRef (un
    // ref sobrevive al doble montaje de StrictMode en desarrollo). Una
    // bandera local acá adentro quedaba en `false` por el cleanup del
    // primer montaje (StrictMode) antes de que el pedido de red llegara a
    // responder, así que CADA respuesta real terminaba descartada -- el
    // selector de barrio nunca se llenaba. setBarrios después de un
    // desmonte real de verdad es inofensivo (React 18 lo ignora solo).
    for (const item of itemsParaBarrio) {
      const clave = claveBarrio(item.lat, item.lng)
      if (barriosPedidosRef.current.has(clave)) continue
      barriosPedidosRef.current.add(clave)
      resolverBarrio(item.lat, item.lng, (barrio) => {
        setBarrios((prev) => ({ ...prev, [clave]: barrio }))
      })
    }
  }, [itemsParaBarrio])

  const itemsFiltrados = useMemo(() => {
    return itemsParaBarrio.filter((item) => {
      if (filtroBarrio === 'todas') return true
      return barrios[claveBarrio(item.lat, item.lng)] === filtroBarrio
    })
  }, [itemsParaBarrio, filtroBarrio, barrios])

  const barriosConActividad = useMemo(() => {
    const vistos = new Set()
    for (const item of itemsParaBarrio) {
      const barrio = barrios[claveBarrio(item.lat, item.lng)]
      if (barrio) vistos.add(barrio)
    }
    return [...vistos].sort((a, b) => a.localeCompare(b))
  }, [itemsParaBarrio, barrios])

  return (
    <div className={`portal-actividad panel-enter ${saliendo ? 'panel-exit' : ''}`} role="dialog" aria-label="Actividad">
      <div className="portal-actividad-header">
        <span className="portal-actividad-titulo"><Newspaper size={18} /> Actividad</span>
        {/* Pedido de usuario (prueba real): lo que filtrás acá adentro, al
            cerrar, se refleja en el filtro de prensa del mapa -- antes eran
            dos filtros sueltos sin relación entre sí. */}
        <button className="detalle-cerrar" onClick={() => onCerrar(filtroCategoria)} aria-label="Cerrar actividad"><X size={16} /></button>
      </div>

      <div className="portal-actividad-filtros">
        <div className="portal-actividad-filtros-fila">
          {FILTROS_FECHA.map((f) => (
            <button key={f.id} className={filtroFecha === f.id ? 'activo' : ''} onClick={() => setFiltroFecha(f.id)}>{f.label}</button>
          ))}
        </div>
        <div className="portal-actividad-filtros-fila">
          {FILTROS_CATEGORIA.map((f) => (
            <button key={f.id} className={filtroCategoria === f.id ? 'activo' : ''} onClick={() => setFiltroCategoria(f.id)}>{f.label}</button>
          ))}
        </div>
        {barriosConActividad.length > 0 && (
          <select
            className="portal-actividad-select-zona"
            value={filtroBarrio}
            onChange={(e) => setFiltroBarrio(e.target.value)}
            aria-label="Filtrar por barrio"
          >
            <option value="todas">Todos los barrios</option>
            {barriosConActividad.map((nombre) => <option key={nombre} value={nombre}>{nombre}</option>)}
          </select>
        )}
      </div>

      <div className="portal-actividad-contador">{itemsFiltrados.length} resultado{itemsFiltrados.length === 1 ? '' : 's'}</div>

      <div className="portal-actividad-lista">
        {itemsFiltrados.length === 0 && (
          <p className="portal-actividad-vacio">No hay actividad con estos filtros.</p>
        )}
        {itemsFiltrados.map((item) => {
          const Icon = ICONOS_CATEGORIA[item.categoria] || Siren
          const color = COLOR_CATEGORIA[item.categoria] || 'gris'
          const barrio = barrios[claveBarrio(item.lat, item.lng)]
          // div+role en vez de <button>: el botón de "leer acá adentro" de
          // más abajo es interactivo por su cuenta -- un control interactivo
          // adentro de un <button> es contenido anidado inválido en HTML.
          return (
            <div
              key={item.id}
              className="portal-actividad-item"
              role="button"
              tabIndex={0}
              onClick={() => onVerEnMapa({ lat: item.lat, lng: item.lng })}
              onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onVerEnMapa({ lat: item.lat, lng: item.lng }) } }}
            >
              <span className={`portal-actividad-item-icono categoria-${color}`}><Icon size={16} /></span>
              <span className="portal-actividad-item-texto">
                <span className="portal-actividad-item-titulo">{item.titulo}</span>
                <span className="portal-actividad-item-meta">
                  {barrio && <span className="portal-actividad-item-zona"><MapPin size={11} /> {barrio}</span>}
                  <span>{formatearAntiguedad(item.fecha, horaActual)}</span>
                  {item.tipo === 'prensa' && item.fuente && <span>· {item.fuente}</span>}
                  {item.tipo === 'reporte' && (item.confirmaciones > 0 || item.desmentidas > 0) && (
                    <span className="portal-actividad-item-votos">
                      {item.confirmaciones > 0 && <span><ThumbsUp size={11} /> {item.confirmaciones}</span>}
                      {item.desmentidas > 0 && <span><ThumbsDown size={11} /> {item.desmentidas}</span>}
                    </span>
                  )}
                </span>
              </span>
              {item.tipo === 'prensa' && item.url && (
                <button
                  className="portal-actividad-item-link"
                  onClick={(e) => { e.stopPropagation(); onAbrirLector({ url: item.url, titulo: item.titulo, fuente: item.fuente }) }}
                  aria-label="Leer nota"
                  title="Leer nota"
                >
                  <BookOpen size={14} />
                </button>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
