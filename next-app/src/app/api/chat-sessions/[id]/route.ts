import { NextRequest, NextResponse } from 'next/server'
import { getDb } from '@/lib/db'

/** GET /api/chat-sessions/{id} ｜ PUT /api/chat-sessions/{id}/title ｜ DELETE /api/chat-sessions/{id} */
export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const id = Number((await params).id)
  const row = getDb()
    .prepare(`SELECT id, title, created_at, updated_at FROM chat_sessions WHERE id = ?`)
    .get(id)
  return NextResponse.json({ session: row ?? null })
}

export async function PUT(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const id = Number((await params).id)
  const body = (await req.json().catch(() => null)) as { title?: string } | null
  const info = getDb()
    .prepare(`UPDATE chat_sessions SET title = ? WHERE id = ?`)
    .run(body?.title ?? '', id)
  if (info.changes === 0) return NextResponse.json({ detail: '会话不存在' }, { status: 404 })
  return NextResponse.json({ success: true, message: '会话标题已更新' })
}

export async function DELETE(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const id = Number((await params).id)
  const info = getDb().prepare(`DELETE FROM chat_sessions WHERE id = ?`).run(id)
  if (info.changes === 0) return NextResponse.json({ detail: '会话不存在' }, { status: 404 })
  return NextResponse.json({ success: true, message: '会话已删除' })
}
