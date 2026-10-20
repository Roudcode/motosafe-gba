// Menu flotante de "más herramientas" (ubicacion, modo viaje, vista
// inclinada, estadisticas, cerrar sesion). A17 (BACKLOG): extraido de
// App.jsx (SES-131) -- bloque autocontenido con una interfaz de props
// chica. Corte-y-pegue con props, sin cambio de comportamiento.

import { LocateFixed, Bike, Box, BarChart3, LogOut, Wrench, X } from 'lucide-react'

export function HerramientasMenu({
  herramientasAbiertas, setHerramientasAbiertas,
  pedirUbicacion, buscandoUbicacion,
  modoViaje, toggleModoViaje,
  vistaNavegacion, setVistaNavegacion,
  setStatsAbierto, setActividadAbierta, setCapasAbiertas,
  sesion,
}) {
  return (
    <div className="herramientas-stack">
      {herramientasAbiertas && (
        <div className="herramientas-menu panel-enter">
          <button onClick={() => { pedirUbicacion(); setHerramientasAbiertas(false) }}>
            {buscandoUbicacion ? <span className="spinner" /> : <LocateFixed size={15} />} Mi ubicación
          </button>
          <button className={modoViaje ? 'activo' : ''} onClick={toggleModoViaje}>
            <Bike size={15} /> Modo Viaje {modoViaje ? '· activo' : ''}
          </button>
          {modoViaje && (
            <button className={vistaNavegacion ? 'activo' : ''} onClick={() => setVistaNavegacion((v) => !v)}>
              <Box size={15} /> Vista inclinada {vistaNavegacion ? '· activa' : ''}
            </button>
          )}
          <button onClick={() => { setStatsAbierto(true); setHerramientasAbiertas(false); setActividadAbierta(false); setCapasAbiertas(false) }}>
            <BarChart3 size={15} /> Estadísticas
          </button>
          {sesion && (
            <button onClick={() => { setHerramientasAbiertas(false); sesion.cerrarSesion() }} title={`Sesión de ${sesion.usuario}`}>
              <LogOut size={15} /> Cerrar sesión
            </button>
          )}
        </div>
      )}
      <button
        className={`herramientas-fab ${herramientasAbiertas ? 'activo' : ''}`}
        onClick={() => setHerramientasAbiertas((v) => !v)}
        aria-label="Más herramientas"
        aria-expanded={herramientasAbiertas}
      >
        {herramientasAbiertas ? <X size={18} /> : <Wrench size={18} />}
      </button>
    </div>
  )
}
