import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

declare const process: any

// https://vite.dev/config/
const backendPort = Number((process as any).env.BACKEND_PORT || 8000)

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: `http://localhost:${backendPort}`,
        changeOrigin: true,
      },
      '/static': {
        target: `http://localhost:${backendPort}`,
        changeOrigin: true,
      },
    },
  },
})
