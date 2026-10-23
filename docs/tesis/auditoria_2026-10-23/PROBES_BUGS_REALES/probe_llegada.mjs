import fs from 'node:fs'
let source=fs.readFileSync('frontend/src/utils/geoRiesgo.js','utf8').replace(/^import .*\n/gm,'')
source="const ORDEN_NIVELES=['bajo','medio','alto','critico']; const UMBRAL_REPORTE_KM=0.6; const API_URL='';\n"+source
const geo=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'))
const coords=[[-34.60,-58.40],[-34.59,-58.40]]
const ultimo={lat:-34.59,lng:-58.40,tipo:'arrive'}
const gps={lat:-34.57,lng:-58.40}
const pUltimo=geo.calcularProgresoRuta(ultimo,coords)
const pGps=geo.calcularProgresoRuta(gps,coords)
const faltanKm=Math.max(0,pUltimo.distanciaRecorridaKm-pGps.distanciaRecorridaKm)
console.log(JSON.stringify({distancia_real_a_destino_km:geo.distanciaKm(gps,ultimo),progreso_ultimo_km:pUltimo.distanciaRecorridaKm,progreso_gps_km:pGps.distanciaRecorridaKm,faltanKm,radio_llegada_km:0.03},null,2))
