import path from 'node:path'
import fs from 'node:fs'
import { getDb } from '../db'
import { PATHS, mediaPathFromBasename } from '../paths'
import { transcribeFile } from '../asr'
import { embed } from '../llm'
import {
  createJob,
  finishJob,
  makeProgress,
  mergeJobResult,
  setProgress,
} from '../progress'
import { extractAudio, hasFfmpeg } from '../media/ffmpeg'
import { downloadWithYtDlp, type YtDlpProgress } from '../media/downloaders'
import { indexTranscriptChunks } from '../rag'
import type { Segment } from '../types'

/**
 * 进程内任务运行器，替代原 Celery process_job_task。
 * 阶段与进度字段和原 download_stage 完全一致（前端 ProgressCard 直接消费）。
 * 失败不抛到调用方：写 failed 帧 + jobs.error。
 */

const running = new Set<number>()

export function isRunning(jobId: number): boolean {
  return running.has(jobId)
}

function emit(jobId: number, fields: Parameters<typeof makeProgress>[1]) {
  setProgress(makeProgress(jobId, fields))
}

/** 上传链路：保存的文件 → ASR → 落库 */
export async function runUploadPipeline(jobId: number, filePath: string, basename: string): Promise<void> {
  running.add(jobId)
  try {
    emit(jobId, { status: 'processing', stage: 'upload_processing', progress_percent: 10, filename: basename, message: '正在处理上传的文件...' })
    emit(jobId, { status: 'ready', stage: 'upload', progress_percent: 100, filename: basename, message: '文件已上传并处理完成,准备进行语音识别' })

    const ext = path.extname(filePath).toLowerCase()
    const isAudio = ['.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg', '.wma'].includes(ext)
    await runAsrAndSave(jobId, filePath, basename, isAudio ? 'audio' : 'video', 'upload')
  } catch (e) {
    failJob(jobId, e)
  } finally {
    running.delete(jobId)
  }
}

/** 下载链路：yt-dlp → ASR → 落库 */
export async function runDownloadPipeline(jobId: number, url: string): Promise<void> {
  running.add(jobId)
  try {
    emit(jobId, { status: 'pending', stage: 'download_start', progress_percent: 0, message: '准备开始下载...' })
    const result = await downloadWithYtDlp({
      url,
      outDir: PATHS.staticDir,
      onProgress: (p: YtDlpProgress) => {
        emit(jobId, {
          status: p.status === 'finished' ? 'ready' : 'in-progress',
          stage: 'download',
          progress_percent: p.progress_percent,
          filename: p.filename,
          current_bytes: p.downloaded_bytes,
          total_bytes: p.total_bytes,
          speed: p.speed,
          eta_seconds: p.eta_seconds,
          message: p.status === 'finished' ? '下载完成,准备进行语音识别' : undefined,
        })
      },
    })
    if (!result.success || !result.basename) {
      throw new Error(result.error || '下载失败')
    }
    const filePath = result.videoPath || result.audioPath!
    const mediaType = result.mediaType === 'video' ? 'video' : 'audio'
    mergeJobResult(jobId, {
      audio_path: result.audioPath,
      video_path: result.videoPath,
      basename: result.basename,
      media_type: mediaType,
      source: 'download',
      static_url: `/static/${encodeURIComponent(result.basename)}`,
    })
    await runAsrAndSave(jobId, filePath, result.basename, mediaType, 'download')
  } catch (e) {
    failJob(jobId, e)
  } finally {
    running.delete(jobId)
  }
}

/** ASR 主链路（上传/下载共用） */
async function runAsrAndSave(
  jobId: number,
  filePath: string,
  basename: string,
  mediaType: 'audio' | 'video',
  source: 'upload' | 'download',
): Promise<void> {
  const stem = path.basename(filePath, path.extname(filePath))

  emit(jobId, { status: 'processing', stage: 'asr_preprocessing', progress_percent: 5, filename: basename, message: '正在准备语音识别...' })
  emit(jobId, { status: 'processing', stage: 'asr_recognizing', progress_percent: 10, filename: basename, message: '正在进行语音识别,请稍候...' })

  // FunASR 对 wav 最稳；其他格式统一抽 16k 单声道 wav（ffmpeg 缺失时回退原文件）
  let asrInput = filePath
  if (path.extname(filePath).toLowerCase() !== '.wav' && hasFfmpeg()) {
    const wav = path.join(PATHS.tmpDir, `${stem}_${Date.now()}.wav`)
    try {
      await extractAudio(filePath, wav)
      asrInput = wav
    } catch {
      asrInput = filePath
    }
  }

  const { segments: raw } = await transcribeFile(asrInput)
  if (asrInput !== filePath) fs.promises.unlink(asrInput).catch(() => {})

  emit(jobId, { status: 'processing', stage: 'asr_postprocessing', progress_percent: 80, filename: basename, message: '语音识别完成,正在处理结果...' })
  const segments: Segment[] = raw.map((s, i) => ({
    index: typeof s.index === 'number' ? s.index : i,
    sentence: s.sentence,
    start_time: s.start_time,
    end_time: s.end_time,
    spk_id: s.spk_id ?? null,
  }))

  emit(jobId, { status: 'processing', stage: 'saving_transcript', progress_percent: 90, filename: basename, message: '正在保存转录结果...' })
  const db = getDb()
  const isVideo = mediaType === 'video'
  const info = db
    .prepare(
      `INSERT INTO transcripts (audio_path, video_path, media_type, segments_json)
       VALUES (?, ?, ?, ?)`,
    )
    .run(
      isVideo ? filePath : filePath,
      isVideo ? filePath : null,
      mediaType,
      JSON.stringify(segments),
    )
  const transcriptId = Number(info.lastInsertRowid)

  emit(jobId, { status: 'completed', stage: 'asr', progress_percent: 100, filename: basename, message: '语音识别完成' })

  // 向量索引失败不阻塞主链路
  try {
    await indexTranscriptChunks(transcriptId, basename, segments)
  } catch {
    /* 检索降级为关键词，见 rag.ts */
  }

  mergeJobResult(jobId, {
    transcript_id: transcriptId,
    basename,
    media_type: mediaType,
    source,
    static_url: `/static/${encodeURIComponent(basename)}`,
  })
  finishJob(jobId, 'success')
  emit(jobId, { status: 'success', stage: 'completed', progress_percent: 100, filename: basename, message: '任务处理完成' })
}

function failJob(jobId: number, e: unknown): void {
  const msg = e instanceof Error ? e.message : String(e)
  finishJob(jobId, 'failed', msg)
  emit(jobId, { status: 'failed', stage: 'error', progress_percent: 0, message: `任务处理失败: ${msg}`, error: msg })
}

/** 供 API 路由使用：新建 job 并后台跑上传链路 */
export function startUploadJob(filePath: string, basename: string): number {
  const jobId = createJob(`upload://${basename}`)
  void runUploadPipeline(jobId, filePath, basename)
  return jobId
}

export function startDownloadJob(url: string): number {
  const jobId = createJob(url)
  void runDownloadPipeline(jobId, url)
  return jobId
}

export { mediaPathFromBasename }
