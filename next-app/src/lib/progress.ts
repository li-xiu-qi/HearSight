import { EventEmitter } from 'node:events'
import { getDb } from './db'
import type { ProgressInfo } from './types'

/**
 * 任务进度：替代原 Celery + Redis pubsub。
 * 进程内 Map 为权威态，jobs.result_json 做结果持久化；
 * SSE（/api/progress/stream-all）通过 EventEmitter 广播。
 * 重启后进行中的任务状态丢失（与原 Redis 方案一致），终态可从 jobs 表恢复。
 */

const bus = new EventEmitter()
bus.setMaxListeners(200)

const progressMap = new Map<number | string, ProgressInfo>()

export const PROGRESS_EVENT = 'progress'

export function setProgress(info: ProgressInfo): void {
  progressMap.set(info.job_id, info)
  bus.emit(PROGRESS_EVENT, info)
}

export function getProgress(jobId: number | string): ProgressInfo | undefined {
  return progressMap.get(jobId)
}

export function allProgress(): ProgressInfo[] {
  return [...progressMap.values()]
}

export function subscribeProgress(handler: (info: ProgressInfo) => void): () => void {
  bus.on(PROGRESS_EVENT, handler)
  return () => bus.off(PROGRESS_EVENT, handler)
}

/** 进度帧构造函数（字段与原 create_progress_info 一致） */
export function makeProgress(
  jobId: number | string,
  fields: Partial<ProgressInfo> & { stage: string; status: string; progress_percent: number },
): ProgressInfo {
  return {
    job_id: jobId,
    timestamp: new Date().toISOString(),
    current_bytes: 0,
    total_bytes: 0,
    speed: 0,
    eta_seconds: null,
    filename: '',
    ...fields,
  }
}

/** 任务结果写入 jobs.result_json（读-改-写浅合并，原 update_job_result 语义） */
export function mergeJobResult(jobId: number, patch: Record<string, unknown>): void {
  const db = getDb()
  const row = db.prepare(`SELECT result_json FROM jobs WHERE id = ?`).get(jobId) as
    | { result_json: string | null }
    | undefined
  const current = row?.result_json ? (JSON.parse(row.result_json) as Record<string, unknown>) : {}
  db.prepare(`UPDATE jobs SET result_json = ? WHERE id = ?`).run(
    JSON.stringify({ ...current, ...patch }),
    jobId,
  )
}

export function createJob(url: string): number {
  const db = getDb()
  const info = db
    .prepare(`INSERT INTO jobs (url, status) VALUES (?, 'pending')`)
    .run(url)
  return Number(info.lastInsertRowid)
}

export function finishJob(jobId: number, status: 'success' | 'failed', error?: string): void {
  const db = getDb()
  db.prepare(
    `UPDATE jobs SET status = ?, finished_at = datetime('now','localtime'), error = ? WHERE id = ?`,
  ).run(status, error ?? null, jobId)
}
