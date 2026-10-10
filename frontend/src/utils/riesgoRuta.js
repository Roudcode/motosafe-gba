// Unificación de los dos ejes de riesgo (siniestros de moto predichos por el
// modelo e inseguridad histórica del GCBA) y cálculo del score de cada ruta.
// Extraído de App.jsx para poder testearlo sin renderizar componentes: son
// funciones puras sobre datos planos, sin estado de React ni efectos.

import { ORDEN_NIVELES, PESO_RIESGO } from '../constants'
import { distanciaAPolilinea, distanciaKm } from './geoRiesgo'

// Pasa los hotspots de inseguridad (general y moto, tal como los devuelve el
// backend) a la misma forma que usan las zonas de siniestro: lat/lng/nivel.
//
// El ajuste por franja horaria de mayor riesgo (antes se calculaba ACA, en
// el navegador, con FRANJA_PICO_INSEGURIDAD_GENERAL/_MOTO y
// calcularAjustePorFranjaHoraria -- ver historial de este archivo) se migró
// al backend (ver FRANJA_PICO_INSEGURIDAD y _aplicar_ajuste_horario en
// backend/main.py), mismo lugar donde ya vive el ajuste por reportes
// recientes de esta misma capa. Motivo: tenerlo en los dos lados a la vez
// hubiera significado DOS calibraciones independientes que mantener
// sincronizadas a mano, y un bug real de doble ajuste (el backend sube un
// escalón, el frontend volvía a subirlo encima) que no se nota mirando
// solo el nivel final. nivel_riesgo que llega acá ya es el final (base +
// reportes + horario); esta función solo le da forma, no vuelve a tocarlo
// -- ajustadoPorHorario/motivoAjusteHorario y ajustadoPorReciente/
// motivoAjuste se pasan tal cual para que la UI pueda explicar el por qué
// sin recalcular nada de este lado.
export function unificarZonasInseguridad(inseguridadGeneral, inseguridadMoto) {
  return [
    ...inseguridadGeneral.map((h) => ({
      id: `insg-general-${h.id}`,
      lat: h.latitud,
      lng: h.longitud,
      nivel: h.nivel_riesgo,
      tipoRiesgo: 'inseguridad',
      subtipoInseguridad: 'general',
      nombre: `Zona de inseguridad: ${h.cantidad_delitos} delitos (${h.tipo_delito_moda || 'varios'})`,
      ajustadoPorHorario: h.ajustado_por_horario ?? false,
      motivoAjusteHorario: h.motivo_ajuste_horario ?? null,
      ajustadoPorReciente: h.ajustado_por_reciente ?? false,
      motivoAjuste: h.motivo_ajuste ?? null,
    })),
    ...inseguridadMoto.map((h) => ({
      id: `insg-moto-${h.id}`,
      lat: h.latitud,
      lng: h.longitud,
      nivel: h.nivel_riesgo,
      tipoRiesgo: 'inseguridad',
      subtipoInseguridad: 'moto',
      nombre: `Zona de robos con moto: ${h.cantidad_delitos} hechos`,
      ajustadoPorHorario: h.ajustado_por_horario ?? false,
      motivoAjusteHorario: h.motivo_ajuste_horario ?? null,
      ajustadoPorReciente: h.ajustado_por_reciente ?? false,
      motivoAjuste: h.motivo_ajuste ?? null,
    })),
  ]
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
// a menos de umbralCruceKm de su trazado. Cada zona devuelta trae además
// distanciaSegmentoKm (A11): la distancia real al punto más cercano del
// trazado, no solo si pasó o no el umbral -- "cruza a 80m" y "cruza a 580m"
// hoy son indistinguibles para quien usa la app, aunque la incertidumbre de
// cuál segmento exacto corresponde a la zona es muy distinta en cada caso.
export function calcularZonasCruzadasPorRuta(rutasCalculadas, zonasRiesgoTodas, umbralCruceKm) {
  return rutasCalculadas.map((r) => zonasRiesgoTodas
    .map((z) => ({ zona: z, distanciaSegmentoKm: distanciaAPolilinea(z, r.coords) }))
    .filter(({ distanciaSegmentoKm }) => distanciaSegmentoKm <= umbralCruceKm)
    .map(({ zona, distanciaSegmentoKm }) => ({ ...zona, distanciaSegmentoKm })))
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

// Cobertura separada por procedencia. Mezclar puntos de siniestros y delitos
// puede hacer parecer cubierto un tramo para el que sólo existe una de las dos
// fuentes. `null` significa que esa fuente no estuvo disponible, distinto de
// 0 (fuente disponible pero sin puntos cerca del trazado).
export function calcularCoberturaPorFuente(rutasCalculadas, zonasRiesgoTodas, umbralKm) {
  const fuentes = ['siniestro', 'inseguridad']
  return rutasCalculadas.map((ruta) => Object.fromEntries(fuentes.map((fuente) => {
    const zonas = zonasRiesgoTodas.filter((zona) => zona.tipoRiesgo === fuente)
    if (!zonas.length) return [fuente, null]
    const puntos = ruta.coords || []
    if (!puntos.length) return [fuente, 0]
    const muestreados = puntos.length > 120 ? puntos.filter((_, i) => i % Math.ceil(puntos.length / 120) === 0) : puntos
    const cubiertos = muestreados.filter(([lat, lng]) =>
      zonas.some((zona) => distanciaKm({ lat, lng }, zona) <= umbralKm)
    ).length
    return [fuente, cubiertos / muestreados.length]
  })))
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

export function calcularRutasConScore(rutasCalculadas, zonasCruzadasPorRuta, coberturaPorRuta = [], coberturaPorFuente = []) {
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
      // La recomendación de menor exposición exige cobertura del eje histórico
      // de siniestros. La capa de inseguridad se informa aparte y no puede
      // reemplazarla, porque responde otra pregunta.
      coberturaRegistrada: coberturaPorFuente[i]?.siniestro ?? coberturaPorRuta[i] ?? 0,
      coberturaPorFuente: coberturaPorFuente[i] || { siniestro: null, inseguridad: null },
      nivelMaximo,
    }
  })

  const scores = conScore.map((r) => r.riesgo)
  return conScore.map((r, i) => ({ ...r, nivelRelativo: nivelRelativoEnLote(r.riesgo, i, scores) }))
}
