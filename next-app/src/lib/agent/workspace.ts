import fs from 'node:fs'
import path from 'node:path'
import { PATHS } from '../paths'

/**
 * step-code 子进程的隔离工作区生成器。
 *
 * 每个问答会话一个工作区（dataDir/agent-workspaces/<key>/），内含：
 *   .step-code/config.toml   provider 指向本地 llama-server + enabled_tools 白名单
 *   .step-code/mcp.json      HearSight 领域 MCP server（stdio，内部打本地 REST API）
 *   .step-code/skills/...    领域协议 skill
 * step-code 以 HOME=<workspace> 启动，三级配置全部落在工作区内，
 * 不碰用户真实 ~/.step-code，也不依赖 ACP 会话级 mcpServers（step-code 不支持热挂）。
 */

const SKILL_NAME = 'hearsight-qa'

/** MCP 工具白名单：skill 激活 + tool_search 发现 + 四个领域工具（名字可预知，显式列全） */
export const AGENT_TOOL_WHITELIST = [
  'skill',
  'tool_search',
  'mcp__hearsight__list_transcripts',
  'mcp__hearsight__search_transcripts',
  'mcp__hearsight__read_segments',
  'mcp__hearsight__transcript_outline',
]

export interface AgentWorkspace {
  /** 工作区目录（同时是 step-code 子进程的 cwd 与 HOME） */
  dir: string
  /** 追加给 step-code 子进程的环境变量 */
  env: Record<string, string>
  /** 生成的 config.toml 路径（排障用） */
  configPath: string
}

function agentAsset(name: string): string {
  const candidates = [
    path.join(process.cwd(), 'agent', name),
    path.join(PATHS.repoRoot, 'next-app', 'agent', name),
  ]
  for (const c of candidates) {
    if (fs.existsSync(c)) return c
  }
  throw new Error(`agent 资源不存在：${name}（已试 ${candidates.join(' / ')}）`)
}

/** 与 lib/llm.ts 同源地读 LLM 配置，保证 agent 与单轮 RAG 两条路打同一个端点 */
function llmEndpoint(): { baseUrl: string; model: string; apiKey: string } {
  return {
    baseUrl:
      process.env.LLM_BASE_URL || process.env.OPENAI_BASE_URL || 'http://127.0.0.1:8080/v1',
    model: process.env.LLM_MODEL || process.env.OPENAI_CHAT_MODEL || 'qwen',
    apiKey: process.env.LLM_API_KEY || process.env.OPENAI_API_KEY || 'local-no-key',
  }
}

/** MCP server 访问 HearSight 自身 API 的基地址；PORT 未显式设置时按 next start 默认推 */
function apiBase(): string {
  if (process.env.HEARSIGHT_API_BASE) return process.env.HEARSIGHT_API_BASE.replace(/\/+$/, '')
  const port = process.env.PORT ?? '3000'
  return `http://127.0.0.1:${port}/api`
}

export function createAgentWorkspace(key: string): AgentWorkspace {
  const safeKey = key.replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 64) || 'default'
  const dir = path.join(PATHS.dataDir, 'agent-workspaces', safeKey)
  const stepDir = path.join(dir, '.step-code')
  fs.mkdirSync(path.join(stepDir, 'skills', SKILL_NAME), { recursive: true })

  const llm = llmEndpoint()

  const configToml = [
    '# 由 HearSight 自动生成，请勿手改（重新生成会覆盖）',
    'provider = "openai"',
    `base_url = "${llm.baseUrl}"`,
    `model = "${llm.model}"`,
    `enabled_tools = [${AGENT_TOOL_WHITELIST.map((t) => `"${t}"`).join(', ')}]`,
    '',
  ].join('\n')
  fs.writeFileSync(path.join(stepDir, 'config.toml'), configToml, 'utf8')

  const mcpJson = {
    mcpServers: {
      hearsight: {
        command: process.env.HEARSIGHT_NODE_BIN || 'node',
        args: [agentAsset('mcp-server.mjs')],
        env: { HEARSIGHT_API_BASE: apiBase() },
        startupTimeoutMs: 15000,
      },
    },
  }
  fs.writeFileSync(path.join(stepDir, 'mcp.json'), JSON.stringify(mcpJson, null, 2), 'utf8')

  // skill 源在 next-app/agent/ 下，每次生成时拷贝进工作区（源改了对新会话生效）
  fs.copyFileSync(
    agentAsset(path.join(SKILL_NAME, 'SKILL.md')),
    path.join(stepDir, 'skills', SKILL_NAME, 'SKILL.md'),
  )

  const env: Record<string, string> = {
    HOME: dir,
    USERPROFILE: dir,
    STEP_CODE_API_KEY: llm.apiKey,
    HEARSIGHT_API_BASE: apiBase(),
  }
  return { dir, env, configPath: path.join(stepDir, 'config.toml') }
}

export function removeAgentWorkspace(key: string): void {
  const safeKey = key.replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 64) || 'default'
  fs.rmSync(path.join(PATHS.dataDir, 'agent-workspaces', safeKey), {
    recursive: true,
    force: true,
  })
}
