// Formulario de ruta: campos de origen/destino con sugerencias de
// dirección, botón para marcar el punto en el mapa, favoritos (Casa/
// Trabajo) y las acciones de buscar/cancelar. A17 (BACKLOG): extraído de
// App.jsx -- corte-y-pegado con props, sin cambio de comportamiento.
//
// El estado que decide CUÁL campo está activo para marcar en el mapa
// (campoActivo) y el efecto que escucha el click en el mapa siguen en
// App.jsx a propósito: ese acoplamiento es compartido con el flujo de
// reportar un incidente (ver comentario de campoActivo en App.jsx), no es
// algo propio de este formulario. Acá solo se lee campoActivo para pintar
// el botón activo y se llama a marcarEnMapa, igual que con cualquier otro
// callback de los que ya recibía este bloque dentro de App.jsx.

import { MapPin, ArrowUpDown, Home, Save, Briefcase, LocateFixed } from 'lucide-react'

export function RutaForm({
  origenTexto, setOrigenTexto, origenPunto, setOrigenPunto, sugOrigen,
  destinoTexto, setDestinoTexto, destinoPunto, setDestinoPunto, sugDestino,
  campoActivo, marcarEnMapa, elegirSugerencia, intercambiar,
  favoritos, guardarFavorito, usarFavorito, usarMiUbicacionComoOrigen,
  rutaError, cerrarTodoRuta, buscarRuta,
}) {
  return (
    <div className="ruta-form panel-enter">
      <div className="ruta-form-fila ruta-form-fila-con-sugerencias">
        <span className="ruta-form-punto ruta-form-punto-origen" />
        <input placeholder="Origen" value={origenTexto} onChange={(e) => { setOrigenTexto(e.target.value); setOrigenPunto(null); sugOrigen.limpiar() }} onKeyDown={(e) => { if (e.key === 'Enter' && !origenPunto) sugOrigen.buscar(origenTexto) }} onBlur={() => setTimeout(sugOrigen.limpiar, 150)} aria-label="Origen de la ruta" autoComplete="off" />
        {sugOrigen.buscando && <span className="ruta-form-sug-spinner spinner spinner-dark" />}
        <button className={`ruta-form-pin ${campoActivo === 'origen' ? 'activo' : ''}`} title="Marcar en el mapa" aria-label="Marcar origen en el mapa" onClick={() => marcarEnMapa('origen')}><MapPin size={14} /></button>
        {(sugOrigen.resultados.length > 0 || sugOrigen.buscada || sugOrigen.error) && (
          <ul className="ruta-form-sugerencias">
            {sugOrigen.resultados.map((s, i) => (
              <li key={i}>
                <button type="button" onMouseDown={() => elegirSugerencia('origen', s)}>
                  <MapPin size={12} /> {s.label}
                </button>
              </li>
            ))}
            {sugOrigen.buscada && sugOrigen.resultados.length === 0 && <li className="ruta-form-sin-resultados">No encontramos esa dirección.</li>}
            {sugOrigen.error && <li className="ruta-form-sin-resultados">No pudimos buscar. Probá de nuevo.</li>}
          </ul>
        )}
      </div>
      <button className="ruta-form-swap" onClick={intercambiar} title="Intercambiar" aria-label="Intercambiar origen y destino"><ArrowUpDown size={13} /></button>
      <div className="ruta-form-fila ruta-form-fila-con-sugerencias">
        <span className="ruta-form-punto ruta-form-punto-destino" />
        <input placeholder="Destino" value={destinoTexto} onChange={(e) => { setDestinoTexto(e.target.value); setDestinoPunto(null); sugDestino.limpiar() }} onKeyDown={(e) => { if (e.key === 'Enter' && !destinoPunto) sugDestino.buscar(destinoTexto) }} onBlur={() => setTimeout(sugDestino.limpiar, 150)} aria-label="Destino de la ruta" autoComplete="off" />
        {sugDestino.buscando && <span className="ruta-form-sug-spinner spinner spinner-dark" />}
        <button className={`ruta-form-pin ${campoActivo === 'destino' ? 'activo' : ''}`} title="Marcar en el mapa" aria-label="Marcar destino en el mapa" onClick={() => marcarEnMapa('destino')}><MapPin size={14} /></button>
        {(sugDestino.resultados.length > 0 || sugDestino.buscada || sugDestino.error) && (
          <ul className="ruta-form-sugerencias">
            {sugDestino.resultados.map((s, i) => (
              <li key={i}>
                <button type="button" onMouseDown={() => elegirSugerencia('destino', s)}>
                  <MapPin size={12} /> {s.label}
                </button>
              </li>
            ))}
            {sugDestino.buscada && sugDestino.resultados.length === 0 && <li className="ruta-form-sin-resultados">No encontramos esa dirección.</li>}
            {sugDestino.error && <li className="ruta-form-sin-resultados">No pudimos buscar. Probá de nuevo.</li>}
          </ul>
        )}
      </div>
      <div className="favoritos-fila">
        {favoritos.casa ? (
          <button className="favorito-chip" onClick={() => usarFavorito(favoritos.casa)}><Home size={12} /> Casa</button>
        ) : destinoTexto.trim() ? (
          <button className="favorito-chip favorito-chip-guardar" onClick={() => guardarFavorito('casa', 'Casa')}><Save size={12} /> Guardar como Casa</button>
        ) : (
          <button className="favorito-chip favorito-chip-vacio" disabled><Home size={12} /> Casa</button>
        )}
        {favoritos.trabajo ? (
          <button className="favorito-chip" onClick={() => usarFavorito(favoritos.trabajo)}><Briefcase size={12} /> Trabajo</button>
        ) : destinoTexto.trim() ? (
          <button className="favorito-chip favorito-chip-guardar" onClick={() => guardarFavorito('trabajo', 'Trabajo')}><Save size={12} /> Guardar como Trabajo</button>
        ) : (
          <button className="favorito-chip favorito-chip-vacio" disabled><Briefcase size={12} /> Trabajo</button>
        )}
      </div>
      {campoActivo && <p className="ruta-form-hint">Tocá el mapa para marcar el {campoActivo}.</p>}
      <button className="ruta-form-miubicacion" onClick={usarMiUbicacionComoOrigen}><LocateFixed size={14} /> Usar mi ubicación como origen</button>
      {rutaError && <p className="ruta-form-error">{rutaError}</p>}
      <div className="ruta-form-acciones">
        <button className="ruta-form-cancelar" onClick={cerrarTodoRuta}>Cancelar</button>
        <button className="ruta-form-buscar" onClick={buscarRuta}>Buscar ruta</button>
      </div>
    </div>
  )
}
