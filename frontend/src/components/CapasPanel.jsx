// Panel único de capas del mapa: reemplaza los dos botones que ciclaban
// estados (vista de fondo / inseguridad) por un panel con todas las opciones
// visibles de entrada. Vista de fondo e inseguridad son dos grupos de radio
// separados (cada uno excluyente puertas adentro, pero independientes entre
// sí: podés tener corredores + inseguridad con moto al mismo tiempo).
//
// Tráfico en vivo es un toggle aparte (no un grupo de radio, es un solo
// booleano): se superpone a cualquier vista de fondo, independiente de todo
// lo demás. Depende de que el backend tenga configurada una API key de
// TomTom (ver backend/main.py, endpoints /trafico/*) — si no está disponible,
// el toggle avisa en vez de fallar en silencio.

import { X, Zap, Newspaper, Bike, CarFront, ShieldAlert, ListFilter } from 'lucide-react'
import { OPCIONES_CAPA_MAPA, OPCIONES_CAPA_INSEGURIDAD } from '../constants'

export function CapasPanel({
  capaMapa, onCambiarCapaMapa,
  capaInseguridad, onCambiarCapaInseguridad,
  capaTrafico, onCambiarCapaTrafico,
  capaPrensa, onCambiarCapaPrensa,
  filtroPrensa, onCambiarFiltroPrensa,
  onCerrar,
}) {
  return (
    <div className="capas-panel panel-enter hazard-edge">
      <div className="capas-panel-header">
        <span className="cercanas-title">Capas del mapa</span>
        <button className="detalle-cerrar" onClick={onCerrar} aria-label="Cerrar capas"><X size={14} /></button>
      </div>

      <span className="capas-grupo-titulo">Vista de fondo</span>
      {OPCIONES_CAPA_MAPA.map((op) => (
        <button
          key={op.id}
          className={`capas-opcion ${capaMapa === op.id ? 'activa' : ''}`}
          onClick={() => onCambiarCapaMapa(op.id)}
        >
          <span className="capas-opcion-radio" />
          <op.Icon size={15} className="capas-opcion-icono" />
          <span className="capas-opcion-texto">
            <span className="capas-opcion-label">{op.label}</span>
            <span className="capas-opcion-desc">{op.desc}</span>
          </span>
        </button>
      ))}

      <span className="capas-grupo-titulo">Inseguridad (delitos)</span>
      {OPCIONES_CAPA_INSEGURIDAD.map((op) => (
        <button
          key={op.id}
          className={`capas-opcion ${capaInseguridad === op.id ? 'activa' : ''}`}
          onClick={() => onCambiarCapaInseguridad(op.id)}
        >
          <span className="capas-opcion-radio" />
          <op.Icon size={15} className="capas-opcion-icono" />
          <span className="capas-opcion-texto">
            <span className="capas-opcion-label">{op.label}</span>
            <span className="capas-opcion-desc">{op.desc}</span>
          </span>
        </button>
      ))}

      <span className="capas-grupo-titulo">Tráfico</span>
      <button
        className={`capas-opcion ${capaTrafico ? 'activa' : ''}`}
        onClick={() => onCambiarCapaTrafico(!capaTrafico)}
      >
        <span className="capas-opcion-radio" />
        <Zap size={15} className="capas-opcion-icono" />
        <span className="capas-opcion-texto">
          <span className="capas-opcion-label">Tráfico en vivo</span>
          <span className="capas-opcion-desc">Congestión actual por calle (TomTom) · se actualiza cada 2 min</span>
        </span>
      </button>
      <span className="capas-grupo-titulo">Prensa</span>
      <button
        className={`capas-opcion ${capaPrensa ? 'activa' : ''}`}
        onClick={() => onCambiarCapaPrensa(!capaPrensa)}
      >
        <span className="capas-opcion-radio" />
        <Newspaper size={15} className="capas-opcion-icono" />
        <span className="capas-opcion-texto">
          <span className="capas-opcion-label">Hechos recientes en noticias</span>
          <span className="capas-opcion-desc">Últimos 30 días, no en vivo · filtrá motos, robos, inseguridad o choques · tocá un punto para ver la nota</span>
        </span>
      </button>
      {capaPrensa && (
        <div className="capas-prensa-filtros" role="group" aria-label="Filtrar noticias de prensa">
          <div className="capas-prensa-filtros-titulo"><ListFilter size={13} /> Mostrando</div>
          <div className="capas-prensa-filtros-opciones">
          {[
            ['todos', 'Todo', Newspaper], ['moto', 'Motos', Bike], ['robo', 'Robos', ShieldAlert],
            ['inseguridad', 'Seguridad', ShieldAlert], ['choque', 'Choques', CarFront],
          ].map(([filtro, etiqueta, Icono]) => (
            <button key={filtro} className={filtroPrensa === filtro ? 'activa' : ''} onClick={() => onCambiarFiltroPrensa(filtro)} aria-pressed={filtroPrensa === filtro}>
              <Icono size={12} /> {etiqueta}
            </button>
          ))}
          </div>
        </div>
      )}

      <p className="capas-panel-nota">
        Tu ruta y las alertas en viaje ya tienen en cuenta la inseguridad esté o no prendida esta capa: esto solo cambia lo que ves dibujado en el mapa.
      </p>
    </div>
  )
}
