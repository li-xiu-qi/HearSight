import fs from 'node:fs'

/**
 * ASR 客户端：调 HearSight ASR backend（FunASR 本地模式，dgx-spark:8003）。
 * 接口：POST {ASR_BACKEND_URL}/asr/transcribe/bytes，multipart 字段名 file。
 * 响应：{ text, language, segments: [{ spk_id, sentence, start_time, end_time, index }], status }
 * 时间戳单位为毫秒（FunASR sentence_info 原生单位）。
 */

const DEFAULT_URL = 'http://127.0.0.1:8003'
/** 长音频识别耗时以十分钟计，默认 30 分钟超时 */
const DEFAULT_TIMEOUT_MS = 30 * 60 * 1000

export function asrBaseUrl(): string {
  return process.env.ASR_BACKEND_URL || DEFAULT_URL
}

export async function transcribeFile(
  filePath: string,
): Promise<{ text: string; language: string; segments: AsrSegment[] }> {
  const buffer = await fs.promises.readFile(filePath)
  return transcribeBytes(buffer, filePath.split(/[\\/]/).pop() || 'audio.wav')
}

export async function transcribeBytes(
  buffer: Buffer,
  filename: string,
): Promise<{ text: string; language: string; segments: AsrSegment[] }> {
  const form = new FormData()
  form.append('file', new Blob([new Uint8Array(buffer)]), filename)

  const timeoutMs = Number(process.env.ASR_TIMEOUT_MS || DEFAULT_TIMEOUT_MS)
  const res = await fetch(`${asrBaseUrl()}/asr/transcribe/bytes`, {
    method: 'POST',
    body: form,
    signal: AbortSignal.timeout(timeoutMs),
  })
  const json = (await res.json()) as AsrResponse
  if (json.status !== 'success') {
    throw new Error(`ASR failed: ${json.error || JSON.stringify(json)}`)
  }
  return { text: json.text ?? '', language: json.language ?? 'unknown', segments: json.segments ?? [] }
}

interface AsrSegment {
  spk_id?: string | null
  sentence: string
  start_time: number
  end_time: number
  index?: number
}

interface AsrResponse {
  status: string
  error?: string
  text?: string
  language?: string
  filename?: string
  segments?: AsrSegment[]
}
