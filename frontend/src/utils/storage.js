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
