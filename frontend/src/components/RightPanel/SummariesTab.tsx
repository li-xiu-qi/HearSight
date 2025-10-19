import { ScrollArea } from "@/components/ui/scroll-area"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Loader2, Copy } from "lucide-react"
import { toast } from "sonner"
import type { Summary } from "../../types"
import { formatTime } from "../../utils"

interface SummariesTabProps {
  readonly summaries: Summary[]
  readonly loading: boolean
  readonly error: string | null
  readonly onGenerate: () => void
  readonly onSeekTo: (timeMs: number) => void
}

export default function SummariesTab({
  summaries,
  loading,
  error,
  onGenerate,
  onSeekTo,
}: Readonly<SummariesTabProps>) {
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
            {summaries.map((sum) => (
              <Card key={`${sum.start_time}-${sum.end_time}`} className="p-3">
                <h4 className="font-semibold text-sm mb-2">{sum.topic}</h4>
                <p className="text-sm text-slate-700 mb-2">{sum.summary}</p>
                {sum.start_time != null && sum.end_time != null && (
                  <button
                    onClick={() => onSeekTo(sum.start_time!)}
                    className="text-xs text-blue-600 hover:underline"
                  >
                    {formatTime(sum.start_time)} ~ {formatTime(sum.end_time)}
                  </button>
                )}
              </Card>
            ))}
          </div>
        )}
      </ScrollArea>
    </div>
  )
}
