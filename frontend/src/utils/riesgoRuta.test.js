import { describe, it, expect } from 'vitest'
import {
  unificarZonasInseguridad, unificarZonasRiesgo, calcularZonasCruzadasPorRuta, calcularRutasConScore,
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

describe('unificarZonasInseguridad con ajuste por franja horaria', () => {
  const general = [
    { id: 1, latitud: -34.6, longitud: -58.4, nivel_riesgo: 'medio', cantidad_delitos: 40, tipo_delito_moda: 'robo' },
  ]

  it('no aplica ningun ajuste si no se pasa horaDelDia (compatibilidad hacia atras)', () => {
    const zonas = unificarZonasInseguridad(general, [])
    expect(zonas[0].nivel).toBe('medio')
    expect(zonas[0].ajusteHorario).toBeUndefined()
  })

  it('sube el nivel en la franja pico (19-23hs, calibrada con dato real)', () => {
    const zonas = unificarZonasInseguridad(general, [], 21)
    expect(zonas[0].nivel).toBe('alto')
    expect(zonas[0].ajusteHorario.enFranjaPico).toBe(true)
  })

  it('no toca el nivel fuera de la franja pico', () => {
    const zonas = unificarZonasInseguridad(general, [], 12)
    expect(zonas[0].nivel).toBe('medio')
    expect(zonas[0].ajusteHorario.enFranjaPico).toBe(false)
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
})
