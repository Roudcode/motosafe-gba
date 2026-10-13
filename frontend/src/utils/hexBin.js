// Agrupa zonas de riesgo en una grilla hexagonal ("hexbin"), pedido de Rodo
// después de ver mapas de cobertura tipo Uber/Cabify: un hexágono con borde
// nítido se lee de un vistazo mucho mejor que un heatmap difuminado para
// "qué tan cubierta de riesgo está esta zona" -- el borde dice dónde
// termina, el heatmap no.
//
// Matemática de grilla hexagonal "pointy-top" estándar (coordenadas axiales,
// ver redblobgames.com/grids/hexagons -- es la referencia de siempre para
// esto). Se opera en metros locales, no en grados: lat/lng no son una
// grilla uniforme (un grado de longitud mide menos que uno de latitud,
// salvo en el ecuador), así que hexágonos "regulares" en grados saldrían
// alargados. La conversión grado->metro es lineal y aproximada (válida a
// la escala de GBA, no pensada para otras latitudes del planeta).
//
// Deliberadamente sin sumar una librería (turf, h3-js) para esto: es la
// misma cantidad de matemática ya resuelta en cualquier lado, no una
// dependencia nueva para ~70 líneas.

const LAT_REF = -34.6 // centro aprox. de GBA -- solo fija la escala de conversión, no importa el metro exacto
const M_POR_GRADO_LAT = 110540
const M_POR_GRADO_LNG = 111320 * Math.cos(LAT_REF * Math.PI / 180)

function aMetros(lat, lng) {
  return { x: lng * M_POR_GRADO_LNG, y: lat * M_POR_GRADO_LAT }
}

function metrosALatLng(x, y) {
  return { lat: y / M_POR_GRADO_LAT, lng: x / M_POR_GRADO_LNG }
}

// Redondeo a coordenadas axiales enteras vía cúbicas (técnica estándar:
// redondear en cúbicas y corregir la componente con más error de redondeo,
// así siempre da un hexágono válido en vez de "entre dos").
function redondearAxial(qFloat, rFloat) {
  const xFloat = qFloat
  const zFloat = rFloat
  const yFloat = -xFloat - zFloat
  let x = Math.round(xFloat)
  const y = Math.round(yFloat)
  let z = Math.round(zFloat)
  const dx = Math.abs(x - xFloat)
  const dy = Math.abs(y - yFloat)
  const dz = Math.abs(z - zFloat)
  // Si el mayor error de redondeo cayó en y (la tercera coordenada cúbica,
  // ni siquiera forma parte del resultado axial), no hace falta corregir
  // nada: x/z ya quedaron bien y son los dos que se devuelven.
  if (dx > dy && dx > dz) x = -y - z
  else if (dy <= dz) z = -x - y
  return { q: x, r: z }
}

function pixelAAxial(x, y, size) {
  const qFloat = (Math.sqrt(3) / 3 * x - 1 / 3 * y) / size
  const rFloat = (2 / 3 * y) / size
  return redondearAxial(qFloat, rFloat)
}

function axialACentro(q, r, size) {
  const x = size * (Math.sqrt(3) * q + Math.sqrt(3) / 2 * r)
  const y = size * (3 / 2 * r)
  return { x, y }
}

function esquinasHexagono(cx, cy, size) {
  const puntos = []
  for (let i = 0; i < 6; i++) {
    const anguloGrados = 60 * i - 30 // pointy-top: primer vértice arriba
    const anguloRad = (Math.PI / 180) * anguloGrados
    puntos.push([cx + size * Math.cos(anguloRad), cy + size * Math.sin(anguloRad)])
  }
  return puntos
}

// zonas: [{lat, lng, cantidad, nivel}]. nivel = el más alto de ORDEN_NIVELES
// presente en la celda, no un promedio -- un hexágono con una zona crítica
// entre varias de nivel bajo sigue siendo un hexágono que conviene mirar,
// promediarlo lo escondería. radioMetros: tamaño del hexágono (centro a
// vértice). Devuelve un FeatureCollection de polígonos, uno por celda no
// vacía. Las propiedades de cada feature incluyen, además del total y el
// nivel máximo, el desglose `cantidad_<nivel>` por nivel -- son propiedades
// planas (no un objeto anidado) porque así las necesita MapLibre para
// mostrarlas en un popup al hacer click en el hexágono.
export function hexBinZonas(zonas, radioMetros, ordenNiveles) {
  const celdas = new Map()
  for (const zona of zonas) {
    const { x, y } = aMetros(zona.lat, zona.lng)
    const { q, r } = pixelAAxial(x, y, radioMetros)
    const clave = `${q},${r}`
    let celda = celdas.get(clave)
    if (!celda) {
      celda = { q, r, cantidad: 0, nivelIndiceMax: 0, cantidadPorNivel: {} }
      celdas.set(clave, celda)
    }
    const cantidad = zona.cantidad || 0
    celda.cantidad += cantidad
    celda.cantidadPorNivel[zona.nivel] = (celda.cantidadPorNivel[zona.nivel] || 0) + cantidad
    const indiceNivel = ordenNiveles.indexOf(zona.nivel)
    if (indiceNivel > celda.nivelIndiceMax) celda.nivelIndiceMax = indiceNivel
  }
  const features = []
  for (const celda of celdas.values()) {
    const { x, y } = axialACentro(celda.q, celda.r, radioMetros)
    const esquinas = esquinasHexagono(x, y, radioMetros).map(([ex, ey]) => {
      const { lat, lng } = metrosALatLng(ex, ey)
      return [lng, lat]
    })
    esquinas.push(esquinas[0])
    const propiedades = { cantidad: celda.cantidad, nivel: ordenNiveles[celda.nivelIndiceMax] }
    for (const nivel of ordenNiveles) propiedades[`cantidad_${nivel}`] = celda.cantidadPorNivel[nivel] || 0
    features.push({
      type: 'Feature',
      geometry: { type: 'Polygon', coordinates: [esquinas] },
      properties: propiedades,
    })
  }
  return { type: 'FeatureCollection', features }
}
