import { NextRequest, NextResponse } from 'next/server'
import { getDb } from '@/lib/db'
import type { ChatMessage } from '@/lib/types'

/**
 * chat_sessions 消息：GET / POST / DELETE /api/chat-sessions/{id}/messages
 * POST 是全量替换语义（先 DELETE 再 INSERT，与原 save_chat_messages 一致）。
 * 消息 id 用自增主键回填（修掉原 type-timestamp 撞 ID 问题，规格 9.6-b），
 * 但对外仍输出 {id: `${type}-${ts}`, type, content, timestamp} 保持前端兼容。
 */

function normalize(raw: Record<string, unknown>): { type: 'user' | 'ai'; content: string; ts: number } {
  const type = (raw.type ?? raw.role) === 'ai' ? 'ai' : 'user'
  const t = raw.timestamp
  let ts: number
  if (typeof t === 'number') ts = t < 1e10 ? t * 1000 : t
  else if (typeof t === 'string') {
    const parsed = Date.parse(t)
    ts = Number.isFinite(parsed) ? parsed : Date.now()
  } else ts = Date.now()
  return { type, content: String(raw.content ?? ''), ts }
}

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const id = Number((await params).id)
  const rows = getDb()
    .prepare(
      `SELECT message_type, content, timestamp FROM chat_messages
       WHERE session_id = ? ORDER BY timestamp ASC`,
    )
    .all(id) as { message_type: string; content: string; timestamp: string }[]
  const messages: ChatMessage[] = rows.map((r) => ({
    id: `${r.message_type}-${Date.parse(r.timestamp) || Date.now()}`,
    type: r.message_type as 'user' | 'ai',
    content: r.content,
    timestamp: Date.parse(r.timestamp) || Date.now(),
  }))
  return NextResponse.json({ messages, has_messages: messages.length > 0 })
}

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const id = Number((await params).id)
  const body = (await req.json().catch(() => null)) as { messages?: Record<string, unknown>[] } | null
  if (!Array.isArray(body?.messages)) {
    return NextResponse.json({ detail: 'messages (list) is required' }, { status: 400 })
  }
  const db = getDb()
  const session = db.prepare(`SELECT id FROM chat_sessions WHERE id = ?`).get(id)
  if (!session) return NextResponse.json({ detail: '会话不存在' }, { status: 404 })
  try {
    const tx = db.transaction((msgs: Record<string, unknown>[]) => {
      db.prepare(`DELETE FROM chat_messages WHERE session_id = ?`).run(id)
      const ins = db.prepare(
        `INSERT INTO chat_messages (session_id, message_type, content, timestamp) VALUES (?, ?, ?, ?)`,
      )
      for (const m of msgs) {
        const { type, content, ts } = normalize(m)
        ins.run(id, type, content, new Date(ts).toISOString())
      }
      db.prepare(`UPDATE chat_sessions SET updated_at = datetime('now','localtime') WHERE id = ?`).run(id)
    })
    tx(body.messages)
    return NextResponse.json({ success: true, message: 'chat消息已保存' })
  } catch {
    return NextResponse.json({ detail: '保存 chat 消息失败（DB error）' }, { status: 500 })
  }
}

export async function DELETE(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const id = Number((await params).id)
  const db = getDb()
  const session = db.prepare(`SELECT id FROM chat_sessions WHERE id = ?`).get(id)
  if (!session) return NextResponse.json({ detail: '会话不存在' }, { status: 404 })
  db.prepare(`DELETE FROM chat_messages WHERE session_id = ?`).run(id)
  return NextResponse.json({ success: true, message: 'chat消息已清空' })
}
