import { forwardRef } from "react"
import { ScrollArea } from "@/components/ui/scroll-area"
import type { Segment } from "../../types"

interface TranscriptTabProps {
  readonly segments: Segment[]
  readonly activeSegIndex: number | null
  readonly onSegmentClick: (segment: Segment) => void
  readonly displayLanguage?: string
}

const TranscriptTab = forwardRef<HTMLDivElement, TranscriptTabProps>(
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
            暂无内容
          </div>
        ) : (
          <div className="p-4 pb-8 text-base leading-7 text-slate-800 text-left min-h-full">
            {segments.map((seg) => {
              const isActive = activeSegIndex === seg.index
              const displayText = getDisplayText(seg)

              return (

                // 这里使用span元素而不是button，是为了让句子能够连续排列形成文本流，
                // 只有在超出容器宽度时才换行，而不是每个句子后都换行。
                // 虽然违反了可访问性规则，但点击功能正常，且视觉效果更符合转录文本的展示需求。
                <span
                  key={seg.index}
                  data-seg-index={seg.index}
                  onClick={() => onSegmentClick(seg)}
                  className={`px-0.5 py-0.5 mr-1 rounded cursor-pointer transition-colors duration-200 break-words ${
                    isActive ? "bg-blue-100 text-slate-900 shadow-inner" : "hover:bg-blue-50"
                  }`}
                >
                  {displayText}
                </span>

              )
            })}
          </div>
        )}
      </ScrollArea>
    )
  }
)

TranscriptTab.displayName = "TranscriptTab"

export default TranscriptTab
