import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  // better-sqlite3 是原生模块，externalize（不在 bundle 里打进来）
  serverExternalPackages: ['better-sqlite3'],
}

export default nextConfig
