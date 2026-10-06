import { createContext, useContext } from 'react'

// Sesión de LoginGate para el resto de la app. Vale null cuando no hay login
// (AUTH_HABILITADO=false), así que el menú no muestra «Cerrar sesión».
export const SesionContext = createContext(null)

export function useSesion() {
  return useContext(SesionContext)
}
