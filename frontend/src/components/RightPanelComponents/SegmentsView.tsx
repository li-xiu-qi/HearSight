import React, { forwardRef, type ForwardedRef } from 'react'
import { List, Empty } from 'antd'
import { PlayCircleOutlined } from '@ant-design/icons'
import type { Segment } from '../../types'
import { formatTime } from '../../utils'
import './styles/SegmentsView.css'

interface SegmentsViewProps {
  segments: Segment[]
  activeSegIndex: number | null
  onSegmentClick: (segment: Segment) => void
}

const SegmentsView = forwardRef<HTMLDivElement, SegmentsViewProps>(
  ({ segments, activeSegIndex, onSegmentClick }, ref: ForwardedRef<HTMLDivElement>) => {
    return (
      <div className="segments-scroll" ref={ref}>
        {segments.length === 0 ? (
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无分句" />
        ) : (
          <List
            split={false}
            dataSource={segments}
            renderItem={(segment: Segment) => {
              const isActive = activeSegIndex === segment.index
              return (
                <List.Item 
                  className="segment-item" 
                  style={{ paddingLeft: 0, paddingRight: 0 }} 
                  data-seg-index={segment.index}
                >
                  <div
                    role="button"
                    tabIndex={0}
                    className={`segment-btn is-div ${isActive ? 'active' : ''}`}
                    onClick={() => onSegmentClick(segment)}
                    title={`跳转到 ${formatTime(segment.start_time)} (${Math.floor(Number(segment.start_time) || 0)} ms)`}
                  >
                    <span className="segment-icon">
                      <PlayCircleOutlined />
                    </span>
                    <div className="seg-card">
                      <div className="seg-head">
                        <span className="seg-time">
                          {formatTime(segment.start_time)}
                          <span className="segment-time-sep">~</span>
                          {formatTime(segment.end_time)}
                        </span>
                        {segment.spk_id && (
                          <span className="seg-spk">SPK {segment.spk_id}</span>
                        )}
                      </div>
                      <div className="seg-body">{segment.sentence || '(空)'}</div>
                    </div>
                  </div>
                </List.Item>
              )
            }}
          />
        )}
      </div>
    )
  }
)

SegmentsView.displayName = 'SegmentsView'

export default SegmentsView