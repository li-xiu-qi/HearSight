#!/usr/bin/env node
/**
 * HearSight 领域 MCP server（stdio transport，零依赖，手写 JSON-RPC 2.0 over NDJSON）。
 *
 * 由 step-code 以子进程方式拉起（mcp.json 的 mcpServers.hearsight），工具面：
 *   list_transcripts / search_transcripts / read_segments / transcript_outline
 * 全部经 HearSight 本地 REST API 取数（HEARSIGHT_API_BASE，默认 127.0.0.1:9187/api），
 * 本进程不碰数据库、不重复业务逻辑。
 *
 * 兼容性说明：客户端是官方 MCP SDK 的 Client。initialize 时回显客户端请求的
 * protocolVersion（必然在客户端支持列表内），避免版本协商失败。
 */

const API_BASE = (process.env.HEARSIGHT_API_BASE || 'http://127.0.0.1:9187/api').replace(/\/+$/, '')

const SERVER_INFO = { name: 'hearsight', version: '1.0.0' }
const PROTOCOL_FALLBACK = '2024-11-10'

// ─── JSON-RPC 基础设施 ────────────────────────────────────────────────────

function send(obj) {
  const line = JSON.stringify(obj)
  process.stdout.write(line + '\n')
}

function reply(id, result) {
  send({ jsonrpc: '2.0', id, result })
}

function replyError(id, code, message) {
  send({ jsonrpc: '2.0', id, error: { code, message } })
}

function toolText(text) {
  return { content: [{ type: 'text', text }] }
}

function toolError(text) {
  return { content: [{ type: 'text', text }], isError: true }
}

// ─── 工具定义 ─────────────────────────────────────────────────────────────

const TOOLS = [
  {
    name: 'list_transcripts',
    description:
      '列出库内全部转写记录（id、标题、媒体类型、片段数）。用于了解有哪些素材可检索，或把用户提到的视频名映射成 transcript_id。',
    inputSchema: { type: 'object', properties: {}, required: [] },
  },
  {
    name: 'search_transcripts',
    description:
      '语义检索转写稿中与 query 最相关的片段。返回命中片段及其毫秒时间戳，是回答内容类问题的主要依据来源。transcript_ids 缺省时检索全部转写。',
    inputSchema: {
      type: 'object',
      properties: {
        query: { type: 'string', description: '检索问题或关键词（自然语言）' },
        transcript_ids: {
          type: 'array',
          description: '限定检索范围的转写 id 列表；缺省检索全部',
        },
      },
      required: ['query'],
    },
  },
  {
    name: 'read_segments',
    description:
      '按片段序号区间精读某篇转写（含毫秒时间戳）。search_transcripts 命中后需要看上下文时用。区间上限 60 段，超出请分段读。',
    inputSchema: {
      type: 'object',
      properties: {
        transcript_id: { type: 'number', description: '转写 id' },
        start_index: { type: 'number', description: '起始片段序号（含）' },
        end_index: { type: 'number', description: '结束片段序号（含）' },
      },
      required: ['transcript_id', 'start_index', 'end_index'],
    },
  },
  {
    name: 'transcript_outline',
    description:
      '某篇转写的大纲：标题、媒体类型、片段总数、总时长，以及按时间均匀采样的代表性句子。用于先建立全文结构再决定精读哪些区间。',
    inputSchema: {
      type: 'object',
      properties: {
        transcript_id: { type: 'number', description: '转写 id' },
      },
      required: ['transcript_id'],
    },
  },
]

// ─── 工具实现（全部走本地 REST API） ──────────────────────────────────────

async function api(pathname, init) {
  const res = await fetch(`${API_BASE}${pathname}`, init)
  const text = await res.text()
  if (!res.ok) throw new Error(`${init?.method ?? 'GET'} ${pathname} -> ${res.status}: ${text.slice(0, 200)}`)
  return text.length > 0 ? JSON.parse(text) : null
}

const postJson = (body) => ({
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
})

function toIds(v) {
  if (!Array.isArray(v)) return undefined
  const ids = v.map((n) => Number(n)).filter((n) => Number.isFinite(n))
  return ids.length > 0 ? ids : undefined
}

function fmtSeg(seg) {
  return `[${seg.index}] ${Number(seg.start_time).toFixed(2)}-${Number(seg.end_time).toFixed(2)} ${String(
    seg.sentence ?? '',
  ).trim()}`
}

async function callTool(name, args) {
  switch (name) {
    case 'list_transcripts': {
      const data = await api('/transcripts?limit=50')
      const items = Array.isArray(data?.items) ? data.items : []
      if (items.length === 0) return toolText('库内暂无转写记录。')
      const lines = items.map(
        (t) => `#${t.id} 《${t.title}》 ${t.media_type} ${t.segment_count} 段（${t.created_at}）`,
      )
      return toolText(`共 ${data?.total ?? items.length} 篇转写：\n` + lines.join('\n'))
    }

    case 'search_transcripts': {
      const query = typeof args?.query === 'string' ? args.query.trim() : ''
      if (query === '') return toolError('search_transcripts 缺少 query 参数')
      const body = { query }
      const ids = toIds(args?.transcript_ids)
      if (ids) body.transcript_ids = ids
      const data = await api('/search', postJson(body))
      const results = Array.isArray(data?.results) ? data.results : []
      if (results.length === 0) return toolText('未检索到相关内容。')
      const blocks = results.map(
        (r) => `《${r.filename}》(transcript_id=${r.transcript_id})\n` + r.segments.map(fmtSeg).join('\n'),
      )
      return toolText(blocks.join('\n\n'))
    }

    case 'read_segments': {
      const tid = Number(args?.transcript_id)
      const start = Number(args?.start_index)
      const end = Number(args?.end_index)
      if (!Number.isFinite(tid) || !Number.isFinite(start) || !Number.isFinite(end)) {
        return toolError('read_segments 需要 transcript_id / start_index / end_index 三个数字参数')
      }
      if (end - start > 60) return toolError('区间超过 60 段，请缩小范围分段读')
      const detail = await api(`/transcripts/${tid}`)
      const segs = Array.isArray(detail?.segments) ? detail.segments : []
      const picked = segs.filter((s) => s.index >= start && s.index <= end)
      if (picked.length === 0) {
        return toolText(`transcript_id=${tid} 在 [${start}, ${end}] 区间没有片段（共 ${segs.length} 段）。`)
      }
      return toolText(
        `《${detail.title ?? tid}》(transcript_id=${tid}) 片段 ${start}-${end}：\n` + picked.map(fmtSeg).join('\n'),
      )
    }

    case 'transcript_outline': {
      const tid = Number(args?.transcript_id)
      if (!Number.isFinite(tid)) return toolError('transcript_outline 需要数字参数 transcript_id')
      const detail = await api(`/transcripts/${tid}`)
      const segs = Array.isArray(detail?.segments) ? detail.segments : []
      if (segs.length === 0) return toolText(`transcript_id=${tid} 没有片段。`)
      const durationMs = Number(segs[segs.length - 1].end_time)
      // 采样上限 40 行：大纲是给模型建结构感的，不是全文搬运。长稿全量返回会把
      // agent 上下文撑爆（本地推理窗口 8K，曾因此第 4 轮请求 400 空答案收场）。
      const step = Math.max(1, Math.ceil(segs.length / 40))
      const sampled = segs.filter((_, i) => i % step === 0)
      const head =
        `《${detail.title ?? tid}》(transcript_id=${tid}) ${detail.media_type}\n` +
        `片段总数 ${segs.length}，总时长 ${(durationMs / 1000).toFixed(1)} 秒。按时间采样的代表性句子（毫秒时间戳）：`
      return toolText(head + '\n' + sampled.map(fmtSeg).join('\n'))
    }

    default:
      return toolError(`未知工具：${name}`)
  }
}

// ─── 方法分发 ─────────────────────────────────────────────────────────────

async function handle(msg) {
  const { id, method, params } = msg
  switch (method) {
    case 'initialize': {
      // 回显客户端请求的协议版本（必然在客户端支持列表内），缺省回落已知稳定版。
      const version =
        typeof params?.protocolVersion === 'string' ? params.protocolVersion : PROTOCOL_FALLBACK
      return reply(id, {
        protocolVersion: version,
        capabilities: { tools: {} },
        serverInfo: SERVER_INFO,
      })
    }
    case 'ping':
      return reply(id, {})
    case 'tools/list':
      return reply(id, { tools: TOOLS })
    case 'tools/call': {
      const name = typeof params?.name === 'string' ? params.name : ''
      try {
        return reply(id, await callTool(name, params?.arguments ?? {}))
      } catch (e) {
        return reply(id, toolError(`工具 ${name} 执行失败：${(e && e.message) || String(e)}`))
      }
    }
    default:
      // 通知（无 id）不回应；未知请求按 JSON-RPC 规范报 method not found。
      if (id === undefined || id === null) return
      return replyError(id, -32601, `method not found: ${method}`)
  }
}

// ─── stdio 读取（NDJSON） ─────────────────────────────────────────────────

let buffer = ''
process.stdin.setEncoding('utf8')
process.stdin.on('data', (chunk) => {
  buffer += chunk
  let idx
  while ((idx = buffer.indexOf('\n')) >= 0) {
    const line = buffer.slice(0, idx).trim()
    buffer = buffer.slice(idx + 1)
    if (line === '') continue
    let msg
    try {
      msg = JSON.parse(line)
    } catch {
      send({ jsonrpc: '2.0', id: null, error: { code: -32700, message: 'parse error' } })
      continue
    }
    void handle(msg)
  }
})
process.stdin.on('end', () => process.exit(0))
