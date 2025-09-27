import React, { forwardRef, type ForwardedRef } from 'react'
import { Empty } from 'antd'
import type { Segment } from '../../types'
import { formatTime } from '../../utils'
import './styles/TranscriptView.css'

interface TranscriptViewProps {
  segments: Segment[]
  activeSegIndex: number | null
  onSegmentClick: (segment: Segment) => void
}

const TranscriptView = forwardRef<HTMLDivElement, TranscriptViewProps>(
  ({ segments, activeSegIndex, onSegmentClick }, ref: ForwardedRef<HTMLDivElement>) => {
    return (
      <div className="transcript-scroll" ref={ref}>
        {segments.length === 0 ? (
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无内容" />
        ) : (
          <div className="transcript-body">
            {segments.map(seg => {
              const isActive = activeSegIndex === seg.index
              return (
                <span
                  key={seg.index}
                  data-seg-index={seg.index}
                  onClick={() => onSegmentClick(seg)}
                  className={`transcript-seg ${isActive ? 'active' : ''}`}
                >
                  <span className="transcript-text">{seg.sentence || '(空)'}</span>
                </span>
              )
            })}
          </div>
        )}
      </div>
    )
  }
)

TranscriptView.displayName = 'TranscriptView'

export default TranscriptView