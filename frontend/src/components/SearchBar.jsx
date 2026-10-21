// Barra de búsqueda de lugar/calle (con sugerencias y recientes) y la
// tarjeta del lugar elegido una vez que se selecciona un resultado. A17
// (BACKLOG): extraído de App.jsx (SES-136) -- dos bloques adyacentes,
// corte-y-pegado con props, sin cambio de comportamiento.
//
// SES-141 (a pedido de Rodo: "el buscador tmb podria mejorar... que sea
// una lupa que se esconda"): colapsada por defecto. El disparador
// (círculo con la lupa) vive en la topbar, agrupado con los demás
// botones de exploración (tema/capas/actividad) -- ver App.jsx. Primero
// probamos un círculo flotando solo a mitad de pantalla, pero Rodo lo
// vio y "quedaba sola ahí, suelta", sin nada que la conecte visualmente
// con el resto de los controles; en la topbar se lee como "un botón más
// del mismo grupo", no como un elemento nuevo aislado.
//
// `abierto`/`setAbierto` viven en App.jsx (no son estado propio de este
// componente) para que el botón de la topbar y el cierre automático de
// acá abajo controlen exactamente el mismo valor.

import { useRef, useEffect } from 'react'
import { Search, X, MapPin, Clock, Navigation } from 'lucide-react'

export function SearchBar({
  abierto, setAbierto,
  vistaNavegacion, busqueda, setBusqueda, sugBusqueda, buscaEnFoco, setBuscaEnFoco,
  recientes, buscarEnMapa, lugarElegido, setLugarElegido, rutaAbierta, irAlLugar,
}) {
  const inputRef = useRef(null)

  useEffect(() => {
    if (abierto) inputRef.current?.focus()
  }, [abierto])

  // Se cierra sola cuando el input pierde el foco sin texto cargado --
  // mismo momento en que ya se limpiaban las sugerencias antes de este
  // cambio, así que tocar afuera sin buscar nada, o elegir un resultado
  // (buscarEnMapa vacía el campo al elegir un lugar), la cierra también,
  // sin necesidad de un botón de "cerrar" aparte.
  function cerrarSiQuedaVacio() {
    setBuscaEnFoco(false)
    setTimeout(() => {
      sugBusqueda.limpiar()
      if (!busqueda.trim()) setAbierto(false)
    }, 150)
  }

  return (
    <>
      {/* Se oculta durante la navegación: no solo no hace falta buscar
          mientras estás en camino, sino que en pantalla chica quedaba
          asomando detrás de la tarjeta de "doblá acá" (se veía en las
          capturas que mandaste) -- las dos ocupaban la misma franja
          horizontal arriba. */}
      {!vistaNavegacion && abierto && (
        <div className="searchbar panel-enter" style={{ animationDelay: '0.05s' }}>
          <button type="button" className="searchbar-icon" onClick={() => sugBusqueda.buscar(busqueda)} aria-label="Buscar dirección" disabled={!busqueda.trim()}><Search size={13} /></button>
          <input ref={inputRef} type="text" placeholder="Buscar lugar, calle o local..." value={busqueda} onChange={(e) => { setBusqueda(e.target.value); sugBusqueda.limpiar() }} onKeyDown={(e) => { if (e.key === 'Enter') sugBusqueda.buscar(busqueda) }} onFocus={() => setBuscaEnFoco(true)} onBlur={cerrarSiQuedaVacio} aria-label="Buscar lugar, calle o local" autoComplete="off" />
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
