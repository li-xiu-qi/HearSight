import { useEffect, useRef } from 'react'
import { seekVideoTo } from '../utils'
import type { Segment } from '../types'

interface UseVideoSyncProps {
  segments: Segment[]
  autoScroll: boolean
  segScrollRef: React.RefObject<HTMLDivElement | null>
  setActiveSegIndex: (index: number | null) => void
  videoRef: React.RefObject<HTMLVideoElement | null>
}

export const useVideoSync = ({
  segments,
  autoScroll,
  segScrollRef,
  setActiveSegIndex,
  videoRef
}: UseVideoSyncProps) => {
  const prevActiveRef = useRef<number | null>(null)

  useEffect(() => {
    const v = videoRef.current
    if (!v) return

    const onTimeUpdate = () => {
      const ms = (v.currentTime || 0) * 1000
      let newIndex: number | null = null
      for (const s of segments) {
        const st = Number(s.start_time) || 0
        const et = Number(s.end_time) || 0
        if (ms >= st && ms < et) {
          newIndex = s.index
          break
        }
      }

      if (prevActiveRef.current !== newIndex) {
        prevActiveRef.current = newIndex
        setActiveSegIndex(newIndex)
        if (autoScroll && newIndex != null && segScrollRef.current) {
          const scrollContainer = segScrollRef.current
          if (scrollContainer) {
            const el = scrollContainer.querySelector(`[data-seg-index="${newIndex}"]`)
            if (el) {
              try { 
                el.scrollIntoView({ behavior: 'smooth', block: 'center' }) 
              } catch {}
            }
          }
        }
      }
    }

    v.addEventListener('timeupdate', onTimeUpdate)
    return () => v.removeEventListener('timeupdate', onTimeUpdate)
  }, [segments, autoScroll, segScrollRef, setActiveSegIndex, videoRef])

  const handleSeekTo = (timeMs: number) => {
    seekVideoTo(videoRef.current, timeMs)
  }

  return {
    handleSeekTo
  }
}
