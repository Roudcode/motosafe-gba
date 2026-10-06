// Hook: búsqueda de lugares con sugerencias (origen, destino y barra de
// búsqueda). Sugiere mientras se escribe: a los 350 ms sin teclear pide
// resultados al backend (/lugares, que consulta TomTom con la clave del
// servidor y cachea la respuesta). Enter o el botón buscan al instante.
//
// `texto`: lo que hay en el campo. Pasar '' desactiva las sugerencias (por
// ejemplo cuando el campo ya tiene un punto elegido).
// `buscar(texto)`: pide resultados ahora. Cancela el pedido anterior si lo había.
// `limpiar()`: descarta resultados y cancela el pedido en vuelo.
//
// Antes (SES-079) solo buscaba con Enter, porque autocompletar contra Nominatim
// lo prohíbe su política. Con TomTom desde el backend, las sugerencias sí son
// válidas (SES-090).
import { useState, useRef, useCallback, useEffect } from 'react'
import { buscarSugerencias } from '../utils/geoRiesgo'

const DEMORA_SUGERENCIAS_MS = 350

export function useBusquedaDireccion(texto = '') {
  const [resultados, setResultados] = useState([])
  const [buscando, setBuscando] = useState(false)
  const [buscada, setBuscada] = useState(false)
  const [error, setError] = useState(false)
  const abortRef = useRef(null)

  const limpiar = useCallback(() => {
    abortRef.current?.abort()
    setResultados([])
    setBuscando(false)
    setBuscada(false)
    setError(false)
  }, [])

  const buscar = useCallback(async (consulta) => {
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller
    setBuscando(true)
    setResultados([])
    setBuscada(false)
    setError(false)
    try {
      const encontrados = await buscarSugerencias(consulta, { signal: controller.signal })
      if (controller.signal.aborted) return
      setResultados(encontrados)
      setBuscada(true)
    } catch (err) {
      if (err.name !== 'AbortError' && !controller.signal.aborted) setError(true)
    } finally {
      if (!controller.signal.aborted) setBuscando(false)
    }
  }, [])

  // Sugerencias mientras se escribe: espera a que el usuario deje de teclear.
  useEffect(() => {
    if (!texto || texto.trim().length < 3) return undefined
    const id = setTimeout(() => buscar(texto), DEMORA_SUGERENCIAS_MS)
    return () => clearTimeout(id)
  }, [texto, buscar])

  return { resultados, buscando, buscada, error, buscar, limpiar }
}
