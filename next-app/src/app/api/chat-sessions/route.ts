import { NextRequest, NextResponse } from 'next/server'
import { getDb } from '@/lib/db'

/** GET /api/chat-sessions?limit=50&offset=0 ｜ POST /api/chat-sessions */
export async function GET(req: NextRequest) {
  const sp = req.nextUrl.searchParams
  const limit = Math.min(200, Math.max(1, Number(sp.get('limit') || 50)))
  const offset = Math.max(0, Number(sp.get('offset') || 0))
  const db = getDb()
  const rows = db
    .prepare(
      `SELECT id, title, created_at, updated_at FROM chat_sessions
       ORDER BY updated_at DESC LIMIT ? OFFSET ?`,
    )
    .all(limit, offset)
  return NextResponse.json({ sessions: rows })
}

export async function POST(req: NextRequest) {
  const body = (await req.json().catch(() => null)) as { title?: string | null } | null
  try {
    const db = getDb()
    const info = db
      .prepare(`INSERT INTO chat_sessions (title) VALUES (?)`)
      .run(body?.title ?? null)
    return NextResponse.json({ success: true, session_id: Number(info.lastInsertRowid) })
  } catch {
    return NextResponse.json({ detail: 'Failed to create chat session' }, { status: 500 })
  }
}
