import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // maplibre-gl arma su worker interno (maplibre-gl-worker.mjs) de una forma
  // que el pre-bundler de Vite (esbuild) no maneja bien en dev -- error
  // conocido de la libreria con Vite. Excluirla del optimizeDeps evita que
  // Vite intente pre-empaquetarla y el problema desaparece.
  optimizeDeps: {
    exclude: ['maplibre-gl'],
  },
})
