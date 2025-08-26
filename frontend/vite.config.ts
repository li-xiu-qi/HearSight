import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

declare const process: any

// https://vite.dev/config/
// 支持通过环境变量配置后端地址/端口，适配本地（localhost）和 docker（服务名）场景
const isDocker = Boolean((process as any).env.USE_DOCKER || (process as any).env.DOCKER)
const backendHost = (process as any).env.BACKEND_HOST || (isDocker ? 'backend' : 'localhost')
const backendPort = Number((process as any).env.BACKEND_PORT || 9999)
const backendTarget = `http://${backendHost}:${backendPort}`

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: backendTarget,
        changeOrigin: true,
      },
      '/static': {
        target: backendTarget,
        changeOrigin: true,
      },
    },
  },
})
