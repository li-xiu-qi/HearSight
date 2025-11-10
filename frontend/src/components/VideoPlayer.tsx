import { forwardRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Loader2, Play } from 'lucide-react'

interface VideoPlayerProps {
  videoSrc: string | null
  mediaType?: string
  loading: boolean
}

const VideoPlayer = forwardRef<HTMLVideoElement, VideoPlayerProps>(({ videoSrc, mediaType, loading }, ref) => {
  const isAudio = mediaType === 'audio' || (videoSrc && /\.(m4a|mp3|wav|flac|aac)$/i.test(videoSrc))
  const playerTitle = isAudio ? '音频播放器' : '视频播放器'
  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center justify-between">
          <span>{playerTitle}</span>
          {videoSrc && (
            <span className="text-xs font-normal text-green-600 bg-green-50 px-2 py-1 rounded">
              可播放
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 flex items-center justify-center p-0">
        {videoSrc ? (
          <div className="w-full h-full flex items-center justify-center bg-black">
            <video
              ref={ref}
              src={videoSrc}
              controls
              className="w-full h-full max-h-[600px] object-contain"
              preload="metadata"
              aria-label="视频播放器"
            />
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center p-8 text-center">
            <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mb-4">
              <Play className="h-8 w-8 text-slate-400" />
            </div>
            <div className="text-base font-medium text-slate-700 mb-2">暂无视频</div>
            <div className="text-sm text-slate-500">
              选择左侧的处理记录，或在上方输入新的视频URL来开始分析
            </div>
          </div>
        )}
        {loading && (
          <div className="absolute inset-0 bg-black/50 flex items-center justify-center text-white">
            <div className="flex items-center gap-2">
              <Loader2 className="h-5 w-5 animate-spin" />
              <span>处理中，请稍候...</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
})

VideoPlayer.displayName = 'VideoPlayer'

export default VideoPlayer
