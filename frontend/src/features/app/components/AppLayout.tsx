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
    setPanelSize,
  } = useLayoutStore()

  // 桌面端：完整可拖拽布局
  return (
    <div className="h-full flex-1">
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
          <div className="h-full min-w-[400px]">
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