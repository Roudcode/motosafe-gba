import { describe, it, expect } from 'vitest'
import { esFranjaPicoInseguridad, calcularAjustePorFranjaHoraria } from './geoRiesgo'

const FRANJA_MOTO = { desde: 19, hasta: 24 }
const FRANJA_GENERAL = { desde: 17, hasta: 22 }

describe('esFranjaPicoInseguridad', () => {
  it('devuelve false si no se pasa la hora', () => {
    expect(esFranjaPicoInseguridad(null, FRANJA_MOTO)).toBe(false)
    expect(esFranjaPicoInseguridad(undefined, FRANJA_MOTO)).toBe(false)
  })

  it('reconoce la franja pico de robos con moto (19-23), calibrada con su distribucion real', () => {
    expect(esFranjaPicoInseguridad(19, FRANJA_MOTO)).toBe(true)
    expect(esFranjaPicoInseguridad(21, FRANJA_MOTO)).toBe(true)
    expect(esFranjaPicoInseguridad(23, FRANJA_MOTO)).toBe(true)
    expect(esFranjaPicoInseguridad(18, FRANJA_MOTO)).toBe(false)
  })

  it('reconoce la franja pico de delito general (17-21), mas temprana y angosta que la de moto', () => {
    expect(esFranjaPicoInseguridad(17, FRANJA_GENERAL)).toBe(true)
    expect(esFranjaPicoInseguridad(21, FRANJA_GENERAL)).toBe(true)
    expect(esFranjaPicoInseguridad(22, FRANJA_GENERAL)).toBe(false)
    expect(esFranjaPicoInseguridad(16, FRANJA_GENERAL)).toBe(false)
  })

  it('no marca como pico las horas de la madrugada, que en el dato real son las de menor incidencia', () => {
    expect(esFranjaPicoInseguridad(2, FRANJA_MOTO)).toBe(false)
    expect(esFranjaPicoInseguridad(4, FRANJA_GENERAL)).toBe(false)
  })

  it('soporta una franja custom que cruza medianoche', () => {
    expect(esFranjaPicoInseguridad(23, { desde: 22, hasta: 6 })).toBe(true)
    expect(esFranjaPicoInseguridad(10, { desde: 22, hasta: 6 })).toBe(false)
  })
})

describe('calcularAjustePorFranjaHoraria', () => {
  it('sube un nivel de riesgo dentro de la franja pasada', () => {
    const ajuste = calcularAjustePorFranjaHoraria({ nivel: 'medio' }, 21, FRANJA_MOTO)
    expect(ajuste.nivel).toBe('alto')
    expect(ajuste.subio).toBe(true)
    expect(ajuste.enFranjaPico).toBe(true)
  })

  it('no toca el nivel fuera de la franja pasada', () => {
    const ajuste = calcularAjustePorFranjaHoraria({ nivel: 'medio' }, 12, FRANJA_MOTO)
    expect(ajuste.nivel).toBe('medio')
    expect(ajuste.subio).toBe(false)
    expect(ajuste.enFranjaPico).toBe(false)
  })

  it('la misma hora puede estar en la franja pico de un subtipo y no del otro (ej. 23hs)', () => {
    const enMoto = calcularAjustePorFranjaHoraria({ nivel: 'medio' }, 23, FRANJA_MOTO)
    const enGeneral = calcularAjustePorFranjaHoraria({ nivel: 'medio' }, 23, FRANJA_GENERAL)
    expect(enMoto.enFranjaPico).toBe(true)
    expect(enGeneral.enFranjaPico).toBe(false)
  })

  it('no sube mas alla de critico (tope de la escala)', () => {
    const ajuste = calcularAjustePorFranjaHoraria({ nivel: 'critico' }, 20, FRANJA_MOTO)
    expect(ajuste.nivel).toBe('critico')
    expect(ajuste.subio).toBe(false)
  })

  it('explica el motivo del ajuste citando el dato real que lo respalda', () => {
    const ajuste = calcularAjustePorFranjaHoraria({ nivel: 'bajo' }, 20, FRANJA_MOTO)
    expect(ajuste.motivos[0]).toMatch(/dato real/i)
  })

  it('no agrega motivos si no hubo ajuste', () => {
    const ajuste = calcularAjustePorFranjaHoraria({ nivel: 'bajo' }, 12, FRANJA_MOTO)
    expect(ajuste.motivos).toEqual([])
  })
})
