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
  onToggleLeft: () => void
  onToggleRight: () => void
}

/**
 * 三栏工作台。高度由 AppPage 的 h-dvh 统一分配，本层只做 flex-1/min-h-0。
 *
 * 侧栏收起开关放在各自面板的外侧顶角（左栏右上、右栏左上），是与拖拽
 * 完全分离的独立按钮，不挂在分隔条上——2026-09-20 实测：挂在
 * ResizableHandle 上的点击控件会被库的拖拽判定吞掉（指针抖动 1-2px 即
 * didMove，onClick 不触发），此路不通。分隔条只负责拖拽调宽。
 * 侧栏收起后分隔条随面板卸载，改由屏幕边缘的展开按钮负责点开。
 */
function AppLayout({
  leftPanel,
  centerPanel,
  rightPanel,
  leftPanelVisible,
  rightPanelVisible,
  onToggleLeft,
  onToggleRight,
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
            >
              <div className="h-full bg-sidebar border-r border-sidebar-border overflow-hidden">
                {leftPanel}
              </div>
            </ResizablePanel>
            <ResizableHandle withHandle title="拖动调整宽度" />
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
            <ResizableHandle withHandle title="拖动调整宽度" />
            <ResizablePanel
              defaultSize={panelSizes.right}
              minSize={15}
              maxSize={40}
            >
              <div className="h-full bg-sidebar border-l border-sidebar-border overflow-hidden">
                {rightPanel}
              </div>
            </ResizablePanel>
          </>
        )}
      </ResizablePanelGroup>

      {/* 收起状态的边缘展开按钮：贴屏幕两侧、垂直居中 */}
      {!leftPanelVisible && (
        <button
          type="button"
          title="展开侧栏"
          onClick={onToggleLeft}
          className="absolute left-0 top-1/2 -translate-y-1/2 z-30 h-20 w-7 flex items-center justify-center rounded-r-md border border-l-0 border-border bg-card text-muted-foreground shadow-sm hover:bg-muted hover:text-foreground transition-colors"
        >
          <PanelLeftOpen className="h-3.5 w-3.5" />
        </button>
      )}
      {!rightPanelVisible && (
        <button
          type="button"
          title="展开文稿面板"
          onClick={onToggleRight}
          className="absolute right-0 top-1/2 -translate-y-1/2 z-30 h-20 w-7 flex items-center justify-center rounded-l-md border border-r-0 border-border bg-card text-muted-foreground shadow-sm hover:bg-muted hover:text-foreground transition-colors"
        >
          <PanelRightOpen className="h-3.5 w-3.5" />
        </button>
      )}
    </div>
  )
}

export default AppLayout
