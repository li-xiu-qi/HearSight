import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  // better-sqlite3 是原生模块，externalize（不在 bundle 里打进来）
  serverExternalPackages: ['better-sqlite3'],
  // 媒体文件对外契约保持 /static/<basename>（与原 StaticFiles 挂载一致），
  // 实际由 /api/static/[...path] 路由提供
  async rewrites() {
    return [{ source: '/static/:path*', destination: '/api/static/:path*' }]
  },
}

export default nextConfig
