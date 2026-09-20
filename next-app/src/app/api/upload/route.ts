import { NextRequest, NextResponse } from 'next/server'
import fs from 'node:fs'
import path from 'node:path'
import { PATHS, staticUrl } from '@/lib/paths'
import { startUploadJob } from '@/lib/tasks/jobRunner'

/**
 * POST /api/upload — multipart，字段名 file。
 * 落盘规则（与原实现一致）：{YYYYmmdd_HHMMSS}_{stem}{ext}，冲突加 -N 后缀。
 * 顺手修两个原 bug：Windows 非法字符清洗（9.6-j）、job_id 用真实自增 id（9.1）。
 */

const SUPPORTED_VIDEO = new Set(['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm'])
const SUPPORTED_AUDIO = new Set(['.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg', '.wma'])
const MAX_FILE_SIZE = 500 * 1024 * 1024

/** 音频占位图：SVG data URI（原 PIL 1280x720 的等价物，前端只当 poster 用） */
function audioPlaceholder(title: string): string {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#1a1a2e"/><stop offset="1" stop-color="#16213e"/>
  </linearGradient></defs>
  <rect width="1280" height="720" fill="url(#g)"/>
  <circle cx="640" cy="330" r="90" fill="none" stroke="#e94560" stroke-width="6"/>
  <polygon points="615,290 615,370 685,330" fill="#e94560"/>
  <text x="640" y="500" font-family="sans-serif" font-size="28" fill="#a0a0b8" text-anchor="middle">${escapeXml(title.slice(0, 40))}</text>
</svg>`
  return `data:image/svg+xml;base64,${Buffer.from(svg).toString('base64')}`
}

function escapeXml(s: string): string {
  return s.replace(/[<>&'"]/g, (c) => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;', "'": '&apos;', '"': '&quot;' })[c]!)
}

function sanitizeStem(stem: string): string {
  // Windows 非法字符 + 控制字符
  return stem.replace(/[<>:"/\\|?*\x00-\x1f]/g, '_').slice(0, 120) || 'audio'
}

function uniqueFilename(dir: string, base: string): string {
  if (!fs.existsSync(path.join(dir, base))) return base
  const ext = path.extname(base)
  const stem = path.basename(base, ext)
  let counter = 1
  let candidate = `${stem}-${counter}${ext}`
  while (fs.existsSync(path.join(dir, candidate))) {
    counter += 1
    candidate = `${stem}-${counter}${ext}`
  }
  return candidate
}

export async function POST(req: NextRequest) {
  let form: FormData
  try {
    form = await req.formData()
  } catch {
    return NextResponse.json({ detail: 'invalid multipart' }, { status: 400 })
  }
  const file = form.get('file')
  if (!file || typeof file === 'string') {
    return NextResponse.json({ detail: '文件名为空' }, { status: 400 })
  }
  const blob = file as File
  const rawName = blob.name || ''
  if (!rawName) return NextResponse.json({ detail: '文件名为空' }, { status: 400 })
  const ext = path.extname(rawName).toLowerCase()
  if (!SUPPORTED_VIDEO.has(ext) && !SUPPORTED_AUDIO.has(ext)) {
    return NextResponse.json(
      { detail: `不支持的文件格式: ${ext}。支持的视频格式: ${[...SUPPORTED_VIDEO].join(', ')}，音频格式: ${[...SUPPORTED_AUDIO].join(', ')}` },
      { status: 400 },
    )
  }
  if (blob.size > MAX_FILE_SIZE) {
    return NextResponse.json({ detail: '文件过大，最大支持 500MB' }, { status: 413 })
  }

  const isAudio = SUPPORTED_AUDIO.has(ext)
  const stamp = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  const ts = `${stamp.getFullYear()}${pad(stamp.getMonth() + 1)}${pad(stamp.getDate())}_${pad(stamp.getHours())}${pad(stamp.getMinutes())}${pad(stamp.getSeconds())}`
  const base = `${ts}_${sanitizeStem(path.basename(rawName, ext))}${ext}`
  const safeName = uniqueFilename(PATHS.staticDir, base)
  const filePath = path.join(PATHS.staticDir, safeName)

  try {
    const buf = Buffer.from(await blob.arrayBuffer())
    await fs.promises.writeFile(filePath, buf)
  } catch (e) {
    return NextResponse.json({ detail: `文件上传失败: ${e instanceof Error ? e.message : String(e)}` }, { status: 500 })
  }

  const jobId = startUploadJob(filePath, safeName)
  return NextResponse.json({
    success: true,
    message: '文件上传成功,正在处理中',
    data: {
      path: path.resolve(filePath),
      basename: safeName,
      static_url: staticUrl(safeName),
      size: blob.size,
      is_audio: isAudio,
      job_id: jobId,
      placeholder_url: isAudio ? audioPlaceholder(safeName) : undefined,
    },
  })
}
