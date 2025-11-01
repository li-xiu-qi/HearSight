export interface LanguageDetectionResult {
  primary_language: 'zh' | 'en' | 'other'
  chinese_ratio: number
  need_confirmation: boolean
  suggestion: string
}

interface Segment {
  sentence?: string
  [key: string]: unknown
}

function getLanguageRatio(text: string): [number, number] {
  let chineseCount = 0
  let englishCount = 0
  
  for (const char of text) {
    const code = char.charCodeAt(0)
    if (code >= 0x4e00 && code <= 0x9fff) {
      chineseCount++
    } else if ((code >= 97 && code <= 122) || (code >= 65 && code <= 90)) {
      englishCount++
    }
  }
  
  const total = chineseCount + englishCount
  if (total === 0) {
    return [0, 0]
  }
  
  return [chineseCount / total, englishCount / total]
}

export function detectLanguage(segments: Segment[]): LanguageDetectionResult {
  if (!segments || segments.length === 0) {
    return {
      primary_language: 'other',
      chinese_ratio: 0,
      need_confirmation: false,
      suggestion: '没有可用分句'
    }
  }
  
  let totalChinese = 0
  let totalEnglish = 0
  
  for (const seg of segments) {
    const sentence = seg.sentence || ''
    if (!sentence) continue
    
    const [chineseRatio, englishRatio] = getLanguageRatio(sentence)
    totalChinese += chineseRatio
    totalEnglish += englishRatio
  }
  
  const segmentCount = segments.length
  const avgChinese = segmentCount > 0 ? totalChinese / segmentCount : 0
  
  if (avgChinese >= 0.8) {
    return {
      primary_language: 'zh',
      chinese_ratio: avgChinese,
      need_confirmation: true,
      suggestion: '检测到主要为中文，是否翻译成英文？'
    }
  }
  
  const avgEnglish = segmentCount > 0 ? totalEnglish / segmentCount : 0
  if (avgEnglish >= 0.8) {
    return {
      primary_language: 'en',
      chinese_ratio: 1 - avgEnglish,
      need_confirmation: false,
      suggestion: '检测到主要为英文，将自动翻译成中文'
    }
  }
  
  return {
    primary_language: 'other',
    chinese_ratio: avgChinese,
    need_confirmation: false,
    suggestion: '检测到混合语言，建议手动翻译'
  }
}
