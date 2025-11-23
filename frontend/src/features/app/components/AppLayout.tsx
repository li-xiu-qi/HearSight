import { useEffect } from 'react'
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from '@/components/ui/resizable'
import { useLayoutStore } from '@/stores/layoutStore'
import type { ReactNode } from 'react'

interface AppLayoutProps {
  leftPanel: ReactNode
  centerPanel: ReactNode
  rightPanel: ReactNode
  leftPanelVisible: boolean
  rightPanelVisible: boolean
}

function AppLayout({
  leftPanel,
  centerPanel,
  rightPanel,
  leftPanelVisible,
  rightPanelVisible
}: AppLayoutProps) {
  const {
    panelSizes,
    panelCollapsed,
    breakpoint,
    setPanelSize,
    setBreakpoint
  } = useLayoutStore()

  // 检测响应式断点
  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth
      if (width < 768) {
        setBreakpoint('mobile')
      } else if (width < 1024) {
        setBreakpoint('tablet')
      } else {
        setBreakpoint('desktop')
      }
    }

    handleResize()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [setBreakpoint])

  // 移动端：单栏布局
  if (breakpoint === 'mobile') {
    return (
      <div className="h-full flex flex-col">
        <div className="flex-1 overflow-auto">
          {centerPanel}
        </div>
      </div>
    )
  }

  // 平板端：可折叠侧边栏
  if (breakpoint === 'tablet') {
    return (
      <div className="h-full flex">
        {leftPanelVisible && !panelCollapsed.left && (
          <div className="w-80 border-r border-slate-200 bg-white overflow-hidden">
            {leftPanel}
          </div>
        )}
        <div className="flex-1 min-w-[400px] overflow-auto">
          {centerPanel}
        </div>
        {rightPanelVisible && !panelCollapsed.right && (
          <div className="w-96 border-l border-slate-200 bg-white overflow-hidden">
            {rightPanel}
          </div>
        )}
      </div>
    )
  }

  // 桌面端：完整可拖拽布局
  return (
    <div className="h-full">
      <ResizablePanelGroup
        direction="horizontal"
        className="h-full"
        onLayout={(sizes) => {
          if (sizes.length === 3) {
            setPanelSize('left', sizes[0])
            setPanelSize('center', sizes[1])
            setPanelSize('right', sizes[2])
          }
        }}
      >
        {leftPanelVisible && (
          <>
            <ResizablePanel
              defaultSize={panelSizes.left}
              minSize={15}
              maxSize={40}
              collapsible
              collapsedSize={0}
              onCollapse={() => setPanelSize('left', 0)}
              onExpand={() => setPanelSize('left', panelSizes.left)}
            >
              <div className="h-full border-r border-slate-200 bg-white overflow-hidden">
                {leftPanel}
              </div>
            </ResizablePanel>
            <ResizableHandle withHandle />
          </>
        )}

        <ResizablePanel
          defaultSize={panelSizes.center}
          minSize={30}
        >
          <div className="h-full min-w-[400px] overflow-auto">
            {centerPanel}
          </div>
        </ResizablePanel>

        {rightPanelVisible && (
          <>
            <ResizableHandle withHandle />
            <ResizablePanel
              defaultSize={panelSizes.right}
              minSize={15}
              maxSize={40}
              collapsible
              collapsedSize={0}
              onCollapse={() => setPanelSize('right', 0)}
              onExpand={() => setPanelSize('right', panelSizes.right)}
            >
              <div className="h-full border-l border-slate-200 bg-white overflow-hidden">
                {rightPanel}
              </div>
            </ResizablePanel>
          </>
        )}
      </ResizablePanelGroup>
    </div>
  )
}

export default AppLayout