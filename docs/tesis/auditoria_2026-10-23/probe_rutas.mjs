import fs from 'node:fs';
let source=fs.readFileSync('frontend/src/utils/riesgoRuta.js','utf8');
source=source.replace(/import .*from .*\n/g,'');
source="const ORDEN_NIVELES=['bajo','medio','alto','critico']; const PESO_RIESGO={bajo:1,medio:2,alto:3,critico:5};\n"+source;
const m=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
function scores(values){return m.calcularRutasConScore(values.map(()=>({})), values.map(n=>Array.from({length:n},()=>({nivel:'bajo',tipoRiesgo:'siniestro'})))).map(r=>r.nivelRelativo)}
const result={ranking_10_11_12:scores([10,11,12]),ranking_10_11_16:scores([10,11,16]),fallback:m.calcularRutasConScore([{}],[[]],[.9],[{siniestro:null,inseguridad:.9}])[0]};
console.log(JSON.stringify(result,null,2));
