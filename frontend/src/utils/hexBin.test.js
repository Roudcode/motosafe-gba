import { describe, it, expect } from 'vitest'
import { hexBinZonas, radioHexagonoPorZoom } from './hexBin'

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

  it('expone el desglose de cantidad por nivel, no solo el total', () => {
    const zonas = [
      { lat: -34.6037, lng: -58.3816, cantidad: 10, nivel: 'bajo' },
      { lat: -34.6038, lng: -58.3817, cantidad: 2, nivel: 'critico' },
      { lat: -34.6036, lng: -58.3815, cantidad: 3, nivel: 'bajo' },
    ]
    const resultado = hexBinZonas(zonas, 500, ORDEN)
    const props = resultado.features[0].properties
    expect(props.cantidad_bajo).toBe(13)
    expect(props.cantidad_critico).toBe(2)
    expect(props.cantidad_medio).toBe(0)
    expect(props.cantidad_alto).toBe(0)
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

describe('radioHexagonoPorZoom', () => {
  it('da celdas grandes bien alejado', () => {
    expect(radioHexagonoPorZoom(9)).toBe(1300)
  })

  it('da el radio de siempre (650) en el rango de zoom default', () => {
    expect(radioHexagonoPorZoom(11)).toBe(650)
    expect(radioHexagonoPorZoom(13)).toBe(650)
  })

  it('da celdas chicas acercado a nivel de barrio/calle', () => {
    expect(radioHexagonoPorZoom(14)).toBe(320)
    expect(radioHexagonoPorZoom(18)).toBe(320)
  })
})
