import { useEffect, useRef, useState } from "react"
import type { FormEvent } from "react"
import { useNavigate } from "react-router-dom"
import LeftPanel from "@/components/LeftPanel"
import VideoPlayer from "@/components/VideoPlayer"
import RightPanel from "@/components/RightPanel"
import { useUrlHandler, useDataLoader, useVideoSync } from "@/hooks"
import { getPendingUrl } from "@/utils/pendingUrl"
import WorkspaceLayout from "./components/WorkspaceLayout"
import HeaderBar from "./components/HeaderBar"
import UploadDialog from "./components/UploadDialog"
import { message } from "@/utils/message"

function AppPage() {
  const navigate = useNavigate()
  const [inputUrl, setInputUrl] = useState("")
  const [autoScroll, setAutoScroll] = useState(true)
  const [leftPanelVisible, setLeftPanelVisible] = useState(globalThis.innerWidth > 768)
  const [rightPanelVisible, setRightPanelVisible] = useState(globalThis.innerWidth > 768)
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false)

  const videoRef = useRef<HTMLVideoElement | null>(null)
  const segScrollRef = useRef<HTMLDivElement | null>(null)
  const seekHandlerRef = useRef<((event: Event) => void) | null>(null)

  const {
    setUrl,
    urlError,
    submitting,
    handleUrlSubmit,
    handleUrlClear,
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
    setVideoSrc,
  } = useDataLoader()

  const [activeSegIndex, setActiveSegIndex] = useState<number | null>(null)

  useVideoSync({
    segments,
    autoScroll,
    segScrollRef,
    setActiveSegIndex,
    videoRef,
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
  }, [handleUrlSubmit, setUrl])

  useEffect(() => {
    const handleResize = () => {
      const isDesktop = globalThis.innerWidth > 768
      setLeftPanelVisible(isDesktop)
      setRightPanelVisible(isDesktop)
    }
    globalThis.addEventListener("resize", handleResize)
    return () => {
      globalThis.removeEventListener("resize", handleResize)
    }
  }, [])

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!inputUrl.trim()) {
      return
    }
    setUrl(inputUrl)
    try {
      await handleUrlSubmit(inputUrl)
    } catch (error) {
      console.error(error)
    }
  }

  const handleUploadSuccess = (data: { static_url: string; is_audio: boolean; placeholder_url?: string }) => {
    message.success("文件上传成功")
    const videoUrl = data.is_audio && data.placeholder_url ? data.placeholder_url : data.static_url
    setVideoSrc(videoUrl)
    setUploadDialogOpen(false)
  }

  const handleUploadError = (error: string) => {
    message.error(error)
  }

  return (
    <div className="h-screen flex flex-col bg-slate-50">
      <HeaderBar
        inputUrl={inputUrl}
        submitting={submitting}
        autoScroll={autoScroll}
        leftPanelVisible={leftPanelVisible}
        urlError={urlError}
        onSubmit={onSubmit}
        onInputUrlChange={setInputUrl}
        onClear={() => {
          handleUrlClear()
          setInputUrl("")
        }}
        onAutoScrollChange={setAutoScroll}
        onToggleLeftPanel={() => setLeftPanelVisible((value) => !value)}
        onNavigateHome={() => navigate("/")}
        onOpenUpload={() => setUploadDialogOpen(true)}
      />
      <WorkspaceLayout
        leftPanelVisible={leftPanelVisible}
        rightPanelVisible={rightPanelVisible}
        leftPanel={
          <LeftPanel
            transcripts={transcripts}
            jobs={jobs}
            activeTranscriptId={activeTranscriptId}
            onLoadTranscript={loadTranscriptDetail}
            onTranscriptsUpdate={loadTranscripts}
          />
        }
        centerPanel={
          <VideoPlayer
            ref={videoRef}
            videoSrc={videoSrc}
            loading={loading}
          />
        }
        rightPanel={
          <RightPanel
            ref={segScrollRef}
            segments={segments}
            activeSegIndex={activeSegIndex}
            autoScroll={autoScroll}
            onSeekTo={handleSeekTo}
            onActiveSegmentChange={setActiveSegIndex}
            transcriptId={activeTranscriptId ?? undefined}
            onTranslateComplete={() => {
              if (activeTranscriptId) {
                loadTranscriptDetail(activeTranscriptId)
              }
            }}
          />
        }
      />
      <UploadDialog
        open={uploadDialogOpen}
        onOpenChange={setUploadDialogOpen}
        onUploadSuccess={handleUploadSuccess}
        onUploadError={handleUploadError}
      />
    </div>
  )
}

export default AppPage
