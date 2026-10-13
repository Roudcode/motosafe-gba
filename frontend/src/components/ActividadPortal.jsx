// Portal de "Actividad": prensa + reportes de usuarios combinados en un solo
// feed, estilo noticias, con filtros de categoría/fecha/zona. Pedido
// explícito de Rodo -- no reemplaza el panel chico de "Actividad reciente"
// (ese es solo el historial de TUS reportes, con su propio criterio de
// vigencia/estado); esto es la ciudad entera.
//
// "Zona" no es un campo que exista en los datos (reportes_prensa y
// reportes_colaborativos solo tienen lat/lng, ver backend/main.py) -- se
// calcula contra la zona de ZONAS_RIESGO más cercana. Si la más cercana
// queda a más de DISTANCIA_MAX_ZONA_KM, se deja sin zona asignada en vez de
// etiquetar con una zona que en los hechos está lejos (un dato fuera de
// CABA no debería figurar como "Caballito" solo porque es la más próxima
// de la lista). Pendiente de revisar con Rodo: el nombre real de zona
// ("Zona 106 (13 siniestros...)") no es un dato que un usuario reconozca --
// ver conversación de SES-115 sobre alternativas (barrio real vía reverse
// geocoding) antes de tocar esto de nuevo.
import { useMemo, useState } from 'react'
import { X, Newspaper, Siren, ShieldAlert, Construction, TrafficCone, LightbulbOff, CarFront, Bike, MapPin, ThumbsUp, ThumbsDown, BookOpen, ArrowUpRight } from 'lucide-react'
import { CATEGORIAS_REPORTE } from '../constants'
import { zonaMasCercana } from '../utils/geoRiesgo'
import { formatearAntiguedad } from '../utils/tiempo'

const DISTANCIA_MAX_ZONA_KM = 2

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
// ícono gris plano sin ninguna jerarquía visual entre "robo" y "falta de
// iluminación", que son urgencias bastante distintas.
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
// "Zona insegura" truncada a "Zona" se confundía con el selector de zona
// GEOGRÁFICA que va debajo (dos cosas distintas con la misma palabra).
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

export function ActividadPortal({ reportesPrensa, reportes, zonasAjustadas, horaActual, onCerrar, onVerEnMapa, saliendo }) {
  const [filtroCategoria, setFiltroCategoria] = useState('todas')
  const [filtroFecha, setFiltroFecha] = useState('7d')
  const [filtroZona, setFiltroZona] = useState('todas')
  // Lector interno: en vez de salir de la pestaña de MotoSafe para leer una
  // nota, se abre acá adentro en un iframe. Algunos diarios bloquean que su
  // sitio se muestre dentro de un iframe ajeno (encabezado X-Frame-Options,
  // para evitar clickjacking) -- eso no se puede destrabar desde este lado,
  // así que el lector siempre deja a mano "Abrir en pestaña nueva" en vez de
  // prometer que toda nota va a cargar acá.
  const [lectorNota, setLectorNota] = useState(null)

  const zonas = useMemo(
    () => zonasAjustadas.map((z) => ({ id: z.id, nombre: z.nombre, lat: z.lat, lng: z.lng })),
    [zonasAjustadas]
  )

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
    return [...dePrensa, ...deReportes]
      .map((item) => {
        const cercana = zonaMasCercana(item, zonas)
        const zona = cercana && cercana.distanciaKm <= DISTANCIA_MAX_ZONA_KM ? cercana.zona : null
        return { ...item, zona }
      })
      .sort((a, b) => new Date(b.fecha) - new Date(a.fecha))
  }, [reportesPrensa, reportes, zonas])

  const itemsFiltrados = useMemo(() => {
    const horasMax = FILTROS_FECHA.find((f) => f.id === filtroFecha)?.horas ?? Infinity
    return items.filter((item) => {
      if (filtroCategoria !== 'todas' && item.categoria !== filtroCategoria) return false
      if (filtroZona !== 'todas' && item.zona?.id !== filtroZona) return false
      if (horasMax !== Infinity) {
        const edadHoras = (horaActual - new Date(item.fecha).getTime()) / 3600000
        if (edadHoras > horasMax) return false
      }
      return true
    })
  }, [items, filtroCategoria, filtroZona, filtroFecha, horaActual])

  const zonasConActividad = useMemo(() => {
    const vistas = new Map()
    for (const item of items) {
      if (item.zona && !vistas.has(item.zona.id)) vistas.set(item.zona.id, item.zona.nombre)
    }
    return [...vistas.entries()].sort((a, b) => a[1].localeCompare(b[1]))
  }, [items])

  return (
    <div className={`portal-actividad panel-enter ${saliendo ? 'panel-exit' : ''}`} role="dialog" aria-label="Actividad">
      <div className="portal-actividad-header">
        <span className="portal-actividad-titulo"><Newspaper size={18} /> Actividad</span>
        <button className="detalle-cerrar" onClick={onCerrar} aria-label="Cerrar actividad"><X size={16} /></button>
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
        {zonasConActividad.length > 0 && (
          <select
            className="portal-actividad-select-zona"
            value={filtroZona}
            onChange={(e) => setFiltroZona(e.target.value)}
            aria-label="Filtrar por zona"
          >
            <option value="todas">Todas las zonas</option>
            {zonasConActividad.map(([id, nombre]) => <option key={id} value={id}>{nombre}</option>)}
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
                  {item.zona && <span className="portal-actividad-item-zona"><MapPin size={11} /> {item.zona.nombre}</span>}
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
                  onClick={(e) => { e.stopPropagation(); setLectorNota({ url: item.url, titulo: item.titulo, fuente: item.fuente }) }}
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

      {lectorNota && (
        <div className="lector-nota" role="dialog" aria-label={`Leyendo: ${lectorNota.titulo}`}>
          <div className="lector-nota-header">
            <span className="lector-nota-fuente">{lectorNota.fuente}</span>
            <div className="lector-nota-acciones">
              <a className="lector-nota-abrir" href={lectorNota.url} target="_blank" rel="noopener noreferrer">
                Abrir en pestaña nueva <ArrowUpRight size={13} />
              </a>
              <button className="detalle-cerrar" onClick={() => setLectorNota(null)} aria-label="Cerrar lector"><X size={16} /></button>
            </div>
          </div>
          <p className="lector-nota-aviso">Algunos sitios no permiten mostrarse acá adentro -- si no carga, abrila en una pestaña nueva.</p>
          <iframe className="lector-nota-iframe" src={lectorNota.url} title={lectorNota.titulo} />
        </div>
      )}
    </div>
  )
}
