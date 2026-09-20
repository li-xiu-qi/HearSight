import { getDb } from '../db'
import { chat } from '../llm'
import {
  buildTranslatePrompt,
  extractTranslations,
  langName,
  splitTranslateBatches,
} from '../prompts/translate'
import type { Segment, TranslationEntry } from '../types'

/**
 * 翻译任务：替代 _background_translate。修复原 stream=True 喂字符串解析器的
 * 必崩 bug（规格 9.3）：统一非流式 chat() + message.content。
 * 进度落 translate_progress 表（替代无 TTL 的 Redis key）。
 */

export interface TranslateProgressRow {
  status: string
  progress: number
  translated_count: number
  total_count: number
  target_lang_code: string | null
  message: string | null
}

export function readProgress(transcriptId: number): TranslateProgressRow {
  const row = getDb()
    .prepare(`SELECT * FROM translate_progress WHERE transcript_id = ?`)
    .get(transcriptId) as TranslateProgressRow | undefined
  return (
    row ?? {
      status: 'idle',
      progress: 0,
      translated_count: 0,
      total_count: 0,
      target_lang_code: null,
      message: '未进行翻译',
    }
  )
}

function writeProgress(
  transcriptId: number,
  fields: Partial<TranslateProgressRow>,
): void {
  const cur = readProgress(transcriptId)
  const next = { ...cur, ...fields }
  getDb()
    .prepare(
      `INSERT INTO translate_progress (transcript_id, status, progress, translated_count, total_count, target_lang_code, message, updated_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
       ON CONFLICT(transcript_id) DO UPDATE SET
         status = excluded.status, progress = excluded.progress,
         translated_count = excluded.translated_count, total_count = excluded.total_count,
         target_lang_code = excluded.target_lang_code, message = excluded.message,
         updated_at = datetime('now','localtime')`,
    )
    .run(
      transcriptId,
      next.status,
      next.progress,
      next.translated_count,
      next.total_count,
      next.target_lang_code,
      next.message,
    )
}

export interface TranslateOptions {
  transcriptId: number
  targetLang: string
  sourceLang?: string | null
  targetLangName?: string | null
  sourceLangName?: string | null
  maxTokens?: number
  forceRetranslate?: boolean
}

export async function runTranslateTask(opts: TranslateOptions): Promise<void> {
  const db = getDb()
  const row = db
    .prepare(`SELECT segments_json, translations_json FROM transcripts WHERE id = ?`)
    .get(opts.transcriptId) as { segments_json: string; translations_json: string | null } | undefined
  if (!row) {
    writeProgress(opts.transcriptId, { status: 'error', message: 'transcript not found' })
    return
  }
  let segments = JSON.parse(row.segments_json) as Segment[]
  let translations = row.translations_json
    ? (JSON.parse(row.translations_json) as Record<string, TranslationEntry[]>)
    : {}

  const targetLang = opts.targetLang || 'zh'
  const sourceName = opts.sourceLangName || (opts.sourceLang ? langName(opts.sourceLang) : '原文')
  const targetName = opts.targetLangName || langName(targetLang)

  // force_retranslate：清掉该语言旧结果
  if (opts.forceRetranslate) {
    delete translations[targetLang]
    segments = segments.map((s) => {
      if (s.translation) {
        const next = { ...s.translation }
        delete next[targetLang]
        return { ...s, translation: next }
      }
      return s
    })
  }

  const untranslated = segments.filter((s) => !s.translation?.[targetLang] && s.sentence.trim())
  writeProgress(opts.transcriptId, {
    status: 'translating',
    progress: 0,
    translated_count: 0,
    total_count: untranslated.length,
    target_lang_code: targetLang,
    message: '翻译中...',
  })
  if (untranslated.length === 0) {
    writeProgress(opts.transcriptId, { status: 'completed', progress: 100, message: '翻译完成：0/0' })
    return
  }

  const maxTokens = opts.maxTokens ?? 4096
  const batches = splitTranslateBatches(untranslated, maxTokens)
  const translatedMap = new Map<number, string>()
  let done = 0

  for (const batch of batches) {
    const prompt = buildTranslatePrompt(batch, segments, sourceName, targetName)
    try {
      const raw = await chat(prompt, { maxTokens, temperature: 0.6 })
      const got = extractTranslations(raw)
      for (const [idx, text] of Object.entries(got)) translatedMap.set(Number(idx), text)
    } catch {
      // 批次失败进重试
    }
    // 质检：漏译/空译的进重试队列（每组 ≤5 句）
    const failed = batch.filter((s) => !translatedMap.get(s.index)?.trim())
    for (let i = 0; i < failed.length; i += 5) {
      const group = failed.slice(i, i + 5)
      try {
        const retryPrompt = buildTranslatePrompt(group, segments, sourceName, targetName)
        const raw = await chat(retryPrompt, { maxTokens: 2048, temperature: 0.6 })
        const got = extractTranslations(raw)
        for (const [idx, text] of Object.entries(got)) {
          if (text.trim()) translatedMap.set(Number(idx), text)
        }
      } catch {
        /* 仍失败记 still_failed，不阻塞 */
      }
    }
    done += batch.length
    const progress = Math.floor((done / untranslated.length) * 100)
    writeProgress(opts.transcriptId, {
      status: 'translating',
      progress,
      translated_count: done,
      total_count: untranslated.length,
      message: `翻译进度：${done}/${untranslated.length}`,
    })
  }

  // 回写：segments.translation[lang] + translations_json[lang] 双写
  const finalSegments = segments.map((s) => {
    const t = translatedMap.get(s.index)
    if (!t) return s
    return { ...s, translation: { ...(s.translation ?? {}), [targetLang]: t } }
  })
  const entries: TranslationEntry[] = finalSegments
    .filter((s) => s.translation?.[targetLang])
    .map((s) => ({
      index: s.index,
      sentence: s.sentence,
      translation: s.translation![targetLang],
      start_time: s.start_time,
      end_time: s.end_time,
    }))
  translations[targetLang] = entries

  try {
    db.prepare(`UPDATE transcripts SET segments_json = ?, translations_json = ? WHERE id = ?`).run(
      JSON.stringify(finalSegments),
      JSON.stringify(translations),
      opts.transcriptId,
    )
    writeProgress(opts.transcriptId, {
      status: 'completed',
      progress: 100,
      translated_count: done,
      total_count: untranslated.length,
      message: `翻译完成：${done}/${untranslated.length}`,
    })
  } catch (e) {
    writeProgress(opts.transcriptId, {
      status: 'error',
      message: `保存到数据库失败: ${e instanceof Error ? e.message : String(e)}`,
    })
  }
}
