// Unificación de los dos ejes de riesgo (siniestros de moto predichos por el
// modelo e inseguridad histórica del GCBA) y cálculo del score de cada ruta.
// Extraído de App.jsx para poder testearlo sin renderizar componentes: son
// funciones puras sobre datos planos, sin estado de React ni efectos.

import { ORDEN_NIVELES, PESO_RIESGO } from '../constants'
import { distanciaAPolilinea, calcularAjusteNocturno } from './geoRiesgo'

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
  // Se pisa el nivel base con el ajustado (heuristica nocturna, ver
  // calcularAjusteNocturno) pero se guarda el ajuste aparte para poder
  // mostrar el motivo en la UI si hace falta, igual que hace calcularAjuste
  // con las zonas de siniestro.
  return zonas.map((z) => {
    const ajusteNocturno = calcularAjusteNocturno(z, horaDelDia)
    return { ...z, nivel: ajusteNocturno.nivel, ajusteNocturno }
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

// Arma, para cada ruta, el score total (suma de PESO_RIESGO de todo lo que
// cruza) desglosado por eje, más el nivel más grave que atraviesa
// (nivelMaximo), que es lo que se muestra como etiqueta interpretable en vez
// del puntaje crudo.
export function calcularRutasConScore(rutasCalculadas, zonasCruzadasPorRuta) {
  return rutasCalculadas.map((r, i) => {
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
      nivelMaximo,
    }
  })
}
