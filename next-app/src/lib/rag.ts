import { getDb } from './db'
import { embed } from './llm'
import type { Segment } from './types'

/**
 * 检索层：替代 ChromaDB（规格 3.6/9.4）。
 * 分块算法复刻 _group_segments_into_chunks：按句子字符数贪心，chunk_size=2000。
 * 向量存 SQLite BLOB（Float32Array），查询为 JS 暴力余弦（个人库规模足够）。
 * embedding 服务不可用时静默降级：检索退化为关键词匹配（取前 N 段连续文本）。
 */

const CHUNK_SIZE = 2000
const N_RESULTS = 5

export interface Chunk {
  chunk_index: number
  segment_indices: number[]
  text: string
}

export function chunkSegments(segments: Segment[], filename: string): Chunk[] {
  const chunks: Chunk[] = []
  let current: Segment[] = []
  let currentLen = 0
  const flush = () => {
    if (current.length === 0) return
    chunks.push({
      chunk_index: chunks.length,
      segment_indices: current.map((s) => s.index),
      text: `文件名：${filename}\n内容：${current.map((s) => s.sentence).join(' ')}`,
    })
    current = []
    currentLen = 0
  }
  for (const seg of segments) {
    if (currentLen + seg.sentence.length > CHUNK_SIZE && current.length > 0) flush()
    current.push(seg)
    currentLen += seg.sentence.length
  }
  flush()
  return chunks
}

export async function indexTranscriptChunks(
  transcriptId: number,
  filename: string,
  segments: Segment[],
): Promise<number> {
  const chunks = chunkSegments(segments, filename)
  if (chunks.length === 0) return 0
  const db = getDb()
  const del = db.prepare(`DELETE FROM segment_embeddings WHERE transcript_id = ?`)
  // 逐块 embedding（失败即整体放弃，走降级）
  const vectors: { chunk: Chunk; vec: number[] }[] = []
  for (const chunk of chunks) {
    const vec = await embed(chunk.text)
    vectors.push({ chunk, vec })
  }
  const insVec = db.prepare(
    `INSERT OR REPLACE INTO segment_embeddings (transcript_id, chunk_index, segment_indices, vec)
     VALUES (?, ?, ?, ?)`,
  )
  let count = 0
  const tx = db.transaction(() => {
    del.run(transcriptId)
    for (const { chunk, vec } of vectors) {
      insVec.run(transcriptId, chunk.chunk_index, JSON.stringify(chunk.segment_indices), Buffer.from(new Float32Array(vec).buffer))
      count += 1
    }
  })
  tx()
  return count
}

export function deleteTranscriptChunks(transcriptId: number): void {
  getDb().prepare(`DELETE FROM segment_embeddings WHERE transcript_id = ?`).run(transcriptId)
}

function cosine(a: Float32Array, b: Float32Array): number {
  let dot = 0
  let na = 0
  let nb = 0
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i]
    na += a[i] * a[i]
    nb += b[i] * b[i]
  }
  if (na === 0 || nb === 0) return 0
  return dot / (Math.sqrt(na) * Math.sqrt(nb))
}

/**
 * 检索：返回命中的 segments（按 index 排序）。
 * 向量检索失败（embedding 服务不在）→ 关键词降级：对每篇稿子的句子做子串匹配，
 * 命中处向两侧扩展成连续段，凑满 N_RESULTS 个 chunk 的等效量。
 */
export async function retrieve(
  question: string,
  transcriptIds: number[],
): Promise<{ transcriptId: number; segments: Segment[] }[]> {
  const db = getDb()
  const out: { transcriptId: number; segments: Segment[] }[] = []

  for (const tid of transcriptIds) {
    const row = db
      .prepare(`SELECT segments_json, audio_path, video_path FROM transcripts WHERE id = ?`)
      .get(tid) as { segments_json: string; audio_path: string; video_path: string | null } | undefined
    if (!row) continue
    const segments = JSON.parse(row.segments_json) as Segment[]

    let picked: Segment[] = []
    try {
      const qv = new Float32Array(await embed(question))
      const rows = db
        .prepare(
          `SELECT chunk_index, segment_indices, vec FROM segment_embeddings WHERE transcript_id = ?`,
        )
        .all(tid) as { chunk_index: number; segment_indices: string; vec: Buffer }[]
      const scored = rows
        .map((r) => ({
          indices: JSON.parse(r.segment_indices) as number[],
          score: cosine(qv, new Float32Array(r.vec.buffer, r.vec.byteOffset, r.vec.byteLength / 4)),
        }))
        .sort((a, b) => b.score - a.score)
        .slice(0, N_RESULTS)
      const indexSet = new Set(scored.flatMap((s) => s.indices))
      picked = segments.filter((s) => indexSet.has(s.index))
    } catch {
      picked = keywordFallback(question, segments)
    }
    if (picked.length > 0) {
      out.push({ transcriptId: tid, segments: picked.sort((a, b) => a.index - b.index) })
    }
  }
  return out
}

/** 关键词降级：按问题中的 2-gram 命中句子，向两侧各扩 2 句 */
function keywordFallback(question: string, segments: Segment[]): Segment[] {
  const q = question.replace(/\s+/g, '')
  const hits = new Set<number>()
  segments.forEach((seg, i) => {
    const text = seg.sentence.replace(/\s+/g, '')
    for (let start = 0; start + 2 <= q.length; start++) {
      if (text.includes(q.slice(start, start + 2))) {
        hits.add(i)
        for (const j of [i - 2, i - 1, i + 1, i + 2]) {
          if (j >= 0 && j < segments.length) hits.add(j)
        }
        break
      }
    }
  })
  return [...hits].sort((a, b) => a - b).slice(0, 40).map((i) => segments[i])
}
