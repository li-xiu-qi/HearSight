import { NextRequest, NextResponse } from 'next/server'
import { getDb } from '@/lib/db'
import { chat } from '@/lib/llm'
import { buildSummarizePrompt, extractSummaries } from '@/lib/prompts/summarize'
import type { Segment, SummaryItem } from '@/lib/types'

/** POST /api/summarize — 非流式，返回 { summaries } */
export async function POST(req: NextRequest) {
  const body = (await req.json().catch(() => null)) as { segments?: Segment[] } | null
  if (!Array.isArray(body?.segments)) {
    return NextResponse.json({ detail: 'segments (list) is required' }, { status: 400 })
  }
  const segments = body.segments
  try {
    const prompt = buildSummarizePrompt(segments)
    const raw = await chat(prompt, { maxTokens: 4096, temperature: 0.6 })
    const summaries: SummaryItem[] = extractSummaries(raw, segments)
    return NextResponse.json({ summaries })
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e)
    if (msg.includes('token') || msg.includes('exceed')) {
      return NextResponse.json({ detail: msg }, { status: 400 })
    }
    return NextResponse.json({ detail: `summarization failed: ${msg}` }, { status: 500 })
  }
}
