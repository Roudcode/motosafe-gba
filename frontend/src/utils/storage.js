// Wrapper de lectura de localStorage con fallback silencioso: si la clave no existe
// o el JSON está corrupto, devuelve el valor por defecto en vez de romper la app.

export function cargarDeLocalStorage(clave, porDefecto) {
  try {
    const guardado = localStorage.getItem(clave)
    return guardado ? JSON.parse(guardado) : porDefecto
  } catch {
    return porDefecto
  }
}

// Contraparte de cargarDeLocalStorage: guarda con el mismo fallback
// silencioso (localStorage puede fallar por cuota llena o por estar en modo
// privado/incógnito, y eso no debería romper la app -- en el peor caso
// simplemente no queda cache para la próxima).
export function guardarEnLocalStorage(clave, valor) {
  try {
    localStorage.setItem(clave, JSON.stringify(valor))
  } catch {
    /* sin cuota o localStorage no disponible: se sigue sin cache */
  }
}

// Fallback de generación de UUID v4 para navegadores/contextos sin crypto.randomUUID
// (esa API requiere contexto seguro: https o localhost). No es criptográficamente tan
// fuerte como crypto.randomUUID, pero alcanza para un identificador de dispositivo que
// solo necesita ser único y tener formato UUID válido (el backend valida el formato).
export function generarUuidV4Fallback() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}
