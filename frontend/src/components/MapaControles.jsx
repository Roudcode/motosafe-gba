// Subcomponentes chicos que dependen del contexto de react-leaflet (useMap /
// useMapEvents) y por eso no pueden vivir como funciones puras: manejan vuelo a un
// punto, seguimiento en vivo de la posición del usuario, zoom, clicks sobre el mapa
// y la escala visual. Se agrupan acá porque todos son "comportamiento del mapa",
// separados de App.jsx que orquesta el estado general de la aplicación.

import { useState, useEffect } from 'react'
import { useMap, useMapEvents } from 'react-leaflet'

export function VueloControlado({ destino }) {
  const map = useMap()
  useEffect(() => {
    if (destino) map.flyTo([destino.lat, destino.lng], destino.zoom || 15, { duration: 1.4, easeLinearity: 0.15 })
  }, [destino, map])
  return null
}

export function SeguimientoEnVivo({ activo, punto }) {
  const map = useMap()
  useEffect(() => {
    if (activo && punto) map.panTo([punto.lat, punto.lng], { animate: true, duration: 0.8 })
  }, [activo, punto, map])
  return null
}

export function ControlesZoom() {
  const map = useMap()
  return (
    <div className="zoom-controls panel-enter" style={{ animationDelay: '0.1s' }}>
      <button onClick={() => map.zoomIn(0.5)} aria-label="Acercar mapa">+</button>
      <button onClick={() => map.zoomOut(0.5)} aria-label="Alejar mapa">−</button>
    </div>
  )
}

export function ClicksDeMapa({ campoActivo, onClick }) {
  useMapEvents({
    click(e) {
      if (campoActivo) onClick({ lat: e.latlng.lat, lng: e.latlng.lng })
    },
  })
  return null
}

export function EscalaMapa() {
  const map = useMap()
  const [texto, setTexto] = useState('')
  useEffect(() => {
    const actualizar = () => {
      const centro = map.getCenter()
      const zoom = map.getZoom()
      const metrosPorPixel = 156543.03392 * Math.cos((centro.lat * Math.PI) / 180) / Math.pow(2, zoom)
      const metros = metrosPorPixel * 80
      const pasos = [10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000]
      const cercano = pasos.reduce((prev, curr) => (Math.abs(curr - metros) < Math.abs(prev - metros) ? curr : prev))
      setTexto(cercano >= 1000 ? `${cercano / 1000} km` : `${cercano} m`)
    }
    actualizar()
    map.on('zoomend moveend', actualizar)
    return () => map.off('zoomend moveend', actualizar)
  }, [map])
  return (
    <div className="escala-mapa">
      <div className="escala-linea" />
      <span>{texto}</span>
    </div>
  )
}
