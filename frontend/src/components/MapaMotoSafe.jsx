// Motor de mapa de MotoSafe GBA, sobre MapLibre GL JS (antes: react-leaflet +
// react-leaflet-cluster + leaflet.heat).
//
// Por qué el cambio: Leaflet es 2D puro, no tiene pitch (inclinación de
// cámara) de ninguna forma. El pedido de "vista tipo Waze/Maps, 2D al mirar
// el mapa y con inclinación 3D al arrancar una ruta" necesita eso, y no hay
// forma de conseguirlo con Leaflet ni con un plugin -- es una limitación del
// motor de renderizado (canvas/DOM 2D vs. WebGL con cámara real). MapLibre
// tiene bearing y pitch nativos, clustering nativo (vía GeoJSON
// clusterProperties) y heatmap nativo, en vez de tres plugins de terceros
// (react-leaflet-cluster y leaflet.heat, que además tenían un problema real:
// Leaflet.markercluster no soporta marcadores rotados, issue sin resolver
// desde 2013 -- ver bitácora).
//
// Tiles: OpenFreeMap (gratis, sin límite, sin API key, MIT). Estilo elegido
// según el tema (dark/light) usando los estilos que ya trae OpenFreeMap, en
// vez del hack de CSS "filter: invert()" que usaba Leaflet con tiles raster.
//
// Arquitectura: este componente es el único que conoce MapLibre. Todo lo
// demás (App.jsx) le pasa datos ya filtrados/calculados por props y recibe
// callbacks -- ninguna lógica de riesgo (utils/riesgoRuta.js, geoRiesgo.js)
// se tocó ni depende de esto.
//
// Estrategia interna: en vez de diffear incrementalmente cada capa contra el
// estado anterior, cada efecto "tira abajo y reconstruye" su fuente/capa
// cuando cambian sus datos. Con los volúmenes de esta app (cientos a pocos
// miles de puntos) reconstruir un GeoJSON source entero es instantáneo, y
// este enfoque es muchísimo más simple y menos propenso a bugs sutiles que
// diffear a mano.

import { useEffect, useRef, useState, memo } from 'react'
// maplibre-gl no tiene export default (solo exports nombrados) -- ver
// node_modules/maplibre-gl/dist/maplibre-gl.mjs.
import { Map as MapaLibre, Marker, Popup } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { NIVELES, NIVELES_INSEGURIDAD_COLOR, CATEGORIAS_REPORTE, VIGENCIA_HORAS_POR_CATEGORIA, VIGENCIA_HORAS_DEFAULT } from '../constants'
import { crearIconoCluster, crearIconoClusterInseguridad } from '../utils/ui'
import { opacidadPorAntiguedad, esReciente, formatearAntiguedad } from '../utils/tiempo'

const ESTILOS = {
  dark: 'https://tiles.openfreemap.org/styles/dark',
  light: 'https://tiles.openfreemap.org/styles/liberty',
}

const PITCH_NAVEGACION = 55
// Zoom "de cámara" durante la vista inclinada -- más cerca que el zoom plano
// de Modo Viaje (ZOOM_NAVEGACION=17 en App.jsx), porque con pitch la cámara
// ya "ve" mucho más terreno por la perspectiva, y a un zoom bajo con
// inclinación se pierde el detalle de calle inmediato que es lo que importa
// mientras estás manejando.
const ZOOM_VISTA_INCLINADA = 17.5
// Corre el punto de la cámara hacia abajo de la pantalla (deja más "mapa por
// delante" visible arriba): el mismo truco de composición que usan Waze y
// Google Maps para la vista de navegación en primera persona.
const PADDING_VISTA_INCLINADA = { top: 0, bottom: 260, left: 0, right: 0 }

// --- helpers de bajo nivel, sin estado de React -----------------------------

function elementoDivIcono(html, size, claseExtra) {
  const wrapper = document.createElement('div')
  wrapper.className = `cluster-icon-wrapper ${claseExtra || ''}`
  wrapper.style.width = `${size}px`
  wrapper.style.height = `${size}px`
  wrapper.innerHTML = html
  return wrapper
}

function elementoCirculo({ size, color, fillColor, fillOpacity, weight, claseExtra }) {
  const el = document.createElement('div')
  el.className = claseExtra || ''
  el.style.width = `${size}px`
  el.style.height = `${size}px`
  el.style.borderRadius = '50%'
  el.style.background = fillColor || color
  el.style.opacity = fillOpacity != null ? fillOpacity : 1
  el.style.border = `${weight || 2}px solid ${color}`
  el.style.boxShadow = '0 1px 4px rgba(0,0,0,0.35)'
  el.style.cursor = 'pointer'
  return el
}

function urlExternaSegura(valor) {
  try {
    const url = new URL(valor)
    return ['https:', 'http:'].includes(url.protocol) ? url.href : null
  } catch {
    return null
  }
}

function contenidoPopupPrensa(rep, etiquetaTipo, horaActual) {
  const contenido = document.createElement('div')
  contenido.className = 'popup-content'
  const fuente = document.createElement('span')
  fuente.className = 'popup-nivel popup-prensa-fuente'
  fuente.textContent = `${etiquetaTipo} · ${rep.fuente || 'Fuente sin identificar'} · ${formatearAntiguedad(rep.fechaReferencia || rep.creadoEn, horaActual)}`
  const titular = document.createElement('strong')
  titular.textContent = rep.titular || 'Noticia sin titular'
  const precision = document.createElement('span')
  precision.className = 'popup-prensa-precision'
  precision.textContent = ETIQUETA_NIVEL_PRECISION[rep.nivelPrecision] || ''
  contenido.append(fuente, titular, precision)

  const url = urlExternaSegura(rep.urlFuente)
  if (url) {
    const boton = document.createElement('button')
    boton.className = 'popup-ver-noticia'
    boton.type = 'button'
    boton.textContent = 'Ver noticia completa'
    boton.addEventListener('click', (evento) => {
      evento.stopPropagation()
      window.open(url, '_blank', 'noopener,noreferrer')
    })
    contenido.append(boton)
  }
  return contenido
}

// Marcador de un reporte de prensa (ver backend/scrapear_noticias_robos.py):
// un ícono propio (no el círculo genérico de reportes de usuario) para que
// se lea de un vistazo como "esto es una noticia, no algo que reportó
// alguien" -- y un halo punteado alrededor cuyo tamaño escala con
// radio_metros, para representar visualmente qué tan precisa (o no) es la
// ubicación: un halo chico si la nota daba una intersección, uno grande si
// solo se pudo ubicar el barrio. Nunca se dibuja como si fuera un punto
// exacto cuando el texto de la noticia no lo era.
//
// Desde v5 el ícono además distingue tipo_incidente (pedido explícito de
// Rodo: "choques de este último mes, robos de este último mes... que estén
// diferenciados por una capa y un ícono"): diario gris para 'robo', auto
// con signo de choque en naranja para 'choque'. Un tipo desconocido (dato
// viejo sin la columna, o valor inesperado) cae al ícono de 'robo' por
// default -- mismo default que usa la tabla en main.py.
const TAMANO_ICONO_PRENSA = 26
const HALO_POR_NIVEL_PRECISION = { interseccion: 0, calle: 34, barrio: 64 }

const ICONOS_POR_TIPO_INCIDENTE = {
  robo: `
    <svg width="${TAMANO_ICONO_PRENSA}" height="${TAMANO_ICONO_PRENSA}" viewBox="0 0 24 24" fill="none">
      <rect x="3" y="4" width="18" height="16" rx="2" fill="#3A3F4B" stroke="#C9CDD3" stroke-width="1.4"/>
      <line x1="7" y1="8" x2="17" y2="8" stroke="#C9CDD3" stroke-width="1.4"/>
      <line x1="7" y1="11.3" x2="17" y2="11.3" stroke="#C9CDD3" stroke-width="1.4"/>
      <line x1="7" y1="14.6" x2="13" y2="14.6" stroke="#C9CDD3" stroke-width="1.4"/>
    </svg>
  `,
  choque: `
    <svg width="${TAMANO_ICONO_PRENSA}" height="${TAMANO_ICONO_PRENSA}" viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="10" fill="#3A2A1A" stroke="#FF9A3D" stroke-width="1.4"/>
      <path d="M12 6.5 L17 16 H7 Z" fill="none" stroke="#FF9A3D" stroke-width="1.5" stroke-linejoin="round"/>
      <line x1="12" y1="10" x2="12" y2="13" stroke="#FF9A3D" stroke-width="1.5" stroke-linecap="round"/>
      <circle cx="12" cy="14.7" r="0.9" fill="#FF9A3D"/>
    </svg>
  `,
}

function elementoMarcadorPrensa(nivelPrecision, tipoIncidente) {
  const halo = HALO_POR_NIVEL_PRECISION[nivelPrecision] ?? HALO_POR_NIVEL_PRECISION.barrio
  const svgIcono = ICONOS_POR_TIPO_INCIDENTE[tipoIncidente] ?? ICONOS_POR_TIPO_INCIDENTE.robo
  const wrapper = document.createElement('div')
  wrapper.className = 'marker-prensa-wrapper'
  wrapper.style.width = `${Math.max(halo, TAMANO_ICONO_PRENSA)}px`
  wrapper.style.height = `${Math.max(halo, TAMANO_ICONO_PRENSA)}px`
  if (halo > 0) {
    const haloEl = document.createElement('div')
    haloEl.className = `marker-prensa-halo${tipoIncidente === 'choque' ? ' marker-prensa-halo--choque' : ''}`
    haloEl.style.width = `${halo}px`
    haloEl.style.height = `${halo}px`
    wrapper.appendChild(haloEl)
  }
  const icono = document.createElement('div')
  icono.className = 'marker-prensa-icono'
  icono.innerHTML = svgIcono
  wrapper.appendChild(icono)
  wrapper.style.cursor = 'pointer'
  return wrapper
}

const ETIQUETA_TIPO_INCIDENTE = { robo: 'Robo', choque: 'Choque' }

const ETIQUETA_NIVEL_PRECISION = {
  interseccion: 'Ubicación aproximada (intersección)',
  calle: 'Ubicación aproximada (cuadra)',
  barrio: 'Ubicación aproximada (zona/barrio)',
}

// Arma (o reconstruye) una capa clusterizada de puntos sobre un GeoJSON
// source, con marcadores HTML propios en vez de círculos de estilo -- así se
// reutiliza el mismo diseño de "burbuja con conteo" que ya existía. Sigue el
// patrón oficial de MapLibre para clusters con marcadores custom
// (querySourceFeatures + maplibregl.Marker administrados a mano, ver import).
function montarCapaClusterizada(map, { sourceId, features, radius, maxZoom, renderBubble, renderPunto, onClickPunto }) {
  map.addSource(sourceId, {
    type: 'geojson',
    data: { type: 'FeatureCollection', features },
    cluster: true,
    clusterRadius: radius,
    clusterMaxZoom: maxZoom,
    clusterProperties: {
      bajo: ['+', ['case', ['==', ['get', 'nivel'], 'bajo'], 1, 0]],
      medio: ['+', ['case', ['==', ['get', 'nivel'], 'medio'], 1, 0]],
      alto: ['+', ['case', ['==', ['get', 'nivel'], 'alto'], 1, 0]],
      critico: ['+', ['case', ['==', ['get', 'nivel'], 'critico'], 1, 0]],
    },
  })

  // Un source de MapLibre SOLO tilea/carga sus datos si hay al menos una
  // layer visible que lo use -- sin esto, isSourceLoaded() da true (no hay
  // nada que cargar) pero querySourceFeatures() siempre devuelve [], porque
  // nunca se generó el índice de tiles que esa función lee. Como acá el
  // renderizado real lo hacen los maplibregl.Marker de HTML (no una layer de
  // estilo), agregamos una layer "ancla" invisible (radio y opacidad 0) solo
  // para forzar ese tileo. Costó bastante encontrar esto: confirmado contra
  // mapbox-gl-js#5686 ("querySourceFeatures returns empty for invisible
  // features"), que documenta exactamente esta limitación.
  const layerAnclaId = `${sourceId}-ancla-query`
  map.addLayer({
    id: layerAnclaId,
    type: 'circle',
    source: sourceId,
    paint: { 'circle-radius': 0, 'circle-opacity': 0 },
  })

  let markersOnScreen = {}

  function actualizar() {
    if (!map.getSource(sourceId) || !map.isSourceLoaded(sourceId)) return
    const nuevos = {}
    const vistas = map.querySourceFeatures(sourceId)
    // Cada feature se procesa en su propio try/catch: antes, si UNA sola
    // feature rota (ej. un id que no matchea nada en el Map de props por
    // string/number) tiraba una excepción sin capturar, el for..of entero se
    // abortaba a mitad de camino y NINGÚN marcador se agregaba, ni de esa
    // feature ni de las que faltaban recorrer -- silencioso en pantalla
    // (sin ningún error visible salvo en la consola del navegador).
    for (const feature of vistas) {
      try {
        const coords = feature.geometry.coordinates
        const props = feature.properties
        if (props.cluster) {
          const id = `c${props.cluster_id}`
          nuevos[id] = markersOnScreen[id] || crearMarkerCluster(coords, props)
        } else {
          const id = `p${props.id}`
          nuevos[id] = markersOnScreen[id] || crearMarkerPunto(coords, props)
        }
      } catch (err) {
        console.error(`[MapaMotoSafe] no se pudo armar un marcador de "${sourceId}"`, feature.properties, err)
      }
    }
    for (const id in markersOnScreen) {
      if (!nuevos[id]) markersOnScreen[id].remove()
    }
    for (const id in nuevos) {
      if (!markersOnScreen[id]) nuevos[id].addTo(map)
    }
    markersOnScreen = nuevos
  }

  function crearMarkerCluster(coords, props) {
    const { html, size } = renderBubble(
      { bajo: props.bajo, medio: props.medio, alto: props.alto, critico: props.critico },
      props.point_count
    )
    // 'capa-fondo-nav': clase que engancha con el atenuado global de
    // navegación (ver .mapa-en-navegacion en App.css) -- así siniestros e
    // inseguridad se atenúan igual sin que este helper genérico tenga que
    // saber cuál de los dos es.
    const el = elementoDivIcono(html, size, 'capa-fondo-nav')
    el.addEventListener('click', (e) => {
      e.stopPropagation()
      const src = map.getSource(sourceId)
      src.getClusterExpansionZoom(props.cluster_id).then((zoom) => {
        map.easeTo({ center: coords, zoom, duration: 400 })
      })
    })
    return new Marker({ element: el }).setLngLat(coords)
  }

  function crearMarkerPunto(coords, props) {
    const el = renderPunto(props)
    if (onClickPunto) {
      el.addEventListener('click', (e) => {
        e.stopPropagation()
        onClickPunto(props.id, coords)
      })
    }
    return new Marker({ element: el }).setLngLat(coords)
  }

  const onData = (e) => { if (e.sourceId === sourceId) actualizar() }
  map.on('data', onData)
  map.on('move', actualizar)
  actualizar()

  return () => {
    map.off('data', onData)
    map.off('move', actualizar)
    Object.values(markersOnScreen).forEach((m) => m.remove())
    // La layer ancla se saca antes que el source: MapLibre no deja borrar un
    // source todavia referenciado por una layer.
    if (map.getLayer(layerAnclaId)) map.removeLayer(layerAnclaId)
    if (map.getSource(sourceId)) map.removeSource(sourceId)
  }
}

// React.memo: App.jsx tiene un tick de reloj (useSegundosDesde, "hace Xs" en
// la topbar) que lo hace re-renderizar cada segundo para siempre. Sin memo,
// eso volvía a invocar este componente -- el más pesado de la app, dueño de
// la instancia real de maplibre-gl -- una vez por segundo aunque ninguno de
// sus props hubiera cambiado en absoluto. Para que memo realmente frene algo
// hace falta que los props función que le pasa App.jsx sean estables entre
// renders (useCallback ahí), no funciones inline nuevas en cada render --
// ver clicMapa/onMapaReady/onTraficoEstadoCambio/onClickZonaMapa/
// manejarPaneoManual en App.jsx.
function MapaMotoSafeInner({
  tema,
  centro,
  zoomInicial,
  onZoomChange,
  onReady,
  apiUrl,
  capaTrafico,
  onTraficoEstado,
  campoActivo,
  onClickMapa,
  zonasFiltradas,
  zonaResaltada,
  zonasCruzadasIds,
  onClickZona,
  atenuarFondo,
  capaMapa,
  corredoresFiltrados,
  capaInseguridad,
  inseguridadFiltrada,
  reportes,
  onVotarReporte,
  reportesPrensa,
  horaActual,
  rutasCalculadas,
  rutaSeleccionada,
  onClickRuta,
  origenPunto,
  destinoPunto,
  ubicacionReporte,
  miUbicacion,
  vistaNavegacion,
  rumboActual,
  progresoRutaIndice,
  siguiendoUbicacion,
  onPaneoManual,
}) {
  const contenedorRef = useRef(null)
  const mapRef = useRef(null)
  // 0 = mapa todavia no listo. Un ref no dispara re-render ni se puede leer
  // en un array de dependencias (react-hooks/refs lo marca como error), asi
  // que la "listo-dad" del mapa vive en estado real. Es un contador (no un
  // booleano) porque necesita cambiar de valor tambien despues de un cambio
  // de estilo (map.setStyle borra todas las capas custom, hay que
  // reagregarlas), no solo la primera vez.
  const [version, setVersion] = useState(0)

  // Refs para callbacks/estado que cambian seguido, leídos desde listeners
  // que se registran una sola vez (evita closures viejas sin tener que
  // recrear el listener en cada render). Se actualizan en un useEffect (no
  // directo en el cuerpo del componente): mutar un ref durante el render es
  // un error para la regla react-hooks/refs de este lint.
  const campoActivoRef = useRef(campoActivo)
  const onClickMapaRef = useRef(onClickMapa)
  const onClickZonaRef = useRef(onClickZona)
  const onClickRutaRef = useRef(onClickRuta)
  const onPaneoManualRef = useRef(onPaneoManual)
  const horaActualRef = useRef(horaActual)
  useEffect(() => {
    campoActivoRef.current = campoActivo
    onClickMapaRef.current = onClickMapa
    onClickZonaRef.current = onClickZona
    onClickRutaRef.current = onClickRuta
    onPaneoManualRef.current = onPaneoManual
    horaActualRef.current = horaActual
  })

  // --- init del mapa (una sola vez) -----------------------------------------
  // OJO con StrictMode (main.jsx envuelve <App/> en <StrictMode>): en dev,
  // React invoca cada efecto de montaje dos veces (monta -> limpia -> vuelve
  // a montar) para detectar efectos no idempotentes. Sin el guard de abajo,
  // esto crea DOS instancias de maplibregl.Map sobre el mismo contenedor: la
  // primera se destruye con map.remove() pero su evento 'load' puede llegar
  // a disparar igual (es async) y pisar mapaRef/version con un mapa ya
  // muerto, mientras las capas (clusters, heatmap, etc.) quedan repartidas
  // de forma inconsistente entre instancia vieja y nueva. Sintoma exacto que
  // reportó el usuario: mapa base visible, cero marcadores, sin errores en
  // consola. El guard evita crear una segunda instancia real; el mapa vive
  // igual toda la vida de la app (MapaMotoSafe nunca se desmonta solo).
  useEffect(() => {
    if (mapRef.current) return

    const map = new MapaLibre({
      container: contenedorRef.current,
      style: ESTILOS[tema] || ESTILOS.dark,
      center: [centro.lng, centro.lat],
      zoom: zoomInicial,
      pitch: 0,
      bearing: 0,
      attributionControl: { compact: true },
    })
    mapRef.current = map

    map.on('load', () => {
      onReady?.(map)
      setVersion((v) => v + 1)
    })
    map.on('zoomend', () => onZoomChange?.(map.getZoom()))
    map.on('click', (e) => {
      if (campoActivoRef.current) onClickMapaRef.current?.({ lat: e.lngLat.lat, lng: e.lngLat.lng })
    })
    // 'dragstart' de maplibre solo lo dispara el handler de arrastre real
    // (gesto del usuario) -- easeTo/panTo/flyTo programáticos (los que usa
    // este mismo componente y App.jsx para seguir el GPS) no lo emiten, así
    // que no hace falta distinguir "quién movió la cámara": si llegó este
    // evento, fue la mano del usuario.
    map.on('dragstart', () => onPaneoManualRef.current?.())

    // Sin cleanup que llame a map.remove(): con el guard de arriba, la
    // "limpieza fantasma" de StrictMode destruiría el único mapa real que
    // vamos a usar. Este componente vive durante toda la vida de la app.
    // Solo al montar: centro/zoomInicial son el estado inicial nomás, tema
    // inicial también -- los cambios de tema post-montaje se manejan aparte.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // --- cambio de tema (recarga el estilo, hay que re-agregar todo después) --
  // OJO: `version` no va en las deps a propósito -- si se agregara, cada
  // 'styledata' (que ya de por sí incrementa version) volvería a disparar
  // este efecto y a llamar setStyle de nuevo, ciclo infinito.
  useEffect(() => {
    const map = mapRef.current
    if (!map || version === 0) return
    const nuevoEstilo = ESTILOS[tema] || ESTILOS.dark
    map.setStyle(nuevoEstilo)
    map.once('styledata', () => setVersion((v) => v + 1))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tema])

  // --- cámara de navegación: pitch + bearing + zoom + centro + padding -----
  // Todo junto en un solo easeTo (no un efecto por propiedad) porque son una
  // sola composición de cámara: cambiar el bearing sin re-centrar en la
  // posición actual, por ejemplo, deja al usuario fuera de foco apenas gira.
  // Mientras vistaNavegacion está activa, ESTE efecto es el único que mueve
  // la cámara (el seguimiento 2D de App.jsx se desactiva a propósito, ver
  // ese componente) para que no compitan dos `easeTo` al mismo tiempo.
  useEffect(() => {
    const map = mapRef.current
    if (!map || version === 0) return
    if (vistaNavegacion && miUbicacion) {
      // siguiendoUbicacion en false = el usuario paneó a mano para mirar
      // alrededor (ver onPaneoManual/dragstart más arriba): se deja la
      // cámara donde la dejó, en vez de tironearla de vuelta en cada fix de
      // GPS. Vuelve a seguir recién cuando toque "recentrar" en App.jsx.
      if (!siguiendoUbicacion) return
      map.easeTo({
        center: [miUbicacion.lng, miUbicacion.lat],
        zoom: ZOOM_VISTA_INCLINADA,
        pitch: PITCH_NAVEGACION,
        bearing: rumboActual || 0,
        padding: PADDING_VISTA_INCLINADA,
        duration: 700,
      })
    } else {
      map.easeTo({ pitch: 0, bearing: 0, padding: { top: 0, bottom: 0, left: 0, right: 0 }, duration: 700 })
    }
  }, [vistaNavegacion, rumboActual, miUbicacion, version, siguiendoUbicacion])

  // --- edificios 3D, solo durante la navegación con vista inclinada --------
  // Es la "vuelta de rosca" visual: con el mapa plano (exploración, clusters,
  // mapa de calor) una capa de edificios extruidos solo agrega ruido, porque
  // sin pitch no hay altura que apreciar. Durante la navegación sí suma la
  // sensación de profundidad tipo Waze/Google Maps. La fuente 'openmaptiles'
  // y la source-layer 'building' ya vienen incluidas en el estilo (mismo
  // vector tileset que usan los clusters), así que alcanza con agregar la
  // layer de extrusión -- no hace falta declarar una fuente nueva.
  useEffect(() => {
    const map = mapRef.current
    if (!map || version === 0) return
    const layerId = 'edificios-3d-navegacion'
    if (vistaNavegacion) {
      if (!map.getLayer(layerId) && map.getSource('openmaptiles')) {
        map.addLayer({
          id: layerId,
          type: 'fill-extrusion',
          source: 'openmaptiles',
          'source-layer': 'building',
          minzoom: 14,
          paint: {
            'fill-extrusion-color': tema === 'light' ? '#C9CDD3' : '#3A4048',
            'fill-extrusion-height': [
              'interpolate', ['linear'], ['zoom'],
              14, 0,
              16, ['coalesce', ['get', 'render_height'], 8],
            ],
            'fill-extrusion-base': ['coalesce', ['get', 'render_min_height'], 0],
            'fill-extrusion-opacity': 0.75,
          },
        })
      }
    } else if (map.getLayer(layerId)) {
      map.removeLayer(layerId)
    }
  }, [vistaNavegacion, version, tema])

  // --- atenuar el fondo mientras se navega ----------------------------------
  // Clase en el contenedor del mapa que engancha con el CSS de App.css
  // (.mapa-en-navegacion .capa-fondo-nav) para bajarle la opacidad a los
  // clusters de siniestros/inseguridad durante la navegación con vista
  // inclinada. No se desmontan (no hay que reconstruir el source cada vez
  // que se activa/desactiva vistaNavegacion, que sería mucho más costoso),
  // solo se atenúan visualmente -- lo mismo que ya hacía atenuarFondo para
  // heatmap/corredores, pero vía clase porque estos son marcadores DOM, no
  // paint properties de una layer nativa.
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    map.getContainer().classList.toggle('mapa-en-navegacion', !!vistaNavegacion)
  }, [vistaNavegacion])

  // --- tráfico en vivo (tiles raster propios, TomTom vía backend) ----------
  useEffect(() => {
    const map = mapRef.current
    if (!map || version === 0) return
    const sourceId = 'trafico'
    const layerId = 'trafico-layer'
    if (!capaTrafico) {
      if (map.getLayer(layerId)) map.removeLayer(layerId)
      if (map.getSource(sourceId)) map.removeSource(sourceId)
      return
    }
    map.addSource(sourceId, {
      type: 'raster',
      tiles: [`${apiUrl}/trafico/tiles/{z}/{x}/{y}.png`],
      tileSize: 256,
    })
    map.addLayer({ id: layerId, type: 'raster', source: sourceId, paint: { 'raster-opacity': 0.75 } })

    const onError = (e) => { if (e.sourceId === sourceId) onTraficoEstado?.(false) }
    const onData = (e) => { if (e.sourceId === sourceId && e.isSourceLoaded) onTraficoEstado?.(true) }
    map.on('error', onError)
    map.on('data', onData)

    return () => {
      map.off('error', onError)
      map.off('data', onData)
      if (map.getLayer(layerId)) map.removeLayer(layerId)
      if (map.getSource(sourceId)) map.removeSource(sourceId)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [capaTrafico, apiUrl, version])

  // --- heatmap de siniestros -------------------------------------------------
  useEffect(() => {
    const map = mapRef.current
    if (!map || version === 0) return
    const sourceId = 'heatmap-siniestros'
    const layerId = 'heatmap-siniestros-layer'
    if (capaMapa !== 'heatmap') {
      if (map.getLayer(layerId)) map.removeLayer(layerId)
      if (map.getSource(sourceId)) map.removeSource(sourceId)
      return
    }
    const features = zonasFiltradas.map((z) => ({
      type: 'Feature',
      geometry: { type: 'Point', coordinates: [z.lng, z.lat] },
      properties: {
        // Misma intensidad ponderada que antes: cantidad normalizada + empujón si hubo mortales.
        intensidad: Math.min((z.cantidad || 0) / 15, 1) + (z.mortales > 0 ? 0.4 : 0),
      },
    }))
    map.addSource(sourceId, { type: 'geojson', data: { type: 'FeatureCollection', features } })
    map.addLayer({
      id: layerId,
      type: 'heatmap',
      source: sourceId,
      paint: {
        'heatmap-weight': ['get', 'intensidad'],
        'heatmap-intensity': 1.1,
        'heatmap-radius': 32,
        'heatmap-opacity': atenuarFondo,
        'heatmap-color': [
          'interpolate', ['linear'], ['heatmap-density'],
          0, 'rgba(0,0,0,0)',
          0.2, '#3DDC84',
          0.5, '#FFD23D',
          0.75, '#FF8C42',
          1, '#FF3B3B',
        ],
      },
    })
    return () => {
      if (map.getLayer(layerId)) map.removeLayer(layerId)
      if (map.getSource(sourceId)) map.removeSource(sourceId)
    }
     
  }, [capaMapa, zonasFiltradas, atenuarFondo, version])

  // --- cluster de siniestros (capaMapa === 'clusters') ----------------------
  useEffect(() => {
    const map = mapRef.current
    if (!map || version === 0 || capaMapa !== 'clusters') return
    const sourceId = 'siniestros'
    const features = zonasFiltradas.map((zona) => ({
      type: 'Feature',
      geometry: { type: 'Point', coordinates: [zona.lng, zona.lat] },
      properties: { id: zona.id, nivel: zona.ajuste.nivel },
    }))
    const zonasPorId = new Map(zonasFiltradas.map((z) => [String(z.id), z]))

    const limpiar = montarCapaClusterizada(map, {
      sourceId,
      features,
      radius: 55,
      maxZoom: 16,
      renderBubble: (conteo, count) => crearIconoCluster(conteo, count, atenuarFondo),
      renderPunto: (props) => {
        const zona = zonasPorId.get(String(props.id))
        const cruzada = zonasCruzadasIds.has(zona.id)
        const resaltada = zonaResaltada === zona.id
        const size = (resaltada ? 14 : zona.ajuste.nivel === 'critico' ? 11 : 8) * 2
        const color = cruzada || resaltada ? '#4FA8E8' : NIVELES[zona.ajuste.nivel].color
        const el = elementoCirculo({
          size, color,
          fillColor: NIVELES[zona.ajuste.nivel].color,
          fillOpacity: 0.75 * atenuarFondo,
          weight: cruzada || zona.ajuste.subio || resaltada ? 3 : 2,
        })
        el.className = `capa-fondo-nav ${zona.ajuste.nivel === 'critico' || resaltada ? 'pulse-marker' : ''}`
        return el
      },
      onClickPunto: (id) => {
        const zona = zonasPorId.get(String(id))
        onClickZonaRef.current?.(zona)
      },
    })
    return limpiar
     
  }, [capaMapa, zonasFiltradas, zonaResaltada, zonasCruzadasIds, atenuarFondo, version])

  // --- corredores de riesgo (capaMapa === 'corredores') ---------------------
  useEffect(() => {
    const map = mapRef.current
    if (!map || version === 0) return
    const sourceId = 'corredores'
    const layerId = 'corredores-layer'
    if (capaMapa !== 'corredores') {
      if (map.getLayer(layerId)) map.removeLayer(layerId)
      if (map.getSource(sourceId)) map.removeSource(sourceId)
      return
    }
    // Antes, TODOS los corredores se dibujaban con el mismo ancho (5) y
    // opacidad (0.75) sin importar el nivel de riesgo -- como la mayoría de
    // las avenidas del GBA tienen algún corredor cargado, con capaMapa
    // "corredores" prendida el mapa quedaba pintado de punta a punta (Rodo
    // lo vio en captura real), y esa saturación visual tapa justo lo que la
    // capa debería resaltar: dónde está el riesgo de verdad. Ahora el ancho
    // y la opacidad escalan con el nivel -- bajo casi no compite con el
    // mapa base, crítico se ve grueso y sólido -- para que el ojo vaya
    // directo a lo que importa en vez de a una alfombra de líneas de color.
    const ANCHO_POR_NIVEL = { bajo: 1.5, medio: 3, alto: 4.5, critico: 6 }
    const OPACIDAD_POR_NIVEL = { bajo: 0.35, medio: 0.55, alto: 0.75, critico: 0.9 }
    const features = corredoresFiltrados.map((c) => ({
      type: 'Feature',
      geometry: { type: 'LineString', coordinates: c.geometria.map(([lat, lng]) => [lng, lat]) },
      properties: {
        id: c.id,
        color: NIVELES[c.nivel_riesgo]?.color || NIVELES.bajo.color,
        ancho: ANCHO_POR_NIVEL[c.nivel_riesgo] ?? ANCHO_POR_NIVEL.bajo,
        opacidad: OPACIDAD_POR_NIVEL[c.nivel_riesgo] ?? OPACIDAD_POR_NIVEL.bajo,
      },
    }))
    map.addSource(sourceId, { type: 'geojson', data: { type: 'FeatureCollection', features } })
    map.addLayer({
      id: layerId,
      type: 'line',
      source: sourceId,
      layout: { 'line-cap': 'round', 'line-join': 'round' },
      paint: {
        'line-color': ['get', 'color'],
        'line-width': ['get', 'ancho'],
        'line-opacity': ['*', ['get', 'opacidad'], atenuarFondo],
      },
    })

    let popup
    const corredoresPorId = new Map(corredoresFiltrados.map((c) => [c.id, c]))
    const onClick = (e) => {
      const f = e.features[0]
      const c = corredoresPorId.get(f.properties.id)
      if (!c) return
      popup?.remove()
      popup = new Popup({ closeButton: true })
        .setLngLat(e.lngLat)
        .setHTML(`
          <div class="popup-content">
            <span class="popup-nivel" style="color:${NIVELES[c.nivel_riesgo]?.color}">${NIVELES[c.nivel_riesgo]?.label}</span>
            <strong>${c.calle}${c.tramos_totales > 1 ? ` — tramo ${c.tramo}/${c.tramos_totales}` : ''}</strong>
            <span>${c.cantidad_siniestros} siniestros históricos · ${c.mortales} mortales · ${c.graves} graves</span>
          </div>
        `)
        .addTo(map)
    }
    const cursorOn = () => { map.getCanvas().style.cursor = 'pointer' }
    const cursorOff = () => { map.getCanvas().style.cursor = '' }
    map.on('click', layerId, onClick)
    map.on('mouseenter', layerId, cursorOn)
    map.on('mouseleave', layerId, cursorOff)

    return () => {
      popup?.remove()
      map.off('click', layerId, onClick)
      map.off('mouseenter', layerId, cursorOn)
      map.off('mouseleave', layerId, cursorOff)
      if (map.getLayer(layerId)) map.removeLayer(layerId)
      if (map.getSource(sourceId)) map.removeSource(sourceId)
    }
     
  }, [capaMapa, corredoresFiltrados, atenuarFondo, version])

  // --- cluster de inseguridad (delitos GCBA) --------------------------------
  useEffect(() => {
    const map = mapRef.current
    if (!map || version === 0 || capaInseguridad === 'apagado') return
    const sourceId = 'inseguridad'
    const features = inseguridadFiltrada.map((h) => ({
      type: 'Feature',
      geometry: { type: 'Point', coordinates: [h.longitud, h.latitud] },
      properties: { id: h.id, nivel: h.nivel_riesgo },
    }))
    const porId = new Map(inseguridadFiltrada.map((h) => [String(h.id), h]))
    let popup

    const limpiar = montarCapaClusterizada(map, {
      sourceId,
      features,
      radius: 60,
      maxZoom: 16,
      renderBubble: crearIconoClusterInseguridad,
      renderPunto: (props) => {
        const h = porId.get(String(props.id))
        const size = (h.nivel_riesgo === 'critico' ? 15 : h.nivel_riesgo === 'alto' ? 12 : 9) * 2
        const color = NIVELES_INSEGURIDAD_COLOR[h.nivel_riesgo] || NIVELES_INSEGURIDAD_COLOR.bajo
        const el = elementoCirculo({ size, color, fillOpacity: 0.4, weight: 1 })
        el.className = `capa-fondo-nav ${h.nivel_riesgo === 'critico' ? 'pulse-marker' : ''}`
        return el
      },
      onClickPunto: (id, coords) => {
        const h = porId.get(String(id))
        popup?.remove()
        popup = new Popup({ closeButton: true })
          .setLngLat(coords)
          .setHTML(`
            <div class="popup-content">
              <span class="popup-nivel" style="color:${NIVELES_INSEGURIDAD_COLOR[h.nivel_riesgo]}">${NIVELES[h.nivel_riesgo]?.label}</span>
              <strong>${h.cantidad_delitos} delitos históricos (${h.tipo_delito_moda || 'varios'})</strong>
              <span>Comuna ${h.comuna_moda} · datos oficiales del GCBA, últimos 3 años</span>
            </div>
          `)
          .addTo(map)
      },
    })
    return () => { popup?.remove(); limpiar() }
     
  }, [capaInseguridad, inseguridadFiltrada, version])

  // --- reportes colaborativos (no clusterizados) ----------------------------
  useEffect(() => {
    const map = mapRef.current
    if (!map || version === 0) return
    let popup
    const markers = reportes.map((rep) => {
      const color = rep.esPropio ? '#FFC933' : '#B98CFF'
      const vigenciaHoras = VIGENCIA_HORAS_POR_CATEGORIA[rep.categoria] || VIGENCIA_HORAS_DEFAULT
      const opacidad = opacidadPorAntiguedad(rep.creadoEn, vigenciaHoras, horaActual)
      const reciente = esReciente(rep.creadoEn, horaActual)
      const el = elementoCirculo({ size: 16, color, fillOpacity: 0.7 * opacidad, weight: 2 })
      el.className = reciente ? 'pulse-marker-report' : ''
      el.addEventListener('click', (e) => {
        e.stopPropagation()
        popup?.remove()
        const label = CATEGORIAS_REPORTE.find((c) => c.id === rep.categoria)?.label || rep.categoria
        const esPropio = rep.esPropio
        // Verificacion social: no se puede votar el propio reporte (el backend
        // igual lo rechaza, ver confirmar_reporte en main.py -- esto solo evita
        // mostrar botones que van a fallar).
        const botonesVoto = esPropio ? '' : `
              <div class="popup-votos">
                <button class="popup-voto-btn popup-voto-confirma" data-tipo="confirma">✓ Sigue ahí (${rep.confirmaciones || 0})</button>
                <button class="popup-voto-btn popup-voto-desmiente" data-tipo="desmiente">✕ Ya no está (${rep.desmentidas || 0})</button>
              </div>`
        popup = new Popup({ closeButton: true })
          .setLngLat([rep.lng, rep.lat])
          .setHTML(`
            <div class="popup-content">
              <span class="popup-nivel" style="color:${color}">${esPropio ? 'Tu reporte' : 'Reporte de otro usuario'} · ${formatearAntiguedad(rep.creadoEn, horaActual)}</span>
              <strong>${label}</strong>
              ${botonesVoto}
            </div>
          `)
          .addTo(map)
        popup.getElement()?.querySelectorAll('.popup-voto-btn').forEach((boton) => {
          boton.addEventListener('click', (ev) => {
            ev.stopPropagation()
            onVotarReporte?.(rep.id, boton.dataset.tipo)
            popup?.remove()
          })
        })
      })
      return new Marker({ element: el }).setLngLat([rep.lng, rep.lat]).addTo(map)
    })
    return () => { popup?.remove(); markers.forEach((m) => m.remove()) }

  }, [reportes, horaActual, version, onVotarReporte])

  // --- reportes de prensa (noticias de robos scrapeadas) --------------------
  // Capa separada de "reportes colaborativos": vigencia, semántica y fuente
  // distintas (ver la nota larga en backend/main.py sobre por qué). Click en
  // el ícono abre la nota original en una pestaña nueva -- esta capa no
  // permite votar/confirmar como los reportes de usuarios, no tiene sentido
  // "desmentir" una noticia ya publicada.
  useEffect(() => {
    const map = mapRef.current
    if (!map || version === 0) return
    let popup
    const markers = (reportesPrensa || []).map((rep) => {
      const el = elementoMarcadorPrensa(rep.nivelPrecision, rep.tipoIncidente)
      el.addEventListener('click', (e) => {
        e.stopPropagation()
        popup?.remove()
        const etiquetaTipo = ETIQUETA_TIPO_INCIDENTE[rep.tipoIncidente] ?? ETIQUETA_TIPO_INCIDENTE.robo
        popup = new Popup({ closeButton: true, maxWidth: '260px' })
          .setLngLat([rep.lng, rep.lat])
          .setDOMContent(contenidoPopupPrensa(rep, etiquetaTipo, horaActualRef.current))
          .addTo(map)
      })
      return new Marker({ element: el }).setLngLat([rep.lng, rep.lat]).addTo(map)
    })
    return () => { popup?.remove(); markers.forEach((m) => m.remove()) }

  // No depende del reloj de la interfaz: antes ese tick rearmaba todos los
  // marcadores cada segundo y el cleanup cerraba el popup inmediatamente.
  }, [reportesPrensa, version])

  // --- rutas calculadas (polilíneas) ----------------------------------------
  useEffect(() => {
    const map = mapRef.current
    if (!map || version === 0) return
    const sourceId = 'rutas'
    const layerId = 'rutas-layer'
    const layerCasingId = 'rutas-layer-casing'
    if (rutasCalculadas.length === 0) {
      if (map.getLayer(layerId)) map.removeLayer(layerId)
      if (map.getLayer(layerCasingId)) map.removeLayer(layerCasingId)
      if (map.getSource(sourceId)) map.removeSource(sourceId)
      return
    }
    const features = []
    rutasCalculadas.forEach((r, i) => {
      const esSeleccionada = i === rutaSeleccionada
      const coordsLngLat = r.coords.map(([lat, lng]) => [lng, lat])
      // Mientras se navega, la ruta seleccionada se corta en dos tramos: lo
      // ya recorrido (atenuado) y lo que falta (destacado) -- el mismo
      // truco visual de Waze/Maps para que de un vistazo se lea cuánto
      // avanzaste, en vez de una sola línea pareja de punta a punta.
      if (esSeleccionada && progresoRutaIndice != null && progresoRutaIndice > 0 && progresoRutaIndice < coordsLngLat.length - 1) {
        features.push({
          type: 'Feature',
          geometry: { type: 'LineString', coordinates: coordsLngLat.slice(0, progresoRutaIndice + 1) },
          properties: { idx: i, seleccionada: true, recorrido: true },
        })
        features.push({
          type: 'Feature',
          geometry: { type: 'LineString', coordinates: coordsLngLat.slice(progresoRutaIndice) },
          properties: { idx: i, seleccionada: true, recorrido: false },
        })
      } else {
        features.push({
          type: 'Feature',
          geometry: { type: 'LineString', coordinates: coordsLngLat },
          properties: { idx: i, seleccionada: esSeleccionada, recorrido: false },
        })
      }
    })
    // La ruta seleccionada se dibuja arriba: se ordenan las features para que
    // queden últimas (MapLibre pinta en orden de aparición dentro del source).
    features.sort((a, b) => Number(a.properties.seleccionada) - Number(b.properties.seleccionada))

    if (map.getSource(sourceId)) {
      map.getSource(sourceId).setData({ type: 'FeatureCollection', features })
    } else {
      map.addSource(sourceId, { type: 'geojson', data: { type: 'FeatureCollection', features } })
      // Casing (contorno oscuro debajo de la línea de color): sin esto, la
      // ruta seleccionada es una línea plana de un solo color que se pierde
      // contra el satelital de fondo (techos, agua, tierra pueden dar casi
      // el mismo tono). Waze/Maps siempre dibujan un borde de contraste
      // detrás de la ruta activa, sin importar qué mapa base tengan debajo
      // -- acá mismo truco: una segunda línea más ancha y oscura, solo para
      // la ruta seleccionada (las alternativas ya son grises punteadas, no
      // necesitan el refuerzo). Se agrega ANTES que la línea de color para
      // que quede pintada por debajo (MapLibre pinta en orden de capas).
      map.addLayer({
        id: layerCasingId,
        type: 'line',
        source: sourceId,
        layout: { 'line-cap': 'round', 'line-join': 'round' },
        filter: ['==', ['get', 'seleccionada'], true],
        paint: {
          'line-color': '#0B1620',
          'line-width': ['case', ['get', 'recorrido'], 7, 8],
          'line-opacity': ['case', ['get', 'recorrido'], 0.4, 0.6],
        },
      })
      map.addLayer({
        id: layerId,
        type: 'line',
        source: sourceId,
        layout: { 'line-cap': 'round', 'line-join': 'round' },
        paint: {
          'line-color': ['case', ['get', 'recorrido'], '#3A4048', ['get', 'seleccionada'], '#4FA8E8', '#6B7178'],
          'line-width': ['case', ['get', 'seleccionada'], 5, 4],
          'line-opacity': ['case', ['get', 'recorrido'], 0.35, ['get', 'seleccionada'], 0.9, 0.45],
          'line-dasharray': ['case', ['get', 'seleccionada'], ['literal', [1, 0]], ['literal', [2, 2]]],
        },
      })
      const onClick = (e) => onClickRutaRef.current?.(e.features[0].properties.idx)
      const cursorOn = () => { map.getCanvas().style.cursor = 'pointer' }
      const cursorOff = () => { map.getCanvas().style.cursor = '' }
      map.on('click', layerId, onClick)
      map.on('mouseenter', layerId, cursorOn)
      map.on('mouseleave', layerId, cursorOff)
    }
    // No hace falta cleanup de listeners acá: se recrean solo cuando el layer
    // se recrea (rutasCalculadas pasa de 0 a >0), y el layer/source se limpian
    // arriba cuando rutasCalculadas vuelve a 0.
     
  }, [rutasCalculadas, rutaSeleccionada, progresoRutaIndice, version])

  // --- origen / destino (marcadores simples y estáticos) --------------------
  useEffect(() => {
    const map = mapRef.current
    if (!map || version === 0) return
    const markers = []
    if (origenPunto) {
      const el = elementoCirculo({ size: 16, color: '#3DDC84', fillOpacity: 1, weight: 3 })
      markers.push(new Marker({ element: el }).setLngLat([origenPunto.lng, origenPunto.lat]).addTo(map))
    }
    if (destinoPunto) {
      const el = elementoCirculo({ size: 16, color: '#FF3B3B', fillOpacity: 1, weight: 3 })
      markers.push(new Marker({ element: el }).setLngLat([destinoPunto.lng, destinoPunto.lat]).addTo(map))
    }
    if (ubicacionReporte) {
      // Marcador visible del punto donde va a quedar el reporte -- antes no
      // había NINGÚN indicio visual de dónde se iba a guardar (ni siquiera
      // cuando el punto era el real del GPS), lo que hacía imposible
      // corregirlo si el GPS pifiaba la esquina.
      const el = elementoCirculo({ size: 18, color: '#FFC933', fillOpacity: 0.85, weight: 3 })
      el.className = 'pulse-marker-report'
      markers.push(new Marker({ element: el }).setLngLat([ubicacionReporte.lng, ubicacionReporte.lat]).addTo(map))
    }
    return () => markers.forEach((m) => m.remove())
     
  }, [origenPunto, destinoPunto, ubicacionReporte, version])

  // --- mi ubicación: marker persistente con movimiento animado --------------
  // Antes este marker se destruía y se recreaba en CADA fix de GPS (cada
  // pocos segundos vía watchPosition), lo que hacía que el puck "saltara" de
  // punto a punto en vez de deslizarse como en Waze/Maps. Ahora el Marker
  // vive en un ref y se recrea solo cuando cambia su estilo visual (puck de
  // navegación vs. punto pulsante) o cuando aparece/desaparece la ubicación
  // -- el desplazamiento entre fixes lo anima el efecto de abajo con
  // requestAnimationFrame, sin tocar la instancia del marker.
  const miUbicacionMarkerRef = useRef(null)
  const miUbicacionMostradaRef = useRef(null)
  const miUbicacionAnimRef = useRef(null)

  useEffect(() => {
    const map = mapRef.current
    if (!map || version === 0) return
    if (miUbicacionMarkerRef.current) {
      miUbicacionMarkerRef.current.remove()
      miUbicacionMarkerRef.current = null
    }
    if (miUbicacion) {
      let el
      if (vistaNavegacion) {
        // Puck direccional tipo Waze/Google Maps en vez del punto pulsante
        // genérico: en navegación importa ver hacia dónde se apunta, no solo
        // dónde se está. El marker de MapLibre no rota con el bearing del
        // mapa (queda fijo a la pantalla), y como la cámara ya gira para
        // dejar el rumbo actual "arriba" (ver el efecto de cámara más
        // arriba), la flecha va siempre apuntando hacia arriba -- si en
        // cambio se mostrara sin la vista inclinada, ahí sí haría falta
        // rotarla por rumboActual, porque el norte queda fijo arriba.
        el = document.createElement('div')
        el.className = 'puck-navegacion'
        // SVG en vez del truco de borders-CSS de antes (un triángulo chato,
        // sin volumen): círculo con relleno solido + un óvalo de brillo
        // (simula una fuente de luz arriba a la izquierda, mismo truco que
        // da la sensación de "objeto" en vez de "recorte plano") + flecha
        // con muesca en la base, la forma clásica de Waze/Maps.
        el.innerHTML = `
          <svg width="34" height="34" viewBox="0 0 34 34" class="puck-navegacion-svg">
            <circle cx="17" cy="17" r="11" fill="#4FA8E8" stroke="#0B1620" stroke-width="2.5" />
            <ellipse cx="13" cy="10.5" rx="4" ry="2.3" fill="#ffffff" opacity="0.3" />
            <path d="M17 7 L23.5 21.5 L17 17.6 L10.5 21.5 Z" fill="#0B1620" />
          </svg>
        `
      } else {
        el = elementoCirculo({ size: 14, color: '#4FA8E8', fillOpacity: 0.9, weight: 3 })
        el.className = 'pulse-marker-yo'
      }
      miUbicacionMarkerRef.current = new Marker({ element: el, rotationAlignment: 'viewport' })
        .setLngLat([miUbicacion.lng, miUbicacion.lat])
        .addTo(map)
      miUbicacionMostradaRef.current = { lng: miUbicacion.lng, lat: miUbicacion.lat }
    } else {
      miUbicacionMostradaRef.current = null
    }
    return () => {
      if (miUbicacionAnimRef.current) cancelAnimationFrame(miUbicacionAnimRef.current)
      miUbicacionMarkerRef.current?.remove()
      miUbicacionMarkerRef.current = null
    }
    // Se reconstruye solo por versión, por cambio del "modo" de puck o
    // cuando la ubicación aparece/desaparece -- NO en cada coordenada nueva
    // (eso lo maneja el efecto de animación de abajo).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [vistaNavegacion, version, !!miUbicacion])

  useEffect(() => {
    const marker = miUbicacionMarkerRef.current
    if (!marker || !miUbicacion) return
    const desde = miUbicacionMostradaRef.current || { lng: miUbicacion.lng, lat: miUbicacion.lat }
    const hasta = { lng: miUbicacion.lng, lat: miUbicacion.lat }
    if (miUbicacionAnimRef.current) cancelAnimationFrame(miUbicacionAnimRef.current)
    // 900ms es aproximadamente el intervalo típico entre fixes de
    // watchPosition -- así el puck llega a la posición nueva justo cuando
    // (o poco antes de) que llegue la siguiente, en vez de quedarse quieto
    // esperando o de completar el salto instantáneamente.
    const duracionMs = 900
    const inicio = performance.now()
    const paso = (ahora) => {
      const t = Math.min(1, (ahora - inicio) / duracionMs)
      const suavizado = 1 - (1 - t) * (1 - t) // ease-out
      const lng = desde.lng + (hasta.lng - desde.lng) * suavizado
      const lat = desde.lat + (hasta.lat - desde.lat) * suavizado
      marker.setLngLat([lng, lat])
      miUbicacionMostradaRef.current = { lng, lat }
      miUbicacionAnimRef.current = t < 1 ? requestAnimationFrame(paso) : null
    }
    miUbicacionAnimRef.current = requestAnimationFrame(paso)
    return () => {
      if (miUbicacionAnimRef.current) cancelAnimationFrame(miUbicacionAnimRef.current)
    }
  }, [miUbicacion])

  // --- vuelo a un punto (buscador, favoritos, "ver en mapa", etc.) ----------
  // Lo dispara App.jsx via onReady exponiendo el mapa (ver App.jsx: efecto
  // sobre `vuelo`, usa el mapa directamente, no hace falta duplicar acá).

  return <div ref={contenedorRef} className="map" />
}

export const MapaMotoSafe = memo(MapaMotoSafeInner)
