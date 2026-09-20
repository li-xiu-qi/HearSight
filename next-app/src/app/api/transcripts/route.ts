import { NextRequest, NextResponse } from 'next/server'
import path from 'node:path'
import { getDb } from '@/lib/db'
import type { Segment, TranscriptMeta } from '@/lib/types'

/** GET /api/transcripts?limit=50&offset=0 — 列表按 id DESC（原 ORDER BY id DESC） */
export async function GET(req: NextRequest) {
  const sp = req.nextUrl.searchParams
  const limit = Math.min(200, Math.max(1, Number(sp.get('limit') || 50)))
  const offset = Math.max(0, Number(sp.get('offset') || 0))
  const db = getDb()
  const rows = db
    .prepare(
      `SELECT id, audio_path, video_path, media_type, segments_json, created_at
       FROM transcripts ORDER BY id DESC LIMIT ? OFFSET ?`,
    )
    .all(limit, offset) as {
    id: number
    audio_path: string
    video_path: string | null
    media_type: string
    segments_json: string
    created_at: string
  }[]
  const items: TranscriptMeta[] = rows.map((r) => ({
    id: r.id,
    audio_path: r.audio_path,
    video_path: r.video_path,
    media_type: r.media_type,
    created_at: r.created_at,
    segment_count: safeParse<Segment[]>(r.segments_json)?.length ?? 0,
    title: path.basename(r.video_path || r.audio_path, path.extname(r.video_path || r.audio_path)),
  }))
  const total = (db.prepare(`SELECT COUNT(*) AS c FROM transcripts`).get() as { c: number }).c
  return NextResponse.json({ total, items })
}

function safeParse<T>(s: string): T | null {
  try {
    return JSON.parse(s) as T
  } catch {
    return null
  }
}
