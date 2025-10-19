import path from "path"
import tailwindcss from "@tailwindcss/vite"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

// 支持通过环境变量配置后端地址/端口，适配本地（localhost）和 docker（服务名）场景
const isDocker = Boolean(process.env.USE_DOCKER || process.env.DOCKER)
const backendHost = process.env.BACKEND_HOST || (isDocker ? "backend" : "localhost")
const backendPort = Number(process.env.BACKEND_PORT || 9999)
const backendTarget = `http://${backendHost}:${backendPort}`

export default defineConfig({
  plugins: [
    react({
      babel: {
        plugins: [["babel-plugin-react-compiler"]],
      },
    }),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    proxy: {
      "/api": {
        target: backendTarget,
        changeOrigin: true,
      },
      "/static": {
        target: backendTarget,
        changeOrigin: true,
      },
    },
  },
})
