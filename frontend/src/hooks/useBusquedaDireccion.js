// Hook: búsqueda de una dirección a pedido del usuario (Enter o botón de
// buscar). Un solo pedido a Nominatim por cada búsqueda confirmada; nunca
// mientras se escribe.
//
// Antes (useSugerenciasDireccion) pedía sugerencias en cada pausa de tipeo.
// Eso es autocompletado, y la política de uso de Nominatim lo prohíbe
// (docs/datos/FICHAS_FUENTES.md, A18). Esta versión deja al usuario
// confirmar la búsqueda y elegir entre los resultados.
//
// `buscar(texto)`: lanza el pedido. Si había uno en vuelo, lo cancela para
// que una respuesta vieja no pise la nueva.
// `limpiar()`: descarta resultados y cancela el pedido en vuelo (al editar el
// campo o al elegir un resultado).
import { useState, useRef } from 'react'
import { buscarSugerencias } from '../utils/geoRiesgo'

export function useBusquedaDireccion() {
  const [resultados, setResultados] = useState([])
  const [buscando, setBuscando] = useState(false)
  const [buscada, setBuscada] = useState(false)
  const [error, setError] = useState(false)
  const abortRef = useRef(null)

  const limpiar = () => {
    abortRef.current?.abort()
    setResultados([])
    setBuscando(false)
    setBuscada(false)
    setError(false)
  }

  const buscar = async (texto) => {
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller
    setBuscando(true)
    setResultados([])
    setBuscada(false)
    setError(false)
    try {
      const encontrados = await buscarSugerencias(texto, { signal: controller.signal })
      if (controller.signal.aborted) return
      setResultados(encontrados)
      setBuscada(true)
    } catch (err) {
      if (err.name !== 'AbortError' && !controller.signal.aborted) setError(true)
    } finally {
      if (!controller.signal.aborted) setBuscando(false)
    }
  }

  return { resultados, buscando, buscada, error, buscar, limpiar }
}
