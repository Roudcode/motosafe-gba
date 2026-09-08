import { describe, it, expect } from 'vitest'
import { esHorarioNocturno, calcularAjusteNocturno } from './geoRiesgo'

describe('esHorarioNocturno', () => {
  it('devuelve false si no se pasa la hora', () => {
    expect(esHorarioNocturno(null)).toBe(false)
    expect(esHorarioNocturno(undefined)).toBe(false)
  })

  it('reconoce la franja nocturna por defecto (22 a 6), que cruza medianoche', () => {
    expect(esHorarioNocturno(23)).toBe(true)
    expect(esHorarioNocturno(0)).toBe(true)
    expect(esHorarioNocturno(3)).toBe(true)
    expect(esHorarioNocturno(22)).toBe(true)
  })

  it('no marca como nocturnas las horas de dia', () => {
    expect(esHorarioNocturno(6)).toBe(false)
    expect(esHorarioNocturno(12)).toBe(false)
    expect(esHorarioNocturno(21)).toBe(false)
  })

  it('soporta una franja custom que no cruza medianoche', () => {
    expect(esHorarioNocturno(14, { desde: 13, hasta: 15 })).toBe(true)
    expect(esHorarioNocturno(16, { desde: 13, hasta: 15 })).toBe(false)
  })
})

describe('calcularAjusteNocturno', () => {
  it('sube un nivel de riesgo en horario nocturno', () => {
    const ajuste = calcularAjusteNocturno({ nivel: 'medio' }, 23)
    expect(ajuste.nivel).toBe('alto')
    expect(ajuste.subio).toBe(true)
    expect(ajuste.nocturno).toBe(true)
  })

  it('no toca el nivel de dia', () => {
    const ajuste = calcularAjusteNocturno({ nivel: 'medio' }, 12)
    expect(ajuste.nivel).toBe('medio')
    expect(ajuste.subio).toBe(false)
    expect(ajuste.nocturno).toBe(false)
  })

  it('no sube mas alla de critico (tope de la escala)', () => {
    const ajuste = calcularAjusteNocturno({ nivel: 'critico' }, 2)
    expect(ajuste.nivel).toBe('critico')
    expect(ajuste.subio).toBe(false)
  })

  it('explica el motivo del ajuste como heuristica, no como dato medido', () => {
    const ajuste = calcularAjusteNocturno({ nivel: 'bajo' }, 1)
    expect(ajuste.motivos[0]).toMatch(/heur[ií]stica/i)
  })

  it('no agrega motivos si no hubo ajuste', () => {
    const ajuste = calcularAjusteNocturno({ nivel: 'bajo' }, 12)
    expect(ajuste.motivos).toEqual([])
  })
})
