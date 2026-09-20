'use client'

import { X, CheckCircle, AlertCircle, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"

interface TranslateProgressState {
  status: 'idle' | 'detecting' | 'translating' | 'done' | 'error'
  progress: number
  message: string
  detectionInfo?: string
  targetLanguage?: string
  newTranscriptId?: number
}

interface TranslateProgressPanelProps {
  state: TranslateProgressState
  onClose: () => void
  onRetry?: () => void
}

export default function TranslateProgressPanel({
  state,
  onClose,
  onRetry,
}: Readonly<TranslateProgressPanelProps>) {
  return (
    <div className="fixed bottom-4 right-4 w-80 rounded-lg border border-border bg-card shadow-lg">
      <div className="flex items-start gap-3 p-4">
        <div className="flex-shrink-0 mt-0.5">
          {state.status === 'detecting' && (
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
          )}
          {state.status === 'translating' && (
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
          )}
          {state.status === 'done' && (
            <CheckCircle className="h-5 w-5 text-success" />
          )}
          {state.status === 'error' && (
            <AlertCircle className="h-5 w-5 text-destructive" />
          )}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2 mb-1">
            <h3 className="text-sm font-semibold text-foreground">
              {state.status === 'detecting' && '检测语言中'}
              {state.status === 'translating' && '翻译中'}
              {state.status === 'done' && '翻译完成'}
              {state.status === 'error' && '翻译失败'}
            </h3>
            <button
              onClick={onClose}
              className="text-muted-foreground hover:text-muted-foreground transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <p className="text-xs text-muted-foreground mb-2">{state.message}</p>

          {state.detectionInfo && (
            <div className="mb-2 rounded bg-primary/10 p-2 text-xs text-primary">
              {state.detectionInfo}
            </div>
          )}

          {(state.status === 'detecting' || state.status === 'translating') && (
            <div className="w-full bg-muted rounded-full h-1.5 overflow-hidden">
              <div
                className="bg-primary h-full transition-all duration-300"
                style={{ width: `${state.progress}%` }}
              />
            </div>
          )}

          {state.status === 'error' && onRetry && (
            <Button
              size="sm"
              variant="outline"
              onClick={onRetry}
              className="w-full mt-2"
            >
              重试
            </Button>
          )}

          {state.status === 'done' && state.newTranscriptId && (
            <p className="text-xs text-muted-foreground mt-2">
              已创建新文稿 (ID: {state.newTranscriptId})
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
