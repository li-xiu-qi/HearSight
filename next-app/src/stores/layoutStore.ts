'use client'

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface LayoutState {
  // 面板大小 (百分比)，由 react-resizable-panels 的布局结果原子写入
  panelSizes: { left: number; center: number; right: number }
  // 面板折叠状态
  panelCollapsed: { left: boolean; right: boolean }
  // 响应式断点
  breakpoint: 'mobile' | 'tablet' | 'desktop'
  // 动作
  setPanelSizes: (sizes: { left: number; center: number; right: number }) => void
  togglePanel: (panel: 'left' | 'right') => void
  setBreakpoint: (breakpoint: 'mobile' | 'tablet' | 'desktop') => void
  resetLayout: () => void
}

const defaultSizes = { left: 25, center: 50, right: 25 }
const defaultCollapsed = { left: false, right: false }

/**
 * 布局持久化。注意：只做「记录」，不做归一化与约束钳制。
 * 2026-09-20 修复：旧实现在 setPanelSize 里对单个面板做归一化+钳制+重算 center，
 * 而 onLayout 每帧会连续调用三次。拖右栏时布局 [25,60,15] 总和 110，归一化把
 * 左栏从 25 拉到 22.7——左栏被右栏拖动牵连，根因就是这套逻辑在和库的求解器
 * 打架。库本身保证总和 100 与 min/max 约束，这里原样落盘即可。
 */
export const useLayoutStore = create<LayoutState>()(
  persist(
    (set) => ({
      panelSizes: defaultSizes,
      panelCollapsed: defaultCollapsed,
      breakpoint: 'desktop',

      setPanelSizes: (sizes) => set({ panelSizes: sizes }),

      togglePanel: (panel) => {
        set((state) => ({
          panelCollapsed: { ...state.panelCollapsed, [panel]: !state.panelCollapsed[panel] }
        }))
      },

      setBreakpoint: (breakpoint) => set({ breakpoint }),

      resetLayout: () => set({
        panelSizes: defaultSizes,
        panelCollapsed: defaultCollapsed
      })
    }),
    {
      name: 'layout-storage',
      partialize: (state) => ({
        panelSizes: state.panelSizes,
        panelCollapsed: state.panelCollapsed
      })
    }
  )
)
