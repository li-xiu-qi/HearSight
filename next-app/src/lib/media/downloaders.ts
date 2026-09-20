import { spawn } from 'node:child_process'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'

/**
 * yt-dlp 子进程封装，替代原 Python media_processing 三下载器。
 * 二进制解析：YTDLP_PATH 环境变量 > ~/hearsight-env/bin/yt-dlp > PATH。
 *
 * 进度通过 --progress-template 输出结构化行（YTDLP_PROGRESS: {json}）解析，
 * 比解析人类可读进度条稳。源识别正则与原 downloader_factory 一致。
 */

export type SourceKind = 'bilibili' | 'youtube' | 'xiaoyuzhou'

const SOURCE_PATTERNS: [SourceKind, RegExp][] = [
  ['bilibili', /(?:https?:\/\/)?(?:www\.)?bilibili\.com/],
  ['youtube', /(?:https?:\/\/)?(?:www\.)?(youtube\.com|youtu\.be)/],
  ['xiaoyuzhou', /(?:https?:\/\/)?(?:www\.)?xiaoyuzhoufm\.com/],
]

export function detectSource(url: string): SourceKind | null {
  for (const [kind, re] of SOURCE_PATTERNS) {
    if (re.test(url)) return kind
  }
  return null
}

export function ytdlpBin(): string {
  if (process.env.YTDLP_PATH) return process.env.YTDLP_PATH
  const home = path.join(os.homedir(), 'hearsight-env', 'bin', process.platform === 'win32' ? 'yt-dlp.exe' : 'yt-dlp')
  if (fs.existsSync(home)) return home
  return 'yt-dlp'
}

export interface YtDlpProgress {
  status: string
  progress_percent: number
  downloaded_bytes: number
  total_bytes: number
  speed: number
  eta_seconds: number
  filename: string
}

export interface DownloadOptions {
  url: string
  outDir: string
  onProgress?: (p: YtDlpProgress) => void
  signal?: AbortSignal
}

export interface DownloadResult {
  videoPath?: string
  audioPath?: string
  basename?: string
  duration?: number | null
  mediaType: 'video' | 'audio' | 'both' | 'unknown'
  success: boolean
  error?: string
}

/** 清洗标题：保留字母数字与空格连字符下划线（中文 isalnum 为 true，原样保留） */
export function safeTitle(title: string, fallback: string): string {
  const cleaned = [...title].filter((c) => /[\w\- ]/.test(c) || /[^\x00-\xff]/.test(c)).join('').trim()
  return cleaned || fallback
}

const PROGRESS_TEMPLATE =
  'YTDLP_PROGRESS:' +
  JSON.stringify({
    status: '%(progress.status)s',
    downloaded_bytes: '%(progress.downloaded_bytes)s',
    total_bytes: '%(progress.total_bytes)s',
    total_bytes_estimate: '%(progress.total_bytes_estimate)s',
    speed: '%(progress.speed)s',
    eta: '%(progress.eta)s',
    filename: '%(progress.filename)s',
  })

export async function downloadWithYtDlp(opts: DownloadOptions): Promise<DownloadResult> {
  const source = detectSource(opts.url)
  if (!source) {
    return { mediaType: 'unknown', success: false, error: `不支持的媒体源，无法识别URL: ${opts.url}` }
  }
  const tmpDir = await fs.promises.mkdtemp(path.join(os.tmpdir(), 'hs_dl_'))
  const outtmpl = path.join(tmpDir, '%(title)s.%(ext)s')
  const format =
    source === 'bilibili'
      ? 'bestvideo[ext=mp4],bestaudio[ext=m4a]/best[ext=mp4]/best'
      : source === 'youtube'
        ? 'best[ext=mp4]/best'
        : 'bestaudio/best'

  const args = [
    '-f', format,
    '-o', outtmpl,
    '--newline',
    '--progress-template', PROGRESS_TEMPLATE,
    '--no-playlist',
  ]
  if (source === 'xiaoyuzhou') {
    args.push('-x', '--audio-format', 'mp3')
  }

  try {
    await new Promise<void>((resolve, reject) => {
      const proc = spawn(ytdlpBin(), [...args, opts.url], { stdio: ['ignore', 'pipe', 'pipe'] })
      let stderrBuf = ''
      const onLine = (line: string) => {
        if (!line.startsWith('YTDLP_PROGRESS:')) return
        try {
          const raw = JSON.parse(line.slice('YTDLP_PROGRESS:'.length)) as Record<string, string>
          const total = Number(raw.total_bytes) || Number(raw.total_bytes_estimate) || 0
          const downloaded = Number(raw.downloaded_bytes) || 0
          opts.onProgress?.({
            status: raw.status || 'unknown',
            progress_percent: total > 0 ? (downloaded / total) * 100 : 0,
            downloaded_bytes: downloaded,
            total_bytes: total,
            speed: Number(raw.speed) || 0,
            eta_seconds: Number(raw.eta) || 0,
            filename: path.basename(raw.filename || ''),
          })
        } catch {
          /* 忽略坏行 */
        }
      }
      let buf = ''
      proc.stdout.on('data', (d: Buffer) => {
        buf += d.toString()
        const lines = buf.split('\n')
        buf = lines.pop() ?? ''
        lines.forEach(onLine)
      })
      proc.stderr.on('data', (d: Buffer) => {
        stderrBuf += d.toString()
      })
      proc.on('error', reject)
      proc.on('close', (code) => {
        if (code === 0) resolve()
        else reject(new Error(`yt-dlp exit ${code}: ${stderrBuf.slice(-800)}`))
      })
      opts.signal?.addEventListener('abort', () => proc.kill('SIGKILL'))
    })

    const files = (await fs.promises.readdir(tmpDir)).map((f) => path.join(tmpDir, f))
    if (files.length === 0) {
      return { mediaType: 'unknown', success: false, error: 'yt-dlp 未产出文件' }
    }
    // 移动到输出目录（保留原下载器语义：视频 .mp4 / 音频 .mp3|.m4a|.aac 规范命名）
    const info = files[0]
    const ext = path.extname(info).toLowerCase()
    const stem = path.basename(info, ext)
    const isVideo = ['.mp4', '.mkv', '.webm', '.mov', '.flv'].includes(ext)
    const target = path.join(opts.outDir, `${safeTitle(stem, `${source}_media`)}${ext}`)
    await fs.promises.copyFile(info, target)
    await fs.promises.rm(tmpDir, { recursive: true, force: true })
    return {
      videoPath: isVideo ? target : undefined,
      audioPath: isVideo ? undefined : target,
      basename: path.basename(target),
      mediaType: isVideo ? 'video' : 'audio',
      success: true,
    }
  } catch (e) {
    await fs.promises.rm(tmpDir, { recursive: true, force: true }).catch(() => {})
    return { mediaType: 'unknown', success: false, error: e instanceof Error ? e.message : String(e) }
  }
}
