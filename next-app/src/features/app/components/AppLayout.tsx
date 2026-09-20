'use client'

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

/**
 * 三栏工作台。高度由 AppPage 的 h-dvh 统一分配，本层只做 flex-1/min-h-0，
 * 不再出现 [90vh] 魔法数（旧实现里 AppLayout 与 RightPanel 各写一份 90vh，
 * 与 header 叠加后底部被截或留白）。
 * 底色分工：左右栏 bg-sidebar（暖纸深一档），中栏 bg-card，形成空间分区。
 */
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

  return (
    <div className="flex-1 min-h-0">
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
              <div className="h-full bg-sidebar border-r border-sidebar-border overflow-hidden">
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
          <div className="h-full min-w-0 bg-card">
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
              <div className="h-full bg-sidebar border-l border-sidebar-border overflow-hidden">
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
