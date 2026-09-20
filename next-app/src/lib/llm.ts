/**
 * LLM 客户端。OpenAI 兼容协议，三态可切：
 *   1. 本地 llama-server（默认，dgx-spark:8080，Qwen3.8-27B）
 *   2. 外部 OpenAI 兼容 API（硅基流动 / 百度 AI Studio，配 key 即用）
 *   3. 未配置 → 抛错，调用方降级
 *
 * 注意 Qwen3.8 系思考模型：流式时 reasoning 走 delta.reasoning_content，
 * 正式回答走 delta.content，本模块只取 content。
 */

export interface LLMConfig {
  baseUrl: string
  apiKey: string
  model: string
}

export function getLLMConfig(): LLMConfig {
  const baseUrl = process.env.LLM_BASE_URL || process.env.OPENAI_BASE_URL || 'http://127.0.0.1:8080/v1'
  const apiKey = process.env.LLM_API_KEY || process.env.OPENAI_API_KEY || 'local-no-key'
  const model = process.env.LLM_MODEL || process.env.OPENAI_CHAT_MODEL || 'qwen'
  return { baseUrl, apiKey, model }
}

export function getEmbeddingConfig(): { baseUrl: string; apiKey: string; model: string } {
  return {
    baseUrl: process.env.EMBEDDING_BASE_URL || 'http://127.0.0.1:8004/v1',
    apiKey: process.env.EMBEDDING_API_KEY || 'local-no-key',
    model: process.env.EMBEDDING_MODEL || 'bge-m3',
  }
}

/** 非流式对话，返回纯文本 */
export async function chat(prompt: string, opts: { maxTokens?: number; temperature?: number } = {}): Promise<string> {
  const { baseUrl, apiKey, model } = getLLMConfig()
  const res = await fetch(`${baseUrl}/chat/completions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${apiKey}` },
    body: JSON.stringify({
      model,
      messages: [{ role: 'user', content: prompt }],
      max_tokens: opts.maxTokens ?? 4096,
      temperature: opts.temperature ?? 0.6,
      stream: false,
    }),
  })
  if (!res.ok) throw new Error(`LLM request failed: ${res.status} ${await res.text()}`)
  const json = (await res.json()) as {
    choices?: { message?: { content?: string } }[]
  }
  return (json.choices?.[0]?.message?.content ?? '').trim()
}

/** 流式对话，逐段 yield content（跳过 reasoning_content） */
export async function* chatStream(
  prompt: string,
  signal?: AbortSignal,
): AsyncGenerator<string> {
  const { baseUrl, apiKey, model } = getLLMConfig()
  const res = await fetch(`${baseUrl}/chat/completions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${apiKey}` },
    body: JSON.stringify({
      model,
      messages: [{ role: 'user', content: prompt }],
      stream: true,
    }),
    signal,
  })
  if (!res.ok) throw new Error(`LLM stream failed: ${res.status} ${await res.text()}`)
  if (!res.body) throw new Error('LLM stream: empty body')

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''
    for (const line of lines) {
      const trimmed = line.trim()
      if (!trimmed.startsWith('data:')) continue
      const payload = trimmed.slice(5).trim()
      if (payload === '[DONE]') return
      try {
        const json = JSON.parse(payload) as {
          choices?: { delta?: { content?: string; reasoning_content?: string } }[]
        }
        const content = json.choices?.[0]?.delta?.content
        if (content) yield content
      } catch {
        // 跳过不完整帧
      }
    }
  }
}

/** 单条文本 embedding */
export async function embed(text: string): Promise<number[]> {
  const { baseUrl, apiKey, model } = getEmbeddingConfig()
  const res = await fetch(`${baseUrl}/embeddings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${apiKey}` },
    body: JSON.stringify({ model, input: text }),
  })
  if (!res.ok) throw new Error(`embedding failed: ${res.status} ${await res.text()}`)
  const json = (await res.json()) as { data?: { embedding: number[] }[] }
  const vec = json.data?.[0]?.embedding
  if (!vec) throw new Error('embedding: empty vector')
  return vec
}
