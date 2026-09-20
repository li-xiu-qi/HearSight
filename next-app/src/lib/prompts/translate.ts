import type { Segment } from '../types'

/**
 * 翻译 prompt 与解析，复刻 Python 侧 translate_prompt_service / translate_result_service。
 * 顺手修掉原实现的 stream=True 喂字符串解析器的必崩 bug（规格 9.3）：
 * 调用方统一走非流式 chat()，解析器异常捕获放宽。
 */

const LANG_NAMES: Record<string, string> = {
  zh: '中文',
  en: '英文',
  ja: '日文',
  ko: '韩文',
  es: '西班牙文',
  fr: '法文',
  de: '德文',
  ru: '俄文',
}

export function langName(code: string): string {
  return LANG_NAMES[code.split('_').slice(-1)[0]] ?? code
}

export function buildTranslatePrompt(
  batch: Segment[],
  allSegments: Segment[],
  sourceLang: string,
  targetLang: string,
): string {
  const header = `你是一个专业的${sourceLang}至${targetLang}翻译专家。

翻译要求：
1. 准确传达原文含义，不要改变、扩展或删减原文内容
2. 保持原文的风格、语气和情感色彩
3. 保留专业术语和专有名词（如人名、地名、技术术语等）
4. 使用目标语言最自然的表达方式，避免生硬翻译
5. 不同语言的翻译长度可能差异很大，这是完全正常的（例如英文"Hello"可能翻译为中文"你好"）

关键要求 - 索引对应规则（必须严格遵守）：
- 【重要】每个翻译结果的 index 必须与【待翻译句子】中的 index 完全相同
- 【重要】每句话都有唯一的 index 标识符，返回的翻译必须一一对应
- 【重要】绝不能漏掉任何一句，绝不能改变顺序，绝不能重复
- 【重要】如果你注意到 index 不是连续的（如 0, 1, 3, 5），这是正常的，保持原样即可

工作流程：
1. 首先阅读【前文上下文】和【后文上下文】以了解语境（但这些内容本身不需要翻译）
2. 然后专注于翻译【待翻译句子】中的所有句子（只翻译这一部分）
3. 逐一确认每个句子都有唯一的翻译结果，index 必须完全对应

返回要求：
- 返回结果必须严格包含 START_TRANSLATIONS 和 END_TRANSLATIONS 边界标记
- 边界标记之间只能包含纯JSON数组格式
- JSON 数组必须包含所有待翻译句子的翻译结果（一个都不能少）
- 每个待翻译句子都必须有一个翻译条目，格式必须是（注意是单个大括号）: {"index": N, "translation": "翻译内容"}
- 严禁混入前文上下文或后文上下文的内容
- 禁止使用Markdown、代码块（\`\`\`）、加粗、列表、编号等特殊格式

格式示例1（注意：假设待翻译句子的 index 是 0, 1, 2）：

START_TRANSLATIONS
[
  {"index": 0, "translation": "翻译后的句子0"},
  {"index": 1, "translation": "翻译后的句子1"},
  {"index": 2, "translation": "翻译后的句子2"}
]
END_TRANSLATIONS

格式示例2（假设输入 index 是 5, 7, 9）：

START_TRANSLATIONS
[
  {"index": 5, "translation": "翻译后的句子"},
  {"index": 7, "translation": "翻译后的句子"},
  {"index": 9, "translation": "翻译后的句子"}
]
END_TRANSLATIONS`

  const lines: string[] = [header, '']
  const firstIdx = batch[0].index
  const lastIdx = batch[batch.length - 1].index
  const maxIdx = allSegments.reduce((m, s) => Math.max(m, s.index), 0)

  if (firstIdx > 0) {
    lines.push('【前文上下文（仅供参考）】')
    for (const seg of allSegments.filter((s) => s.index < firstIdx).slice(-2)) {
      lines.push(`${seg.index}: ${seg.sentence.trim()}`)
    }
    lines.push('')
  }

  lines.push('【待翻译句子】（必须逐一翻译，index必须一一对应）')
  for (const seg of batch) {
    if (seg.sentence.trim()) lines.push(`${seg.index}: ${seg.sentence.trim()}`)
  }
  lines.push('')
  lines.push(`（共 ${batch.length} 个句子需要翻译，检查：是否一个都没漏，是否顺序没乱，是否 index 完全对应）`)

  if (lastIdx < maxIdx) {
    lines.push('【后文上下文（仅供参考）】')
    for (const seg of allSegments.filter((s) => s.index > lastIdx).slice(0, 2)) {
      lines.push(`${seg.index}: ${seg.sentence.trim()}`)
    }
    lines.push('')
  }
  return lines.join('\n')
}

/** 解析翻译结果 → { index: translation }。宽容解析，任何失败返回 {} */
export function extractTranslations(raw: string): Record<number, string> {
  const start = raw.indexOf('START_TRANSLATIONS')
  const end = raw.indexOf('END_TRANSLATIONS')
  if (start !== -1 && end !== -1) {
    return parseArray(raw.slice(start + 'START_TRANSLATIONS'.length, end))
  }
  // 向后兼容与裸 JSON 兜底
  let text = raw.trim()
  const fence = text.match(/```(?:json)?\s*([\s\S]*?)```/)
  if (fence) text = fence[1].trim()
  const lb = text.indexOf('[')
  const rb = text.lastIndexOf(']')
  if (lb === -1 || rb === -1 || rb <= lb) return {}
  return parseArray(text.slice(lb, rb + 1))
}

function parseArray(block: string): Record<number, string> {
  try {
    const parsed = JSON.parse(block) as unknown
    if (!Array.isArray(parsed)) return {}
    const out: Record<number, string> = {}
    for (const item of parsed) {
      if (!item || typeof item !== 'object') continue
      const rec = item as Record<string, unknown>
      const idx = Number(rec.index)
      const trans = rec.translation
      if (Number.isFinite(idx) && typeof trans === 'string' && trans.trim()) {
        out[idx] = trans
      }
    }
    return out
  } catch {
    return {}
  }
}

/** 按 10 句一批、再按 token 估算贪心细切（复刻 _split_segments_by_output_tokens） */
export function splitTranslateBatches(segments: Segment[], maxTokens = 4096): Segment[][] {
  const batches: Segment[][] = []
  for (let i = 0; i < segments.length; i += 10) {
    batches.push(segments.slice(i, i + 10))
  }
  const out: Segment[][] = []
  for (const batch of batches) {
    let current: Segment[] = []
    let total = 0
    for (const seg of batch) {
      const est = Math.floor(seg.sentence.length * 1.5) + 20
      if (total + est > maxTokens && current.length > 0) {
        out.push(current)
        current = []
        total = 0
      }
      current.push(seg)
      total += est
    }
    if (current.length > 0) out.push(current)
  }
  return out
}
