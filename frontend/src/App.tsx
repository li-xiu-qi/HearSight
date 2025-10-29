import { useEffect, useRef, useState } from "react"
import { useNavigate } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Loader2, Home, Menu, X } from "lucide-react"
import { useUrlHandler, useDataLoader, useVideoSync } from "./hooks"
import { getPendingUrl } from "./HomePage/HomePage"
import LeftPanel from "./components/LeftPanel"
import VideoPlayer from "./components/VideoPlayer"
import RightPanel from "./components/RightPanel/RightPanel"

function App() {
  const navigate = useNavigate()
  const [inputUrl, setInputUrl] = useState("")
  const [autoScroll, setAutoScroll] = useState(true)
  const [leftPanelVisible, setLeftPanelVisible] = useState(globalThis.innerWidth > 768)
  const [rightPanelVisible, setRightPanelVisible] = useState(globalThis.innerWidth > 768)
  
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const segScrollRef = useRef<HTMLDivElement | null>(null)
  const seekHandlerRef = useRef<((event: Event) => void) | null>(null)

  const {
    url,
    setUrl,
    urlError,
    submitting,
    handleUrlSubmit,
    handleUrlClear
  } = useUrlHandler()

  const {
    segments,
    loading,
    transcripts,
    jobs,
    videoSrc,
    activeTranscriptId,
    loadTranscriptDetail,
    loadTranscripts,
  } = useDataLoader()

  const [activeSegIndex, setActiveSegIndex] = useState<number | null>(null)
  
  useVideoSync({
    segments,
    autoScroll,
    segScrollRef,
    setActiveSegIndex,
    videoRef
  })
  
  const handleSeekTo = (timeMs: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = timeMs / 1000
    }
  }

  useEffect(() => {
    seekHandlerRef.current = (event: Event) => {
      const timeMs = (event as CustomEvent).detail
      if (typeof timeMs === "number") {
        handleSeekTo(timeMs)
      }
    }
  }, [])

  useEffect(() => {
    const handler = (event: Event) => {
      seekHandlerRef.current?.(event)
    }

    globalThis.addEventListener("seekToTime", handler)
    return () => {
      globalThis.removeEventListener("seekToTime", handler)
    }
  }, [])

  useEffect(() => {
    const pending = getPendingUrl()
    if (pending) {
      setUrl(pending)
      setInputUrl(pending)
      handleUrlSubmit(pending).catch(() => {})
    }
  }, [])

  useEffect(() => {
    const handleResize = () => {
      const isDesktop = globalThis.innerWidth > 768
      setLeftPanelVisible(isDesktop)
      setRightPanelVisible(isDesktop)
    }
    globalThis.addEventListener('resize', handleResize)
    return () => globalThis.removeEventListener('resize', handleResize)
  }, [])

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (inputUrl.trim()) {
      setUrl(inputUrl)
      try {
        await handleUrlSubmit(inputUrl)
      } catch (error) {
        console.error(error)
      }
    }
  }

  return (
    <div className="h-screen flex flex-col bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-4 sticky top-0 z-50 shadow-sm">
        <div className="h-14 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setLeftPanelVisible(!leftPanelVisible)}
              className="lg:hidden"
            >
              {leftPanelVisible ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
            </Button>
            <h3 className="text-lg font-semibold text-slate-900">HearSight</h3>
          </div>
          
          <form onSubmit={onSubmit} className="flex-1 max-w-2xl flex items-center gap-2">
            <Input
              type="text"
              placeholder="输入 bilibili.com 视频链接"
              value={inputUrl}
              onChange={(e) => setInputUrl(e.target.value)}
              className="flex-1"
              disabled={submitting}
            />
            <Button type="submit" disabled={submitting} size="sm">
              {submitting ? (
                <><Loader2 className="mr-1 h-3 w-3 animate-spin" />提交</>
              ) : "提交"}
            </Button>
            {url && (
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  handleUrlClear()
                  setInputUrl("")
                }}
                disabled={submitting}
                size="sm"
              >
                清除
              </Button>
            )}
          </form>

          <div className="flex items-center gap-3">
            <div className="hidden md:flex items-center gap-2">
              <Switch
                id="auto-scroll"
                checked={autoScroll}
                onCheckedChange={setAutoScroll}
              />
              <Label htmlFor="auto-scroll" className="text-sm cursor-pointer">
                自动滚动
              </Label>
            </div>
            <Button variant="ghost" onClick={() => navigate("/")} size="sm" className="gap-1.5">
              <Home className="h-4 w-4" />
              <span className="hidden sm:inline">首页</span>
            </Button>
          </div>
        </div>
        {urlError && (
          <div className="pb-2">
            <p className="text-xs text-red-600">{urlError}</p>
          </div>
        )}
      </header>

      {/* Main Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel */}
        {leftPanelVisible && (
          <div className="w-80 border-r border-slate-200 bg-white overflow-hidden">
            <LeftPanel
              transcripts={transcripts}
              jobs={jobs}
              activeTranscriptId={activeTranscriptId}
              onLoadTranscript={loadTranscriptDetail}
              onTranscriptsUpdate={loadTranscripts}
            />
          </div>
        )}

        {/* Center: Video Player */}
        <div className="flex-1 p-4 overflow-auto">
          <VideoPlayer
            ref={videoRef}
            videoSrc={videoSrc}
            loading={loading}
          />
        </div>

        {/* Right Panel - Placeholder */}
        {rightPanelVisible && (
          <div className="w-96 border-l border-slate-200 bg-white overflow-hidden">
            <RightPanel
              ref={segScrollRef}
              segments={segments}
              activeSegIndex={activeSegIndex}
              autoScroll={autoScroll}
              onSeekTo={handleSeekTo}
              onActiveSegmentChange={setActiveSegIndex}
              transcriptId={activeTranscriptId ?? undefined}
            />
          </div>
        )}
      </div>
    </div>
  )
}

export default App
