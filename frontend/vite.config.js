import react from '@vitejs/plugin-react'
import basicSsl from '@vitejs/plugin-basic-ssl'
import { env } from 'node:process'
import { defineConfig } from 'vite'

// Para levantar una instancia aparte (por ejemplo un E2E contra otro backend,
// sin tocar el :8000 que publica Tailscale Funnel): MOTOSAFE_API_TARGET cambia
// el destino del proxy /api y MOTOSAFE_SIN_HTTPS=1 sirve por http (en
// localhost la geolocalizacion funciona igual). Sin estas variables, nada cambia.
const API_TARGET = env.MOTOSAFE_API_TARGET || 'http://127.0.0.1:8000'
const CON_HTTPS = env.MOTOSAFE_SIN_HTTPS !== '1'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), ...(CON_HTTPS ? [basicSsl()] : [])],
  // host: true expone el server en la red local (no solo localhost), asi se
  // puede abrir desde el celular. https: true (via basic-ssl) es necesario
  // porque la Geolocation API del navegador exige contexto seguro -- y esa
  // excepcion solo aplica a "localhost", no a una IP de LAN como 192.168.x.x,
  // asi que sin esto el GPS quedaria roto al entrar desde el celular aunque
  // la pagina cargue bien.
  //
  // El proxy /api resuelve tres problemas de un saque sin tocar el backend:
  // CORS (el fetch queda same-origin desde el navegador), contenido mixto
  // (HTTPS pidiendo a HTTP -- el forward pasa por Vite, no por el browser) y
  // que el celular no intente pegarle a su propio localhost:8000 (ver
  // API_URL en constants.js, ahora relativo).
  server: {
    host: true,
    https: CON_HTTPS,
    // Vite bloquea por defecto cualquier Host header que no reconozca (para
    // frenar ataques de DNS rebinding) -- eso incluye el hostname que arma
    // un tunel temporal (cloudflared/ngrok) para probar desde el celular sin
    // estar en la misma red que la PC. true == confiar en cualquier host;
    // aceptable ahora porque este server solo corre en dev, en la PC de
    // Rodo, nunca expuesto de forma permanente.
    allowedHosts: true,
    proxy: {
      '/api': {
        target: API_TARGET,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
  // maplibre-gl arma su worker interno (maplibre-gl-worker.mjs) de una forma
  // que el pre-bundler de Vite (esbuild) no maneja bien en dev -- error
  // conocido de la libreria con Vite. Excluirla del optimizeDeps evita que
  // Vite intente pre-empaquetarla y el problema desaparece.
  optimizeDeps: {
    exclude: ['maplibre-gl'],
  },
  // El worker de MapLibre (ver setWorkerUrl en MapaMotoSafe.jsx) es un módulo
  // ES y MapLibre lo crea con { type: 'module' }.
  worker: {
    format: 'es',
  },
})
