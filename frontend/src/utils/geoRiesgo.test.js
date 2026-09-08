import { describe, it, expect } from 'vitest'
import { esFranjaPicoInseguridad, calcularAjustePorFranjaHoraria } from './geoRiesgo'

describe('esFranjaPicoInseguridad', () => {
  it('devuelve false si no se pasa la hora', () => {
    expect(esFranjaPicoInseguridad(null)).toBe(false)
    expect(esFranjaPicoInseguridad(undefined)).toBe(false)
  })

  it('reconoce la franja pico por defecto (19 a 23), calibrada con la distribucion real de robos con moto', () => {
    expect(esFranjaPicoInseguridad(19)).toBe(true)
    expect(esFranjaPicoInseguridad(21)).toBe(true)
    expect(esFranjaPicoInseguridad(23)).toBe(true)
  })

  it('no marca como pico las horas de la madrugada, que en el dato real son las de menor incidencia', () => {
    expect(esFranjaPicoInseguridad(2)).toBe(false)
    expect(esFranjaPicoInseguridad(4)).toBe(false)
  })

  it('no marca como pico las horas de la manana ni el mediodia', () => {
    expect(esFranjaPicoInseguridad(9)).toBe(false)
    expect(esFranjaPicoInseguridad(12)).toBe(false)
    expect(esFranjaPicoInseguridad(18)).toBe(false)
  })

  it('soporta una franja custom que cruza medianoche', () => {
    expect(esFranjaPicoInseguridad(23, { desde: 22, hasta: 6 })).toBe(true)
    expect(esFranjaPicoInseguridad(10, { desde: 22, hasta: 6 })).toBe(false)
  })
})

describe('calcularAjustePorFranjaHoraria', () => {
  it('sube un nivel de riesgo en la franja pico (19-23hs)', () => {
    const ajuste = calcularAjustePorFranjaHoraria({ nivel: 'medio' }, 21)
    expect(ajuste.nivel).toBe('alto')
    expect(ajuste.subio).toBe(true)
    expect(ajuste.enFranjaPico).toBe(true)
  })

  it('no toca el nivel fuera de la franja pico', () => {
    const ajuste = calcularAjustePorFranjaHoraria({ nivel: 'medio' }, 12)
    expect(ajuste.nivel).toBe('medio')
    expect(ajuste.subio).toBe(false)
    expect(ajuste.enFranjaPico).toBe(false)
  })

  it('no sube mas alla de critico (tope de la escala)', () => {
    const ajuste = calcularAjustePorFranjaHoraria({ nivel: 'critico' }, 20)
    expect(ajuste.nivel).toBe('critico')
    expect(ajuste.subio).toBe(false)
  })

  it('explica el motivo del ajuste citando el dato real que lo respalda', () => {
    const ajuste = calcularAjustePorFranjaHoraria({ nivel: 'bajo' }, 20)
    expect(ajuste.motivos[0]).toMatch(/dato real/i)
  })

  it('no agrega motivos si no hubo ajuste', () => {
    const ajuste = calcularAjustePorFranjaHoraria({ nivel: 'bajo' }, 12)
    expect(ajuste.motivos).toEqual([])
  })
})
