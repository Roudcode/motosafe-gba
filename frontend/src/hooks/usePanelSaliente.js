import { useEffect, useState } from 'react'

// Los paneles flotantes (.panel-enter) tenían animación de entrada pero
// ninguna de salida: al cerrarse, React los desmonta en el mismo instante
// en que el estado pasa a false, así que desaparecían de golpe en vez de
// salir suave como entraron. Este hook no toca el estado que ya controla
// el resto de la app (`abierto` sigue siendo la única fuente de verdad
// para todo lo demás, ej. qué botón queda resaltado) -- solo retrasa
// cuándo deja de renderizarse el DOM del panel, lo justo para que la
// animación de salida en CSS (`.panel-exit`) termine de jugar.
//
// El cambio de estado ante un prop que cambió se hace durante el render
// comparando contra estado (no contra un ref -- el lint de hooks de este
// proyecto no permite leer/escribir refs durante el render). El timer en
// sí vive en un efecto normal: el setState que lo cierra ocurre dentro
// del callback de setTimeout, no sincrónicamente en el cuerpo del efecto.
export function usePanelSaliente(abierto, exitMs = 180) {
  const [prevAbierto, setPrevAbierto] = useState(abierto)
  const [estado, setEstado] = useState(abierto ? 'abierto' : 'cerrado')

  if (abierto !== prevAbierto) {
    setPrevAbierto(abierto)
    setEstado(abierto ? 'abierto' : 'saliendo')
  }

  useEffect(() => {
    if (estado !== 'saliendo') return undefined
    const id = setTimeout(() => setEstado('cerrado'), exitMs)
    return () => clearTimeout(id)
  }, [estado, exitMs])

  return { montado: estado !== 'cerrado', saliendo: estado === 'saliendo' }
}
