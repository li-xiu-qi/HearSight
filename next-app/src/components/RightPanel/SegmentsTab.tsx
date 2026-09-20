'use client'

import { forwardRef } from "react"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Play } from "lucide-react"
import type { Segment } from "../../types"
import { formatTime } from "../../utils"

interface SegmentsTabProps {
  readonly segments: Segment[]
  readonly activeSegIndex: number | null
  readonly onSegmentClick: (segment: Segment) => void
  readonly displayLanguage?: string
}

/**
 * 转写稿句子卡片——全页签名元素。
 * 左侧等宽时间轨（tabular-nums 对齐成轨），播放键 hover 才出现；
 * 当前句用 2px 主色左边线标识，不用整卡染色，保持阅读面安静。
 */
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
          <div className="flex items-center justify-center h-40 text-sm text-muted-foreground">
            暂无分句
          </div>
        ) : (
          <div className="py-2 min-h-full">
            {segments.map((seg) => {
              const isActive = activeSegIndex === seg.index
              return (
                <button
                  key={seg.index}
                  data-seg-index={seg.index}
                  aria-label={`跳转到 ${formatTime(seg.start_time)}`}
                  onClick={() => onSegmentClick(seg)}
                  type="button"
                  className={`
                    group w-full text-left px-4 py-2.5 cursor-pointer
                    border-l-2 transition-colors
                    ${isActive
                      ? "border-primary bg-primary/[0.06]"
                      : "border-transparent hover:bg-muted"}
                  `}
                >
                  <div className="flex items-baseline gap-3">
                    {/* 时间轨：等宽数字，hover/当前态显播放键 */}
                    <span className="flex items-center gap-1.5 w-[92px] flex-shrink-0 font-mono text-xs tabular-nums text-muted-foreground">
                      <Play
                        className={`
                          h-3 w-3 flex-shrink-0 transition-opacity text-primary
                          ${isActive ? "opacity-100" : "opacity-0 group-hover:opacity-100"}
                        `}
                      />
                      {formatTime(seg.start_time)}
                    </span>
                    <span className="flex-1 min-w-0">
                      <span className="block text-[15px] leading-7 text-foreground">
                        {getDisplayText(seg)}
                      </span>
                      {seg.spk_id && (
                        <span className="mt-1 inline-block rounded bg-muted px-1.5 py-0.5 font-mono text-[11px] text-muted-foreground">
                          SPK {seg.spk_id}
                        </span>
                      )}
                    </span>
                  </div>
                </button>
              )
            })}
          </div>
        )}
      </ScrollArea>
  )
})

SegmentsTab.displayName = "SegmentsTab"

export default SegmentsTab
