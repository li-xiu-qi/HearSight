import { useState, useCallback, useRef, useEffect } from 'react'

interface UsePanelResizeProps {
  initialWidth: number
  minWidth?: number
  maxWidth: number
  isRightPanel?: boolean
  minVideoWidth?: number
  getSiblingPanelWidth?: () => number
}

interface UsePanelResizeReturn {
  width: number
  isResizing: boolean
  startResizing: (e: React.MouseEvent) => void
  stopResizing: () => void
  maxWidth: number
}

export const usePanelResize = ({
  initialWidth,
  minWidth = 320,
  maxWidth: initialMaxWidth,
  isRightPanel = false,
  minVideoWidth = globalThis.innerWidth * 0.3,
  getSiblingPanelWidth
}: UsePanelResizeProps): UsePanelResizeReturn => {
  const [width, setWidth] = useState(initialWidth)
  const [isResizing, setIsResizing] = useState(false)
  const [maxWidth, setMaxWidth] = useState(initialMaxWidth)
  const startXRef = useRef(0)
  const startWidthRef = useRef(0)

  const startResizing = useCallback((e: React.MouseEvent) => {
    setIsResizing(true)
    startXRef.current = e.clientX
    startWidthRef.current = width
    e.preventDefault()
  }, [width])

  const stopResizing = useCallback(() => {
    setIsResizing(false)
  }, [])

  const updateWidth = useCallback((newWidth: number) => {
    setWidth(Math.min(Math.max(newWidth, minWidth), maxWidth))
  }, [minWidth, maxWidth])

  useEffect(() => {
    const handleResize = () => {
      const newMaxWidth = globalThis.innerWidth * 0.5
      setMaxWidth(newMaxWidth)
      if (width > newMaxWidth) {
        setWidth(newMaxWidth)
      }
    }

    globalThis.addEventListener('resize', handleResize)
    return () => globalThis.removeEventListener('resize', handleResize)
  }, [width])

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return
      
      const diff = e.clientX - startXRef.current
      const actualDiff = isRightPanel ? -diff : diff
      let newWidth = startWidthRef.current + actualDiff
      
      const siblingWidth = getSiblingPanelWidth ? getSiblingPanelWidth() : 0
      const constrainedMaxWidth = Math.min(maxWidth, globalThis.innerWidth - siblingWidth - minVideoWidth)
      
      newWidth = Math.min(Math.max(newWidth, minWidth), constrainedMaxWidth)
      
      updateWidth(newWidth)
    }

    const handleMouseUp = () => {
      if (isResizing) {
        stopResizing()
      }
    }

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isResizing, stopResizing, updateWidth, isRightPanel, minWidth, maxWidth, getSiblingPanelWidth, minVideoWidth])

  return {
    width,
    isResizing,
    startResizing,
    stopResizing,
    maxWidth
  }
}
