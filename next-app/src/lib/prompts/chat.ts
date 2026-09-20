import type { Segment } from '../types'

/**
 * 多视频问答 prompt，逐字复刻 chat_prompt_service._build_multi_video_prompt。
 * 时间戳格式：[视频名 92000.00-113620.00]（毫秒，两位小数），
 * 前端 MessageList 用正则从回答里抽这个格式渲染可点按钮，格式不能改。
 */

const HEADER = `你是一个专业的多视频内容分析助手。请基于下面的多个视频字幕内容，使用代码格式回答用户的问题。

要求：
1) 仔细分析所有视频的字幕内容，准确回答用户问题
2) 回答中引用相关内容时，严格遵守时间戳放置规则：
   - 以段落为单位组织回答内容
   - 每个段落只能在末尾添加一个时间戳，格式为：[视频名 开始时间-结束时间]
   - 时间戳必须放在段落末尾，前面不能有任何内容（除了段落文本）
   - 时间戳后需要换行，以便区分不同段落
   - 禁止在句子中间或句子末尾添加时间戳（除非整个段落只有一个句子）
3) 时间戳格式要求：
   - 使用毫秒为单位，保留两位小数
   - 使用连字符(-)分隔开始时间和结束时间
   - 包含视频名称：[视频名 92000.00-113620.00]
4) 时间戳格式示例：
   - 正确：人工智能在多个领域都有广泛应用。[example.mp4 92000.00-113620.00]
   - 错误：人工智能在医疗领域可以帮助医生诊断疾病[example.mp4 121540.00-145440.00]，在教育领域可以个性化辅导学生。
5) 保持回答简洁清晰，使用中文
6) 特别注意：对于与视频内容无关的通用问题（如打招呼、感谢、确认类问题等），请直接简洁回答，不要引用字幕内容，也不需要添加时间戳。

通用问题示例：
- "你好"、"您好"、"hello"
- "谢谢"、"感谢"
- "是的"、"好的"、"明白了"
- "再见"、"拜拜"

输出示例1（引用字幕内容时）：

人工智能在多个领域都有广泛应用。[example.mp4 92000.00-113620.00]

特别是在医疗领域，人工智能可以帮助医生进行疾病诊断。[video1.mp4 121540.00-145440.00]

输出示例2（通用问题时）：

你好！有什么我可以帮你的？

用户问题：{question}

多视频字幕内容：`

export interface VideoContext {
  filename: string
  transcript_id: number
  segments: Segment[]
}

export function buildMultiVideoPrompt(question: string, videos: VideoContext[]): string {
  const header = HEADER.replace('{question}', question)
  const bodyLines: string[] = []
  for (const video of videos) {
    if (video.segments.length === 0) continue
    bodyLines.push(`[视频开始: ${video.filename}]`)
    let chunkNum = 1
    let chunkStart = video.segments[0]
    let prev = video.segments[0]
    const flush = (endSeg: Segment) => {
      bodyLines.push(`  [块开始: ${chunkNum} - 索引: ${chunkStart.index}-${endSeg.index}]`)
      for (const seg of video.segments) {
        if (seg.index >= chunkStart.index && seg.index <= endSeg.index) {
          bodyLines.push(`  [${video.filename} ${seg.start_time.toFixed(2)}-${seg.end_time.toFixed(2)}] ${seg.sentence.trim()}`)
        }
      }
      bodyLines.push(`  [块结束: ${chunkNum}]`)
      bodyLines.push('')
      chunkNum += 1
    }
    for (let i = 1; i < video.segments.length; i++) {
      const seg = video.segments[i]
      if (seg.index === prev.index + 1) {
        prev = seg
        continue
      }
      flush(prev)
      chunkStart = seg
      prev = seg
    }
    flush(prev)
    bodyLines.push(`[视频结束: ${video.filename}]`)
    bodyLines.push('')
  }
  return header + '\n' + bodyLines.join('\n')
}
