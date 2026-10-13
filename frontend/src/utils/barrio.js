// Resuelve el barrio real de un punto contra /lugares/reversa (TomTom, ver
// backend/main.py), con una cache compartida a nivel de módulo -- sobrevive
// a que el portal de Actividad se cierre y se vuelva a abrir, así que no se
// vuelve a pedir el mismo barrio dos veces en la misma sesión.
//
// A propósito en una cola secuencial con una pausa chica entre pedidos, no
// todos en paralelo: un feed con decenas de notas en la misma cuadra ya
// cae en la misma clave redondeada (ver REDONDEO), así que en la práctica
// termina siendo un puñado de pedidos reales, pero igual se pacean para no
// mandar una ráfaga de 50 pedidos simultáneos a TomTom apenas se abre el
// portal.
import { API_URL } from '../constants'

const REDONDEO = 3 // ~100 m -- mismo redondeo que usa la cache del backend
// 300ms, no menos: el backend limita este endpoint a 300/min (ver
// main.py) -- a 300ms por pedido el cliente nunca se acerca a ese techo
// aunque el feed completo tenga cientos de puntos distintos sin cachear.
const PAUSA_ENTRE_PEDIDOS_MS = 300

const cache = new Map() // clave -> { estado: 'cargando' | 'listo', barrio, esperando: [] }
let colaPendiente = Promise.resolve()

function claveDe(lat, lng) {
  return `${lat.toFixed(REDONDEO)},${lng.toFixed(REDONDEO)}`
}

// callback(barrio: string|null) -- se llama una sola vez cuando se resuelve
// (ya, si estaba en cache; en su turno de la cola, si no).
export function resolverBarrio(lat, lng, callback) {
  const clave = claveDe(lat, lng)
  const entrada = cache.get(clave)
  if (entrada?.estado === 'listo') { callback(entrada.barrio); return }
  if (entrada) { entrada.esperando.push(callback); return }
  const nueva = { estado: 'cargando', barrio: null, esperando: [callback] }
  cache.set(clave, nueva)
  colaPendiente = colaPendiente
    .then(() => new Promise((resolve) => setTimeout(resolve, PAUSA_ENTRE_PEDIDOS_MS)))
    .then(() => fetch(`${API_URL}/lugares/reversa?lat=${lat}&lng=${lng}`, { credentials: 'include' }))
    .then((r) => (r.ok ? r.json() : { barrio: null }))
    .catch(() => ({ barrio: null }))
    .then((datos) => {
      nueva.estado = 'listo'
      nueva.barrio = datos.barrio || null
      nueva.esperando.forEach((cb) => cb(nueva.barrio))
      nueva.esperando = []
    })
}
