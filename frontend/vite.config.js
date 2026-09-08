import react from '@vitejs/plugin-react'
import basicSsl from '@vitejs/plugin-basic-ssl'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), basicSsl()],
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
    https: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
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
})
