// Cálculos geoespaciales y de ajuste de riesgo: distancias, geocodificación,
// y la lógica que sube el nivel de riesgo de una zona según clima/reportes activos.

import { ORDEN_NIVELES, CODIGOS_LLUVIA, UMBRAL_REPORTE_KM, BBOX_GBA, FRANJA_PICO_INSEGURIDAD } from '../constants'

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

// Es franja de mayor riesgo segun FRANJA_PICO_INSEGURIDAD (ver constants.js:
// calibrada con la distribucion horaria real de robos con moto, no con un
// criterio generico). Maneja el caso en que la franja cruce medianoche, por
// si en el futuro se recalibra a un rango que la cruce.
export function esFranjaPicoInseguridad(horaDelDia, franja = FRANJA_PICO_INSEGURIDAD) {
  if (horaDelDia == null) return false
  return franja.desde > franja.hasta
    ? horaDelDia >= franja.desde || horaDelDia < franja.hasta
    : horaDelDia >= franja.desde && horaDelDia < franja.hasta
}

// Ajuste de inseguridad por franja horaria de mayor riesgo (no depende de
// clima ni de reportes, esos ya se manejan aparte en calcularAjuste para
// siniestros). A diferencia de la primera version de esto, ya no es una
// heuristica sin sustento: FRANJA_PICO_INSEGURIDAD sale de la distribucion
// horaria real del dataset de Delitos (ver constants.js).
export function calcularAjustePorFranjaHoraria(zona, horaDelDia) {
  const idxBase = ORDEN_NIVELES.indexOf(zona.nivel)
  const enFranjaPico = esFranjaPicoInseguridad(horaDelDia)
  const idx = enFranjaPico && idxBase < 3 ? idxBase + 1 : idxBase
  return {
    nivel: ORDEN_NIVELES[idx],
    subio: idx > idxBase,
    enFranjaPico,
    motivos: enFranjaPico && idx > idxBase ? ['franja horaria de mayor incidencia de robos con moto (19-23hs, dato real)'] : [],
  }
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
