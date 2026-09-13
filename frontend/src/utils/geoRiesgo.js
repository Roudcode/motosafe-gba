// Cálculos geoespaciales y de ajuste de riesgo: distancias, geocodificación,
// y la lógica que sube el nivel de riesgo de una zona según clima/reportes activos.

import { ORDEN_NIVELES, UMBRAL_REPORTE_KM, BBOX_GBA, FRANJA_PICO_INSEGURIDAD_MOTO } from '../constants'

export function distanciaKm(a, b) {
  const R = 6371
  const dLat = (b.lat - a.lat) * Math.PI / 180
  const dLng = (b.lng - a.lng) * Math.PI / 180
  const lat1 = a.lat * Math.PI / 180
  const lat2 = b.lat * Math.PI / 180
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) ** 2
  return 2 * R * Math.asin(Math.sqrt(h))
}

// Rumbo (bearing inicial, en grados 0-360 desde el norte) del punto a al
// punto b. Se usa como fallback para la vista de navegación cuando el GPS no
// entrega coords.heading (pasa seguido con poca velocidad o en navegadores
// que no lo soportan): calculamos la dirección de movimiento a partir de las
// últimas dos posiciones, igual que hacen Waze/Google Maps cuando no tienen
// brújula del dispositivo.
export function calcularRumbo(a, b) {
  const lat1 = a.lat * Math.PI / 180
  const lat2 = b.lat * Math.PI / 180
  const dLng = (b.lng - a.lng) * Math.PI / 180
  const y = Math.sin(dLng) * Math.cos(lat2)
  const x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLng)
  const rumbo = Math.atan2(y, x) * 180 / Math.PI
  return (rumbo + 360) % 360
}

// Progreso sobre una ruta ya calculada: a qué distancia (en km) del punto
// dado está cada vértice de la polilínea, cuál es el más cercano, y cuánto
// falta para llegar al final desde ahí. Es la base de la barra de "X km · Y
// min · llegás a las Z" que usan Waze/Maps durante la navegación -- antes de
// esto la app solo sabía la distancia/tiempo TOTAL de la ruta, no cuánto iba
// quedando a medida que se avanza. No usa la ruta real (grafo vial): aproxima
// por el vértice más cercano de la polilínea ya devuelta por el backend, que
// alcanza para una barra de progreso (no para recalcular giros).
export function calcularProgresoRuta(punto, coords) {
  if (!punto || !coords || coords.length < 2) {
    return { indiceCercano: 0, distanciaTotalKm: 0, distanciaRecorridaKm: 0, distanciaRestanteKm: 0, fraccionRecorrida: 0 }
  }
  const acumulado = [0]
  for (let i = 0; i < coords.length - 1; i++) {
    const [lat1, lng1] = coords[i]
    const [lat2, lng2] = coords[i + 1]
    acumulado.push(acumulado[i] + distanciaKm({ lat: lat1, lng: lng1 }, { lat: lat2, lng: lng2 }))
  }
  const distanciaTotalKm = acumulado[acumulado.length - 1]
  let indiceCercano = 0
  let mejorDist = Infinity
  for (let i = 0; i < coords.length; i++) {
    const [lat, lng] = coords[i]
    const d = distanciaKm(punto, { lat, lng })
    if (d < mejorDist) { mejorDist = d; indiceCercano = i }
  }
  const distanciaRecorridaKm = acumulado[indiceCercano]
  const distanciaRestanteKm = Math.max(0, distanciaTotalKm - distanciaRecorridaKm)
  return {
    indiceCercano,
    distanciaTotalKm,
    distanciaRecorridaKm,
    distanciaRestanteKm,
    fraccionRecorrida: distanciaTotalKm > 0 ? distanciaRecorridaKm / distanciaTotalKm : 0,
  }
}

// Distancia a un SEGMENTO de la polilinea (no a un vertice suelto): proyecta el
// punto sobre la recta que forman a-b y clampea al rango [0,1] para no medir
// mas alla de los extremos del segmento. Aproximacion plana (valida a la
// escala de una calle/avenida, unos pocos km): convierte grados a km
// localmente con un factor de longitud ajustado por la latitud (los
// meridianos se acercan entre si al alejarse del ecuador).
function distanciaAPuntoEnSegmento(punto, a, b) {
  const latMedia = (a[0] + b[0]) / 2 * Math.PI / 180
  const kmPorGradoLat = 111.32
  const kmPorGradoLng = 111.32 * Math.cos(latMedia)
  const ax = a[1] * kmPorGradoLng, ay = a[0] * kmPorGradoLat
  const bx = b[1] * kmPorGradoLng, by = b[0] * kmPorGradoLat
  const px = punto.lng * kmPorGradoLng, py = punto.lat * kmPorGradoLat
  const dx = bx - ax, dy = by - ay
  const largoCuadrado = dx * dx + dy * dy
  let t = largoCuadrado > 0 ? ((px - ax) * dx + (py - ay) * dy) / largoCuadrado : 0
  t = Math.max(0, Math.min(1, t))
  const cx = ax + t * dx, cy = ay + t * dy
  return Math.hypot(px - cx, py - cy)
}

// Distancia minima de un punto a la ruta completa, usada para detectar
// desvios y disparar el reroute automatico (ver App.jsx). Antes media contra
// cada VERTICE de la polilinea por separado: en un tramo largo y recto con
// vertices espaciados (tipico de autopistas/avenidas anchas, donde TomTom no
// necesita un vertice cada pocos metros porque no hay curvas), eso podia
// marcar "desvio" a alguien que segui yendo derecho por la ruta correcta,
// simplemente porque cayo lejos de los dos vertices mas cercanos aunque
// estuviera literalmente sobre la calle entre ellos. Medir contra cada
// SEGMENTO (no cada vertice) elimina ese falso positivo sin importar que tan
// separados esten los vertices.
export function distanciaAPolilinea(punto, coords) {
  if (!coords || coords.length === 0) return Infinity
  if (coords.length === 1) return distanciaKm(punto, { lat: coords[0][0], lng: coords[0][1] })
  let min = Infinity
  for (let i = 0; i < coords.length - 1; i++) {
    const d = distanciaAPuntoEnSegmento(punto, coords[i], coords[i + 1])
    if (d < min) min = d
  }
  return min
}

export function calcularAjuste(zona, reportes) {
  let idx = ORDEN_NIVELES.indexOf(zona.nivel)
  const motivos = []
  // El modelo del backend ya incorpora clima; repetir lluvia en el navegador
  // inflaba el nivel. Para el eje vial sólo se consideran reportes viales,
  // no robo/inseguridad, que pertenecen a otra dimensión de riesgo.
  const reportesCercanos = reportes.filter((r) => (
    ['pavimento', 'corte', 'iluminacion'].includes(r.categoria)
    && distanciaKm(zona, r) <= UMBRAL_REPORTE_KM
  )).length
  if (reportesCercanos > 0 && idx < 3) { idx += 1; motivos.push(`${reportesCercanos} reporte${reportesCercanos > 1 ? 's' : ''} cerca`) }
  return { nivel: ORDEN_NIVELES[idx], subio: idx > ORDEN_NIVELES.indexOf(zona.nivel), motivos, reportesCercanos }
}

// Es franja de mayor riesgo segun la franja pasada (ver constants.js:
// FRANJA_PICO_INSEGURIDAD_MOTO / _GENERAL, cada una calibrada con la
// distribucion horaria real de su propio subtipo, no con un criterio
// generico). Maneja el caso en que la franja cruce medianoche, por si en el
// futuro se recalibra a un rango que la cruce.
export function esFranjaPicoInseguridad(horaDelDia, franja = FRANJA_PICO_INSEGURIDAD_MOTO) {
  if (horaDelDia == null) return false
  return franja.desde > franja.hasta
    ? horaDelDia >= franja.desde || horaDelDia < franja.hasta
    : horaDelDia >= franja.desde && horaDelDia < franja.hasta
}

// Ajuste de inseguridad por franja horaria de mayor riesgo (no depende de
// clima ni de reportes, esos ya se manejan aparte en calcularAjuste para
// siniestros). franja es obligatorio: cada subtipo (general/moto) tiene su
// propia franja pico calibrada con su propia distribucion horaria real (ver
// constants.js) -- una franja compartida entre los dos subtipos no calzaba
// bien con ninguno de los dos.
export function calcularAjustePorFranjaHoraria(zona, horaDelDia, franja) {
  const idxBase = ORDEN_NIVELES.indexOf(zona.nivel)
  const enFranjaPico = esFranjaPicoInseguridad(horaDelDia, franja)
  const idx = enFranjaPico && idxBase < 3 ? idxBase + 1 : idxBase
  return {
    nivel: ORDEN_NIVELES[idx],
    subio: idx > idxBase,
    enFranjaPico,
    motivos: enFranjaPico && idx > idxBase ? ['franja horaria de mayor incidencia (dato real, no heurística)'] : [],
  }
}

function itemNominatimAPunto(item) {
  return {
    lat: parseFloat(item.lat),
    lng: parseFloat(item.lon),
    label: item.display_name.split(',').slice(0, 2).join(','),
  }
}

export async function geocodificar(texto) {
  const q = encodeURIComponent(`${texto}, Buenos Aires, Argentina`)
  const url = `https://nominatim.openstreetmap.org/search?format=json&q=${q}&viewbox=${BBOX_GBA}&bounded=1&limit=1`
  const res = await fetch(url, { headers: { 'Accept-Language': 'es' } })
  const data = await res.json()
  if (!data || data.length === 0) return null
  return itemNominatimAPunto(data[0])
}

// Sugerencias en vivo mientras se escribe el origen/destino de una ruta --
// mismo geocoder (Nominatim) que ya usaba geocodificar() al confirmar la
// ruta, ahora con limit=5 en vez de 1 para armar un desplegable. Antes el
// único feedback de que "Ramos Meji" no alcanzaba para ubicar algo llegaba
// recién al tocar "Buscar ruta" -- con la lista en vivo se corrige mientras
// se escribe, sin tener que fallar primero.
// `signal` (AbortSignal) deja cancelar un pedido en vuelo cuando el usuario
// sigue tipeando: sin esto, una tecla vieja que tarda más en volver podía
// pisar el resultado de una tecla más reciente que ya volvió.
export async function buscarSugerencias(texto, { signal } = {}) {
  if (!texto || texto.trim().length < 3) return []
  const q = encodeURIComponent(`${texto}, Buenos Aires, Argentina`)
  const url = `https://nominatim.openstreetmap.org/search?format=json&q=${q}&viewbox=${BBOX_GBA}&bounded=1&limit=5`
  const res = await fetch(url, { headers: { 'Accept-Language': 'es' }, signal })
  const data = await res.json()
  if (!data || data.length === 0) return []
  return data.map(itemNominatimAPunto)
}
