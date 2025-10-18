import React, { forwardRef } from 'react'
import { Card, Tag, Empty } from 'antd'

interface VideoPlayerProps {
  videoSrc: string | null
  loading: boolean
}

const VideoPlayer = forwardRef<HTMLVideoElement, VideoPlayerProps>(({ videoSrc, loading }, ref) => {
  return (
    <Card 
      title="视频播放器" 
      extra={videoSrc && <Tag color="green">可播放</Tag>}
      className="fullscreen-video-card"
    >
      {videoSrc ? (
        <div className="video-container">
          <video
            ref={ref}
            src={videoSrc}
            controls
            className="fullscreen-video"
            preload="metadata"
            aria-label="视频播放器"
            role="application"
          />
        </div>
      ) : (
        <div className="video-placeholder empty-state">
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} />
          <div className="empty-title">暂无视频</div>
          <div className="empty-description">
            选择左侧的处理记录，或在上方输入新的视频URL来开始分析。
          </div>
        </div>
      )}
      {loading && (
        <div className="loading-overlay">
          处理中，请稍候…（首次识别会较慢）
        </div>
      )}
    </Card>
  )
})

VideoPlayer.displayName = 'VideoPlayer'

export default VideoPlayer