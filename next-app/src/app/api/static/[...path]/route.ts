import { NextRequest, NextResponse } from 'next/server'
import fs from 'node:fs'
import path from 'node:path'
import { PATHS } from '@/lib/paths'

/** 媒体文件服务：/static/<basename> → app_datas/download_videos/<basename> */
export async function GET(
  _req: NextRequest,
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
  const stream = fs.createReadStream(filePath)
  return new NextResponse(stream as unknown as ReadableStream, {
    headers: {
      'Content-Type': MIME[ext] || 'application/octet-stream',
      'Content-Length': String(stat.size),
      'Accept-Ranges': 'bytes',
    },
  })
}
