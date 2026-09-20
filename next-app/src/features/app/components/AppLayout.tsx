'use client'

import { useRef } from 'react'
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

/** 竖条图标按钮：44px 触控区，选中态主色底丸，角标承载计数 */
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
 * 三栏工作台 + 双侧竖条。高度由 AppPage 的 h-dvh 统一分配，本层只做 flex-1/min-h-0。
 *
 * 布局语义：
 * - 左竖条常驻：置顶一枚收起/展开开关，下方两个图标切 素材库/任务。
 *   常驻所以收起态永远有可见入口，不需要屏幕边缘浮动按钮。
 * - 右竖条仅在右栏收起时出现：同样置顶一枚展开开关，与左竖条对称。
 * - 三栏宽度拖拽：面板必须带稳定 id（库对条件渲染面板的要求）；布局只在
 *   拖动结束或结构变化时原子写入 store，拖动过程中不反馈——2026-09-20 修复：
 *   旧实现把每帧布局拆成三次单面板写入、每次还做归一化，拖右栏会牵连左栏。
 * - 分隔条只做拖拽调宽，不挂点击控件（库的拖拽判定会吞掉点击）。
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
  const { panelSizes, setPanelSizes } = useLayoutStore()

  // 拖动中的布局只进 ref，松手才落库；isDragging 兜底结构变化（面板显隐）时立即落库
  const latestLayout = useRef(panelSizes)
  const isDragging = useRef(false)

  const commitLayout = (left: number, center: number, right: number) => {
    latestLayout.current = { left, center, right }
    if (!isDragging.current) setPanelSizes(latestLayout.current)
  }

  return (
    <div className="flex-1 min-h-0 relative flex">
      {/* 左竖条：常驻 */}
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
            commitLayout(sizes[0], sizes[1], sizes[2])
          }
        }}
      >
        {leftPanelVisible && (
          <>
            <ResizablePanel
              id="left"
              order={1}
              defaultSize={panelSizes.left}
              minSize={15}
              maxSize={40}
            >
              <div className="h-full bg-sidebar overflow-hidden">
                {leftPanel}
              </div>
            </ResizablePanel>
            <ResizableHandle
              withHandle
              title="拖动调整宽度"
              onDragging={(dragging) => {
                isDragging.current = dragging
                if (!dragging) setPanelSizes(latestLayout.current)
              }}
            />
          </>
        )}

        <ResizablePanel
          id="center"
          order={2}
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
              withHandle
              title="拖动调整宽度"
              onDragging={(dragging) => {
                isDragging.current = dragging
                if (!dragging) setPanelSizes(latestLayout.current)
              }}
            />
            <ResizablePanel
              id="right"
              order={3}
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

      {/* 右竖条：仅右栏收起时出现，与左竖条对称（置顶展开开关） */}
      {!rightPanelVisible && (
        <nav
          aria-label="文稿面板入口"
          className="absolute right-0 top-0 bottom-0 z-30 w-12 bg-sidebar border-l border-sidebar-border flex flex-col items-center pt-3"
        >
          <RailButton active={false} title="展开文稿面板" onClick={onToggleRight}>
            <PanelRightOpen className="h-5 w-5" />
          </RailButton>
        </nav>
      )}
    </div>
  )
}

export default AppLayout
