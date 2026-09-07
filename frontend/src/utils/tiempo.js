// Utilidades de tiempo relativo para los reportes colaborativos: cuanto hace que
// se creo un reporte ("hace 12 min") y que tan opaco se debe ver en el mapa segun
// su antiguedad relativa a la vigencia de su categoria. Mas fresco = mas solido,
// mas cerca de vencer = mas transparente (nunca desaparece del todo por opacidad:
// eso lo decide el backend dejando de devolverlo cuando vence de verdad).

export function formatearAntiguedad(fechaIso, ahoraMs) {
  const diffMin = Math.floor((ahoraMs - new Date(fechaIso).getTime()) / 60000)
  if (diffMin < 1) return 'recién'
  if (diffMin < 60) return `hace ${diffMin} min`
  const horas = Math.floor(diffMin / 60)
  if (horas < 24) return `hace ${horas}h`
  const dias = Math.floor(horas / 24)
  return `hace ${dias}d`
}

export function opacidadPorAntiguedad(fechaIso, vigenciaHoras, ahoraMs) {
  const edadHoras = (ahoraMs - new Date(fechaIso).getTime()) / 3600000
  const fraccion = Math.min(Math.max(edadHoras / vigenciaHoras, 0), 1)
  return 1 - fraccion * 0.65
}

export function esReciente(fechaIso, ahoraMs, minutos = 15) {
  return (ahoraMs - new Date(fechaIso).getTime()) / 60000 <= minutos
}
