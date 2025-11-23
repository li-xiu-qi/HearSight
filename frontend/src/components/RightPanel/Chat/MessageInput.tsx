import type { KeyboardEvent } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Send, Loader2 } from "lucide-react"

interface MessageInputProps {
  readonly inputValue: string
  readonly loading: boolean
  readonly disabled: boolean
  readonly onInputChange: (value: string) => void
  readonly onSend: () => void
}

export default function MessageInput({
  inputValue,
  loading,
  disabled,
  onInputChange,
  onSend,
}: MessageInputProps) {
  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (!loading && inputValue.trim()) {
        onSend()
      }
    }
  }

  return (
    <>
      <Textarea
        value={inputValue}
        onChange={(e) => onInputChange(e.target.value)}
        onKeyDown={handleKeyPress}
        placeholder="请输入您的问题..."
        className="min-h-[80px] resize-none"
      />
      <Button
        onClick={onSend}
        disabled={disabled}
        className="w-full gap-2"
      >
        {loading ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            发送中
          </>
        ) : (
          <>
            <Send className="h-4 w-4" />
            发送
          </>
        )}
      </Button>
    </>
  )
}