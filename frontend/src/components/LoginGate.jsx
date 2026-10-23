import { useEffect, useState, useCallback } from 'react'
import { Bike, Eye, EyeOff } from 'lucide-react'
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
  const [nombreUsuario, setNombreUsuario] = useState(null)

  const verificarSesion = useCallback(
    () =>
      fetch(`${API_URL}/auth/me`, { credentials: 'include' })
        .then((respuesta) => (respuesta.ok ? respuesta.json() : null))
        .then((datos) => {
          setUsuario(datos?.usuario ?? null)
          setNombreUsuario(datos?.nombre_usuario ?? null)
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
    return <FlujoAcceso onLogin={verificarSesion} />
  }

  if (estado === 'sin_login') {
    return children
  }

  // La opción «Cerrar sesión» vive en el menú de herramientas de App (SES-083),
  // no en un botón fijo que tapaba «Reportar» y la atribución del mapa.
  return (
    <SesionContext.Provider value={{ usuario, nombreUsuario, cerrarSesion }}>
      {children}
    </SesionContext.Provider>
  )
}

// F11 (SES-165): antes esto era un único formulario de login contra un
// usuario fijo. Ahora es un flujo chico de pantallas (login / crear cuenta /
// verificar código / olvidé contraseña / código + contraseña nueva), todas
// dentro de la misma SPA -- nunca una página pública aparte que lea un token
// de la URL (decisión ya tomada: el código de 6 dígitos se tipea acá). Mismo
// patrón visual que ya existía (.login-fondo/.login-tarjeta/.login-input),
// sin ningún componente ni librería nueva.
function FlujoAcceso({ onLogin }) {
  // login | registro | verificar | olvide | reset
  const [pantalla, setPantalla] = useState('login')
  // Email que se arrastra entre pantallas (registro -> verificar, olvide -> reset)
  // para no pedirlo de nuevo dos veces seguidas.
  const [emailEnCurso, setEmailEnCurso] = useState('')
  const [avisoVerificar, setAvisoVerificar] = useState('')

  const irAVerificar = (email, aviso) => {
    setEmailEnCurso(email)
    setAvisoVerificar(aviso || '')
    setPantalla('verificar')
  }

  return (
    <div className="login-fondo">
      {pantalla === 'login' && (
        <FormularioLogin
          onLogin={onLogin}
          onCrearCuenta={() => setPantalla('registro')}
          onOlvide={() => setPantalla('olvide')}
          onRequiereVerificacion={(email) => irAVerificar(email, 'Confirmá tu cuenta con el código que te mandamos a tu correo.')}
        />
      )}
      {pantalla === 'registro' && (
        <FormularioRegistro
          onRegistrado={(email) => irAVerificar(email, 'Te mandamos un código de 6 dígitos a tu correo.')}
          onVolver={() => setPantalla('login')}
        />
      )}
      {pantalla === 'verificar' && (
        <PantallaVerificarCodigo
          email={emailEnCurso}
          avisoInicial={avisoVerificar}
          onVerificado={() => setPantalla('login')}
          onVolver={() => setPantalla('login')}
        />
      )}
      {pantalla === 'olvide' && (
        <FormularioOlvidePassword
          onCodigoPedido={(email) => { setEmailEnCurso(email); setPantalla('reset') }}
          onVolver={() => setPantalla('login')}
        />
      )}
      {pantalla === 'reset' && (
        <FormularioResetPassword
          email={emailEnCurso}
          onReseteado={() => setPantalla('login')}
          onVolver={() => setPantalla('login')}
        />
      )}
    </div>
  )
}

// F11 (SES-166): Rodo lo pidió después de probar el registro real ("un ojo
// que permita ver que estás escribiendo") -- un solo campo reusado en los
// cinco lugares donde se tipea una contraseña, en vez de repetir el mismo
// toggle cinco veces.
function CampoPassword({ id, label, value, onChange, placeholder, autoComplete, autoFocus }) {
  const [visible, setVisible] = useState(false)
  return (
    <div className="login-campo">
      <label htmlFor={id}>{label}</label>
      <div className="login-input-con-ojo">
        <input
          id={id} type={visible ? 'text' : 'password'} placeholder={placeholder} value={value}
          onChange={onChange} autoComplete={autoComplete} autoFocus={autoFocus} className="login-input"
        />
        <button
          type="button" className="login-ojo" onClick={() => setVisible((v) => !v)}
          aria-label={visible ? 'Ocultar contraseña' : 'Mostrar contraseña'} tabIndex={-1}
        >
          {visible ? <EyeOff size={16} /> : <Eye size={16} />}
        </button>
      </div>
    </div>
  )
}

function FormularioLogin({ onLogin, onCrearCuenta, onOlvide, onRequiereVerificacion }) {
  const [email, setEmail] = useState('')
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
        body: JSON.stringify({ email, password: contrasena }),
      })
      if (respuesta.ok) {
        onLogin()
        return
      }
      if (respuesta.status === 429) {
        setError('Demasiados intentos. Esperá un minuto y volvé a intentar.')
      } else if (respuesta.status === 403) {
        // Cuenta real, contraseña correcta, pero falta verificar el mail --
        // ofrecemos la salida (reenviar código) en vez de un error genérico.
        // Si se logueó con nombre de usuario, "email" no es un email real:
        // usamos el que manda el backend en X-Email (verificar/reenviar
        // código solo aceptan email).
        onRequiereVerificacion(respuesta.headers.get('X-Email') || email)
      } else {
        setError('Email/usuario o contraseña incorrectos.')
      }
    } catch {
      setError('No se pudo conectar con el servidor.')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <form onSubmit={enviar} className="login-tarjeta">
      <span className="login-marca"><Bike size={26} /></span>
      <h1 className="login-titulo">MotoSafe GBA</h1>
      <p className="login-subtitulo">Iniciar sesión</p>
      <div className="login-campo">
        <label htmlFor="login-email">Email o nombre de usuario</label>
        <input
          id="login-email" type="text" placeholder="tu@email.com o tu nombre de usuario" value={email}
          onChange={(e) => setEmail(e.target.value)} autoFocus autoComplete="username" className="login-input"
        />
      </div>
      <CampoPassword
        id="login-contrasena" label="Contraseña" placeholder="Tu contraseña" value={contrasena}
        onChange={(e) => setContrasena(e.target.value)} autoComplete="current-password"
      />
      {error && <p className="login-error" role="alert">{error}</p>}
      <button type="submit" disabled={enviando} className="login-boton">
        {enviando && <span className="spinner spinner-dark" />}
        {enviando ? 'Entrando...' : 'Entrar'}
      </button>
      <div className="login-enlaces">
        <button type="button" className="login-enlace" onClick={onOlvide}>¿Olvidaste tu contraseña?</button>
        <button type="button" className="login-enlace" onClick={onCrearCuenta}>Crear cuenta</button>
      </div>
    </form>
  )
}

function FormularioRegistro({ onRegistrado, onVolver }) {
  const [email, setEmail] = useState('')
  const [nombreUsuario, setNombreUsuario] = useState('')
  const [contrasena, setContrasena] = useState('')
  const [confirmar, setConfirmar] = useState('')
  const [error, setError] = useState('')
  const [enviando, setEnviando] = useState(false)

  const enviar = async (evento) => {
    evento.preventDefault()
    setError('')
    if (!nombreUsuario.trim()) {
      setError('Ingresá un nombre de usuario.')
      return
    }
    if (contrasena.length < 8) {
      setError('La contraseña tiene que tener al menos 8 caracteres.')
      return
    }
    if (contrasena !== confirmar) {
      setError('Las contraseñas no coinciden.')
      return
    }
    setEnviando(true)
    try {
      const respuesta = await fetch(`${API_URL}/auth/registro`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, nombre_usuario: nombreUsuario.trim(), password: contrasena }),
      })
      const datos = await respuesta.json().catch(() => null)
      if (respuesta.ok) {
        onRegistrado(email)
        return
      }
      if (respuesta.status === 409) setError(datos?.detail || 'Ese email o nombre de usuario ya está en uso.')
      else setError(datos?.detail || 'No pudimos crear la cuenta.')
    } catch {
      setError('No se pudo conectar con el servidor.')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <form onSubmit={enviar} className="login-tarjeta">
      <span className="login-marca"><Bike size={26} /></span>
      <h1 className="login-titulo">MotoSafe GBA</h1>
      <p className="login-subtitulo">Crear cuenta</p>
      <div className="login-campo">
        <label htmlFor="registro-nombre">Nombre de usuario</label>
        <input
          id="registro-nombre" type="text" placeholder="Cómo querés que te llamemos" value={nombreUsuario}
          onChange={(e) => setNombreUsuario(e.target.value)} autoFocus autoComplete="nickname" className="login-input"
        />
      </div>
      <div className="login-campo">
        <label htmlFor="registro-email">Email</label>
        <input
          id="registro-email" type="email" placeholder="tu@email.com" value={email}
          onChange={(e) => setEmail(e.target.value)} autoComplete="username" className="login-input"
        />
      </div>
      <CampoPassword
        id="registro-contrasena" label="Contraseña" placeholder="Al menos 8 caracteres" value={contrasena}
        onChange={(e) => setContrasena(e.target.value)} autoComplete="new-password"
      />
      <CampoPassword
        id="registro-confirmar" label="Confirmar contraseña" placeholder="Repetí la contraseña" value={confirmar}
        onChange={(e) => setConfirmar(e.target.value)} autoComplete="new-password"
      />
      {error && <p className="login-error" role="alert">{error}</p>}
      <button type="submit" disabled={enviando} className="login-boton">
        {enviando && <span className="spinner spinner-dark" />}
        {enviando ? 'Creando cuenta...' : 'Crear cuenta'}
      </button>
      <div className="login-enlaces">
        <button type="button" className="login-enlace" onClick={onVolver}>Ya tengo cuenta</button>
      </div>
    </form>
  )
}

function PantallaVerificarCodigo({ email, avisoInicial, onVerificado, onVolver }) {
  const [codigo, setCodigo] = useState('')
  const [error, setError] = useState('')
  const [aviso, setAviso] = useState(avisoInicial)
  const [enviando, setEnviando] = useState(false)
  const [reenviando, setReenviando] = useState(false)

  const confirmar = async (evento) => {
    evento.preventDefault()
    setError(''); setAviso('')
    setEnviando(true)
    try {
      const respuesta = await fetch(`${API_URL}/auth/verificar-codigo`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, codigo }),
      })
      const datos = await respuesta.json().catch(() => null)
      if (respuesta.ok) {
        setAviso('Cuenta verificada. Ya podés iniciar sesión.')
        setTimeout(onVerificado, 900)
        return
      }
      setError(datos?.detail || 'No pudimos verificar el código.')
    } catch {
      setError('No se pudo conectar con el servidor.')
    } finally {
      setEnviando(false)
    }
  }

  const reenviar = async () => {
    setError(''); setAviso(''); setReenviando(true)
    try {
      await fetch(`${API_URL}/auth/reenviar-codigo`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      })
      setAviso('Si tu cuenta está pendiente de verificar, te mandamos un código nuevo.')
    } catch {
      setError('No se pudo conectar con el servidor.')
    } finally {
      setReenviando(false)
    }
  }

  return (
    <form onSubmit={confirmar} className="login-tarjeta">
      <span className="login-marca"><Bike size={26} /></span>
      <h1 className="login-titulo">MotoSafe GBA</h1>
      <p className="login-subtitulo">Te mandamos un código a {email}</p>
      <div className="login-campo">
        <label htmlFor="verificar-codigo">Código de 6 dígitos</label>
        <input
          id="verificar-codigo" type="text" inputMode="numeric" placeholder="000000" value={codigo}
          onChange={(e) => setCodigo(e.target.value.replace(/\D/g, '').slice(0, 6))}
          autoFocus autoComplete="one-time-code" className="login-input login-input-codigo"
        />
      </div>
      {error && <p className="login-error" role="alert">{error}</p>}
      {aviso && <p className="login-aviso" role="status">{aviso}</p>}
      <button type="submit" disabled={enviando || codigo.length !== 6} className="login-boton">
        {enviando && <span className="spinner spinner-dark" />}
        {enviando ? 'Verificando...' : 'Verificar'}
      </button>
      <div className="login-enlaces">
        <button type="button" className="login-enlace" onClick={reenviar} disabled={reenviando}>
          {reenviando ? 'Reenviando...' : 'Reenviar código'}
        </button>
        <button type="button" className="login-enlace" onClick={onVolver}>Volver</button>
      </div>
    </form>
  )
}

function FormularioOlvidePassword({ onCodigoPedido, onVolver }) {
  const [email, setEmail] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState('')

  const enviar = async (evento) => {
    evento.preventDefault()
    setError('')
    setEnviando(true)
    try {
      await fetch(`${API_URL}/auth/olvide-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      })
      // Misma respuesta exista o no la cuenta (así responde el backend): no
      // hay forma de "fallar" este paso desde la UI, siempre se avanza.
      onCodigoPedido(email)
    } catch {
      setError('No se pudo conectar con el servidor.')
      setEnviando(false)
    }
  }

  return (
    <form onSubmit={enviar} className="login-tarjeta">
      <span className="login-marca"><Bike size={26} /></span>
      <h1 className="login-titulo">MotoSafe GBA</h1>
      <p className="login-subtitulo">¿Olvidaste tu contraseña?</p>
      <div className="login-campo">
        <label htmlFor="olvide-email">Email</label>
        <input
          id="olvide-email" type="email" placeholder="tu@email.com" value={email}
          onChange={(e) => setEmail(e.target.value)} autoFocus autoComplete="username" className="login-input"
        />
      </div>
      {error && <p className="login-error" role="alert">{error}</p>}
      <button type="submit" disabled={enviando} className="login-boton">
        {enviando && <span className="spinner spinner-dark" />}
        {enviando ? 'Enviando...' : 'Mandarme un código'}
      </button>
      <div className="login-enlaces">
        <button type="button" className="login-enlace" onClick={onVolver}>Volver</button>
      </div>
    </form>
  )
}

function FormularioResetPassword({ email, onReseteado, onVolver }) {
  const [codigo, setCodigo] = useState('')
  const [contrasena, setContrasena] = useState('')
  const [confirmar, setConfirmar] = useState('')
  const [error, setError] = useState('')
  const [aviso, setAviso] = useState('')
  const [enviando, setEnviando] = useState(false)

  const enviar = async (evento) => {
    evento.preventDefault()
    setError(''); setAviso('')
    if (contrasena.length < 8) {
      setError('La contraseña tiene que tener al menos 8 caracteres.')
      return
    }
    if (contrasena !== confirmar) {
      setError('Las contraseñas no coinciden.')
      return
    }
    setEnviando(true)
    try {
      const respuesta = await fetch(`${API_URL}/auth/resetear-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, codigo, password_nueva: contrasena }),
      })
      const datos = await respuesta.json().catch(() => null)
      if (respuesta.ok) {
        setAviso('Contraseña actualizada. Ya podés iniciar sesión.')
        setTimeout(onReseteado, 900)
        return
      }
      setError(datos?.detail || 'No pudimos actualizar la contraseña.')
    } catch {
      setError('No se pudo conectar con el servidor.')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <form onSubmit={enviar} className="login-tarjeta">
      <span className="login-marca"><Bike size={26} /></span>
      <h1 className="login-titulo">MotoSafe GBA</h1>
      <p className="login-subtitulo">Código y contraseña nueva para {email}</p>
      <div className="login-campo">
        <label htmlFor="reset-codigo">Código de 6 dígitos</label>
        <input
          id="reset-codigo" type="text" inputMode="numeric" placeholder="000000" value={codigo}
          onChange={(e) => setCodigo(e.target.value.replace(/\D/g, '').slice(0, 6))}
          autoFocus autoComplete="one-time-code" className="login-input login-input-codigo"
        />
      </div>
      <CampoPassword
        id="reset-contrasena" label="Contraseña nueva" placeholder="Al menos 8 caracteres" value={contrasena}
        onChange={(e) => setContrasena(e.target.value)} autoComplete="new-password"
      />
      <CampoPassword
        id="reset-confirmar" label="Confirmar contraseña" placeholder="Repetí la contraseña" value={confirmar}
        onChange={(e) => setConfirmar(e.target.value)} autoComplete="new-password"
      />
      {error && <p className="login-error" role="alert">{error}</p>}
      {aviso && <p className="login-aviso" role="status">{aviso}</p>}
      <button type="submit" disabled={enviando || codigo.length !== 6} className="login-boton">
        {enviando && <span className="spinner spinner-dark" />}
        {enviando ? 'Actualizando...' : 'Actualizar contraseña'}
      </button>
      <div className="login-enlaces">
        <button type="button" className="login-enlace" onClick={onVolver}>Volver</button>
      </div>
    </form>
  )
}
