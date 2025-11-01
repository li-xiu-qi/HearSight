import { useCallback } from 'react'
import type { Segment } from '../../../types'

export const useSegmentHandlers = (
  onActiveSegmentChange: (index: number) => void,
  onSeekTo: (timeMs: number) => void
) => {
  const handleSegmentClick = useCallback(
    (segment: Segment) => {
      onActiveSegmentChange(segment.index)
      onSeekTo(segment.start_time)
    },
    [onActiveSegmentChange, onSeekTo]
  )

  return { handleSegmentClick }
}
