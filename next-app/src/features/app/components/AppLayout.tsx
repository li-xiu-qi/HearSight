'use client'

import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from '@/components/ui/resizable'
import { ChevronLeft, ChevronRight, PanelLeftOpen, PanelRightOpen } from 'lucide-react'
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
 * 侧栏开关放在中间分隔条上（最容易被看到的位置）：分隔条中央是一枚 48×20 的
 * 胶囊按钮，点击收起对应侧栏。注意不开启库自带的 collapsible——拖到边缘折叠
 * 会让面板 0 宽但 React 可见状态不变，边缘展开按钮不渲染，用户被卡死
 * （2026-09-20 实测踩坑）。收起只走点击这一条路，minSize 挡住拖拽下限，
  * 状态与渲染永远同步；指针未移动才触发 onClick（点击/拖动区分由库完成）。
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
            <ResizableHandle
              onClick={onToggleLeft}
              title="点击收起侧栏 · 拖动调整宽度"
              className="cursor-pointer"
            >
              <div className="z-10 flex h-12 w-5 items-center justify-center rounded-full border border-border bg-card text-muted-foreground shadow-sm transition-colors hover:border-primary/40 hover:text-primary">
                <ChevronLeft className="h-3.5 w-3.5" />
              </div>
            </ResizableHandle>
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
            <ResizableHandle
              onClick={onToggleRight}
              title="点击收起面板 · 拖动调整宽度"
              className="cursor-pointer"
            >
              <div className="z-10 flex h-12 w-5 items-center justify-center rounded-full border border-border bg-card text-muted-foreground shadow-sm transition-colors hover:border-primary/40 hover:text-primary">
                <ChevronRight className="h-3.5 w-3.5" />
              </div>
            </ResizableHandle>
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
