import { NextRequest, NextResponse } from 'next/server'
import { getDb } from '@/lib/db'
import type { ChatMessage } from '@/lib/types'

/**
 * transcript 级聊天历史。原实现误写进 chat_messages 表（session_id 外键必炸，
 * 规格 9.6-a），这里改存 transcripts.chat_messages_json。
 */

function load(tid: number): ChatMessage[] {
  const row = getDb()
    .prepare(`SELECT chat_messages_json FROM transcripts WHERE id = ?`)
    .get(tid) as { chat_messages_json: string | null } | undefined
  if (!row?.chat_messages_json) return []
  try {
    return JSON.parse(row.chat_messages_json) as ChatMessage[]
  } catch {
    return []
  }
}

function save(tid: number, messages: ChatMessage[]): void {
  getDb()
    .prepare(`UPDATE transcripts SET chat_messages_json = ? WHERE id = ?`)
    .run(JSON.stringify(messages), tid)
}

/** 归一化入站消息（原 chat_message_crud 的 type/timestamp 解析规则） */
function normalize(raw: Record<string, unknown>): ChatMessage {
  const typeRaw = raw.type ?? raw.role
  const type = typeRaw === 'ai' ? 'ai' : 'user'
  let ts: number
  const t = raw.timestamp
  if (typeof t === 'number') ts = t < 1e10 ? t * 1000 : t
  else if (typeof t === 'string') {
    const parsed = Date.parse(t)
    ts = Number.isFinite(parsed) ? parsed : Date.now()
  } else ts = Date.now()
  return {
    id: `${type}-${ts}-${Math.random().toString(36).slice(2, 8)}`,
    type,
    content: String(raw.content ?? ''),
    timestamp: ts,
  }
}

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const id = Number((await params).id)
  const row = getDb().prepare(`SELECT id FROM transcripts WHERE id = ?`).get(id)
  if (!row) return NextResponse.json({ detail: `Transcript ${id} not found` }, { status: 404 })
  const messages = load(id)
  return NextResponse.json({ messages, has_messages: messages.length > 0 })
}

/** 全量替换语义（与原 save_chat_messages 一致：先清后插） */
export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const id = Number((await params).id)
  const body = (await req.json().catch(() => null)) as { messages?: Record<string, unknown>[] } | null
  if (!Array.isArray(body?.messages)) {
    return NextResponse.json({ detail: 'messages (list) is required' }, { status: 400 })
  }
  const exists = getDb().prepare(`SELECT id FROM transcripts WHERE id = ?`).get(id)
  if (!exists) return NextResponse.json({ detail: `Transcript ${id} not found` }, { status: 404 })
  save(id, body.messages.map(normalize))
  return NextResponse.json({ success: true, message: 'chat消息已保存', transcript_id: id })
}

export async function DELETE(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const id = Number((await params).id)
  const exists = getDb().prepare(`SELECT id FROM transcripts WHERE id = ?`).get(id)
  if (!exists) return NextResponse.json({ detail: `Transcript ${id} not found` }, { status: 404 })
  save(id, [])
  return NextResponse.json({ success: true, message: 'chat消息已清空', transcript_id: id })
}
