'use client'

import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from '@/components/ui/resizable'
import { Library, ListChecks, PanelLeftClose, PanelLeftOpen, PanelRightOpen } from 'lucide-react'
import { useLayoutStore } from '@/stores/layoutStore'
import { cn } from '@/lib/utils'
import type { ReactNode } from 'react'

export type LeftView = 'library' | 'tasks'

interface AppLayoutProps {
  leftPanel: ReactNode
  centerPanel: ReactNode
  rightPanel: ReactNode
  leftPanelVisible: boolean
  rightPanelVisible: boolean
  leftView: LeftView
  runningJobCount: number
  onToggleLeft: () => void
  onSelectLeftView: (view: LeftView) => void
  onToggleRight: () => void
}

/** 活动条图标按钮：44px 触控区，选中态用主色底丸，角标承载进行中任务数 */
function RailButton({
  active,
  title,
  badge,
  onClick,
  children,
}: {
  readonly active: boolean
  readonly title: string
  readonly badge?: number
  readonly onClick: () => void
  readonly children: ReactNode
}) {
  return (
    <button
      type="button"
      title={title}
      onClick={onClick}
      className={cn(
        'relative flex h-11 w-11 items-center justify-center rounded-lg transition-colors',
        active ? 'bg-accent text-primary' : 'text-muted-foreground hover:bg-muted hover:text-foreground',
      )}
    >
      {children}
      {badge != null && badge > 0 && (
        <span className="absolute right-0.5 top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-primary px-1 text-[10px] font-medium text-primary-foreground">
          {badge}
        </span>
      )}
    </button>
  )
}

/**
 * 三栏工作台 + 活动条。高度由 AppPage 的 h-dvh 统一分配，本层只做 flex-1/min-h-0。
 *
 * 左栏宽度控制收敛到活动条：置顶一枚显式收起/展开开关，下方两个图标
 * 切换 素材库/任务（同时负责在收起态点开）。活动条常驻 48px，所以收起态
 * 永远有可见入口，不需要屏幕边缘浮动按钮。右栏保持「面板内按钮收起 +
 * 边缘按钮展开」。分隔条只做拖拽调宽，不挂点击控件（库的拖拽判定会吞掉
 * 点击，见记忆观察）。
 */
function AppLayout({
  leftPanel,
  centerPanel,
  rightPanel,
  leftPanelVisible,
  rightPanelVisible,
  leftView,
  runningJobCount,
  onToggleLeft,
  onSelectLeftView,
  onToggleRight,
}: AppLayoutProps) {
  const {
    panelSizes,
    setPanelSize,
  } = useLayoutStore()

  return (
    <div className="flex-1 min-h-0 relative flex">
      {/* 活动条：常驻，左栏的导航与宽度控制都在这里 */}
      <nav
        aria-label="侧栏导航"
        className="w-12 flex-shrink-0 bg-sidebar border-r border-sidebar-border flex flex-col items-center py-3 gap-1"
      >
        {/* 收起/展开开关置顶：它控制整条侧栏的显隐，是最结构化的操作 */}
        <RailButton
          active={false}
          title={leftPanelVisible ? '收起侧栏' : '展开侧栏'}
          onClick={onToggleLeft}
        >
          {leftPanelVisible ? <PanelLeftClose className="h-5 w-5" /> : <PanelLeftOpen className="h-5 w-5" />}
        </RailButton>
        <RailButton
          active={leftView === 'library'}
          title={leftPanelVisible && leftView === 'library' ? '素材库（再次点击收起）' : '素材库'}
          onClick={() => onSelectLeftView('library')}
        >
          <Library className="h-5 w-5" />
        </RailButton>
        <RailButton
          active={leftView === 'tasks'}
          title={leftPanelVisible && leftView === 'tasks' ? '任务（再次点击收起）' : '任务'}
          badge={runningJobCount}
          onClick={() => onSelectLeftView('tasks')}
        >
          <ListChecks className="h-5 w-5" />
        </RailButton>
      </nav>

      <ResizablePanelGroup
        direction="horizontal"
        className="h-full flex-1 min-w-0"
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
              <div className="h-full bg-sidebar overflow-hidden">
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
              <div className="h-full bg-sidebar overflow-hidden">
                {rightPanel}
              </div>
            </ResizablePanel>
          </>
        )}
      </ResizablePanelGroup>

      {/* 右栏收起态的边缘展开按钮（左栏由活动条负责，不需要边缘按钮） */}
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
