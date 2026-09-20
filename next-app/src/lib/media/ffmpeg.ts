import { execFile } from 'node:child_process'
import { promisify } from 'node:util'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'

const run = promisify(execFile)

/**
 * ffmpeg / ffprobe 定位。dgx-spark 无 sudo 装不了系统包，
 * 用 micromamba 用户态环境 ~/ffmpeg-env/bin/ffmpeg（FFMPEG_PATH 可覆盖）。
 */

function which(name: string): string | null {
  const envKey = name === 'ffmpeg' ? 'FFMPEG_PATH' : 'FFPROBE_PATH'
  if (process.env[envKey]) return process.env[envKey] as string
  const candidates = [
    path.join(os.homedir(), 'ffmpeg-env', 'bin', name),
    path.join(os.homedir(), 'mm', 'envs', 'ffmpeg-env', 'bin', name),
  ]
  for (const c of candidates) {
    if (fs.existsSync(c)) return c
  }
  // PATH 兜底
  const dirs = (process.env.PATH || '').split(path.delimiter)
  for (const d of dirs) {
    const p = path.join(d, name)
    if (fs.existsSync(p)) return p
  }
  return null
}

export function ffmpegBin(): string {
  return which('ffmpeg') || 'ffmpeg'
}

export function ffprobeBin(): string {
  return which('ffprobe') || 'ffprobe'
}

export function hasFfmpeg(): boolean {
  return which('ffmpeg') !== null
}

/**
 * 缩略图：区间中点单帧。复刻 thumbnail_service.generate_thumbnail_ffmpeg：
 * ffmpeg -ss {sec} -i {video} -frames:v 1 -vf scale={width}:-1 -c:v png -y {tmp}
 * 返回 data:image/png;base64,...（失败返回 null）
 */
export async function generateThumbnail(
  videoPath: string,
  startMs: number,
  endMs: number,
  width = 320,
): Promise<string | null> {
  if (!fs.existsSync(videoPath)) return null
  const timeSec = (startMs + endMs) / 2 / 1000
  const tmp = path.join(os.tmpdir(), `hs_thumb_${Date.now()}_${Math.random().toString(36).slice(2)}.png`)
  try {
    await run(
      ffmpegBin(),
      ['-ss', String(timeSec), '-i', videoPath, '-frames:v', '1', '-vf', `scale=${width}:-1`, '-c:v', 'png', '-y', tmp],
      { timeout: 15000 },
    )
    const buf = await fs.promises.readFile(tmp)
    return `data:image/png;base64,${buf.toString('base64')}`
  } catch {
    return null
  } finally {
    fs.promises.unlink(tmp).catch(() => {})
  }
}

/**
 * 抽音轨：16k 单声道 PCM wav。
 * 输出后缀必须与编码匹配：曾用 libvorbis 配 .wav 输出名，ffmpeg 不报错但写出
 * 「Vorbis-in-WAV」（fmt 标签非 PCM），FunASR 按 wav 解析直接拒绝。
 * 16k 单声道是 FunASR 各模型的本地采样率，免二次重采样。
 */
export async function extractAudio(input: string, output: string): Promise<void> {
  await run(ffmpegBin(), ['-i', input, '-vn', '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', '-y', output], {
    timeout: 600000,
  })
}

/** B 站视频 + 音频合并（下载器产物） */
export async function mergeAudioVideo(videoPath: string, audioPath: string, output: string): Promise<void> {
  await run(
    ffmpegBin(),
    ['-i', videoPath, '-i', audioPath, '-c:v', 'copy', '-c:a', 'copy', '-map', '0:v:0', '-map', '1:a:0', '-y', output],
    { timeout: 600000 },
  )
}

/** 音频时长（秒），失败返回 null */
export async function probeDuration(filePath: string): Promise<number | null> {
  try {
    const { stdout } = await run(
      ffprobeBin(),
      ['-v', 'quiet', '-print_format', 'json', '-show_format', filePath],
      { timeout: 30000 },
    )
    const data = JSON.parse(stdout) as { format?: { duration?: string } }
    const d = Number(data.format?.duration)
    return Number.isFinite(d) ? d : null
  } catch {
    return null
  }
}
