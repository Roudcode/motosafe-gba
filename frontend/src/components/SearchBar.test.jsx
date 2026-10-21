// @vitest-environment jsdom
//
// T02 (SES-146): hallazgo real -- la lista de resultados del buscador no
// era alcanzable por teclado porque el blur del input la desmontaba sin
// importar adónde se movía el foco. Este test reproduce exactamente eso:
// enfoca el input, escribe, tabula (sin mouse) y confirma que el foco
// llega a un botón de resultado real y que Enter lo selecciona -- no solo
// que el HTML de la lista "existe" en algún render intermedio.
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SearchBar } from './SearchBar'

function sugBusquedaConResultados(resultados) {
  return {
    resultados,
    buscando: false,
    buscada: true,
    error: null,
    buscar: vi.fn(),
    limpiar: vi.fn(),
  }
}

function propsBase(overrides = {}) {
  return {
    abierto: true,
    setAbierto: vi.fn(),
    vistaNavegacion: false,
    busqueda: 'florida',
    setBusqueda: vi.fn(),
    sugBusqueda: sugBusquedaConResultados([
      { label: 'Florida 123, CABA', lat: -34.6, lng: -58.37 },
      { label: 'Florida 456, CABA', lat: -34.61, lng: -58.38 },
    ]),
    buscaEnFoco: true,
    setBuscaEnFoco: vi.fn(),
    recientes: [],
    buscarEnMapa: vi.fn(),
    lugarElegido: null,
    setLugarElegido: vi.fn(),
    rutaAbierta: false,
    irAlLugar: vi.fn(),
    ...overrides,
  }
}

afterEach(() => cleanup())

describe('SearchBar -- navegación por teclado de los resultados', () => {
  it('Tab desde el input llega a un botón de resultado real (no se desmonta la lista)', async () => {
    const user = userEvent.setup()
    render(<SearchBar {...propsBase()} />)

    const input = screen.getByRole('textbox', { name: 'Buscar lugar, calle o local' })
    input.focus()
    expect(document.activeElement).toBe(input)

    // Orden real de tabulación dentro del buscador: input -> botón
    // "Limpiar búsqueda" (aparece porque hay texto cargado) -> primer
    // resultado. Dos Tab, no uno, para llegar al resultado real.
    await user.tab()
    await user.tab()

    const activo = document.activeElement
    expect(activo).not.toBe(document.body)
    expect(activo.tagName).toBe('BUTTON')
    expect(activo.textContent).toContain('Florida 123, CABA')
  })

  it('Enter sobre un resultado enfocado por teclado lo selecciona', async () => {
    const user = userEvent.setup()
    const buscarEnMapa = vi.fn()
    render(<SearchBar {...propsBase({ buscarEnMapa })} />)

    const input = screen.getByRole('textbox', { name: 'Buscar lugar, calle o local' })
    input.focus()
    await user.tab()
    await user.tab()
    await user.keyboard('{Enter}')

    expect(buscarEnMapa).toHaveBeenCalledWith(
      expect.objectContaining({ label: 'Florida 123, CABA' })
    )
  })

  it('perder el foco del todo (afuera del buscador) sigue cerrando si no hay texto', async () => {
    vi.useFakeTimers()
    const setAbierto = vi.fn()
    const sugBusqueda = sugBusquedaConResultados([])
    render(
      <SearchBar {...propsBase({ busqueda: '', setAbierto, sugBusqueda })} />
    )
    const input = screen.getByRole('textbox', { name: 'Buscar lugar, calle o local' })
    input.focus()

    // blur sin relatedTarget (foco se va afuera del documento/contenedor)
    input.blur()
    vi.advanceTimersByTime(200)

    expect(setAbierto).toHaveBeenCalledWith(false)
    vi.useRealTimers()
  })
})
