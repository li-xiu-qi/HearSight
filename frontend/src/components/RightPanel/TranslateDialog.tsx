import { useEffect, useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Loader2 } from "lucide-react"
import { detectLanguage, type LanguageDetectionResult } from "../../utils/language-detector"

interface TranslateDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  transcriptId?: number
  segments?: Array<{ sentence?: string }>
  onStartTranslate: (targetLanguage: string, forceRetranslate: boolean) => void
  isTranslating?: boolean
}

const LANGUAGE_OPTIONS = [
  { code: 'zh', name: 'Chinese (中文)' },
  { code: 'en', name: 'English (英文)' },
]

export default function TranslateDialog({
  open,
  onOpenChange,
  transcriptId,
  segments,
  onStartTranslate,
  isTranslating = false,
}: Readonly<TranslateDialogProps>) {
  const [step, setStep] = useState<'detecting' | 'selecting'>('detecting')
  const [detection, setDetection] = useState<LanguageDetectionResult | null>(null)
  const [targetLanguage, setTargetLanguage] = useState('zh')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [forceRetranslate, setForceRetranslate] = useState(false)

  useEffect(() => {
    if (!open || !segments || segments.length === 0) return

    setLoading(true)
    setError(null)
    try {
      const result = detectLanguage(segments)
      setDetection(result)
      
      if (result.primary_language === 'zh') {
        setTargetLanguage('en')
      } else if (result.primary_language === 'en') {
        setTargetLanguage('zh')
      } else {
        setTargetLanguage('zh')
      }
      
      setStep('selecting')
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }, [open, segments])

  const handleTranslate = () => {
    if (!transcriptId) return
    onStartTranslate(targetLanguage, forceRetranslate)
    onOpenChange(false)
    setStep('detecting')
  }

  const handleClose = () => {
    onOpenChange(false)
    setStep('detecting')
    setError(null)
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>翻译文稿</DialogTitle>
          <DialogDescription>
            {step === 'detecting' && '检测内容语言中...'}
            {step === 'selecting' && '选择目标语言'}
          </DialogDescription>
        </DialogHeader>

        {step === 'detecting' && (
          <div className="flex justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          </div>
        )}

        {step === 'selecting' && detection && (
          <div className="space-y-4 py-4">
            <div className="rounded-lg bg-blue-50 p-4">
              <p className="text-sm font-medium text-blue-900">{detection.suggestion}</p>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">选择目标语言</label>
              <Select value={targetLanguage} onValueChange={setTargetLanguage}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {LANGUAGE_OPTIONS.map((lang) => (
                    <SelectItem key={lang.code} value={lang.code}>
                      {lang.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="flex items-center space-x-2 rounded-lg bg-orange-50 p-4">
              <input
                type="checkbox"
                id="force-retranslate"
                checked={forceRetranslate}
                onChange={(e) => setForceRetranslate(e.target.checked)}
                className="h-4 w-4 rounded border-slate-300 text-orange-600"
              />
              <label htmlFor="force-retranslate" className="text-sm font-medium text-orange-900 cursor-pointer">
                强制重新翻译
              </label>
            </div>
            {forceRetranslate && (
              <p className="text-xs text-orange-700">
                即使已有翻译内容，也会重新翻译所有分句。
              </p>
            )}
            
            {error && (
              <div className="rounded-lg bg-red-50 p-4">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}
          </div>
        )}

        <DialogFooter className="flex gap-2">
          {step === 'selecting' && (
            <>
              <Button variant="outline" onClick={handleClose} disabled={loading || isTranslating}>
                取消
              </Button>
              <Button onClick={handleTranslate} disabled={loading || isTranslating}>
                {loading || isTranslating ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                {isTranslating ? '翻译中...' : '开始翻译'}
              </Button>
            </>
          )}
          {step === 'detecting' && (
            <Button disabled className="w-full">
              检测中...
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
