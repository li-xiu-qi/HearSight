import path from 'node:path'
import { getDb } from '../db'
import { chatStream } from '../llm'
import { buildMultiVideoPrompt, type VideoContext } from '../prompts/chat'
import { retrieve } from '../rag'
import type { Segment } from '../types'

/**
 * 问答核心：检索 + 多视频 prompt + 流式生成。
 * A 路（/api/chat/stream）逐段 yield 纯文本，由路由包 [chunk] 标记；
 * B 路（/api/chat/streaming + SSE）由调用方直接拿 chunk。
 * 线上原走 chat_service.chat_with_transcripts_stream，ReAct 子系统是死代码不移植。
 */

export interface ChatRunResult {
  videos: VideoContext[]
}

export async function prepareChatContext(
  question: string,
  transcriptIds: number[],
): Promise<VideoContext[]> {
  const db = getDb()
  const hits = await retrieve(question, transcriptIds)
  const videos: VideoContext[] = []
  for (const hit of hits) {
    const row = db
      .prepare(`SELECT video_path, audio_path FROM transcripts WHERE id = ?`)
      .get(hit.transcriptId) as { video_path: string | null; audio_path: string } | undefined
    if (!row) continue
    const filename = path.basename(row.video_path || row.audio_path) || '未知文件'
    videos.push({ filename, transcript_id: hit.transcriptId, segments: hit.segments })
  }
  return videos
}

export function buildChatPrompt(question: string, videos: VideoContext[]): string {
  return buildMultiVideoPrompt(question, videos)
}

/** 流式生成，逐段 yield content */
export async function* runChatStream(
  question: string,
  transcriptIds: number[],
  signal?: AbortSignal,
): AsyncGenerator<string> {
  const videos = await prepareChatContext(question, transcriptIds)
  if (videos.length === 0) {
    throw new ChatError('No relevant content found in the selected transcripts')
  }
  const prompt = buildChatPrompt(question, videos)
  yield* chatStream(prompt, signal)
}

/** 流式生成，每段经 onChunk 回调吐出（SSE B 路用） */
export async function runChatWithCallback(
  question: string,
  transcriptIds: number[],
  onChunk: (chunk: string) => void,
): Promise<string> {
  let full = ''
  for await (const chunk of runChatStream(question, transcriptIds)) {
    full += chunk
    onChunk(chunk)
  }
  return full
}

export class ChatError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'ChatError'
  }
}

/** 供 SSE 完成帧使用：收集完整答案（A 路之外的批量场景） */
export async function runChatCollect(
  question: string,
  transcriptIds: number[],
): Promise<{ finalAnswer: string; videos: VideoContext[] }> {
  const videos = await prepareChatContext(question, transcriptIds)
  if (videos.length === 0) {
    throw new ChatError('No relevant content found in the selected transcripts')
  }
  const finalAnswer = await runChatWithCallback(question, transcriptIds, () => {})
  return { finalAnswer, videos }
}

export type { Segment }
