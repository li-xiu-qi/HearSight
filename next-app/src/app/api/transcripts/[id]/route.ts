import { NextRequest, NextResponse } from 'next/server'
import fs from 'node:fs'
import path from 'node:path'
import { getDb } from '@/lib/db'
import { PATHS } from '@/lib/paths'
import { deleteTranscriptChunks } from '@/lib/rag'
import type { Segment, SummaryItem, TranslationEntry, TranscriptDetail } from '@/lib/types'

/** GET /api/transcripts/{id} */
export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id: rawId } = await params
  const id = Number(rawId)
  if (!Number.isFinite(id)) return NextResponse.json({ detail: 'invalid id' }, { status: 400 })
  const db = getDb()
  const row = db
    .prepare(
      `SELECT id, audio_path, video_path, media_type, segments_json, summaries_json, translations_json, created_at
       FROM transcripts WHERE id = ?`,
    )
    .get(id) as
    | {
        id: number
        audio_path: string
        video_path: string | null
        media_type: string
        segments_json: string
        summaries_json: string | null
        translations_json: string | null
        created_at: string
      }
    | undefined
  if (!row) return NextResponse.json({ detail: `transcript not found: ${id}` }, { status: 404 })

  const detail: TranscriptDetail = {
    id: row.id,
    audio_path: row.audio_path,
    video_path: row.video_path,
    media_type: row.media_type,
    created_at: row.created_at,
    segments: parse<Segment[]>(row.segments_json) ?? [],
    summaries: parse<SummaryItem[]>(row.summaries_json),
    translations: parse<Record<string, TranslationEntry[]>>(row.translations_json),
  }
  return NextResponse.json(detail)
}

/** DELETE /api/transcripts/{id} — 修复原实现不删文件的 bug（规格 9.5） */
export async function DELETE(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const id = Number((await params).id)
  const db = getDb()
  const row = db
    .prepare(`SELECT audio_path, video_path FROM transcripts WHERE id = ?`)
    .get(id) as { audio_path: string; video_path: string | null } | undefined
  if (!row) {
    return NextResponse.json({ detail: '转写记录不存在或已被删除' }, { status: 404 })
  }

  const deleted: string[] = []
  const errors: string[] = []
  const candidates = [row.audio_path, row.video_path]
  for (const p of candidates) {
    if (!p) continue
    // 路径穿越防护（保留原逻辑）
    const resolved = path.resolve(p)
    const rel = path.relative(path.resolve(PATHS.staticDir), resolved)
    const target = rel.startsWith('..') || path.isAbsolute(rel) ? path.join(PATHS.staticDir, path.basename(p)) : p
    try {
      if (fs.existsSync(target)) {
        await fs.promises.unlink(target)
        deleted.push(path.basename(target))
      }
      // 音频占位图
      const placeholder = path.join(path.dirname(target), `${path.basename(target, path.extname(target))}_placeholder.jpg`)
      if (fs.existsSync(placeholder)) {
        await fs.promises.unlink(placeholder)
        deleted.push(path.basename(placeholder))
      }
    } catch (e) {
      errors.push(e instanceof Error ? e.message : String(e))
    }
  }

  db.prepare(`DELETE FROM transcripts WHERE id = ?`).run(id)
  deleteTranscriptChunks(id)

  const message = errors.length
    ? `已删除 ${deleted.length} 个视频文件，转写记录删除成功，但有 ${errors.length} 个错误`
    : `已删除 ${deleted.length} 个视频文件，转写记录删除成功`
  return NextResponse.json({ success: true, message, transcript_id: id, deleted_files: deleted, errors: errors.length ? errors : null })
}

function parse<T>(s: string | null): T | null {
  if (!s) return null
  try {
    return JSON.parse(s) as T
  } catch {
    return null
  }
}
