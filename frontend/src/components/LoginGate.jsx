import { useEffect, useState, useCallback } from 'react'
import { API_URL } from '../constants'

// Envuelve <App/> y no renderiza nada de la app hasta confirmar que hay una
// sesion valida. El backend es la unica fuente de verdad sobre la sesion
// (cookie HttpOnly, no se puede leer desde JS) -- este componente solo le
// pregunta a /auth/me y reacciona.
export function LoginGate({ children }) {
  // verificando | logueado | anonimo | sin_login (despliegue publico, AUTH_HABILITADO=false)
  const [estado, setEstado] = useState('verificando')
  const [usuario, setUsuario] = useState(null)

  const verificarSesion = useCallback(
    () =>
      fetch(`${API_URL}/auth/me`, { credentials: 'include' })
        .then((respuesta) => (respuesta.ok ? respuesta.json() : null))
        .then((datos) => {
          setUsuario(datos?.usuario ?? null)
          if (datos?.auth_habilitado === false) setEstado('sin_login')
          else setEstado(datos ? 'logueado' : 'anonimo')
        })
        // Sin red o backend caido: no tiene sentido mostrar el login (no va a
        // poder loguear igual), pero tampoco dejar la pantalla en blanco.
        .catch(() => setEstado('anonimo')),
    []
  )

  useEffect(() => {
    verificarSesion()
  }, [verificarSesion])

  const cerrarSesion = useCallback(async () => {
    await fetch(`${API_URL}/auth/logout`, { method: 'POST', credentials: 'include' })
    setUsuario(null)
    setEstado('anonimo')
  }, [])

  if (estado === 'verificando') {
    return <div style={estilos.fondoVerificando} />
  }

  if (estado === 'anonimo') {
    return <FormularioLogin onLogin={verificarSesion} />
  }

  if (estado === 'sin_login') {
    return children
  }

  return (
    <>
      {children}
      <button
        type="button"
        onClick={cerrarSesion}
        title={`Cerrar sesion (${usuario})`}
        style={estilos.botonLogout}
      >
        Salir
      </button>
    </>
  )
}

function FormularioLogin({ onLogin }) {
  const [usuario, setUsuario] = useState('')
  const [contrasena, setContrasena] = useState('')
  const [error, setError] = useState('')
  const [enviando, setEnviando] = useState(false)

  const enviar = async (evento) => {
    evento.preventDefault()
    setError('')
    setEnviando(true)
    try {
      const respuesta = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: usuario, password: contrasena }),
      })
      if (respuesta.ok) {
        onLogin()
        return
      }
      if (respuesta.status === 429) {
        setError('Demasiados intentos. Esperá un minuto y volvé a intentar.')
      } else {
        setError('Usuario o contraseña incorrectos.')
      }
    } catch {
      setError('No se pudo conectar con el servidor.')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div style={estilos.fondo}>
      <form onSubmit={enviar} style={estilos.tarjeta}>
        <h1 style={estilos.titulo}>MotoSafe GBA</h1>
        <p style={estilos.subtitulo}>Acceso privado</p>
        <input
          type="text"
          placeholder="Usuario"
          value={usuario}
          onChange={(e) => setUsuario(e.target.value)}
          autoFocus
          autoComplete="username"
          style={estilos.input}
        />
        <input
          type="password"
          placeholder="Contraseña"
          value={contrasena}
          onChange={(e) => setContrasena(e.target.value)}
          autoComplete="current-password"
          style={estilos.input}
        />
        {error && <p style={estilos.error}>{error}</p>}
        <button type="submit" disabled={enviando} style={estilos.boton}>
          {enviando ? 'Entrando...' : 'Entrar'}
        </button>
      </form>
    </div>
  )
}

const estilos = {
  fondoVerificando: {
    position: 'fixed', inset: 0, background: '#14171A',
  },
  fondo: {
    position: 'fixed', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
    background: '#14171A', fontFamily: "'Inter', sans-serif", padding: 16,
  },
  tarjeta: {
    display: 'flex', flexDirection: 'column', gap: 12, width: '100%', maxWidth: 320,
    background: '#1F2328', border: '1px solid #2C3138', borderRadius: 12, padding: 28,
  },
  titulo: { color: '#E8EAED', fontSize: 22, fontWeight: 700, margin: 0, textAlign: 'center' },
  subtitulo: { color: '#8A9099', fontSize: 13, margin: '0 0 8px', textAlign: 'center' },
  input: {
    background: '#14171A', border: '1px solid #2C3138', borderRadius: 8, padding: '10px 12px',
    color: '#E8EAED', fontSize: 15, outline: 'none',
  },
  boton: {
    background: '#FFC933', color: '#14171A', border: 'none', borderRadius: 8, padding: '10px 12px',
    fontSize: 15, fontWeight: 700, cursor: 'pointer', marginTop: 4,
  },
  error: { color: '#FF3B3B', fontSize: 13, margin: 0, textAlign: 'center' },
  botonLogout: {
    position: 'fixed', bottom: 12, right: 12, zIndex: 9999,
    background: 'rgba(31,35,40,0.85)', color: '#C8CDD3', border: '1px solid #2C3138',
    borderRadius: 8, padding: '6px 10px', fontSize: 12, cursor: 'pointer',
  },
}
