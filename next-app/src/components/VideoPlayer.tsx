'use client'

import { forwardRef } from 'react'
import { Loader2, Music, Play } from 'lucide-react'

interface VideoPlayerProps {
  videoSrc: string | null
  mediaType?: string
  loading: boolean
}

/**
 * 中栏播放器。去掉了原 Card 头部（「可播放」徽标是无信息量状态）
 * 和音频态的内联 SVG 渐变海报（紫色渐变音符属装饰性噪音，与设计系统冲突）；
 * 音频态用产品色系的静符图标占位。loading 遮罩从黑底白字改为纸面半透明。
 */
const VideoPlayer = forwardRef<HTMLVideoElement, VideoPlayerProps>(({ videoSrc, mediaType, loading }, ref) => {
  const isAudio = mediaType === 'audio' || (videoSrc && /\.(m4a|mp3|wav|flac|aac|ogg|wma)$/i.test(videoSrc))
  const playerTitle = isAudio ? '音频播放器' : '视频播放器'

  return (
    <div className="h-full flex flex-col">
      {videoSrc ? (
        <div className="flex-1 min-h-0 flex items-center justify-center relative overflow-hidden bg-black">
          {isAudio && (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 text-primary-foreground/70">
              <Music className="h-12 w-12" />
              <span className="text-sm">{playerTitle}</span>
            </div>
          )}
          <video
            ref={ref}
            src={videoSrc}
            controls
            className="w-full h-full object-contain relative z-10"
            style={{ objectFit: isAudio ? 'cover' : 'contain' }}
            preload="metadata"
            aria-label={playerTitle}
          />
          {loading && (
            <div className="absolute inset-0 bg-foreground/40 flex items-center justify-center z-20">
              <div className="flex items-center gap-2 bg-card rounded-md px-4 py-2.5 shadow-lg">
                <Loader2 className="h-4 w-4 animate-spin text-primary" />
                <span className="text-sm text-foreground">处理中，请稍候…</span>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
          <div className="w-14 h-14 rounded-full bg-muted flex items-center justify-center mb-4">
            <Play className="h-6 w-6 text-muted-foreground" />
          </div>
          <div className="text-sm font-medium text-foreground mb-1">还没有加载媒体</div>
          <div className="text-xs text-muted-foreground leading-5 max-w-xs">
            从左侧素材库选择一条记录，或在顶栏粘贴链接、上传文件开始新的分析
          </div>
          {loading && (
            <div className="flex items-center gap-2 mt-6 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin text-primary" />
              处理中，请稍候…
            </div>
          )}
        </div>
      )}
    </div>
  )
})

VideoPlayer.displayName = 'VideoPlayer'

export default VideoPlayer
