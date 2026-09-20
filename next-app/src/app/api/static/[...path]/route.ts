import { NextRequest, NextResponse } from 'next/server'
import fs from 'node:fs'
import path from 'node:path'
import { PATHS } from '@/lib/paths'

/**
 * 媒体文件服务：/static/<basename>（rewrite 指来）→ data/download_videos/<basename>
 * 支持 Range（视频 seek 必需，不实现时浏览器每次 seek 整文件重下）
 */
export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ path: string[] }> },
) {
  const { path: segs } = await params
  const basename = path.basename(decodeURIComponent(segs.join('/')))
  // 路径穿越防护：只允许 static_dir 直接子文件
  const filePath = path.join(PATHS.staticDir, basename)
  const rel = path.relative(path.resolve(PATHS.staticDir), path.resolve(filePath))
  if (rel.startsWith('..') || path.isAbsolute(rel)) {
    return new NextResponse('Forbidden', { status: 403 })
  }
  if (!fs.existsSync(filePath)) {
    return new NextResponse('Not Found', { status: 404 })
  }
  const stat = fs.statSync(filePath)
  const ext = path.extname(basename).toLowerCase()
  const MIME: Record<string, string> = {
    '.mp4': 'video/mp4',
    '.webm': 'video/webm',
    '.mov': 'video/quicktime',
    '.mkv': 'video/x-matroska',
    '.mp3': 'audio/mpeg',
    '.wav': 'audio/wav',
    '.m4a': 'audio/mp4',
    '.aac': 'audio/aac',
    '.flac': 'audio/flac',
    '.ogg': 'audio/ogg',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
  }
  const contentType = MIME[ext] || 'application/octet-stream'

  // Range: bytes=start-end（end 省略表示到文件尾；非法头忽略走 200）
  const range = req.headers.get('range')
  const m = /^bytes=(\d+)-(\d*)$/.exec(range || '')
  if (m) {
    const start = Number(m[1])
    const end = m[2] ? Math.min(Number(m[2]), stat.size - 1) : stat.size - 1
    if (start > end || start >= stat.size) {
      return new NextResponse('Range Not Satisfiable', {
        status: 416,
        headers: { 'Content-Range': `bytes */${stat.size}` },
      })
    }
    const stream = fs.createReadStream(filePath, { start, end })
    return new NextResponse(stream as unknown as ReadableStream, {
      status: 206,
      headers: {
        'Content-Type': contentType,
        'Content-Length': String(end - start + 1),
        'Content-Range': `bytes ${start}-${end}/${stat.size}`,
        'Accept-Ranges': 'bytes',
      },
    })
  }

  const stream = fs.createReadStream(filePath)
  return new NextResponse(stream as unknown as ReadableStream, {
    headers: {
      'Content-Type': contentType,
      'Content-Length': String(stat.size),
      'Accept-Ranges': 'bytes',
    },
  })
}
