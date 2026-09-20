import { NextRequest, NextResponse } from 'next/server'
import { getDb } from '@/lib/db'
import { runTranslateTask } from '@/lib/tasks/translateTask'
import type { Segment, TranslationEntry } from '@/lib/types'

/** POST /api/transcripts/{id}/translate — 启动后台翻译 */
export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const id = Number((await params).id)
  const db = getDb()
  const row = db.prepare(`SELECT segments_json FROM transcripts WHERE id = ?`).get(id) as
    | { segments_json: string }
    | undefined
  if (!row) return NextResponse.json({ detail: `transcript not found: ${id}` }, { status: 404 })

  const body = (await req.json().catch(() => null)) as
    | {
        target_lang_code?: string
        source_lang_code?: string | null
        max_tokens?: number
        source_lang_display_name?: string | null
        target_lang_display_name?: string | null
        force_retranslate?: boolean
      }
    | null

  const segments = JSON.parse(row.segments_json) as Segment[]
  const totalCount = segments.filter((s) => !s.translation?.[body?.target_lang_code || 'zh']).length
  if (segments.length === 0) {
    return NextResponse.json({ detail: 'No segments to translate' }, { status: 400 })
  }

  void runTranslateTask({
    transcriptId: id,
    targetLang: body?.target_lang_code || 'zh',
    sourceLang: body?.source_lang_code ?? null,
    targetLangName: body?.target_lang_display_name ?? null,
    sourceLangName: body?.source_lang_display_name ?? null,
    maxTokens: body?.max_tokens ?? 4096,
    forceRetranslate: body?.force_retranslate ?? false,
  })
  return NextResponse.json({ status: 'started', transcript_id: id, total_count: totalCount })
}

/** GET /api/transcripts/{id}/translations */
export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const id = Number((await params).id)
  try {
    const row = getDb()
      .prepare(`SELECT translations_json FROM transcripts WHERE id = ?`)
      .get(id) as { translations_json: string | null } | undefined
    const translations = row?.translations_json
      ? (JSON.parse(row.translations_json) as Record<string, TranslationEntry[]>)
      : null
    return NextResponse.json({ translations, has_translations: !!translations })
  } catch (e) {
    return NextResponse.json(
      { detail: `Failed to get translations: ${e instanceof Error ? e.message : String(e)}` },
      { status: 500 },
    )
  }
}
