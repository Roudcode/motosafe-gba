// Helpers de presentación: iconos/textos de clima y maniobras de ruta, sonido de
// alerta, e ícono de burbuja para clusters de hotspots en el mapa (usa Leaflet).

import L from 'leaflet'
import {
  Sun, CloudSun, CloudFog, CloudDrizzle, CloudRain, CloudSnow, CloudLightning, Thermometer,
  Flag, Navigation, RefreshCw, ArrowLeft, ArrowRight, Undo2, ArrowUp,
} from 'lucide-react'
import { NIVELES } from '../constants'

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

export function crearIconoCluster(cluster) {
  const count = cluster.getChildCount()
  const hijos = cluster.getAllChildMarkers()

  // El relleno del cluster refleja el nivel de riesgo dominante entre sus hotspots,
  // no solo si "hay o no" un caso crítico adentro (como era antes). Si al menos un
  // 15% de los hotspots del cluster son críticos, el cluster entero se pinta crítico
  // — la misma lógica de "priorizar no subestimar" que ya se usa en los umbrales del
  // modelo (backend/main.py: nivel_desde_probabilidades). Si no, se usa el nivel más
  // frecuente entre los hotspots agrupados.
  const conteoPorNivel = { bajo: 0, medio: 0, alto: 0, critico: 0 }
  hijos.forEach((m) => {
    const nivel = m.options.nivelData
    if (conteoPorNivel[nivel] !== undefined) conteoPorNivel[nivel] += 1
  })
  const propCritico = count > 0 ? conteoPorNivel.critico / count : 0
  const nivelDominante = propCritico >= 0.15
    ? 'critico'
    : Object.entries(conteoPorNivel).sort((a, b) => b[1] - a[1])[0][0]

  const color = NIVELES[nivelDominante].color
  const colorTexto = TEXTO_SOBRE_NIVEL[nivelDominante]
  const size = count < 10 ? 34 : count < 30 ? 42 : 50

  return L.divIcon({
    html: `<div class="cluster-bubble ${nivelDominante === 'critico' ? 'cluster-critico' : ''}" style="width:${size}px;height:${size}px;line-height:${size}px;background:${color}E6;border-color:${color};color:${colorTexto};">${count}</div>`,
    className: 'cluster-icon-wrapper',
    iconSize: L.point(size, size),
  })
}
