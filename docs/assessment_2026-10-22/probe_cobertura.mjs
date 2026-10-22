// Importa las funciones de producción sin copiarlas ni modificarlas.
import fs from 'node:fs'
import path from 'node:path'
import {fileURLToPath, pathToFileURL} from 'node:url'
import {createRequire} from 'node:module'
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..')
const dataUrl = text => `data:text/javascript;base64,${Buffer.from(text).toString('base64')}`
const requireFrontend = createRequire(path.join(root,'frontend/package.json'))
const icons = pathToFileURL(requireFrontend.resolve('lucide-react')).href
const constants = dataUrl('import.meta.env = {};\n' + fs.readFileSync(path.join(root,'frontend/src/constants.js'),'utf8').replace("'lucide-react'",JSON.stringify(icons)))
const geo = dataUrl(fs.readFileSync(path.join(root,'frontend/src/utils/geoRiesgo.js'),'utf8').replace("'../constants'",JSON.stringify(constants)))
const risk = dataUrl(fs.readFileSync(path.join(root,'frontend/src/utils/riesgoRuta.js'),'utf8').replace("'../constants'",JSON.stringify(constants)).replace("'./geoRiesgo'",JSON.stringify(geo)))
const {calcularCoberturaPorFuente, calcularRutasConScore} = await import(risk)
const {distanciaKm} = await import(geo)
// Mismo segmento recto: 100 vértices en los primeros 110m y un extremo a 11km.
const denseStart = Array.from({length:100},(_,i)=>[-34.6+i*0.00001,-58.4])
const end = [-34.5,-58.4]
const routes = [{coords:[denseStart[0],end]},{coords:[...denseStart,end]}]
const zones = [{lat:-34.6,lng:-58.4,tipoRiesgo:'siniestro',nivel:'medio'}]
const coverage = calcularCoberturaPorFuente(routes,zones,0.6)
console.log(JSON.stringify({same_geometry_coverage:coverage,eligible_at_60pct:coverage.map(x=>x.siniestro>=0.6),length_km:distanciaKm(zones[0],{lat:end[0],lng:end[1]}),approx_length_coverage:0.6/distanciaKm(zones[0],{lat:end[0],lng:end[1]})},null,2))
console.log(JSON.stringify({missing_siniestro_fallback:calcularRutasConScore([routes[0]],[[]],[1],[{siniestro:null,inseguridad:1}])[0].coberturaRegistrada},null,2))
