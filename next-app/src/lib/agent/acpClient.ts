import { spawn, type ChildProcess } from 'node:child_process'
import { createAgentWorkspace, type AgentWorkspace } from './workspace'

/**
 * step-code ACP 子进程客户端（newline-delimited JSON-RPC 2.0 over stdio）。
 *
 * 形态：HearSight 为每个问答会话 spawn 一个 `step --acp` 子进程，
 * HOME 指向隔离工作区（config.toml + mcp.json + skills 全在区内）。
 * 会话多轮复用同一进程与同一 ACP session（agent 自行保留上下文）。
 *
 * 事件映射（ACP session/update → 回调）：
 *   agent_message_chunk → onText
 *   tool_call(in_progress) → onStep（人类可读标签）
 *   tool_call_update(completed/failed) → onToolResult
 * 权限请求（session/request_permission）一律自动 allow-once：
 * 工具面已被 enabled_tools 白名单收窄到领域工具，放行是既定策略。
 */

export interface AcpAgentEvents {
  onText: (text: string) => void
  onStep: (label: string) => void
  onToolResult?: (info: { name: string; isError: boolean; preview: string }) => void
}

interface Pending {
  resolve: (result: any) => void
  reject: (error: Error) => void
}

const STEP_BIN = process.env.HEARSIGHT_STEP_BIN || 'step'

/** 工具名 → 人类可读的步骤标签 */
function stepLabel(name: string, input: unknown): string {
  const q = (v: unknown) => (typeof v === 'string' && v.trim() !== '' ? v.trim() : '')
  const args = (input ?? {}) as Record<string, unknown>
  switch (name) {
    case 'skill':
      return `加载领域协议：${q(args.name) || 'hearsight-qa'}`
    case 'tool_search':
      return `检索可用工具：${q(args.query) || ''}`
    case 'mcp__hearsight__list_transcripts':
      return '查看转写库列表'
    case 'mcp__hearsight__search_transcripts':
      return `检索转写稿：${q(args.query)}`
    case 'mcp__hearsight__read_segments':
      return `精读片段 #${q(args.start_index)}-${q(args.end_index)}`
    case 'mcp__hearsight__transcript_outline':
      return `读取转写大纲 #${q(args.transcript_id)}`
    default:
      return `调用工具 ${name}`
  }
}

export class AcpAgentProcess {
  private readonly proc: ChildProcess
  private readonly pending = new Map<number, Pending>()
  private readonly stderrTail: string[] = []
  private rpcSeq = 0
  private buffer = ''
  private sessionId: string | null = null
  private closed = false

  private constructor(
    proc: ChildProcess,
    private readonly workspace: AgentWorkspace,
  ) {
    this.proc = proc
    proc.stdout?.setEncoding('utf8')
    proc.stdout?.on('data', (chunk: string) => this.onStdout(chunk))
    proc.stderr?.setEncoding('utf8')
    proc.stderr?.on('data', (chunk: string) => {
      // step-code 的 [acp] 诊断走 stderr；留尾部供排障，不进协议流。
      this.stderrTail.push(chunk)
      if (this.stderrTail.length > 40) this.stderrTail.shift()
    })
    proc.on('exit', (code) => {
      this.closed = true
      for (const [, p] of this.pending) {
        p.reject(new Error(`step-code 进程退出（code=${code}）。stderr 尾部：${this.stderrTail.join('').slice(-500)}`))
      }
      this.pending.clear()
    })
    proc.on('error', (e) => {
      this.closed = true
      for (const [, p] of this.pending) p.reject(new Error(`step-code 进程错误：${e.message}`))
      this.pending.clear()
    })
  }

  /** spawn 并完成 initialize 握手。握手失败（如二进制不存在）即抛，由调用方决定降级。 */
  static async start(workspaceKey: string): Promise<AcpAgentProcess> {
    const workspace = createAgentWorkspace(workspaceKey)
    const bin = process.env.HEARSIGHT_STEP_BIN || 'step'
    // 传 .js 入口时用当前 node 跑（本地开发/未全局安装 step 时用）；否则按 PATH 上的命令跑。
    const isJsEntry = /\.(js|mjs|cjs)$/.test(bin)
    const command = isJsEntry ? process.execPath : bin
    const args = isJsEntry ? [bin, '--acp'] : ['--acp']
    const proc = spawn(command, args, {
      cwd: workspace.dir,
      env: { ...process.env, ...workspace.env },
      stdio: ['pipe', 'pipe', 'pipe'],
    })
    const agent = new AcpAgentProcess(proc, workspace)
    await agent.initialize()
    return agent
  }

  private request(method: string, params: Record<string, unknown> = {}): Promise<any> {
    return new Promise((resolve, reject) => {
      if (this.closed) {
        reject(new Error('ACP 连接已关闭'))
        return
      }
      const id = ++this.rpcSeq
      this.pending.set(id, { resolve, reject })
      this.write({ jsonrpc: '2.0', id, method, params })
    })
  }

  private write(obj: unknown): void {
    this.proc.stdin?.write(JSON.stringify(obj) + '\n')
  }

  private notify(method: string, params: Record<string, unknown> = {}): void {
    this.write({ jsonrpc: '2.0', method, params })
  }

  private onStdout(chunk: string): void {
    this.buffer += chunk
    let idx: number
    while ((idx = this.buffer.indexOf('\n')) >= 0) {
      const line = this.buffer.slice(0, idx).trim()
      this.buffer = this.buffer.slice(idx + 1)
      if (line === '') continue
      let msg: any
      try {
        msg = JSON.parse(line)
      } catch {
        continue
      }
      this.dispatch(msg)
    }
  }

  private dispatch(msg: any): void {
    // 我方请求的响应
    if (msg.id !== undefined && msg.id !== null && (msg.result !== undefined || msg.error !== undefined)) {
      const p = this.pending.get(Number(msg.id))
      if (p !== undefined) {
        this.pending.delete(Number(msg.id))
        if (msg.error !== undefined && msg.error !== null) {
          p.reject(new Error(typeof msg.error.message === 'string' ? msg.error.message : 'ACP error'))
        } else {
          p.resolve(msg.result)
        }
      }
      return
    }
    // server→client 请求（权限弹窗）：白名单已收窄工具面，一律 allow-once。
    if (msg.method === 'session/request_permission') {
      this.write({ jsonrpc: '2.0', id: msg.id, result: { optionId: 'allow-once' } })
      return
    }
    // 通知
    if (msg.method === 'session/update') {
      this.onSessionUpdate(msg.params ?? {})
    }
  }

  private onSessionUpdate(params: any): void {
    if (this.sessionId !== null && params.sessionId !== this.sessionId) return
    switch (params.sessionUpdate) {
      case 'agent_message_chunk':
        if (typeof params.content?.text === 'string') this.events?.onText(params.content.text)
        break
      case 'tool_call':
        if (typeof params.title === 'string') {
          if (params.toolCallId !== undefined) {
            this.toolNames.set(String(params.toolCallId), params.title)
          }
          // 连续重复公告去重（权限路径 + 执行路径各发一条）。同一工具被 genuinely
          // 重复调用时中间必有 tool_call_update，指纹会被清掉，不会误吞。
          const fp = `${params.title}|${JSON.stringify(params.rawInput ?? {})}`
          if (fp !== this.lastToolCallFingerprint) {
            this.lastToolCallFingerprint = fp
            this.events?.onStep(stepLabel(params.title, params.rawInput))
          }
        }
        break
      case 'tool_call_update': {
        this.lastToolCallFingerprint = null
        const blocks: any[] = Array.isArray(params.content) ? params.content : []
        const text = blocks.map((b) => (b?.type === 'text' ? String(b.text ?? '') : `[${b?.type}]`)).join('\n')
        this.events?.onToolResult?.({
          name: this.toolNames.get(String(params.toolCallId)) ?? 'tool',
          isError: params.status === 'failed',
          preview: text.slice(0, 200),
        })
        break
      }
      default:
        break
    }
  }

  private events: AcpAgentEvents | null = null
  private readonly toolNames = new Map<string, string>()
  private currentPromptReject: ((error: Error) => void) | null = null
  /** 上一条 tool_call 公告的指纹：权限路径（authorizeToolCall）与执行路径（tool_start）
   *  会对同一次调用各发一条 tool_call，前端步骤不能重复展示，连续同指纹的跳过。 */
  private lastToolCallFingerprint: string | null = null

  private async initialize(): Promise<void> {
    await this.request('initialize', {
      protocolVersion: 1,
      clientCapabilities: { fs: { readTextFile: false, writeTextFile: false } },
    })
    this.notify('notifications/initialized')
  }

  /** 发送一轮对话。同一进程可多次调用（多轮，agent 自留上下文）。返回本轮完整正文。 */
  async prompt(text: string, events: AcpAgentEvents): Promise<string> {
    const prev = this.events
    let full = ''
    this.events = {
      ...events,
      onText: (t) => {
        full += t
        events.onText(t)
      },
    }
    try {
      if (this.sessionId === null) {
        const created = await this.request('session/new', { cwd: this.workspace.dir })
        this.sessionId = String(created.sessionId)
      }
      await new Promise<void>((resolve, reject) => {
        this.currentPromptReject = reject
        this.request('session/prompt', {
          sessionId: this.sessionId,
          prompt: [{ type: 'text', text }],
        }).then(() => resolve(), reject)
      })
    } finally {
      this.currentPromptReject = null
      this.events = prev
    }
    return full
  }

  /** 中止当前轮（客户端断开时调用）：通知 ACP 取消并让在途 prompt 以 AbortError 结束。 */
  cancel(): void {
    if (this.sessionId !== null) this.notify('session/cancel', { sessionId: this.sessionId })
    this.currentPromptReject?.(new Error('ABORTED'))
    this.currentPromptReject = null
  }

  /** 中止当前轮并关闭进程。 */
  async close(): Promise<void> {
    if (this.closed) return
    this.closed = true
    try {
      if (this.sessionId !== null) this.notify('session/cancel', { sessionId: this.sessionId })
    } catch {
      /* 进程可能已退出 */
    }
    this.proc.stdin?.end()
    setTimeout(() => {
      if (!this.proc.killed) this.proc.kill()
    }, 1000).unref()
  }
}
