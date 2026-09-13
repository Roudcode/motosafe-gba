import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cargarDeLocalStorage, guardarEnLocalStorage } from './storage'

describe('storage seguro', () => {
  let datos

  beforeEach(() => {
    datos = new Map()
    vi.stubGlobal('localStorage', {
      getItem: (clave) => datos.get(clave) ?? null,
      setItem: (clave, valor) => datos.set(clave, valor),
      clear: () => datos.clear(),
    })
  })

  afterEach(() => vi.unstubAllGlobals())

  it('devuelve el valor por defecto ante JSON corrupto', () => {
    datos.set('clave', '{no-json')
    expect(cargarDeLocalStorage('clave', { segura: true })).toEqual({ segura: true })
  })

  it('no propaga un fallo de cuota al guardar', () => {
    localStorage.setItem = vi.fn(() => { throw new Error('cuota') })
    expect(() => guardarEnLocalStorage('clave', { valor: 1 })).not.toThrow()
  })
})
