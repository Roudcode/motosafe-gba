// Panel completo de opciones de ruta: SOLO antes de arrancar a navegar.
// Elegir entre rutas alternativas no tiene sentido una vez que ya estás en
// camino -- ahí lo único que hace falta ver es el próximo giro
// (navegacion-panel, en App.jsx) y cuánto falta (nav-resumen-mini, también
// en App.jsx). Tenerlo abierto durante la navegación era el problema de
// clutter más visible de las capturas que mandó Rodo.
//
// A17 (BACKLOG): extraído de App.jsx (SES-128) como primer paso de la
// separación incremental pedida -- es el bloque más grande y más
// autocontenido de JSX que quedaba inline (145 líneas), con una interfaz de
// props chica y bien definida. El comportamiento es idéntico al que tenía
// adentro de App.jsx: esto es un corte-y-pegue con props, no un rediseño.

import { Pencil, Zap, Scale, ShieldCheck, TriangleAlert, CircleCheck, Siren, ShieldAlert,
  ChevronDown, ChevronUp, Navigation, X, Clock, Newspaper } from 'lucide-react'
import { NIVELES } from '../constants'
import { formatearDistancia } from '../utils/tiempo'

const NOMBRE_FUENTE = { siniestro: 'siniestros', inseguridad: 'inseguridad' }

export function RutaResumenPanel({
  panelRuta, editarRuta,
  rutasConScore, rutaSeleccionada, setRutaSeleccionada,
  idxMasRapida, idxEquilibrada, idxMasSegura,
  brechaCoberturaRecomendada,
  detalleRutaAbierto, setDetalleRutaAbierto,
  zonasCruzadasOrdenadas,
  iniciarNavegacionRuta, cerrarTodoRuta,
}) {
  if (!panelRuta.montado) return null

  return (
    <div className={`ruta-resumen panel-enter hazard-edge ${panelRuta.saliendo ? 'panel-exit' : ''}`}>
      {/* "Iniciar viaje" quedaba adentro del mismo scroll que la lista de
          rutas y zonas cruzadas -- con 2+ rutas y varias zonas, ese botón
          terminaba fuera de vista sin scrollear (Rodo lo reportó en
          captura real). Ahora solo esta parte de arriba scrollea; el CTA
          y las acciones secundarias quedan fijas abajo del panel, visibles
          siempre sin importar cuánto contenido haya arriba. */}
      <div className="ruta-resumen-scroll">
        <div className="ruta-resumen-header">
          <span className="cercanas-title">Opciones de ruta</span>
          <button className="ruta-resumen-editar" onClick={editarRuta} aria-label="Editar origen y destino"><Pencil size={13} /></button>
        </div>
        {rutasConScore.length > 1 && (
          <div className="ruta-prioridad">
            <button className={rutaSeleccionada === idxMasRapida ? 'activa' : ''} onClick={() => setRutaSeleccionada(idxMasRapida)}><Zap size={12} /> Rápida</button>
            {rutasConScore.length >= 3 && (
              <button className={rutaSeleccionada === idxEquilibrada ? 'activa' : ''} onClick={() => setRutaSeleccionada(idxEquilibrada)}><Scale size={12} /> Equilibrada</button>
            )}
            <button className={rutaSeleccionada === idxMasSegura ? 'activa' : ''} onClick={() => setRutaSeleccionada(idxMasSegura)} title="Menor exposición registrada entre estas alternativas"><ShieldCheck size={12} /> Menor exposición</button>
          </div>
        )}
        {rutasConScore.map((r, i) => (
          <button key={i} className={`ruta-opcion ${i === rutaSeleccionada ? 'activa' : ''}`} onClick={() => setRutaSeleccionada(i)}>
            <span className="ruta-opcion-num">
              Ruta {i + 1}
              {i === idxMasRapida && i === idxMasSegura && r.coberturaRegistrada >= 0.6 && <span className="ruta-opcion-badge badge-ambas"><Zap size={10} /><ShieldCheck size={10} /> rápida y menor exposición</span>}
              {i === idxMasRapida && i !== idxMasSegura && <span className="ruta-opcion-badge badge-rapida"><Zap size={10} /> rápida</span>}
              {i === idxMasSegura && i !== idxMasRapida && r.coberturaRegistrada >= 0.6 && <span className="ruta-opcion-badge badge-segura"><ShieldCheck size={10} /> menor exposición</span>}
              {i === idxEquilibrada && i !== idxMasRapida && i !== idxMasSegura && <span className="ruta-opcion-badge badge-equilibrada"><Scale size={10} /> equilibrada</span>}
            </span>
            <span className="ruta-opcion-datos">
              {r.km} km · {r.min} min
              {r.etaTrafico && (
                <span className="ruta-opcion-trafico" title="Tiempo estimado con tráfico en vivo (TomTom) -- puede variar del trazado exacto de esta ruta">
                  {' '}· <Zap size={10} /> {r.etaTrafico.con_trafico_min} min con tráfico
                </span>
              )}
            </span>
            <span className={`ruta-opcion-riesgo ${r.riesgo === 0 ? 'ok' : `nivel-${r.nivelRelativo}`}`}>
              {r.coberturaRegistrada < 0.6
                ? <><TriangleAlert size={12} /> cobertura registrada insuficiente</>
                : r.riesgo === 0
                ? <><CircleCheck size={12} /> sin zonas registradas cerca</>
                : <><TriangleAlert size={12} /> exposición {NIVELES[r.nivelRelativo]?.label.toLowerCase()} entre alternativas</>}
            </span>
            {detalleRutaAbierto && (
              <span className="ruta-opcion-cobertura">
                Cobertura: siniestros {r.coberturaPorFuente.siniestro == null ? 'sin datos' : `${Math.round(r.coberturaPorFuente.siniestro * 100)}%`}
                {' · '}inseguridad {r.coberturaPorFuente.inseguridad == null ? 'sin datos' : `${Math.round(r.coberturaPorFuente.inseguridad * 100)}%`}
              </span>
            )}
            {detalleRutaAbierto && r.riesgo > 0 && (
              <span className="ruta-opcion-desglose">
                {r.cantSiniestros > 0 && <span className="desglose-item desglose-siniestro" title={`${r.cantSiniestros} zonas de siniestro cruzadas`}><Siren size={11} /> {r.cantSiniestros}</span>}
                {r.cantInseguridad > 0 && <span className="desglose-item desglose-inseguridad" title={`${r.cantInseguridad} zonas de inseguridad cruzadas`}><ShieldAlert size={11} /> {r.cantInseguridad}</span>}
                <span className="desglose-pts" title="Puntaje interno: suma de severidad de cada zona cruzada">{r.riesgo} pts</span>
              </span>
            )}
          </button>
        ))}
        {rutasConScore.length === 1 && (
          <p className="ruta-sin-alternativa">No encontramos una ruta alternativa razonable para este tramo.</p>
        )}
        <p className="ruta-cobertura-aviso">
          La exposición compara zonas históricas registradas; no estima la probabilidad de un siniestro ni confirma cobertura completa fuera de las áreas con datos.
        </p>
        {/* DEC-026 (D03, caso 2): la recomendación de "menor exposición" puede
            depender de una fuente con mucha menos cobertura registrada que la
            otra en ese mismo trazado -- eso puede hacerla parecer más segura
            sin serlo, solo porque falta dato. */}
        {brechaCoberturaRecomendada && (
          <p className="ruta-cobertura-aviso ruta-cobertura-aviso-brecha">
            <TriangleAlert size={12} /> La recomendación de menor exposición se apoya en datos de cobertura parcial
            de {NOMBRE_FUENTE[brechaCoberturaRecomendada.fuenteMenor]} ({Math.round(brechaCoberturaRecomendada.coberturaMenor * 100)}%,
            contra {Math.round(brechaCoberturaRecomendada.coberturaMayor * 100)}% de la otra fuente) -- puede haber zonas sin ese dato que no se están viendo.
          </p>
        )}
        {/* R-04/R-05 (Capitulo 6): toggle de detalle + ejemplo visual fijo
            en vez de un tooltip que solo aparece con hover (inutil en
            celular, que es como la mayoria usa esto en la calle). La
            prueba real mostro que el texto aclaratorio solo no alcanza
            para que se entienda "cobertura" (Casos 1, 3, 10, 12); un
            ejemplo concreto con numeros reales es mas dificil de leer mal
            que una definicion abstracta. */}
        <button
          type="button"
          className="ruta-detalle-toggle"
          onClick={() => setDetalleRutaAbierto((v) => !v)}
          aria-expanded={detalleRutaAbierto}
        >
          {detalleRutaAbierto ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          {detalleRutaAbierto ? 'Ocultar cómo se calcula' : 'Ver cómo se calcula'}
        </button>
        {detalleRutaAbierto && (
          <p className="ruta-detalle-ejemplo">
            Ejemplo: "siniestros 40%" significa que 4 de cada 10 tramos de esta ruta pasan cerca de un punto con
            siniestros de moto ya registrados; el 60% restante no tiene ese registro, no significa que ahí no
            ocurran. Los "pts" de cada zona son un puntaje interno para ordenar rutas entre sí, no una chance de
            choque.
          </p>
        )}
        {zonasCruzadasOrdenadas.length > 0 && (
          <div className="ruta-resumen-detalle">
            {zonasCruzadasOrdenadas.slice(0, 6).map((z) => (
              <div key={z.id} className="ruta-resumen-item">
                <span className="cercanas-dot" style={{ background: NIVELES[z.nivel].color }} />
                {z.tipoRiesgo === 'inseguridad' ? <ShieldAlert size={11} className="ruta-resumen-icono" /> : <Siren size={11} className="ruta-resumen-icono" />}
                {z.nombre}
                {/* A11: distancia real al segmento de ruta más cercano, no
                    solo "cruza" (el umbral ya filtra eso). "cruza a 80m" y
                    "cruza a 580m" expresan una incertidumbre muy distinta
                    sobre si la zona corresponde de verdad al tramo. */}
                {Number.isFinite(z.distanciaSegmentoKm) && (
                  <span
                    className="ruta-resumen-distancia"
                    title="Distancia desde esta zona al punto más cercano del trazado de la ruta"
                  >
                    a {formatearDistancia(z.distanciaSegmentoKm)}
                  </span>
                )}
                {z.ajustadoPorHorario && (
                  <Clock size={11} className="ruta-resumen-ajuste" title={z.motivoAjusteHorario || 'Nivel subido por franja horaria'} />
                )}
                {z.ajustadoPorReciente && (
                  <Newspaper size={11} className="ruta-resumen-ajuste" title={z.motivoAjuste || 'Nivel subido por un reporte de prensa reciente'} />
                )}
              </div>
            ))}
            {zonasCruzadasOrdenadas.length > 6 && (
              <p className="ruta-resumen-mas">+ {zonasCruzadasOrdenadas.length - 6} zonas más de menor riesgo</p>
            )}
          </div>
        )}
      </div>
      <button className="ruta-resumen-iniciar" onClick={iniciarNavegacionRuta}>
        <Navigation size={15} /> Iniciar viaje
      </button>
      <div className="ruta-resumen-acciones-finales">
        {/* Antes iba "Compartir" acá -- a pedido de Rodo, se cambia por
            un Cancelar más directo (mismo cierre completo que ya hacía
            "Nueva ruta") para que salir de "Opciones de ruta" y volver a
            la búsqueda sea más fácil, sin tener que buscar el ícono de
            editar (lápiz) arriba del panel. */}
        <button className="ruta-resumen-compartir" onClick={cerrarTodoRuta}><X size={13} /> Cancelar</button>
        <button className="ruta-resumen-nueva" onClick={cerrarTodoRuta}>Nueva ruta</button>
      </div>
    </div>
  )
}
