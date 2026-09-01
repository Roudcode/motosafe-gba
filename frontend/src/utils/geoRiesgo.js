// Cálculos geoespaciales y de ajuste de riesgo: distancias, geocodificación,
// y la lógica que sube el nivel de riesgo de una zona según clima/reportes activos.

import { ORDEN_NIVELES, CODIGOS_LLUVIA, UMBRAL_REPORTE_KM, BBOX_GBA } from '../constants'

export function distanciaKm(a, b) {
  const R = 6371
  const dLat = (b.lat - a.lat) * Math.PI / 180
  const dLng = (b.lng - a.lng) * Math.PI / 180
  const lat1 = a.lat * Math.PI / 180
  const lat2 = b.lat * Math.PI / 180
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) ** 2
  return 2 * R * Math.asin(Math.sqrt(h))
}

export function distanciaAPolilinea(punto, coords) {
  let min = Infinity
  for (const [lat, lng] of coords) {
    const d = distanciaKm(punto, { lat, lng })
    if (d < min) min = d
  }
  return min
}

export function calcularAjuste(zona, climaCode, reportes) {
  let idx = ORDEN_NIVELES.indexOf(zona.nivel)
  const motivos = []
  const esLluvia = climaCode != null && CODIGOS_LLUVIA.includes(climaCode)
  if (esLluvia && idx < 3) { idx += 1; motivos.push('lluvia actual') }
  const reportesCercanos = reportes.filter((r) => distanciaKm(zona, r) <= UMBRAL_REPORTE_KM).length
  if (reportesCercanos > 0 && idx < 3) { idx += 1; motivos.push(`${reportesCercanos} reporte${reportesCercanos > 1 ? 's' : ''} tuyo${reportesCercanos > 1 ? 's' : ''} cerca`) }
  return { nivel: ORDEN_NIVELES[idx], subio: idx > ORDEN_NIVELES.indexOf(zona.nivel), motivos, reportesCercanos }
}

export async function geocodificar(texto) {
  const q = encodeURIComponent(`${texto}, Buenos Aires, Argentina`)
  const url = `https://nominatim.openstreetmap.org/search?format=json&q=${q}&viewbox=${BBOX_GBA}&bounded=1&limit=1`
  const res = await fetch(url, { headers: { 'Accept-Language': 'es' } })
  const data = await res.json()
  if (!data || data.length === 0) return null
  return {
    lat: parseFloat(data[0].lat),
    lng: parseFloat(data[0].lon),
    label: data[0].display_name.split(',').slice(0, 2).join(','),
  }
}
