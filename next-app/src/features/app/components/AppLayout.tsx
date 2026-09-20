'use client'

import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from '@/components/ui/resizable'
import { PanelLeftOpen, PanelRightOpen } from 'lucide-react'
import { useLayoutStore } from '@/stores/layoutStore'
import type { ReactNode } from 'react'

interface AppLayoutProps {
  leftPanel: ReactNode
  centerPanel: ReactNode
  rightPanel: ReactNode
  leftPanelVisible: boolean
  rightPanelVisible: boolean
  onExpandLeft: () => void
  onExpandRight: () => void
}

/**
 * 三栏工作台。高度由 AppPage 的 h-dvh 统一分配，本层只做 flex-1/min-h-0。
 * 侧栏收起后不留残影：面板整体卸载，屏幕边缘浮出展开按钮（edge tab），
 * 点它或拖拽中栏都能把侧栏找回来。底色分工：左右栏 sidebar，中栏 card。
 */
function AppLayout({
  leftPanel,
  centerPanel,
  rightPanel,
  leftPanelVisible,
  rightPanelVisible,
  onExpandLeft,
  onExpandRight,
}: AppLayoutProps) {
  const {
    panelSizes,
    setPanelSize,
  } = useLayoutStore()

  return (
    <div className="flex-1 min-h-0 relative">
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

      {/* 收起状态的边缘展开按钮：贴屏幕两侧、垂直居中、低调不抢内容 */}
      {!leftPanelVisible && (
        <button
          type="button"
          title="展开侧栏"
          onClick={onExpandLeft}
          className="absolute left-0 top-1/2 -translate-y-1/2 z-30 h-16 w-6 flex items-center justify-center rounded-r-md border border-l-0 border-border bg-card text-muted-foreground shadow-sm hover:bg-muted hover:text-foreground transition-colors"
        >
          <PanelLeftOpen className="h-3.5 w-3.5" />
        </button>
      )}
      {!rightPanelVisible && (
        <button
          type="button"
          title="展开文稿面板"
          onClick={onExpandRight}
          className="absolute right-0 top-1/2 -translate-y-1/2 z-30 h-16 w-6 flex items-center justify-center rounded-l-md border border-r-0 border-border bg-card text-muted-foreground shadow-sm hover:bg-muted hover:text-foreground transition-colors"
        >
          <PanelRightOpen className="h-3.5 w-3.5" />
        </button>
      )}
    </div>
  )
}

export default AppLayout
