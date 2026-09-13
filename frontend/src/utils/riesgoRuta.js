// Unificación de los dos ejes de riesgo (siniestros de moto predichos por el
// modelo e inseguridad histórica del GCBA) y cálculo del score de cada ruta.
// Extraído de App.jsx para poder testearlo sin renderizar componentes: son
// funciones puras sobre datos planos, sin estado de React ni efectos.

import { ORDEN_NIVELES, PESO_RIESGO, FRANJA_PICO_INSEGURIDAD_GENERAL, FRANJA_PICO_INSEGURIDAD_MOTO } from '../constants'
import { distanciaAPolilinea, distanciaKm, calcularAjustePorFranjaHoraria } from './geoRiesgo'

// Pasa los hotspots de inseguridad (general y moto, tal como los devuelve el
// backend) a la misma forma que usan las zonas de siniestro: lat/lng/nivel.
// horaDelDia es opcional (0-23): si no se pasa, no se aplica ningun ajuste
// nocturno y el nivel queda tal como viene del backend (compatibilidad con
// los tests existentes y con cualquier caller que todavia no la pase).
export function unificarZonasInseguridad(inseguridadGeneral, inseguridadMoto, horaDelDia = null) {
  const zonas = [
    ...inseguridadGeneral.map((h) => ({
      id: `insg-general-${h.id}`,
      lat: h.latitud,
      lng: h.longitud,
      nivel: h.nivel_riesgo,
      tipoRiesgo: 'inseguridad',
      subtipoInseguridad: 'general',
      nombre: `Zona de inseguridad: ${h.cantidad_delitos} delitos (${h.tipo_delito_moda || 'varios'})`,
    })),
    ...inseguridadMoto.map((h) => ({
      id: `insg-moto-${h.id}`,
      lat: h.latitud,
      lng: h.longitud,
      nivel: h.nivel_riesgo,
      tipoRiesgo: 'inseguridad',
      subtipoInseguridad: 'moto',
      nombre: `Zona de robos con moto: ${h.cantidad_delitos} hechos`,
    })),
  ]
  if (horaDelDia == null) return zonas
  // Se pisa el nivel base con el ajustado (franja horaria de mayor riesgo,
  // calibrada con dato real, DISTINTA por subtipo -- ver constants.js y
  // calcularAjustePorFranjaHoraria) pero se guarda el ajuste aparte para
  // poder mostrar el motivo en la UI si hace falta, igual que hace
  // calcularAjuste con las zonas de siniestro.
  return zonas.map((z) => {
    const franja = z.subtipoInseguridad === 'moto' ? FRANJA_PICO_INSEGURIDAD_MOTO : FRANJA_PICO_INSEGURIDAD_GENERAL
    const ajusteHorario = calcularAjustePorFranjaHoraria(z, horaDelDia, franja)
    return { ...z, nivel: ajusteHorario.nivel, ajusteHorario }
  })
}

// Junta siniestros (con ajuste de clima/reportes ya aplicado) e inseguridad
// en un solo listado con la misma forma (lat/lng/nivel/tipoRiesgo), para que
// el cruce con rutas y las alertas en viaje no tengan que conocer la
// diferencia entre ambos. nivel ya viene en la misma escala ordinal en los
// dos casos (percentiles calculados dentro de cada dataset por separado),
// así que sumar PESO_RIESGO entre tipos es válido — sumar cantidades crudas
// de siniestros y delitos no lo sería, porque son magnitudes distintas.
export function unificarZonasRiesgo(zonasAjustadas, zonasInseguridadUnificadas) {
  return [
    ...zonasAjustadas.map((z) => ({ ...z, nivel: z.ajuste.nivel, tipoRiesgo: 'siniestro' })),
    ...zonasInseguridadUnificadas,
  ]
}

// Para cada ruta calculada, las zonas de riesgo (de cualquier eje) que pasan
// a menos de umbralCruceKm de su trazado.
export function calcularZonasCruzadasPorRuta(rutasCalculadas, zonasRiesgoTodas, umbralCruceKm) {
  return rutasCalculadas.map((r) => zonasRiesgoTodas.filter((z) => distanciaAPolilinea(z, r.coords) <= umbralCruceKm))
}

// Proporción de vértices del trazado que quedan cerca de alguna zona con dato
// registrado. No es una medida de seguridad: sirve para no interpretar la
// ausencia de zonas como exposición baja cuando el recorrido queda fuera del
// universo disponible.
export function calcularCoberturaRegistrada(rutasCalculadas, zonasRiesgoTodas, umbralKm) {
  return rutasCalculadas.map((ruta) => {
    const puntos = ruta.coords || []
    if (!puntos.length || !zonasRiesgoTodas.length) return 0
    const muestreados = puntos.length > 120 ? puntos.filter((_, i) => i % Math.ceil(puntos.length / 120) === 0) : puntos
    const cubiertos = muestreados.filter(([lat, lng]) =>
      zonasRiesgoTodas.some((zona) => distanciaKm({ lat, lng }, zona) <= umbralKm)
    ).length
    return cubiertos / muestreados.length
  })
}

// Arma, para cada ruta, el score total (suma de PESO_RIESGO de todo lo que
// cruza) desglosado por eje, más el nivel más grave que atraviesa
// (nivelMaximo) y el nivel relativo a las demás alternativas de este mismo
// pedido (nivelRelativo).
//
// nivelMaximo se guarda pero YA NO se usa para la etiqueta que ve el usuario:
// en una ciudad densa, una ruta de pocos km cruza decenas de zonas de riesgo
// de tres fuentes distintas (siniestros del modelo + inseguridad general +
// inseguridad moto), cada una con su propio 5% "critico". Con esa cantidad de
// cruces, la probabilidad de tocar AL MENOS UNA zona critica en algun punto
// del trayecto es alta para practicamente cualquier ruta -- asi que "cruzo
// una critica" deja de servir para comparar rutas entre si (mismo sintoma que
// niveles_relativos_desde_matriz en el backend, un nivel mas arriba: ahi el
// problema era "casi todo hotspot sale alto", aca es "casi toda ruta cruza
// un hotspot alto"). Lo que de verdad le importa a quien elige es cual ruta
// es MAS o MENOS riesgosa que las otras que se le estan ofreciendo para el
// mismo viaje, no si tuvo la mala suerte de pasar a 30m de la unica zona
// critica de todo el trayecto.
//
// nivelRelativo resuelve eso: ordena las rutas de este pedido por su score
// total y ubica a cada una segun su posicion relativa (la de menor score es
// 'bajo', la de mayor 'alto'), en vez de por un corte absoluto. Solo escala a
// 'critico' cuando la peor ruta no es apenas la peor de un lote parejo, sino
// que se destaca claramente MAL respecto a las otras opciones ofrecidas (se
// compara contra el promedio de las DEMAS, sin contarse a si misma, para que
// la comparacion no se diluya con el propio valor alto) -- ahi si vale la
// alarma extra, en vez de simplemente "es la peor de tres opciones similares".
function nivelRelativoEnLote(score, indice, scoresDelLote) {
  if (score === 0) return 'bajo'
  if (scoresDelLote.length <= 1) return score <= 4 ? 'medio' : 'alto'

  // Si todas las alternativas empatan con exposición positiva, ninguna es
  // realmente "baja" respecto de las demás. indexOf antes daba rango cero a
  // todas y terminaba etiquetándolas como bajo por accidente.
  if (new Set(scoresDelLote).size === 1) return score <= 4 ? 'medio' : 'alto'

  const ordenados = [...scoresDelLote].sort((a, b) => a - b)
  const rank = ordenados.indexOf(score)
  const percentil = rank / (ordenados.length - 1)
  const esLaPeorDelLote = score === ordenados[ordenados.length - 1]

  const otros = scoresDelLote.filter((_, j) => j !== indice)
  const promedioOtros = otros.length > 0 ? otros.reduce((acc, s) => acc + s, 0) / otros.length : 0

  if (esLaPeorDelLote && promedioOtros > 0 && score >= promedioOtros * 1.4) return 'critico'
  if (percentil >= 0.6) return 'alto'
  if (percentil >= 0.3) return 'medio'
  return 'bajo'
}

export function calcularRutasConScore(rutasCalculadas, zonasCruzadasPorRuta, coberturaPorRuta = []) {
  const conScore = rutasCalculadas.map((r, i) => {
    const cruces = zonasCruzadasPorRuta[i] || []
    const crucesSiniestro = cruces.filter((z) => z.tipoRiesgo === 'siniestro')
    const crucesInseguridad = cruces.filter((z) => z.tipoRiesgo === 'inseguridad')
    const nivelMaximo = cruces.reduce(
      (peor, z) => (ORDEN_NIVELES.indexOf(z.nivel) > ORDEN_NIVELES.indexOf(peor) ? z.nivel : peor),
      'bajo'
    )
    return {
      ...r,
      riesgo: cruces.reduce((acc, z) => acc + PESO_RIESGO[z.nivel], 0),
      riesgoSiniestros: crucesSiniestro.reduce((acc, z) => acc + PESO_RIESGO[z.nivel], 0),
      riesgoInseguridad: crucesInseguridad.reduce((acc, z) => acc + PESO_RIESGO[z.nivel], 0),
      cantSiniestros: crucesSiniestro.length,
      cantInseguridad: crucesInseguridad.length,
      coberturaRegistrada: coberturaPorRuta[i] ?? 0,
      nivelMaximo,
    }
  })

  const scores = conScore.map((r) => r.riesgo)
  return conScore.map((r, i) => ({ ...r, nivelRelativo: nivelRelativoEnLote(r.riesgo, i, scores) }))
}
