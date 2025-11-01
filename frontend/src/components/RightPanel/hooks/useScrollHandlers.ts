import { useRef } from 'react'

export const useScrollHandlers = () => {
  const segmentsScrollRef = useRef<HTMLDivElement | null>(null)
  const transcriptScrollRef = useRef<HTMLDivElement | null>(null)

  const scrollUp = (activeTab: string) => {
    if (activeTab === 'segments') {
      segmentsScrollRef.current?.scrollBy({ top: -160, behavior: 'smooth' })
    } else if (activeTab === 'transcript') {
      transcriptScrollRef.current?.scrollBy({ top: -160, behavior: 'smooth' })
    }
  }

  const scrollDown = (activeTab: string) => {
    if (activeTab === 'segments') {
      segmentsScrollRef.current?.scrollBy({ top: 160, behavior: 'smooth' })
    } else if (activeTab === 'transcript') {
      transcriptScrollRef.current?.scrollBy({ top: 160, behavior: 'smooth' })
    }
  }

  const centerActiveSegment = (activeSegIndex: number | null, activeTab: string) => {
    if (activeSegIndex == null) return
    if (activeTab === 'segments') {
      const el = segmentsScrollRef.current?.querySelector(
        `[data-seg-index="${activeSegIndex}"]`
      ) as HTMLElement | null
      el?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    } else if (activeTab === 'transcript') {
      const el = transcriptScrollRef.current?.querySelector(
        `[data-seg-index="${activeSegIndex}"]`
      ) as HTMLElement | null
      el?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }

  return {
    segmentsScrollRef,
    transcriptScrollRef,
    scrollUp,
    scrollDown,
    centerActiveSegment,
  }
}
