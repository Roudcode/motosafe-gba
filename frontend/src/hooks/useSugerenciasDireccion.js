// Hook: sugerencias en vivo mientras se escribe una dirección (origen o
// destino de una ruta). Antes el único feedback de que el geocoder no iba a
// poder ubicar lo escrito llegaba recién al tocar "Buscar ruta" -- con esto
// se corrige mientras se escribe, sin tener que fallar primero.
//
// `texto`: lo que el usuario está tipeando en el campo.
// `yaResuelto`: true cuando el campo ya tiene un punto confirmado (elegido
// de una sugerencia, marcado en el mapa, o "mi ubicación") -- en ese caso no
// tiene sentido seguir pidiendo sugerencias contra lo que ya se resolvió.
//
// Debounce de 400ms: menos que eso y cada tecla dispara un pedido a
// Nominatim (que es un servicio público compartido, no propio -- pegarle una
// vez por tecla es un mal uso). Un AbortController cancela el pedido anterior
// cuando llega una tecla nueva antes de que responda, para que una respuesta
// vieja que tarda no pise el resultado de una búsqueda más reciente.
import { useState, useEffect, useRef } from 'react'
import { buscarSugerencias } from '../utils/geoRiesgo'

const DEBOUNCE_MS = 400

export function useSugerenciasDireccion(texto, yaResuelto) {
  const [sugerencias, setSugerencias] = useState([])
  const [buscando, setBuscando] = useState(false)
  const abortRef = useRef(null)

  useEffect(() => {
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller
    // Los dos casos disparan el setState desde un callback (setTimeout), no
    // en el cuerpo del efecto en sí -- lo pide el linter (set-state-in-effect)
    // para no encadenar renders sincrónicos, y de paso mantiene un solo
    // patrón para las dos ramas en vez de una sincrónica y otra async.
    if (yaResuelto || !texto || texto.trim().length < 3) {
      const id = setTimeout(() => { setSugerencias([]); setBuscando(false) }, 0)
      return () => clearTimeout(id)
    }
    const id = setTimeout(() => {
      setBuscando(true)
      buscarSugerencias(texto, { signal: controller.signal })
        .then((resultados) => { setSugerencias(resultados); setBuscando(false) })
        .catch((err) => {
          if (err.name !== 'AbortError') setBuscando(false)
        })
    }, DEBOUNCE_MS)
    return () => { clearTimeout(id); controller.abort() }
  }, [texto, yaResuelto])

  return { sugerencias, buscando, limpiar: () => setSugerencias([]) }
}
