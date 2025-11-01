import { ScrollArea } from "@/components/ui/scroll-area"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Loader2, Copy, PlayCircle } from "lucide-react"
import { toast } from "sonner"
import { useState, useEffect } from "react"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import {
  Dialog,
  DialogContent,
  DialogTrigger,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog"
import type { Summary } from "../../types"
import { formatTime } from "../../utils"
import { fetchThumbnail } from "../../services/api"

interface SummariesTabProps {
  readonly summaries: Summary[]
  readonly loading: boolean
  readonly error: string | null
  readonly onGenerate: () => void
  readonly onSeekTo: (timeMs: number) => void
  readonly transcriptId?: number
}

export default function SummariesTab({
  summaries,
  loading,
  error,
  onGenerate,
  onSeekTo,
  transcriptId,
}: Readonly<SummariesTabProps>) {
  const [imageModeEnabled, setImageModeEnabled] = useState(false)
  const [frameCache, setFrameCache] = useState<Record<string, string>>({})

  // 加载所有总结的时间戳截图
  useEffect(() => {
    if (!imageModeEnabled || !transcriptId) return

    const loadAllThumbnails = async () => {
      const timeStamps: { startTime: number; endTime: number; cacheKey: string }[] = []

      // 收集所有总结中的时间戳
      for (const summary of summaries) {
        if (summary.start_time != null && summary.end_time != null) {
          const startTimeMs = summary.start_time
          const endTimeMs = summary.end_time
          // 使用秒作为缓存键，避免毫秒精度差异导致的重复缓存
          const startTimeSec = Math.floor(startTimeMs / 1000)
          const endTimeSec = Math.floor(endTimeMs / 1000)
          const cacheKey = `${startTimeSec}-${endTimeSec}`
          if (!frameCache[cacheKey]) {
            timeStamps.push({ startTime: startTimeMs, endTime: endTimeMs, cacheKey })
          }
        }
      }

      // 加载未缓存的截图
      for (const { startTime, endTime, cacheKey } of timeStamps) {
        try {
          const url = await fetchThumbnail(transcriptId, startTime, endTime, 320)
          if (url) {
            setFrameCache(prev => ({ ...prev, [cacheKey]: url }))
          }
        } catch (error) {
          console.error('Failed to fetch thumbnail:', error)
        }
      }
    }

    loadAllThumbnails()
  }, [imageModeEnabled, summaries, transcriptId, frameCache])
  const handleCopySummaries = async () => {
    const text = summaries
      .map((sum) => `${sum.topic}\n${sum.summary}`)
      .join("\n\n")
    try {
      await navigator.clipboard.writeText(text)
      toast.success("总结已复制到剪贴板")
    } catch (err) {
      console.error("复制失败:", err)
      toast.error("复制失败")
    }
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-3 border-b flex-shrink-0">
        <div className="flex gap-2 justify-between items-center">
          <div className="flex gap-2">
            <Button onClick={onGenerate} disabled={loading} size="sm">
              {loading && <Loader2 className="mr-1 h-3 w-3 animate-spin" />}
              生成总结
            </Button>
            <Button
              onClick={handleCopySummaries}
              disabled={summaries.length === 0}
              variant="outline"
              size="sm"
            >
              <Copy className="mr-1 h-3 w-3" />
              复制总结
            </Button>
          </div>
          <div className="flex items-center gap-2">
            <Switch
              id="image-mode-summaries"
              checked={imageModeEnabled}
              onCheckedChange={setImageModeEnabled}
            />
            <Label htmlFor="image-mode-summaries" className="text-sm cursor-pointer">
              图文展示
            </Label>
          </div>
        </div>
      </div>
      <ScrollArea className="flex-1 min-h-0">
        {error && (
          <div className="m-3 p-3 bg-red-50 text-red-700 text-sm rounded">
            {error}
          </div>
        )}
        {loading && (
          <div className="flex items-center justify-center h-40">
            <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
          </div>
        )}
        {!loading && summaries.length > 0 && (
          <div className="p-3 space-y-3">
            {summaries.map((sum) => {
              if (sum.start_time === null || sum.start_time === undefined || 
                  sum.end_time === null || sum.end_time === undefined) {
                return (
                  <Card key={`${sum.start_time}-${sum.end_time}`} className="p-3">
                    <h4 className="font-semibold text-sm mb-2">{sum.topic}</h4>
                    <p className="text-sm text-slate-700 mb-2">{sum.summary}</p>
                  </Card>
                )
              }

              const startTimeSec = Math.floor(sum.start_time / 1000)
              const endTimeSec = Math.floor(sum.end_time / 1000)
              const cacheKey = `${startTimeSec}-${endTimeSec}`
              const cachedImage = frameCache[cacheKey]

              return (
                <Card key={`${sum.start_time}-${sum.end_time}`} className="p-3">
                  <h4 className="font-semibold text-sm mb-2">{sum.topic}</h4>
                  <p className="text-sm text-slate-700 mb-2">{sum.summary}</p>
                  <div className="flex items-start gap-2">
                    {imageModeEnabled && (
                      <div className="flex-shrink-0">
                        {cachedImage ? (
                          <Dialog>
                            <DialogTrigger asChild>
                              <img
                                src={cachedImage}
                                alt={`总结截图 ${formatTime(sum.start_time)}`}
                                className="w-20 h-12 object-cover rounded border cursor-pointer hover:opacity-80 transition-opacity"
                              />
                            </DialogTrigger>
                            <DialogContent className="max-w-4xl">
                              <DialogTitle className="sr-only">总结截图预览</DialogTitle>
                              <DialogDescription className="sr-only">
                                总结截图 {formatTime(sum.start_time)} 的预览
                              </DialogDescription>
                              <img
                                src={cachedImage}
                                alt={`总结截图 ${formatTime(sum.start_time)}`}
                                className="w-full h-auto max-h-[80vh] object-contain"
                              />
                            </DialogContent>
                          </Dialog>
                        ) : (
                          <div className="w-20 h-12 bg-gray-200 rounded flex items-center justify-center">
                            <Loader2 className="h-3 w-3 animate-spin" />
                          </div>
                        )}
                      </div>
                    )}
                    <button
                      type="button"
                      onClick={() => onSeekTo(sum.start_time!)}
                      className="inline-flex items-center gap-1 text-xs text-blue-600 hover:underline"
                    >
                      <PlayCircle className="h-3 w-3" />
                      {formatTime(sum.start_time)} ~ {formatTime(sum.end_time)}
                    </button>
                  </div>
                </Card>
              )
            })}
          </div>
        )}
      </ScrollArea>
    </div>
  )
}
