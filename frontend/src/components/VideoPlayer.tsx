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
          />
        </div>
      ) : (
        <div className="video-placeholder">
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无视频" />
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