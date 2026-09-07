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
