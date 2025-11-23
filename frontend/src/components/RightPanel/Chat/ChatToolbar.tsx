import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Trash2 } from "lucide-react"

interface ChatToolbarProps {
  readonly imageModeEnabled: boolean
  readonly isAudio: boolean
  readonly messagesLength: number
  readonly onImageModeChange: (enabled: boolean) => void
  readonly onClearChat: () => void
}

export default function ChatToolbar({
  imageModeEnabled,
  isAudio,
  messagesLength,
  onImageModeChange,
  onClearChat,
}: ChatToolbarProps) {
  return (
    <div className="flex justify-between items-center">
      <div className="flex items-center gap-2">
        <Switch
          id="image-mode"
          checked={imageModeEnabled}
          onCheckedChange={onImageModeChange}
          disabled={isAudio}
        />
        <Label
          htmlFor="image-mode"
          className={`text-sm cursor-pointer ${isAudio ? 'text-slate-400' : ''}`}
          title={isAudio ? '音频文件不支持图文展示' : ''}
        >
          图文展示
        </Label>
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