// Tira mínima de navegación activa (velocidad, tiempo/distancia restante,
// botón de salir), botón de recentrar y velocímetro en vivo. A17
// (BACKLOG): extraído de App.jsx (SES-136) -- tres bloques adyacentes,
// corte-y-pegado con props, sin cambio de comportamiento.

import { Square, LocateFixed, Gauge } from 'lucide-react'

export function NavegacionResumen({
  rutasCalculadas, modoViaje, velocidadActual, etaInfo, rutasConScore, rutaSeleccionada,
  desactivarModoViaje, siguiendoUbicacion, recentrarUbicacion, vistaNavegacion,
}) {
  return (
    <>
      {/* Tira mínima de navegación activa: reemplaza al panel completo de
          arriba mientras hay ruta + Modo Viaje. Es la barra de "cuánto
          falta" que le faltaba a la app -- antes, una vez que arrancabas a
          navegar, no había NINGÚN indicador de progreso del viaje. */}
      {rutasCalculadas.length > 0 && modoViaje && (
        <div className="nav-resumen-mini panel-enter" role="status" aria-live="polite">
          {velocidadActual != null && (
            <div className="viaje-velocidad" title="Velocidad actual (GPS)">
              <strong>{Math.round(velocidadActual * 3.6)}</strong>
              <span>km/h</span>
            </div>
          )}
          <div className="viaje-tiempo">
            <strong>{etaInfo ? etaInfo.minRestante : rutasConScore[rutaSeleccionada]?.min} min</strong>
            <span>
              {etaInfo ? etaInfo.distanciaRestanteKm.toFixed(1) : rutasConScore[rutaSeleccionada]?.km} km
              {etaInfo && <> · llegás {etaInfo.horaLlegada}</>}
            </span>
          </div>
          <button className="viaje-salir" onClick={() => desactivarModoViaje()} aria-label="Detener navegación">
            <Square size={12} /> <span>Salir</span>
          </button>
        </div>
      )}

      {/* Botón de recentrar (estilo Waze/Maps): aparece solo cuando el
          usuario paneó el mapa a mano durante el viaje y la cámara dejó de
          seguir al GPS -- ver siguiendoUbicacion más arriba. */}
      {modoViaje && !siguiendoUbicacion && (
        <button className="recenter-fab panel-enter" onClick={recentrarUbicacion} aria-label="Volver a mi ubicación">
          <LocateFixed size={18} />
        </button>
      )}

      {/* Velocímetro en vivo (mismo lugar que en Waze/Maps: círculo abajo a
          la izquierda). Solo aparece si el GPS realmente entrega velocidad
          -- no todos los navegadores/dispositivos la dan, y mostrar 0 fijo
          sería peor que no mostrar nada. */}
      {vistaNavegacion && velocidadActual != null && (
        <div className="velocimetro panel-enter" title="Velocidad actual (GPS)">
          <Gauge size={12} className="velocimetro-icono" />
          <strong>{Math.round(velocidadActual * 3.6)}</strong>
          <span>km/h</span>
        </div>
      )}
    </>
  )
}
