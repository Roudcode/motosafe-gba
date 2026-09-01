// Hook: cuenta segundos desde que se montó el componente que lo usa
// (se usa para mostrar "hace X segundos" en indicadores de estado en vivo).

import { useState, useEffect } from 'react'

export function useSegundosDesde() {
  const [segundos, setSegundos] = useState(0)
  useEffect(() => {
    const id = setInterval(() => setSegundos((s) => s + 1), 1000)
    return () => clearInterval(id)
  }, [])
  return segundos
}
