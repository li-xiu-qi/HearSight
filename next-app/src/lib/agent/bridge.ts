import path from 'node:path'
import { getDb } from '../db'
import { AcpAgentProcess } from './acpClient'
import { runChatStream } from '../tasks/chatTask'

/**
 * agent 问答桥：HearSight 现有 SSE 协议 ↔ step-code ACP agent。
 *
 * 进程池按聊天会话维度复用（同一会话多轮对话共用一个 step-code 进程，
 * agent 自行保留上下文）；空闲超时回收。引擎起不来时回落既有单轮 RAG，
 * 不删旧链路（既定退路）。
 */

export interface AgentTurnEvents {
  onChunk: (chunk: string) => void
  onStep: (label: string) => void
}

interface PoolEntry {
  proc: AcpAgentProcess
  lastUsed: number
}

const IDLE_MS = 10 * 60 * 1000
const pool = new Map<string, PoolEntry>()

// 空闲回收：unref 不拖住事件循环，Next server 退出不受影响。
const reaper = setInterval(() => {
  const now = Date.now()
  for (const [key, entry] of pool) {
    if (now - entry.lastUsed > IDLE_MS) {
      void entry.proc.close()
      pool.delete(key)
    }
  }
}, 60 * 1000)
reaper.unref?.()

/** 选中转写注入 prompt：引用时间戳需要文件名，预先给齐，省一次 list 往返。 */
function selectedTranscriptsBlock(transcriptIds: number[]): string {
  const db = getDb()
  const lines: string[] = []
  for (const id of transcriptIds) {
    const row = db
      .prepare(`SELECT audio_path, video_path, segments_json FROM transcripts WHERE id = ?`)
      .get(id) as { audio_path: string; video_path: string | null; segments_json: string } | undefined
    if (!row) continue
    const filename = path.basename(row.video_path || row.audio_path) || `transcript-${id}`
    let count = 0
    try {
      count = (JSON.parse(row.segments_json) as unknown[])?.length ?? 0
    } catch {
      /* 忽略损坏 JSON，计数为 0 */
    }
    lines.push(`#${id} 《${filename}》（${count} 段）`)
  }
  return lines.join('\n')
}

function buildAgentPrompt(question: string, transcriptIds: number[]): string {
  const block = selectedTranscriptsBlock(transcriptIds)
  return [
    `用户问题：${question}`,
    '',
    '当前选中的转写（引用时间戳时视频名用这里的文件名）：',
    block === '' ? '（未提供）' : block,
    '',
    '先调用 skill 工具激活 hearsight-qa 协议，再按协议检索与回答。',
  ].join('\n')
}

/** 单轮 RAG 回落（agent 引擎不可用时）。 */
async function runFallback(
  question: string,
  transcriptIds: number[],
  events: AgentTurnEvents,
  signal?: AbortSignal,
): Promise<string> {
  let full = ''
  for await (const chunk of runChatStream(question, transcriptIds, signal)) {
    full += chunk
    events.onChunk(chunk)
  }
  return full
}

export async function runAgentTurn(
  sessionKey: string,
  question: string,
  transcriptIds: number[],
  events: AgentTurnEvents,
  signal?: AbortSignal,
): Promise<string> {
  let entry = pool.get(sessionKey)
  if (entry === undefined) {
    try {
      const proc = await AcpAgentProcess.start(sessionKey)
      entry = { proc, lastUsed: Date.now() }
      pool.set(sessionKey, entry)
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e)
      events.onStep(`agent 引擎不可用（${msg}），回落单轮检索`)
      return runFallback(question, transcriptIds, events, signal)
    }
  }
  entry.lastUsed = Date.now()

  const onAbort = () => entry?.proc.cancel()
  signal?.addEventListener('abort', onAbort, { once: true })
  try {
    return await entry.proc.prompt(buildAgentPrompt(question, transcriptIds), {
      onText: events.onChunk,
      onStep: events.onStep,
    })
  } catch (e) {
    if (e instanceof Error && e.message === 'ABORTED') throw e
    // 进程级失败：清池让下次重启新进程，错误上抛由路由层转 [error]。
    pool.delete(sessionKey)
    await entry.proc.close().catch(() => {})
    throw e
  } finally {
    signal?.removeEventListener('abort', onAbort)
  }
}

/** 聊天会话关闭时调用（尽快回收进程；不调用也有空闲回收兜底）。 */
export async function disposeAgentSession(sessionKey: string): Promise<void> {
  const entry = pool.get(sessionKey)
  if (entry === undefined) return
  pool.delete(sessionKey)
  await entry.proc.close().catch(() => {})
}
