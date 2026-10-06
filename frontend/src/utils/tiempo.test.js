import { describe, it, expect } from 'vitest'
import { formatearAntiguedad, opacidadPorAntiguedad, esReciente, formatearDistancia, formatearPeriodo } from './tiempo'

const AHORA = new Date('2026-09-07T12:00:00.000Z').getTime()
const hace = (ms) => new Date(AHORA - ms).toISOString()

describe('formatearAntiguedad', () => {
  it('muestra "recién" para algo creado hace menos de un minuto', () => {
    expect(formatearAntiguedad(hace(30 * 1000), AHORA)).toBe('recién')
  })

  it('muestra minutos por debajo de una hora', () => {
    expect(formatearAntiguedad(hace(5 * 60 * 1000), AHORA)).toBe('hace 5 min')
    expect(formatearAntiguedad(hace(59 * 60 * 1000), AHORA)).toBe('hace 59 min')
  })

  it('cambia a horas justo al llegar a los 60 minutos', () => {
    expect(formatearAntiguedad(hace(60 * 60 * 1000), AHORA)).toBe('hace 1h')
  })

  it('muestra horas por debajo de un día', () => {
    expect(formatearAntiguedad(hace(23 * 60 * 60 * 1000), AHORA)).toBe('hace 23h')
  })

  it('cambia a días justo al llegar a las 24 horas', () => {
    expect(formatearAntiguedad(hace(24 * 60 * 60 * 1000), AHORA)).toBe('hace 1d')
  })

  it('muestra días para algo bien viejo', () => {
    expect(formatearAntiguedad(hace(5 * 24 * 60 * 60 * 1000), AHORA)).toBe('hace 5d')
  })
})

describe('opacidadPorAntiguedad', () => {
  it('devuelve opacidad máxima (1) para algo recién creado', () => {
    expect(opacidadPorAntiguedad(hace(0), 12, AHORA)).toBeCloseTo(1, 5)
  })

  it('devuelve la opacidad mínima (0.35) justo cuando cumple la vigencia completa', () => {
    // vigencia de 12hs (categoria "corte"), edad = 12hs exactas -> fraccion = 1
    expect(opacidadPorAntiguedad(hace(12 * 3600000), 12, AHORA)).toBeCloseTo(0.35, 5)
  })

  it('interpola linealmente a mitad de la vigencia', () => {
    // mitad de 12hs = 6hs -> fraccion 0.5 -> opacidad 1 - 0.5*0.65 = 0.675
    expect(opacidadPorAntiguedad(hace(6 * 3600000), 12, AHORA)).toBeCloseTo(0.675, 5)
  })

  it('no baja de 0.35 aunque ya haya vencido hace rato (clamp superior de fraccion)', () => {
    // el backend ya debería haber dejado de devolver esto, pero si por lo que sea
    // llega algo vencido, la opacidad no debe salirse del rango [0.35, 1]
    expect(opacidadPorAntiguedad(hace(100 * 3600000), 12, AHORA)).toBeCloseTo(0.35, 5)
  })

  it('respeta vigencias largas (ej. 30 dias para pavimento/iluminacion)', () => {
    const vigencia720h = 24 * 30
    expect(opacidadPorAntiguedad(hace(0), vigencia720h, AHORA)).toBeCloseTo(1, 5)
    expect(opacidadPorAntiguedad(hace(15 * 24 * 3600000), vigencia720h, AHORA)).toBeCloseTo(0.675, 5)
  })
})

describe('esReciente', () => {
  it('es true justo en el borde de los 15 minutos por defecto', () => {
    expect(esReciente(hace(15 * 60 * 1000), AHORA)).toBe(true)
  })

  it('es false apenas se pasa del borde', () => {
    expect(esReciente(hace(15 * 60 * 1000 + 1000), AHORA)).toBe(false)
  })

  it('respeta un umbral de minutos custom', () => {
    expect(esReciente(hace(45 * 60 * 1000), AHORA, 60)).toBe(true)
    expect(esReciente(hace(61 * 60 * 1000), AHORA, 60)).toBe(false)
  })
})

describe('formatearDistancia', () => {
  it('muestra metros redondeados por debajo de 1km', () => {
    expect(formatearDistancia(0.15)).toBe('150 m')
    expect(formatearDistancia(0.003)).toBe('3 m')
  })

  it('muestra km con un decimal a partir de 1km (el bug real que reemplaza: antes se mostraba "47056 m")', () => {
    expect(formatearDistancia(47.056)).toBe('47.1 km')
    expect(formatearDistancia(1)).toBe('1.0 km')
  })

  it('redondea el borde justo en 999m sin saltar a km de más', () => {
    expect(formatearDistancia(0.999)).toBe('999 m')
  })
})

describe('formatearPeriodo', () => {
  it('muestra solo años cuando la cobertura son años completos', () => {
    expect(formatearPeriodo('2019-01-01', '2025-12-31')).toBe('2019–2025')
    expect(formatearPeriodo('2025-01-01', '2025-12-31')).toBe('2025')
  })

  it('agrega el mes cuando el período empieza o termina a mitad de año', () => {
    expect(formatearPeriodo('2023-03-15', '2025-09-09')).toBe('mar 2023–sep 2025')
  })

  it('no inventa un período si falta una fecha', () => {
    expect(formatearPeriodo(null, '2025-12-31')).toBeNull()
  })
})
