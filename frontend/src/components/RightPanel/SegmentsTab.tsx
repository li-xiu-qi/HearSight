import { forwardRef } from "react"
import { ScrollArea } from "@/components/ui/scroll-area"
import { PlayCircle } from "lucide-react"
import type { Segment } from "../../types"
import { formatTime } from "../../utils"

interface SegmentsTabProps {
  readonly segments: Segment[]
  readonly activeSegIndex: number | null
  readonly onSegmentClick: (segment: Segment) => void
  readonly displayLanguage?: string
}

const SegmentsTab = forwardRef<HTMLDivElement, SegmentsTabProps>(
  ({ segments, activeSegIndex, onSegmentClick, displayLanguage = 'original' }, ref) => {
  const getDisplayText = (segment: Segment) => {
    if (displayLanguage === 'original') {
      return segment.sentence || "(空)"
    }
    if (segment.translation?.[displayLanguage]) {
      return segment.translation[displayLanguage]
    }
    return segment.sentence || "(空)"
  }

  return (
      <ScrollArea ref={ref} className="h-full">
        {segments.length === 0 ? (
          <div className="flex items-center justify-center h-40 text-sm text-slate-500">
            暂无分句
          </div>
        ) : (
          <div className="p-2 pb-4 space-y-1 min-h-full">
            {segments.map((seg) => {
              const isActive = activeSegIndex === seg.index
              return (
                <button
                  key={seg.index}
                  data-seg-index={seg.index}
                  aria-label={`跳转到 ${formatTime(seg.start_time)}`}
                  onClick={() => onSegmentClick(seg)}
                  className={`
                    w-full text-left p-3 rounded-md cursor-pointer transition-colors
                    ${isActive ? "bg-blue-50 border border-blue-200" : "hover:bg-slate-50"}
                  `}
                  type="button"
                >
                  <div className="flex items-start gap-2">
                    <PlayCircle className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 text-xs text-slate-500 mb-1">
                        <span>
                          {formatTime(seg.start_time)} ~ {formatTime(seg.end_time)}
                        </span>
                        {seg.spk_id && (
                          <span className="px-1.5 py-0.5 bg-slate-200 rounded text-xs">
                            SPK {seg.spk_id}
                          </span>
                        )}
                      </div>
                      <div className="text-sm text-slate-900">{getDisplayText(seg)}</div>
                    </div>
                  </div>
                </button>
              )
            })}
          </div>
        )}
      </ScrollArea>
    )
  }
)

SegmentsTab.displayName = "SegmentsTab"

export default SegmentsTab
