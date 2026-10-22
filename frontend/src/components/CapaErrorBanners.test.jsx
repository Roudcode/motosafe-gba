// @vitest-environment jsdom
//
// V10 (SES-153): "sin datos" (una capa real responde 200 con lista vacía,
// p.ej. /corredores con `if not resultado: return []`) no es lo mismo que
// "fallo, reintentando" (erroresCapas). Estos tests confirman que el aviso
// de capa vacía solo aparece cuando la capa NO está en erroresCapas, y que
// nunca trae ícono de alerta ni botón de reintento (no tiene sentido
// reintentar algo que no falló).
import { describe, it, expect, afterEach, vi } from 'vitest'
import { render, screen, cleanup } from '@testing-library/react'
import { CapaErrorBanners } from './CapaErrorBanners'

afterEach(cleanup)

function propsBase(overrides = {}) {
  return {
    backendError: false,
    cargarHotspots: vi.fn(),
    erroresCapas: {},
    ultimaConsultaCapas: null,
    setRecargaCapas: vi.fn(),
    capaTrafico: false,
    traficoNoDisponible: false,
    setCapaTrafico: vi.fn(),
    capasVacias: {},
    ...overrides,
  }
}

describe('CapaErrorBanners -- aviso de capa sin datos (V10)', () => {
  it('muestra el aviso cuando una capa real responde vacía y no está fallando', () => {
    render(<CapaErrorBanners {...propsBase({ capasVacias: { corredores: true } })} />)
    expect(screen.getByText(/sin datos registrados todavía en esta zona/i)).toBeTruthy()
    expect(screen.getByText(/corredores/i)).toBeTruthy()
  })

  it('no muestra botón de reintento en el aviso de capa vacía', () => {
    render(<CapaErrorBanners {...propsBase({ capasVacias: { corredores: true } })} />)
    expect(screen.queryByRole('button', { name: /reintentar/i })).toBeNull()
  })

  it('no muestra el aviso de vacía si esa misma capa ya está marcada como fallando', () => {
    render(<CapaErrorBanners {...propsBase({
      capasVacias: { corredores: true },
      erroresCapas: { corredores: true },
    })} />)
    expect(screen.queryByText(/sin datos registrados todavía/i)).toBeNull()
    // el banner de fallo real (con reintento) sí debe seguir mostrándose
    expect(screen.getByRole('button', { name: /reintentar capas/i })).toBeTruthy()
  })

  it('lista varias capas vacías juntas en un solo aviso', () => {
    render(<CapaErrorBanners {...propsBase({
      capasVacias: { corredores: true, inseguridadGeneral: true, inseguridadMoto: false },
    })} />)
    const aviso = screen.getByText(/sin datos registrados todavía/i)
    expect(aviso.textContent).toMatch(/corredores/i)
    expect(aviso.textContent).toMatch(/inseguridad general/i)
    expect(aviso.textContent).not.toMatch(/inseguridad con moto/i)
  })

  it('no muestra ningún aviso cuando no hay capas vacías', () => {
    render(<CapaErrorBanners {...propsBase()} />)
    expect(screen.queryByText(/sin datos registrados todavía/i)).toBeNull()
  })

  it('DEC-025: muestra el aviso de vacía para hotspots, igual que corredores/inseguridad', () => {
    render(<CapaErrorBanners {...propsBase({ capasVacias: { hotspots: true } })} />)
    const aviso = screen.getByText(/sin datos registrados todavía/i)
    expect(aviso.textContent).toMatch(/hotspots de siniestros/i)
    expect(screen.queryByRole('button', { name: /reintentar/i })).toBeNull()
  })
})
