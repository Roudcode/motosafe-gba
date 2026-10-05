import { describe, it, expect } from 'vitest'
import { calcularAjuste, calcularRumbo, calcularProgresoRuta, distanciaAPolilinea, distanciaKm, buscarSugerencias } from './geoRiesgo'

describe('calcularAjuste', () => {
  it('solo aplica reportes viales al eje de siniestros', () => {
    const zona = { lat: -34.6, lng: -58.4, nivel: 'medio' }
    const ajuste = calcularAjuste(zona, [
      { lat: -34.6, lng: -58.4, categoria: 'robo' },
      { lat: -34.6, lng: -58.4, categoria: 'pavimento' },
    ])
    expect(ajuste.nivel).toBe('alto')
    expect(ajuste.reportesCercanos).toBe(1)
  })
})

// El ajuste de inseguridad por franja horaria (esFranjaPicoInseguridad y
// calcularAjustePorFranjaHoraria, que vivian y se testeaban acá) se migró al
// backend -- la cobertura equivalente ahora está en
// backend/tests/test_main.py (test_hotspots_inseguridad_en_franja_pico_*,
// test_hotspots_inseguridad_fuera_de_franja_pico_*,
// test_hotspots_inseguridad_moto_usa_su_propia_franja_*,
// test_hotspots_inseguridad_ajuste_horario_y_reciente_se_apilan). Ver el
// comentario largo en utils/riesgoRuta.js (unificarZonasInseguridad) para
// el motivo de la migración.

describe('calcularRumbo', () => {
  it('da 0 (norte) cuando el movimiento es puro hacia el norte', () => {
    const rumbo = calcularRumbo({ lat: -34.60, lng: -58.40 }, { lat: -34.50, lng: -58.40 })
    expect(rumbo).toBeCloseTo(0, 0)
  })

  it('da 180 (sur) cuando el movimiento es puro hacia el sur', () => {
    const rumbo = calcularRumbo({ lat: -34.50, lng: -58.40 }, { lat: -34.60, lng: -58.40 })
    expect(rumbo).toBeCloseTo(180, 0)
  })

  it('da 90 (este) cuando el movimiento es puro hacia el este', () => {
    const rumbo = calcularRumbo({ lat: -34.60, lng: -58.50 }, { lat: -34.60, lng: -58.40 })
    expect(rumbo).toBeCloseTo(90, 0)
  })

  it('da 270 (oeste) cuando el movimiento es puro hacia el oeste', () => {
    const rumbo = calcularRumbo({ lat: -34.60, lng: -58.40 }, { lat: -34.60, lng: -58.50 })
    expect(rumbo).toBeCloseTo(270, 0)
  })

  it('siempre devuelve un valor normalizado entre 0 y 360', () => {
    const rumbo = calcularRumbo({ lat: -34.60, lng: -58.40 }, { lat: -34.59, lng: -58.41 })
    expect(rumbo).toBeGreaterThanOrEqual(0)
    expect(rumbo).toBeLessThan(360)
  })
})

describe('calcularProgresoRuta', () => {
  // Polilínea recta norte-sur de 3 tramos iguales (cada uno ~1.11 km, un
  // centésimo de grado de latitud en el ecuador de distancias).
  const RUTA_RECTA = [
    [-34.60, -58.40],
    [-34.59, -58.40],
    [-34.58, -58.40],
    [-34.57, -58.40],
  ]

  it('en el punto de partida, la distancia recorrida es 0 y la restante es el total', () => {
    const p = calcularProgresoRuta({ lat: -34.60, lng: -58.40 }, RUTA_RECTA)
    expect(p.indiceCercano).toBe(0)
    expect(p.distanciaRecorridaKm).toBeCloseTo(0, 3)
    expect(p.distanciaRestanteKm).toBeCloseTo(p.distanciaTotalKm, 3)
    expect(p.fraccionRecorrida).toBeCloseTo(0, 3)
  })

  it('en el punto de llegada, la distancia restante es 0', () => {
    const p = calcularProgresoRuta({ lat: -34.57, lng: -58.40 }, RUTA_RECTA)
    expect(p.indiceCercano).toBe(RUTA_RECTA.length - 1)
    expect(p.distanciaRestanteKm).toBeCloseTo(0, 3)
    expect(p.fraccionRecorrida).toBeCloseTo(1, 3)
  })

  it('en el vértice intermedio, la fracción recorrida refleja esa posición sobre 3 tramos iguales (1/3)', () => {
    // RUTA_RECTA tiene 4 vértices (3 tramos iguales) -- el vértice de índice
    // 1 no es la mitad del recorrido, es un tercio. La cuenta real (no la
    // mitad "a ojo") es la que valida que el cálculo de tramos acumulados
    // está bien, no solo el caso trivial de los extremos.
    const p = calcularProgresoRuta({ lat: -34.59, lng: -58.40 }, RUTA_RECTA)
    expect(p.indiceCercano).toBe(1)
    expect(p.fraccionRecorrida).toBeCloseTo(1 / 3, 1)
    expect(p.distanciaRestanteKm).toBeCloseTo(p.distanciaRecorridaKm * 2, 1)
  })

  it('avanza de forma continua dentro de un tramo largo, sin saltar al vértice siguiente', () => {
    const p = calcularProgresoRuta({ lat: -34.595, lng: -58.40 }, RUTA_RECTA)
    expect(p.fraccionRecorrida).toBeCloseTo(1 / 6, 1)
    expect(p.distanciaRecorridaKm).toBeGreaterThan(0)
  })

  it('recorrida + restante siempre suman el total', () => {
    const p = calcularProgresoRuta({ lat: -34.583, lng: -58.401 }, RUTA_RECTA)
    expect(p.distanciaRecorridaKm + p.distanciaRestanteKm).toBeCloseTo(p.distanciaTotalKm, 3)
  })

  it('devuelve ceros si no hay coords suficientes o falta el punto', () => {
    expect(calcularProgresoRuta(null, RUTA_RECTA).distanciaTotalKm).toBe(0)
    expect(calcularProgresoRuta({ lat: -34.6, lng: -58.4 }, [[-34.6, -58.4]]).distanciaTotalKm).toBe(0)
  })
})

describe('distanciaAPolilinea', () => {
  it('da 0 para un punto que esta exactamente sobre un vertice', () => {
    const coords = [[-34.60, -58.40], [-34.50, -58.40]]
    expect(distanciaAPolilinea({ lat: -34.60, lng: -58.40 }, coords)).toBeCloseTo(0, 6)
  })

  // Este es el caso que motivo el cambio de "distancia al vertice mas cercano"
  // a "distancia al segmento mas cercano": en un tramo largo y recto (pocos
  // vertices, tipico de una avenida/autopista sin curvas), un punto que sigue
  // yendo derecho por la ruta correcta puede caer lejos de los DOS vertices
  // que lo encierran aunque este literalmente sobre la calle entre ellos.
  it('da ~0 para un punto sobre la mitad de un tramo largo, aunque este lejos de ambos vertices', () => {
    // Tramo recto norte-sur de ~11 km (0.1 grado de latitud). El punto medio
    // esta a ~5.5 km de cada vertice -- si se midiera contra vertices sueltos
    // (la implementacion vieja) esto daria ~5.5 km de "desvio" y dispararia
    // un reroute innecesario a alguien que nunca se fue de la ruta.
    const coords = [[-34.60, -58.40], [-34.50, -58.40]]
    const puntoMedio = { lat: -34.55, lng: -58.40 }
    expect(distanciaAPolilinea(puntoMedio, coords)).toBeLessThan(0.01)
  })

  it('para un punto realmente desviado, la distancia se acerca a la distancia perpendicular real', () => {
    const coords = [[-34.60, -58.40], [-34.50, -58.40]]
    // ~1km al este del punto medio del tramo (a esta latitud, 1 grado de
    // longitud son ~92 km, entonces 1km son unos 0.0109 grados).
    const puntoDesviado = { lat: -34.55, lng: -58.40 + 0.0109 }
    const d = distanciaAPolilinea(puntoDesviado, coords)
    expect(d).toBeGreaterThan(0.9)
    expect(d).toBeLessThan(1.1)
  })

  it('nunca es mayor que la distancia al vertice mas cercano (el segmento como maximo iguala eso)', () => {
    const coords = [[-34.60, -58.40], [-34.55, -58.42], [-34.50, -58.40]]
    const punto = { lat: -34.52, lng: -58.35 }
    const dSegmento = distanciaAPolilinea(punto, coords)
    const dVerticeMasCercano = Math.min(...coords.map(([lat, lng]) => distanciaKm(punto, { lat, lng })))
    expect(dSegmento).toBeLessThanOrEqual(dVerticeMasCercano + 1e-9)
  })

  it('con una sola coordenada, devuelve la distancia directa a ese punto', () => {
    const d = distanciaAPolilinea({ lat: -34.60, lng: -58.40 }, [[-34.61, -58.40]])
    expect(d).toBeCloseTo(distanciaKm({ lat: -34.60, lng: -58.40 }, { lat: -34.61, lng: -58.40 }), 6)
  })

  it('sin coordenadas, devuelve Infinity', () => {
    expect(distanciaAPolilinea({ lat: -34.60, lng: -58.40 }, [])).toBe(Infinity)
  })
})

describe('buscarSugerencias', () => {
  it('no pega contra la red con menos de 3 caracteres (evita un pedido por cada tecla al empezar a escribir)', async () => {
    expect(await buscarSugerencias('')).toEqual([])
    expect(await buscarSugerencias('  ')).toEqual([])
    expect(await buscarSugerencias('ab')).toEqual([])
  })
})
