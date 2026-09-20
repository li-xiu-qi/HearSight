import type { Segment, SummaryItem } from '../types'

/**
 * 摘要 prompt 与解析，逐字复刻 Python 侧 text_process/summarize.py。
 * 输出契约：START_SUMMARIES ... END_SUMMARIES 之间的 JSON 数组。
 */

const HEADER = `你是一个专业的内容总结助手。请遵循以下格式要求（必须严格遵守）：

# 格式要求
1. 禁止使用Markdown、代码块（\`\`\`）、加粗、列表、编号等特殊格式
2. 禁止输出任何与总结无关的文字或说明
3. 只能输出纯文本格式的JSON数组

# 输出格式（必须严格遵守，不要多也不要少）
START_SUMMARIES
[
  {"topic": "<主题短句>", "summary": "<中文总结，允许换行但不包含引号>", "start_time": <起始时间戳>, "end_time": <结束时间戳>},
  {"topic": "<主题短句>", "summary": "<中文总结>", "start_time": <起始时间戳>, "end_time": <结束时间戳>}
]
END_SUMMARIES

# 要求说明
1. 仔细分析下面的对话/内容，从中提炼出2-5个清晰的主题
2. 为每个主题生成一段简明中文总结，准确涵盖主要信息点，避免流水账
3. 为每个主题指定对应的时间范围，使用该主题相关句子的起始和结束时间戳
4. 总结中如果需要换行，使用\\n表示，不要真实换行
5. 根据内容复杂度和信息量合理确定主题数量

下面是带时间戳的句子片段：`.trim()

const FOOTER = `请仔细分析内容，严格按上述格式输出，只输出START_SUMMARIES到END_SUMMARIES之间的内容。`

export function buildSummarizePrompt(segments: Segment[]): string {
  const body = segments.map((s) => `[${s.start_time.toFixed(2)}-${s.end_time.toFixed(2)}] ${s.sentence.trim()}`)
  return [HEADER, ...body, '', FOOTER].join('\n')
}

/** 解析 LLM 输出；空结果时回退为「全文单条」 */
export function extractSummaries(raw: string, segments: Segment[]): SummaryItem[] {
  const start = raw.indexOf('START_SUMMARIES')
  const end = raw.indexOf('END_SUMMARIES')
  if (start === -1 || end === -1) return fallback(segments)
  const block = raw.slice(start + 'START_SUMMARIES'.length, end)
  try {
    const parsed = JSON.parse(block) as unknown
    if (!Array.isArray(parsed)) return fallback(segments)
    const out: SummaryItem[] = []
    for (const item of parsed) {
      if (!item || typeof item !== 'object') continue
      const rec = item as Record<string, unknown>
      if (!('topic' in rec) || !('summary' in rec)) continue
      out.push({
        topic: String(rec.topic ?? '').trim(),
        summary: String(rec.summary ?? '')
          .trim()
          .replace(/\\n/g, '\n'),
        start_time: numOr(rec.start_time, minStart(segments)),
        end_time: numOr(rec.end_time, maxEnd(segments)),
      })
    }
    return out.length > 0 ? out : fallback(segments)
  } catch {
    return fallback(segments)
  }
}

function fallback(segments: Segment[]): SummaryItem[] {
  return [
    {
      topic: '',
      summary: segments.map((s) => s.sentence).join(''),
      start_time: minStart(segments),
      end_time: maxEnd(segments),
    },
  ]
}

function minStart(segments: Segment[]): number {
  return segments.reduce((m, s) => Math.min(m, s.start_time), Number.MAX_SAFE_INTEGER) || 0
}
function maxEnd(segments: Segment[]): number {
  return segments.reduce((m, s) => Math.max(m, s.end_time), 0)
}
function numOr(v: unknown, dflt: number): number {
  const n = typeof v === 'number' ? v : Number(v)
  return Number.isFinite(n) ? n : dflt
}
