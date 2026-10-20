// Barra de búsqueda de lugar/calle (con sugerencias y recientes) y la
// tarjeta del lugar elegido una vez que se selecciona un resultado. A17
// (BACKLOG): extraído de App.jsx (SES-136) -- dos bloques adyacentes,
// corte-y-pegado con props, sin cambio de comportamiento.

import { Search, X, MapPin, Clock, Navigation } from 'lucide-react'

export function SearchBar({
  vistaNavegacion, busqueda, setBusqueda, sugBusqueda, buscaEnFoco, setBuscaEnFoco,
  recientes, buscarEnMapa, lugarElegido, setLugarElegido, rutaAbierta, irAlLugar,
}) {
  return (
    <>
      {/* Se oculta durante la navegación: no solo no hace falta buscar
          mientras estás en camino, sino que en pantalla chica quedaba
          asomando detrás de la tarjeta de "doblá acá" (se veía en las
          capturas que mandaste) -- las dos ocupaban la misma franja
          horizontal arriba.
          Sin hazard-edge: la franja de "cinta de peligro" sobre una píldora
          se veía mal (a pedido de Rodo) -- ese motivo queda reservado para
          paneles de datos de riesgo, no para el buscador. */}
      {!vistaNavegacion && (
        <div className="searchbar panel-enter" style={{ animationDelay: '0.05s' }}>
          <button type="button" className="searchbar-icon" onClick={() => sugBusqueda.buscar(busqueda)} aria-label="Buscar dirección" disabled={!busqueda.trim()}><Search size={13} /></button>
          <input type="text" placeholder="Buscar lugar, calle o local..." value={busqueda} onChange={(e) => { setBusqueda(e.target.value); sugBusqueda.limpiar() }} onKeyDown={(e) => { if (e.key === 'Enter') sugBusqueda.buscar(busqueda) }} onFocus={() => setBuscaEnFoco(true)} onBlur={() => { setBuscaEnFoco(false); setTimeout(sugBusqueda.limpiar, 150) }} aria-label="Buscar lugar, calle o local" autoComplete="off" />
          {sugBusqueda.buscando && <span className="ruta-form-sug-spinner spinner spinner-dark" />}
          {busqueda && <button className="searchbar-clear" onClick={() => { setBusqueda(''); sugBusqueda.limpiar() }} aria-label="Limpiar búsqueda"><X size={12} /></button>}
          {(sugBusqueda.resultados.length > 0 || sugBusqueda.buscada || sugBusqueda.error) && (
            <ul className="ruta-form-sugerencias searchbar-sugerencias">
              {sugBusqueda.resultados.map((s, i) => (
                <li key={i}>
                  <button type="button" onMouseDown={() => buscarEnMapa(s)}>
                    <MapPin size={12} /> {s.label}
                  </button>
                </li>
              ))}
              {sugBusqueda.buscada && sugBusqueda.resultados.length === 0 && <li className="ruta-form-sin-resultados">No encontramos esa dirección. Probá con más detalle.</li>}
              {sugBusqueda.error && <li className="ruta-form-sin-resultados">No pudimos buscar. Probá de nuevo.</li>}
            </ul>
          )}
          {buscaEnFoco && !busqueda.trim() && recientes.length > 0 && (
            <ul className="ruta-form-sugerencias searchbar-sugerencias">
              <li className="ruta-form-sin-resultados">Recientes</li>
              {recientes.map((r, i) => (
                <li key={`${r.label}-${i}`}>
                  <button type="button" onMouseDown={() => buscarEnMapa(r)}>
                    <Clock size={12} /> {r.label}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {lugarElegido && !rutaAbierta && (
        <div className="lugar-card panel-enter" role="dialog" aria-label="Lugar elegido">
          <div className="lugar-card-texto">
            <MapPin size={14} />
            <span>
              {lugarElegido.label}
              {lugarElegido.categoria && <em className="lugar-card-categoria">{lugarElegido.categoria}</em>}
            </span>
          </div>
          <div className="lugar-card-acciones">
            <button type="button" className="lugar-card-cerrar" onClick={() => setLugarElegido(null)}>Cerrar</button>
            <button type="button" className="lugar-card-ir" onClick={irAlLugar}><Navigation size={13} /> Ir</button>
          </div>
        </div>
      )}
    </>
  )
}
