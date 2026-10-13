import { describe, it, expect } from 'vitest'
import { hexBinZonas } from './hexBin'

const ORDEN = ['bajo', 'medio', 'alto', 'critico']

describe('hexBinZonas', () => {
  it('agrupa dos zonas muy cercanas en la misma celda', () => {
    const zonas = [
      { lat: -34.6037, lng: -58.3816, cantidad: 10, nivel: 'medio' },
      { lat: -34.6038, lng: -58.3817, cantidad: 5, nivel: 'bajo' },
    ]
    const resultado = hexBinZonas(zonas, 500, ORDEN)
    expect(resultado.features.length).toBe(1)
    expect(resultado.features[0].properties.cantidad).toBe(15)
  })

  it('separa zonas lejanas en celdas distintas', () => {
    const zonas = [
      { lat: -34.6037, lng: -58.3816, cantidad: 10, nivel: 'medio' },
      { lat: -34.65, lng: -58.45, cantidad: 5, nivel: 'bajo' },
    ]
    const resultado = hexBinZonas(zonas, 500, ORDEN)
    expect(resultado.features.length).toBe(2)
  })

  it('una celda se queda con el nivel más alto presente, no un promedio', () => {
    const zonas = [
      { lat: -34.6037, lng: -58.3816, cantidad: 10, nivel: 'bajo' },
      { lat: -34.6038, lng: -58.3817, cantidad: 2, nivel: 'critico' },
    ]
    const resultado = hexBinZonas(zonas, 500, ORDEN)
    expect(resultado.features[0].properties.nivel).toBe('critico')
  })

  it('cada polígono es un hexágono cerrado (7 puntos, el primero y el último iguales)', () => {
    const zonas = [{ lat: -34.6037, lng: -58.3816, cantidad: 1, nivel: 'bajo' }]
    const resultado = hexBinZonas(zonas, 500, ORDEN)
    const anillo = resultado.features[0].geometry.coordinates[0]
    expect(anillo.length).toBe(7)
    expect(anillo[0]).toEqual(anillo[6])
  })

  it('sin zonas, devuelve un FeatureCollection vacío', () => {
    const resultado = hexBinZonas([], 500, ORDEN)
    expect(resultado.features).toEqual([])
  })
})
