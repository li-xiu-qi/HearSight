import { forwardRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Loader2, Play, Music } from 'lucide-react'

interface VideoPlayerProps {
  videoSrc: string | null
  mediaType?: string
  loading: boolean
}

const VideoPlayer = forwardRef<HTMLVideoElement, VideoPlayerProps>(({ videoSrc, mediaType, loading }, ref) => {
  const isAudio = mediaType === 'audio' || (videoSrc && /\.(m4a|mp3|wav|flac|aac|ogg|wma)$/i.test(videoSrc))
  const playerTitle = isAudio ? '音频播放器' : '视频播放器'
  
  return (
    <Card className="h-full flex flex-col gap-0 py-0">
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
      <CardContent className="flex-1 flex items-center justify-center p-0 relative">
        {videoSrc ? (
          <div className="w-full h-full flex items-center justify-center relative overflow-hidden bg-black">
            <video
              ref={ref}
              src={videoSrc}
              controls
              className="w-full max-w-full max-h-[80vh] object-contain relative z-10"
              style={{ objectFit: isAudio ? 'cover' : 'contain' }}
              preload="metadata"
              poster={isAudio ? "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='800' height='600'%3E%3Cdefs%3E%3ClinearGradient id='grad1' x1='0%25' y1='0%25' x2='100%25' y2='100%25'%3E%3Cstop offset='0%25' style='stop-color:%231e293b;stop-opacity:1' /%3E%3Cstop offset='100%25' style='stop-color:%231e3a5f;stop-opacity:1' /%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='800' height='600' fill='url(%23grad1)'/%3E%3Ccircle cx='400' cy='260' r='60' fill='url(%23musicGrad)'/%3E%3ClinearGradient id='musicGrad' x1='0%25' y1='0%25' x2='100%25' y2='100%25'%3E%3Cstop offset='0%25' style='stop-color:%23a855f7;stop-opacity:1' /%3E%3Cstop offset='100%25' style='stop-color:%23ec4899;stop-opacity:1' /%3E%3C/linearGradient%3E%3Cpath d='M 380 240 L 380 270 C 380 275 385 280 390 280 L 400 280 C 405 280 410 275 410 270 L 410 235 L 420 235 L 420 245 C 420 250 415 255 410 255 L 410 270 C 410 280 415 285 425 285 C 435 285 440 280 440 270 L 440 230 L 410 230 L 410 240 L 380 240 Z' fill='white'/%3E%3C/svg%3E" : undefined}
              aria-label={isAudio ? '音频播放器' : '视频播放器'}
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
          <div className="absolute inset-0 bg-black/50 flex items-center justify-center text-white z-20">
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
