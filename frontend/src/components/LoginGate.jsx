import { useEffect, useState, useCallback } from 'react'
import { Bike } from 'lucide-react'
import { API_URL } from '../constants'
import { SesionContext } from '../sesion'

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
    return <div className="login-fondo" />
  }

  if (estado === 'anonimo') {
    return <FormularioLogin onLogin={verificarSesion} />
  }

  if (estado === 'sin_login') {
    return children
  }

  // La opción «Cerrar sesión» vive en el menú de herramientas de App (SES-083),
  // no en un botón fijo que tapaba «Reportar» y la atribución del mapa.
  return (
    <SesionContext.Provider value={{ usuario, cerrarSesion }}>
      {children}
    </SesionContext.Provider>
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
    <div className="login-fondo">
      <form onSubmit={enviar} className="login-tarjeta">
        <span className="login-marca"><Bike size={26} /></span>
        <h1 className="login-titulo">MotoSafe GBA</h1>
        <p className="login-subtitulo">Acceso privado</p>
        <div className="login-campo">
          <label htmlFor="login-usuario">Usuario</label>
          <input
            id="login-usuario"
            type="text"
            placeholder="Tu usuario"
            value={usuario}
            onChange={(e) => setUsuario(e.target.value)}
            autoFocus
            autoComplete="username"
            className="login-input"
          />
        </div>
        <div className="login-campo">
          <label htmlFor="login-contrasena">Contraseña</label>
          <input
            id="login-contrasena"
            type="password"
            placeholder="Tu contraseña"
            value={contrasena}
            onChange={(e) => setContrasena(e.target.value)}
            autoComplete="current-password"
            className="login-input"
          />
        </div>
        {error && <p className="login-error" role="alert">{error}</p>}
        <button type="submit" disabled={enviando} className="login-boton">
          {enviando && <span className="spinner spinner-dark" />}
          {enviando ? 'Entrando...' : 'Entrar'}
        </button>
      </form>
    </div>
  )
}
