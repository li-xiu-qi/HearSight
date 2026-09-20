'use client'

import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Trash2 } from "lucide-react"

interface ChatToolbarProps {
  readonly imageModeEnabled: boolean
  readonly isAudio: boolean
  readonly messagesLength: number
  /** agent 模式（多轮工具循环）开关；关闭即单轮检索 */
  readonly agentMode: boolean
  readonly onImageModeChange: (enabled: boolean) => void
  readonly onAgentModeChange: (enabled: boolean) => void
  readonly onClearChat: () => void
}

export default function ChatToolbar({
  imageModeEnabled,
  isAudio,
  messagesLength,
  agentMode,
  onImageModeChange,
  onAgentModeChange,
  onClearChat,
}: ChatToolbarProps) {
  return (
    <div className="flex justify-between items-center">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Switch
            id="image-mode"
            checked={imageModeEnabled}
            onCheckedChange={onImageModeChange}
            disabled={isAudio}
          />
          <Label
            htmlFor="image-mode"
            className={`text-sm cursor-pointer ${isAudio ? 'text-muted-foreground' : ''}`}
            title={isAudio ? '音频文件不支持图文展示' : ''}
          >
            图文展示
          </Label>
        </div>
        <div className="flex items-center gap-2">
          <Switch
            id="agent-mode"
            checked={agentMode}
            onCheckedChange={onAgentModeChange}
          />
          <Label
            htmlFor="agent-mode"
            className="text-sm cursor-pointer"
            title="开启后由 agent 自主检索转写稿并多轮追问，回答带检索过程"
          >
            Agent 模式
          </Label>
        </div>
      </div>
      <Button
        variant="ghost"
        size="sm"
        onClick={onClearChat}
        disabled={messagesLength === 0}
        className="gap-1"
      >
        <Trash2 className="h-3 w-3" />
        清空对话
      </Button>
    </div>
  )
}