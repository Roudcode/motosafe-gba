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

// Distancia legible para el cartel de navegación: en metros redondeados si es
// corta (asi se lee "150 m", no "0.15 km"), en km con un decimal si es larga
// (asi se lee "1.4 km", no "1400 m" ni, el bug real que esto reemplaza,
// "47056 m" sin separador de miles ni unidad legible).
export function formatearDistancia(km) {
  if (km < 1) return `${Math.round(km * 1000)} m`
  return `${km.toFixed(1)} km`
}

const MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']

// Período de cobertura de una capa (A10/A11/A15): "2019–2025" si cubre años
// completos, si no con mes ("mar 2023–sep 2025"). Fechas 'AAAA-MM-DD' del
// backend (/capas/cobertura); se leen como texto para no correr el día por zona horaria.
export function formatearPeriodo(desde, hasta) {
  if (!desde || !hasta) return null
  const [ad, md, dd] = desde.split('-').map(Number)
  const [ah, mh, dh] = hasta.split('-').map(Number)
  if (md === 1 && dd === 1 && mh === 12 && dh === 31) return ad === ah ? `${ad}` : `${ad}–${ah}`
  return `${MESES[md - 1]} ${ad}–${MESES[mh - 1]} ${ah}`
}

// Cuánto falta para que un reporte venza, en lenguaje corto (SES-094).
export function formatearVence(isoVencimiento, ahoraMs = Date.now()) {
  if (!isoVencimiento) return ''
  const horas = (new Date(isoVencimiento).getTime() - ahoraMs) / 3600000
  if (Number.isNaN(horas)) return ''
  if (horas <= 0) return 'ya venció'
  if (horas < 1) return 'vence en menos de 1 h'
  if (horas < 48) return `vence en ${Math.round(horas)} h`
  return `vence en ${Math.round(horas / 24)} días`
}
