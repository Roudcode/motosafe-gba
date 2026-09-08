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

import { useEffect, useRef, useState } from 'react'
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

  let markersOnScreen = {}

  function actualizar() {
    if (!map.getSource(sourceId) || !map.isSourceLoaded(sourceId)) return
    const nuevos = {}
    const vistas = map.querySourceFeatures(sourceId)
    for (const feature of vistas) {
      const coords = feature.geometry.coordinates
      const props = feature.properties
      if (props.cluster) {
        const id = `c${props.cluster_id}`
        nuevos[id] = markersOnScreen[id] || crearMarkerCluster(coords, props)
      } else {
        const id = `p${props.id}`
        nuevos[id] = markersOnScreen[id] || crearMarkerPunto(coords, props)
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
    const el = elementoDivIcono(html, size)
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
    if (map.getSource(sourceId)) map.removeSource(sourceId)
  }
}

export function MapaMotoSafe({
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
  autorId,
  horaActual,
  rutasCalculadas,
  rutaSeleccionada,
  onClickRuta,
  origenPunto,
  destinoPunto,
  miUbicacion,
  vistaNavegacion,
  rumboActual,
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
  useEffect(() => {
    campoActivoRef.current = campoActivo
    onClickMapaRef.current = onClickMapa
    onClickZonaRef.current = onClickZona
    onClickRutaRef.current = onClickRuta
  })

  // --- init del mapa (una sola vez) -----------------------------------------
  useEffect(() => {
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

    return () => {
      map.remove()
      mapRef.current = null
    }
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

  // --- pitch/bearing: vista inclinada real al entrar en navegación ---------
  useEffect(() => {
    const map = mapRef.current
    if (!map || version === 0) return
    map.easeTo({ pitch: vistaNavegacion ? PITCH_NAVEGACION : 0, bearing: vistaNavegacion ? (rumboActual || 0) : 0, duration: 700 })
  }, [vistaNavegacion, rumboActual, version])

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
        el.className = zona.ajuste.nivel === 'critico' || resaltada ? 'pulse-marker' : ''
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
    const features = corredoresFiltrados.map((c) => ({
      type: 'Feature',
      geometry: { type: 'LineString', coordinates: c.geometria.map(([lat, lng]) => [lng, lat]) },
      properties: { id: c.id, color: NIVELES[c.nivel_riesgo]?.color || NIVELES.bajo.color },
    }))
    map.addSource(sourceId, { type: 'geojson', data: { type: 'FeatureCollection', features } })
    map.addLayer({
      id: layerId,
      type: 'line',
      source: sourceId,
      layout: { 'line-cap': 'round', 'line-join': 'round' },
      paint: { 'line-color': ['get', 'color'], 'line-width': 5, 'line-opacity': 0.75 * atenuarFondo },
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
        el.className = h.nivel_riesgo === 'critico' ? 'pulse-marker' : ''
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
      const color = rep.autorId === autorId ? '#FFC933' : '#B98CFF'
      const vigenciaHoras = VIGENCIA_HORAS_POR_CATEGORIA[rep.categoria] || VIGENCIA_HORAS_DEFAULT
      const opacidad = opacidadPorAntiguedad(rep.creadoEn, vigenciaHoras, horaActual)
      const reciente = esReciente(rep.creadoEn, horaActual)
      const el = elementoCirculo({ size: 16, color, fillOpacity: 0.7 * opacidad, weight: 2 })
      el.className = reciente ? 'pulse-marker-report' : ''
      el.addEventListener('click', (e) => {
        e.stopPropagation()
        popup?.remove()
        const label = CATEGORIAS_REPORTE.find((c) => c.id === rep.categoria)?.label || rep.categoria
        popup = new Popup({ closeButton: true })
          .setLngLat([rep.lng, rep.lat])
          .setHTML(`
            <div class="popup-content">
              <span class="popup-nivel" style="color:${color}">${rep.autorId === autorId ? 'Tu reporte' : 'Reporte de otro usuario'} · ${formatearAntiguedad(rep.creadoEn, horaActual)}</span>
              <strong>${label}</strong>
            </div>
          `)
          .addTo(map)
      })
      return new Marker({ element: el }).setLngLat([rep.lng, rep.lat]).addTo(map)
    })
    return () => { popup?.remove(); markers.forEach((m) => m.remove()) }
     
  }, [reportes, autorId, horaActual, version])

  // --- rutas calculadas (polilíneas) ----------------------------------------
  useEffect(() => {
    const map = mapRef.current
    if (!map || version === 0) return
    const sourceId = 'rutas'
    const layerId = 'rutas-layer'
    if (rutasCalculadas.length === 0) {
      if (map.getLayer(layerId)) map.removeLayer(layerId)
      if (map.getSource(sourceId)) map.removeSource(sourceId)
      return
    }
    const features = rutasCalculadas.map((r, i) => ({
      type: 'Feature',
      geometry: { type: 'LineString', coordinates: r.coords.map(([lat, lng]) => [lng, lat]) },
      properties: { idx: i, seleccionada: i === rutaSeleccionada },
    }))
    // La ruta seleccionada se dibuja arriba: se ordenan las features para que
    // quede última (MapLibre pinta en orden de aparición dentro del source).
    features.sort((a, b) => Number(a.properties.seleccionada) - Number(b.properties.seleccionada))

    if (map.getSource(sourceId)) {
      map.getSource(sourceId).setData({ type: 'FeatureCollection', features })
    } else {
      map.addSource(sourceId, { type: 'geojson', data: { type: 'FeatureCollection', features } })
      map.addLayer({
        id: layerId,
        type: 'line',
        source: sourceId,
        layout: { 'line-cap': 'round', 'line-join': 'round' },
        paint: {
          'line-color': ['case', ['get', 'seleccionada'], '#4FA8E8', '#6B7178'],
          'line-width': ['case', ['get', 'seleccionada'], 5, 4],
          'line-opacity': ['case', ['get', 'seleccionada'], 0.9, 0.45],
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
     
  }, [rutasCalculadas, rutaSeleccionada, version])

  // --- origen / destino / mi ubicación (marcadores simples) -----------------
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
    if (miUbicacion) {
      const el = elementoCirculo({ size: 14, color: '#4FA8E8', fillOpacity: 0.9, weight: 3 })
      el.className = 'pulse-marker-yo'
      markers.push(new Marker({ element: el }).setLngLat([miUbicacion.lng, miUbicacion.lat]).addTo(map))
    }
    return () => markers.forEach((m) => m.remove())
     
  }, [origenPunto, destinoPunto, miUbicacion, version])

  // --- vuelo a un punto (buscador, favoritos, "ver en mapa", etc.) ----------
  // Lo dispara App.jsx via onReady exponiendo el mapa (ver App.jsx: efecto
  // sobre `vuelo`, usa el mapa directamente, no hace falta duplicar acá).

  return <div ref={contenedorRef} className="map" />
}
