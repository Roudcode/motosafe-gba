// Helpers de presentación: iconos/textos de clima y maniobras de ruta, sonido de
// alerta, y armado del HTML de burbuja para clusters de hotspots en el mapa.
// Agnóstico del motor de mapa (antes usaba L.divIcon de Leaflet; ahora
// MapaMotoSafe.jsx arma el DOM element a partir del HTML que devuelven estas
// funciones, para usarlo con maplibregl.Marker).

import {
  Sun, CloudSun, CloudFog, CloudDrizzle, CloudRain, CloudSnow, CloudLightning, Thermometer,
  Flag, Navigation, RefreshCw, ArrowLeft, ArrowRight, Undo2, ArrowUp,
} from 'lucide-react'
import { NIVELES, NIVELES_INSEGURIDAD_COLOR } from '../constants'

export function iconoClima(code) {
  if (code === 0) return { Icon: Sun, label: 'Despejado' }
  if ([1, 2, 3].includes(code)) return { Icon: CloudSun, label: 'Parcialmente nublado' }
  if ([45, 48].includes(code)) return { Icon: CloudFog, label: 'Niebla' }
  if ([51, 53, 55, 56, 57].includes(code)) return { Icon: CloudDrizzle, label: 'Llovizna' }
  if ([61, 63, 65, 66, 67, 80, 81, 82].includes(code)) return { Icon: CloudRain, label: 'Lluvia' }
  if ([71, 73, 75, 77, 85, 86].includes(code)) return { Icon: CloudSnow, label: 'Nieve' }
  if ([95, 96, 99].includes(code)) return { Icon: CloudLightning, label: 'Tormenta' }
  return { Icon: Thermometer, label: 'Sin datos' }
}

export function reproducirBeep() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)()
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.connect(gain)
    gain.connect(ctx.destination)
    osc.frequency.value = 880
    gain.gain.setValueAtTime(0.15, ctx.currentTime)
    osc.start()
    osc.stop(ctx.currentTime + 0.3)
  } catch { /* silencioso si el navegador bloquea audio sin interacción previa */ }
}

export function textoManiobra(paso) {
  const dir = {
    left: 'a la izquierda', right: 'a la derecha',
    'slight left': 'levemente a la izquierda', 'slight right': 'levemente a la derecha',
    'sharp left': 'bruscamente a la izquierda', 'sharp right': 'bruscamente a la derecha',
    straight: 'derecho', uturn: 'en U',
  }[paso.modificador] || ''
  const conCalle = paso.calle && paso.calle !== 'la vía'
  if (paso.tipo === 'depart') return conCalle ? `Salí por ${paso.calle}` : 'Salí y continuá'
  if (paso.tipo === 'arrive') return 'Llegaste a destino'
  if (paso.tipo === 'turn') return conCalle ? `Doblá ${dir} en ${paso.calle}` : `Doblá ${dir}`
  if (paso.tipo === 'roundabout' || paso.tipo === 'rotary') return conCalle ? `En la rotonda, tomá ${paso.calle}` : 'Tomá la rotonda'
  if (paso.tipo === 'merge') return conCalle ? `Incorporate a ${paso.calle}` : 'Incorporate a la vía'
  if (paso.tipo === 'fork') return conCalle ? `Mantenete ${dir} hacia ${paso.calle}` : `Mantenete ${dir}`
  if (paso.tipo === 'end of road') return conCalle ? `Al final de la calle, doblá ${dir} hacia ${paso.calle}` : `Al final de la calle, doblá ${dir}`
  return conCalle ? `Continuá por ${paso.calle}` : 'Continuá derecho'
}

export function iconoManiobra(paso) {
  if (paso.tipo === 'arrive') return Flag
  if (paso.tipo === 'depart') return Navigation
  if (paso.tipo === 'roundabout' || paso.tipo === 'rotary') return RefreshCw
  if (paso.modificador?.includes('left')) return ArrowLeft
  if (paso.modificador?.includes('right')) return ArrowRight
  if (paso.modificador === 'uturn') return Undo2
  return ArrowUp
}

// Colores de texto legibles sobre cada color de nivel de riesgo (no dependen del
// tema claro/oscuro: son fijos porque el fondo de la burbuja siempre es el color
// de riesgo, que es el mismo en los dos temas).
const TEXTO_SOBRE_NIVEL = { bajo: '#0F1A14', medio: '#1F1A05', alto: '#2A1204', critico: '#FCEAEA' }
const TEXTO_SOBRE_NIVEL_INSEGURIDAD = { bajo: '#2A0F3D', medio: '#2A0F3D', alto: '#FDF0FF', critico: '#FDF0FF' }

// Nivel dominante entre los hotspots agrupados en un cluster: si al menos un
// 15% son críticos, el cluster entero se pinta crítico (misma lógica de
// "priorizar no subestimar" que los umbrales del modelo en backend/main.py,
// nivel_desde_probabilidades); si no, se usa el nivel más frecuente.
//
// Antes recibía los child markers de Leaflet.markercluster y contaba a mano;
// ahora recibe directamente el conteo por nivel (lo arma MapLibre solo, vía
// `clusterProperties` al definir el GeoJSON source -- ver MapaMotoSafe.jsx),
// asi que la funcion queda mas simple y sigue siendo pura/testeable.
export function nivelDominanteDe(conteoPorNivel) {
  const count = Object.values(conteoPorNivel).reduce((a, b) => a + b, 0)
  const propCritico = count > 0 ? (conteoPorNivel.critico || 0) / count : 0
  return propCritico >= 0.15
    ? 'critico'
    : Object.entries(conteoPorNivel).sort((a, b) => b[1] - a[1])[0][0]
}

function burbujaClusterHtml({ count, nivelDominante, colorPorNivel, textoPorNivel, size, opacidad, claseForma }) {
  const color = colorPorNivel[nivelDominante]
  const colorTexto = textoPorNivel[nivelDominante]
  return `<div class="cluster-bubble ${claseForma || ''} ${nivelDominante === 'critico' ? 'cluster-critico' : ''}" style="width:${size}px;height:${size}px;line-height:${size}px;background:${color}E6;border-color:${color};color:${colorTexto};opacity:${opacidad};">${count}</div>`
}

// opacidad: se usa para atenuar los clusters de siniestros cuando la capa de
// inseguridad esta prendida encima (ver App.jsx, atenuarFondo), asi la capa
// que el usuario acaba de activar queda como protagonista en vez de competir
// en igualdad de jerarquia visual con lo que ya estaba.
//
// `conteoPorNivel` viene de las clusterProperties del source de MapLibre:
// { bajo, medio, alto, critico, point_count }.
export function crearIconoCluster(conteoPorNivel, count, opacidad = 1) {
  const nivelDominante = nivelDominanteDe(conteoPorNivel)
  const size = count < 10 ? 34 : count < 30 ? 42 : 50
  const colorPorNivel = Object.fromEntries(Object.entries(NIVELES).map(([k, v]) => [k, v.color]))
  return {
    html: burbujaClusterHtml({ count, nivelDominante, colorPorNivel, textoPorNivel: TEXTO_SOBRE_NIVEL, size, opacidad, claseForma: '' }),
    size,
  }
}

// Paleta violeta/magenta (NIVELES_INSEGURIDAD_COLOR) y forma de burbuja distinta
// (cluster-bubble-inseguridad, ver App.css) para que un cluster de inseguridad
// no se confunda con uno de siniestros ni siquiera de reojo. Nunca se atenúa
// (siempre opacidad 1): es la capa que el usuario prendió a proposito, la que
// se atenúa es el fondo, no ella.
export function crearIconoClusterInseguridad(conteoPorNivel, count) {
  const nivelDominante = nivelDominanteDe(conteoPorNivel)
  const size = count < 10 ? 30 : count < 30 ? 38 : 46
  return {
    html: burbujaClusterHtml({ count, nivelDominante, colorPorNivel: NIVELES_INSEGURIDAD_COLOR, textoPorNivel: TEXTO_SOBRE_NIVEL_INSEGURIDAD, size, opacidad: 1, claseForma: 'cluster-bubble-inseguridad' }),
    size,
  }
}
