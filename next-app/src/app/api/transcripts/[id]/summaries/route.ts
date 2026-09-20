import { NextRequest, NextResponse } from 'next/server'
import { getDb } from '@/lib/db'
import type { SummaryItem } from '@/lib/types'

/** GET /api/transcripts/{id}/summaries */
export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const id = Number((await params).id)
  const db = getDb()
  const row = db.prepare(`SELECT summaries_json FROM transcripts WHERE id = ?`).get(id) as
    | { summaries_json: string | null }
    | undefined
  const summaries = row?.summaries_json ? parse<SummaryItem[]>(row.summaries_json) : null
  return NextResponse.json({ summaries, has_summaries: !!summaries?.length })
}

/** POST /api/transcripts/{id}/summaries — 覆盖写（原 save_summaries 语义） */
export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const id = Number((await params).id)
  const body = (await req.json().catch(() => null)) as { summaries?: SummaryItem[] } | null
  if (!Array.isArray(body?.summaries)) {
    return NextResponse.json({ detail: 'summaries (list) is required' }, { status: 400 })
  }
  const db = getDb()
  const info = db
    .prepare(`UPDATE transcripts SET summaries_json = ? WHERE id = ?`)
    .run(JSON.stringify(body.summaries), id)
  return NextResponse.json({
    success: info.changes > 0,
    message: info.changes > 0 ? '总结已保存' : '转写记录不存在',
    saved: info.changes > 0,
    transcript_id: id,
  })
}

function parse<T>(s: string | null): T | null {
  if (!s) return null
  try {
    return JSON.parse(s) as T
  } catch {
    return null
  }
}
