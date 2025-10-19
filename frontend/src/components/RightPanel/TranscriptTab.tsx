import { forwardRef } from "react"
import type { Segment } from "../../types"

interface TranscriptTabProps {
  readonly segments: Segment[]
  readonly activeSegIndex: number | null
  readonly onSegmentClick: (segment: Segment) => void
}

const TranscriptTab = forwardRef<HTMLDivElement, TranscriptTabProps>(
  ({ segments, activeSegIndex, onSegmentClick }, ref) => {
    return (
      <div ref={ref} className="h-full overflow-y-auto">
        {segments.length === 0 ? (
          <div className="flex items-center justify-center h-40 text-sm text-slate-500">
            暂无内容
          </div>
        ) : (
          <div className="text-base leading-7 text-slate-800 text-left flex flex-row flex-wrap">
            {segments.map((seg) => {
              const isActive = activeSegIndex === seg.index
              const displayText = seg.sentence || "(空)"

              return (
                <button
                  key={seg.index}
                  data-seg-index={seg.index}
                  type="button"
                  onClick={() => onSegmentClick(seg)}
                  className={`px-0.5 py-0.5 mr-1 rounded border-none bg-transparent cursor-pointer transition-colors duration-200 flex-shrink-0 ${
                    isActive ? "bg-blue-100 text-slate-900 shadow-inner" : "hover:bg-blue-50"
                  }`}
                >
                  {displayText}
                </button>
              )
            })}
          </div>
        )}
      </div>
    )
  }
)

TranscriptTab.displayName = "TranscriptTab"

export default TranscriptTab
