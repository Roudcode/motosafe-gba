import { describe, it, expect } from 'vitest'
import {
  unificarZonasInseguridad, unificarZonasRiesgo, calcularZonasCruzadasPorRuta, calcularCoberturaRegistrada, calcularCoberturaPorFuente, calcularRutasConScore,
  brechaCoberturaEnRecomendada,
} from './riesgoRuta'

describe('unificarZonasInseguridad', () => {
  const general = [
    { id: 1, latitud: -34.6, longitud: -58.4, nivel_riesgo: 'alto', cantidad_delitos: 40, tipo_delito_moda: 'robo' },
  ]
  const moto = [
    { id: 7, latitud: -34.61, longitud: -58.41, nivel_riesgo: 'critico', cantidad_delitos: 12, tipo_delito_moda: null },
  ]

  it('prefija los ids para que no choquen entre datasets', () => {
    const zonas = unificarZonasInseguridad(general, moto)
    expect(zonas.map((z) => z.id)).toEqual(['insg-general-1', 'insg-moto-7'])
  })

  it('marca tipoRiesgo y subtipoInseguridad correctamente para cada dataset', () => {
    const zonas = unificarZonasInseguridad(general, moto)
    expect(zonas[0]).toMatchObject({ tipoRiesgo: 'inseguridad', subtipoInseguridad: 'general', nivel: 'alto' })
    expect(zonas[1]).toMatchObject({ tipoRiesgo: 'inseguridad', subtipoInseguridad: 'moto', nivel: 'critico' })
  })

  it('copia lat/lng desde latitud/longitud (nombres de columna del backend)', () => {
    const zonas = unificarZonasInseguridad(general, moto)
    expect(zonas[0]).toMatchObject({ lat: -34.6, lng: -58.4 })
  })

  it('no rompe si falta tipo_delito_moda', () => {
    const zonas = unificarZonasInseguridad(general, moto)
    expect(zonas[1].nombre).toContain('12 hechos')
  })
})

describe('unificarZonasInseguridad pasa el ajuste del backend tal cual (no vuelve a calcularlo)', () => {
  // El ajuste por franja horaria y por reportes recientes ya vienen hechos
  // en /hotspots-inseguridad (ver FRANJA_PICO_INSEGURIDAD y
  // _aplicar_ajuste_horario/_aplicar_ajuste_riesgo en backend/main.py).
  // Esta funcion no debe recalcular nada -- solo le da forma a lo que ya
  // llego, para que no se repita el ajuste en los dos lados (ver el
  // comentario largo en riesgoRuta.js sobre por que se migro el calculo).
  const general = [
    {
      id: 1, latitud: -34.6, longitud: -58.4, nivel_riesgo: 'alto', cantidad_delitos: 40, tipo_delito_moda: 'robo',
      ajustado_por_horario: true, motivo_ajuste_horario: 'Ahora (18hs) es franja de mayor incidencia histórica de este tipo de delito (17-21hs)',
      ajustado_por_reciente: false, motivo_ajuste: null,
    },
  ]
  const moto = [
    {
      id: 7, latitud: -34.61, longitud: -58.41, nivel_riesgo: 'critico', cantidad_delitos: 12, tipo_delito_moda: null,
      ajustado_por_horario: false, motivo_ajuste_horario: null,
      ajustado_por_reciente: true, motivo_ajuste: '1 robo reportado en prensa en los últimos 7 días cerca de esta zona (más reciente: "Robo en Retiro")',
    },
  ]

  it('usa el nivel_riesgo del backend sin modificarlo', () => {
    const zonas = unificarZonasInseguridad(general, moto)
    expect(zonas[0].nivel).toBe('alto')
    expect(zonas[1].nivel).toBe('critico')
  })

  it('pasa ajustadoPorHorario/motivoAjusteHorario tal cual vienen del backend', () => {
    const zonas = unificarZonasInseguridad(general, moto)
    expect(zonas[0].ajustadoPorHorario).toBe(true)
    expect(zonas[0].motivoAjusteHorario).toContain('18hs')
    expect(zonas[1].ajustadoPorHorario).toBe(false)
    expect(zonas[1].motivoAjusteHorario).toBeNull()
  })

  it('pasa ajustadoPorReciente/motivoAjuste tal cual vienen del backend', () => {
    const zonas = unificarZonasInseguridad(general, moto)
    expect(zonas[0].ajustadoPorReciente).toBe(false)
    expect(zonas[1].ajustadoPorReciente).toBe(true)
    expect(zonas[1].motivoAjuste).toContain('Robo en Retiro')
  })

  it('no rompe si el backend todavia no manda los campos de ajuste (defaults seguros)', () => {
    const zonas = unificarZonasInseguridad(
      [{ id: 1, latitud: -34.6, longitud: -58.4, nivel_riesgo: 'bajo', cantidad_delitos: 5 }],
      []
    )
    expect(zonas[0].ajustadoPorHorario).toBe(false)
    expect(zonas[0].motivoAjusteHorario).toBeNull()
    expect(zonas[0].ajustadoPorReciente).toBe(false)
    expect(zonas[0].motivoAjuste).toBeNull()
  })
})

describe('unificarZonasRiesgo', () => {
  const zonasAjustadas = [
    { id: 's1', lat: -34.6, lng: -58.4, nombre: 'Zona A', ajuste: { nivel: 'alto', subio: true, motivos: ['lluvia actual'] } },
    { id: 's2', lat: -34.65, lng: -58.45, nombre: 'Zona B', ajuste: { nivel: 'bajo', subio: false, motivos: [] } },
  ]
  const zonasInseguridad = [
    { id: 'insg-general-1', lat: -34.61, lng: -58.41, nivel: 'critico', tipoRiesgo: 'inseguridad' },
  ]

  it('usa el nivel ya ajustado (post clima/reportes) para las zonas de siniestro, no el nivel base', () => {
    const todas = unificarZonasRiesgo(zonasAjustadas, zonasInseguridad)
    const s1 = todas.find((z) => z.id === 's1')
    expect(s1.nivel).toBe('alto')
    expect(s1.tipoRiesgo).toBe('siniestro')
  })

  it('conserva las zonas de inseguridad tal cual, sin tocarlas', () => {
    const todas = unificarZonasRiesgo(zonasAjustadas, zonasInseguridad)
    const insg = todas.find((z) => z.id === 'insg-general-1')
    expect(insg).toEqual(zonasInseguridad[0])
  })

  it('no pierde ni duplica zonas: el total es la suma de ambos ejes', () => {
    const todas = unificarZonasRiesgo(zonasAjustadas, zonasInseguridad)
    expect(todas).toHaveLength(zonasAjustadas.length + zonasInseguridad.length)
  })
})

describe('calcularZonasCruzadasPorRuta', () => {
  // Ruta recta corta cerca de Plaza de Mayo, sobre la que se prueban zonas a
  // distintas distancias conocidas.
  const ruta = { coords: [[-34.6083, -58.3712], [-34.6090, -58.3720]] }
  const zonaEncimaDeLaRuta = { id: 'z1', lat: -34.6083, lng: -58.3712, nivel: 'alto', tipoRiesgo: 'siniestro' }
  // ~1.1km al norte, bien afuera del umbral por defecto (0.6km)
  const zonaLejos = { id: 'z2', lat: -34.598, lng: -58.3712, nivel: 'critico', tipoRiesgo: 'inseguridad' }

  it('incluye una zona que está exactamente sobre un punto de la ruta', () => {
    const cruces = calcularZonasCruzadasPorRuta([ruta], [zonaEncimaDeLaRuta, zonaLejos], 0.6)
    expect(cruces[0].map((z) => z.id)).toContain('z1')
  })

  it('excluye una zona bien alejada del trazado con el umbral por defecto', () => {
    const cruces = calcularZonasCruzadasPorRuta([ruta], [zonaEncimaDeLaRuta, zonaLejos], 0.6)
    expect(cruces[0].map((z) => z.id)).not.toContain('z2')
  })

  it('incluye la zona lejana si se agranda el umbral lo suficiente', () => {
    const cruces = calcularZonasCruzadasPorRuta([ruta], [zonaEncimaDeLaRuta, zonaLejos], 1.5)
    expect(cruces[0].map((z) => z.id)).toContain('z2')
  })

  it('devuelve un array vacío por ruta si ninguna zona cruza, sin reventar', () => {
    const cruces = calcularZonasCruzadasPorRuta([ruta], [zonaLejos], 0.6)
    expect(cruces[0]).toEqual([])
  })

  it('calcula por separado para cada ruta cuando hay varias', () => {
    const otraRuta = { coords: [[-34.598, -58.3712]] }
    const cruces = calcularZonasCruzadasPorRuta([ruta, otraRuta], [zonaEncimaDeLaRuta, zonaLejos], 0.6)
    expect(cruces[0].map((z) => z.id)).toEqual(['z1'])
    expect(cruces[1].map((z) => z.id)).toEqual(['z2'])
  })

  it('A11: cada zona cruzada trae distanciaSegmentoKm, la distancia real al trazado', () => {
    const cruces = calcularZonasCruzadasPorRuta([ruta], [zonaEncimaDeLaRuta, zonaLejos], 1.5)
    const z1 = cruces[0].find((z) => z.id === 'z1')
    const z2 = cruces[0].find((z) => z.id === 'z2')
    // Zona exactamente sobre un punto de la ruta: distancia ~0.
    expect(z1.distanciaSegmentoKm).toBeCloseTo(0, 2)
    // Zona a ~1.1km: la distancia real queda registrada, no solo "cruzó".
    expect(z2.distanciaSegmentoKm).toBeGreaterThan(1)
    expect(z2.distanciaSegmentoKm).toBeLessThan(1.5)
  })

  it('A11: no muta las zonas originales (devuelve copias con el campo agregado)', () => {
    calcularZonasCruzadasPorRuta([ruta], [zonaEncimaDeLaRuta], 0.6)
    expect(zonaEncimaDeLaRuta.distanciaSegmentoKm).toBeUndefined()
  })
})

describe('calcularCoberturaRegistrada', () => {
  it('distingue trazado cercano a datos registrados de ausencia de cobertura', () => {
    const rutas = [
      { coords: [[-34.6, -58.4], [-34.601, -58.401]] },
      { coords: [[-35.2, -59.2], [-35.201, -59.201]] },
    ]
    const zonas = [{ lat: -34.6, lng: -58.4, nivel: 'alto' }]
    const [cubierta, sinCobertura] = calcularCoberturaRegistrada(rutas, zonas, 0.5)
    expect(cubierta).toBeGreaterThanOrEqual(0.5)
    expect(sinCobertura).toBe(0)
  })
})

describe('calcularCoberturaPorFuente', () => {
  it('no deja que una fuente cubra artificialmente a la otra', () => {
    const rutas = [{ coords: [[-34.6, -58.4], [-34.601, -58.401]] }]
    const zonas = [
      { lat: -34.6, lng: -58.4, tipoRiesgo: 'inseguridad' },
      { lat: -35.2, lng: -59.2, tipoRiesgo: 'siniestro' },
    ]
    const [cobertura] = calcularCoberturaPorFuente(rutas, zonas, 0.5)
    expect(cobertura.inseguridad).toBeGreaterThanOrEqual(0.5)
    expect(cobertura.siniestro).toBe(0)
  })

  it('distingue una fuente no disponible de una fuente sin cobertura', () => {
    const [cobertura] = calcularCoberturaPorFuente(
      [{ coords: [[-34.6, -58.4]] }],
      [{ lat: -34.6, lng: -58.4, tipoRiesgo: 'siniestro' }], 0.5
    )
    expect(cobertura.siniestro).toBe(1)
    expect(cobertura.inseguridad).toBeNull()
  })
})

describe('calcularRutasConScore', () => {
  const rutasCalculadas = [
    { min: 12, coords: [] },
    { min: 20, coords: [] },
  ]

  it('suma PESO_RIESGO de todas las zonas cruzadas para el score total', () => {
    const cruces = [
      [
        { id: 'a', nivel: 'alto', tipoRiesgo: 'siniestro' }, // peso 3
        { id: 'b', nivel: 'critico', tipoRiesgo: 'inseguridad' }, // peso 5
      ],
      [],
    ]
    const [ruta1] = calcularRutasConScore(rutasCalculadas, cruces)
    expect(ruta1.riesgo).toBe(8)
  })

  it('desglosa el riesgo y la cantidad por eje (siniestro vs inseguridad) por separado', () => {
    const cruces = [
      [
        { id: 'a', nivel: 'alto', tipoRiesgo: 'siniestro' },
        { id: 'b', nivel: 'medio', tipoRiesgo: 'siniestro' },
        { id: 'c', nivel: 'critico', tipoRiesgo: 'inseguridad' },
      ],
      [],
    ]
    const [ruta1] = calcularRutasConScore(rutasCalculadas, cruces)
    expect(ruta1.riesgoSiniestros).toBe(3 + 2)
    expect(ruta1.cantSiniestros).toBe(2)
    expect(ruta1.riesgoInseguridad).toBe(5)
    expect(ruta1.cantInseguridad).toBe(1)
  })

  it('nivelMaximo toma el nivel más grave cruzado, sin importar el eje ni el orden', () => {
    const cruces = [
      [
        { id: 'a', nivel: 'bajo', tipoRiesgo: 'siniestro' },
        { id: 'b', nivel: 'critico', tipoRiesgo: 'inseguridad' },
        { id: 'c', nivel: 'medio', tipoRiesgo: 'siniestro' },
      ],
      [],
    ]
    const [ruta1] = calcularRutasConScore(rutasCalculadas, cruces)
    expect(ruta1.nivelMaximo).toBe('critico')
  })

  it('una ruta sin ninguna zona cruzada da score 0 y nivelMaximo "bajo"', () => {
    const cruces = [[], []]
    const [ruta1, ruta2] = calcularRutasConScore(rutasCalculadas, cruces)
    expect(ruta1.riesgo).toBe(0)
    expect(ruta1.nivelMaximo).toBe('bajo')
    expect(ruta2.riesgo).toBe(0)
  })

  it('conserva los campos originales de la ruta (ej. min) además de los nuevos', () => {
    const cruces = [[], []]
    const [ruta1] = calcularRutasConScore(rutasCalculadas, cruces)
    expect(ruta1.min).toBe(12)
  })

  it('usa cobertura de siniestros como cobertura registrada para recomendar', () => {
    const [ruta] = calcularRutasConScore(rutasCalculadas, [[], []], [
      { siniestro: 0.4, inseguridad: 1 }, { siniestro: 1, inseguridad: 0.1 },
    ])
    expect(ruta.coberturaRegistrada).toBe(0.4)
    expect(ruta.coberturaPorFuente.inseguridad).toBe(1)
  })

  it('sin dato de siniestros, la cobertura registrada queda null -- nunca toma el valor de otra fuente', () => {
    const [ruta] = calcularRutasConScore(rutasCalculadas, [[], []], [
      { siniestro: null, inseguridad: 0.9 }, { siniestro: 1, inseguridad: 0.1 },
    ])
    expect(ruta.coberturaRegistrada).toBeNull()
  })
})

describe('calcularRutasConScore — nivelRelativo (comparativo entre alternativas, no absoluto)', () => {
  // Reproduce el caso real reportado: las tres rutas cruzan igual alguna
  // zona critica en algun punto (nivelMaximo = 'critico' para las tres, por
  // eso antes las tres etiquetaban "riesgo critico" sin diferenciarse), pero
  // sus scores totales son bien distintos entre si.
  const zonaCritica = { id: 'z', nivel: 'critico', tipoRiesgo: 'inseguridad' }

  it('con scores bien distintos, la de menor score sale "bajo" aunque las tres tengan nivelMaximo critico', () => {
    const rutasSimplificadas = [
      { min: 14, coords: [] },
      { min: 14, coords: [] },
      { min: 15, coords: [] },
    ]
    const crucesConScoresReales = [
      Array(16).fill(zonaCritica), // 80 pts
      Array(24).fill(zonaCritica), // 120 pts
      Array(13).fill(zonaCritica), // 65 pts
    ]
    const rutas = calcularRutasConScore(rutasSimplificadas, crucesConScoresReales)
    expect(rutas.every((r) => r.nivelMaximo === 'critico')).toBe(true) // el bug viejo: las tres tocan una critica
    expect(rutas[2].nivelRelativo).toBe('bajo') // la de menor score (65) es la mas segura de las tres
    expect(rutas[1].nivelRelativo).toBe('critico') // la de mayor score (120) esta bastante por encima del resto
    expect(rutas[0].riesgo).toBeLessThan(rutas[1].riesgo)
  })

  it('con una sola ruta (sin alternativa para comparar), usa un umbral absoluto razonable', () => {
    const [ruta1] = calcularRutasConScore([{ min: 10, coords: [] }], [[{ id: 'a', nivel: 'alto', tipoRiesgo: 'siniestro' }]])
    expect(ruta1.nivelRelativo).toBe('medio')
  })

  it('score 0 siempre da nivelRelativo "bajo", tenga o no alternativas', () => {
    const rutas = calcularRutasConScore(
      [{ min: 12, coords: [] }, { min: 20, coords: [] }],
      [[], [{ id: 'x', nivel: 'medio', tipoRiesgo: 'siniestro' }]]
    )
    expect(rutas[0].nivelRelativo).toBe('bajo')
  })

  it('con dos rutas de score parejo (diferencia menor al 40%), ninguna escala a critico solo por ser la peor de las dos', () => {
    const rutas = calcularRutasConScore(
      [{ min: 10, coords: [] }, { min: 11, coords: [] }],
      [
        [{ id: 'a', nivel: 'alto', tipoRiesgo: 'siniestro' }], // score 3
        [{ id: 'b', nivel: 'alto', tipoRiesgo: 'siniestro' }, { id: 'c', nivel: 'bajo', tipoRiesgo: 'siniestro' }], // score 4 (33% mas, no alcanza el 40%)
      ]
    )
    expect(rutas[1].nivelRelativo).not.toBe('critico')
  })

  it('no etiqueta como bajo alternativas empatadas que sí cruzan zonas', () => {
    const rutas = calcularRutasConScore(
      [{ min: 10, coords: [] }, { min: 11, coords: [] }],
      [[{ id: 'a', nivel: 'alto', tipoRiesgo: 'siniestro' }], [{ id: 'b', nivel: 'alto', tipoRiesgo: 'siniestro' }]]
    )
    expect(rutas.map((r) => r.nivelRelativo)).toEqual(['medio', 'medio'])
  })
})

describe('brechaCoberturaEnRecomendada (DEC-026, D03 caso 2)', () => {
  // Reproduce las coberturas reales medidas en los 4 casos de
  // docs/evidencias/2026-09-13/D03/rutas_referencia.csv para la ruta que el
  // sistema marca como "menor exposición" en cada uno -- solo el caso 2 (la
  // única con brecha real >= 20pp entre fuentes) tiene que disparar el aviso.
  const rutasCalculadas = [{ min: 1, coords: [] }]

  function rutaRecomendada(siniestro, inseguridad) {
    const [ruta] = calcularRutasConScore(rutasCalculadas, [[]], [{ siniestro, inseguridad }])
    return [ruta]
  }

  it('caso 1 (desvío, sin89%/inseg89% en la Ruta1 recomendada): sin aviso, brecha de 11pp', () => {
    expect(brechaCoberturaEnRecomendada(rutaRecomendada(1.0, 0.89), 0)).toBeNull()
  })

  it('caso 2 real (Ruta3 recomendada, siniestros 86% / inseguridad 56%): dispara el aviso', () => {
    const resultado = brechaCoberturaEnRecomendada(rutaRecomendada(0.86, 0.56), 0)
    expect(resultado).toEqual({ fuenteMenor: 'inseguridad', coberturaMenor: 0.56, coberturaMayor: 0.86 })
  })

  it('caso 3 (empate, 100%/100%): sin aviso, brecha cero', () => {
    expect(brechaCoberturaEnRecomendada(rutaRecomendada(1.0, 1.0), 0)).toBeNull()
  })

  it('caso 4 (discordancia de fuentes, Ruta2 recomendada: sin100%/inseg99%): sin aviso, brecha de 1pp', () => {
    expect(brechaCoberturaEnRecomendada(rutaRecomendada(1.0, 0.99), 0)).toBeNull()
  })

  it('no dispara si falta el dato de alguna fuente (null, no es lo mismo que cobertura baja)', () => {
    expect(brechaCoberturaEnRecomendada(rutaRecomendada(0.86, null), 0)).toBeNull()
  })

  it('identifica cuál de las dos fuentes es la de menor cobertura cuando es siniestros', () => {
    const resultado = brechaCoberturaEnRecomendada(rutaRecomendada(0.5, 0.9), 0)
    expect(resultado).toEqual({ fuenteMenor: 'siniestro', coberturaMenor: 0.5, coberturaMayor: 0.9 })
  })
})
