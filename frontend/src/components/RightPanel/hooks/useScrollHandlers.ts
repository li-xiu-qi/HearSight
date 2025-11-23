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
      // 对于TranscriptTab，使用ScrollArea，需要找到正确的滚动容器
      const scrollContainer = transcriptScrollRef.current?.querySelector('[data-radix-scroll-area-viewport]') as HTMLElement | null
      const el = scrollContainer?.querySelector(
        `[data-seg-index="${activeSegIndex}"]`
      ) as HTMLElement | null
      if (el && scrollContainer) {
        // 计算元素相对于滚动容器的位置
        const elementRect = el.getBoundingClientRect()
        const containerRect = scrollContainer.getBoundingClientRect()
        const scrollTop = scrollContainer.scrollTop
        const elementTop = elementRect.top - containerRect.top + scrollTop
        const containerHeight = scrollContainer.clientHeight
        const targetScrollTop = elementTop - containerHeight / 2 + el.offsetHeight / 2

        scrollContainer.scrollTo({
          top: targetScrollTop,
          behavior: 'smooth'
        })
      }
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
