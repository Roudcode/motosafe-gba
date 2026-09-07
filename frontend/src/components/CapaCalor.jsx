// Capa de mapa de calor, alternativa a los clusters discretos. Igual que los
// controles de MapaControles.jsx, usa useMap() para acceder a la instancia de
// Leaflet y manejar la capa de forma imperativa, porque leaflet.heat no tiene
// un wrapper nativo de react-leaflet.
//
// Se agrega/saca del mapa según `activa`, sin tocar ni desmontar el resto de
// las capas (clusters, rutas, etc.) — es aditiva, no reemplaza nada del
// render existente.
//
// `atenuada`: cuando la capa de inseguridad está prendida encima, el calor de
// siniestros se atenúa en vez de competir con ella en la misma jerarquía
// visual (mismo criterio que aplica a clusters/corredores, ver App.jsx).

import { useEffect, useRef } from 'react'
import { useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet.heat'

export function CapaCalor({ zonas, activa, atenuada }) {
  const map = useMap()
  const capaRef = useRef(null)

  useEffect(() => {
    if (!activa) return
    // Intensidad ponderada: cantidad de siniestros normalizada + un empujón
    // extra si el cluster tuvo algún mortal, para que la mancha de calor no
    // trate igual a una zona con 50 siniestros leves que a una con mortales.
    const puntos = zonas.map((z) => {
      const intensidad = Math.min((z.cantidad || 0) / 15, 1) + (z.mortales > 0 ? 0.4 : 0)
      return [z.lat, z.lng, intensidad]
    })
    capaRef.current = L.heatLayer(puntos, { radius: 32, blur: 28, maxZoom: 14, max: 1.2 }).addTo(map)
    return () => {
      if (capaRef.current) map.removeLayer(capaRef.current)
    }
  }, [activa, zonas, map])

  useEffect(() => {
    if (capaRef.current?._canvas) {
      capaRef.current._canvas.style.opacity = atenuada ? 0.4 : 1
    }
  }, [atenuada, activa, zonas])

  return null
}
