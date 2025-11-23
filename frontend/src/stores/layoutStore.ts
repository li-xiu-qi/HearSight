import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface LayoutState {
  // 面板大小 (百分比)
  panelSizes: { left: number; center: number; right: number }
  // 面板折叠状态
  panelCollapsed: { left: boolean; right: boolean }
  // 响应式断点
  breakpoint: 'mobile' | 'tablet' | 'desktop'
  // 动作
  setPanelSize: (panel: 'left' | 'center' | 'right', size: number) => void
  togglePanel: (panel: 'left' | 'right') => void
  setBreakpoint: (breakpoint: 'mobile' | 'tablet' | 'desktop') => void
  resetLayout: () => void
}

const defaultSizes = { left: 25, center: 50, right: 25 }
const defaultCollapsed = { left: false, right: false }

export const useLayoutStore = create<LayoutState>()(
  persist(
    (set, get) => ({
      panelSizes: defaultSizes,
      panelCollapsed: defaultCollapsed,
      breakpoint: 'desktop',

      setPanelSize: (panel, size) => {
        set((state) => {
          const newSizes = { ...state.panelSizes, [panel]: size }

          // 确保总和为 100%
          const total = Object.values(newSizes).reduce((sum, s) => sum + s, 0)
          if (Math.abs(total - 100) > 0.1) {
            // 重新计算比例
            const factor = 100 / total
            newSizes.left *= factor
            newSizes.center *= factor
            newSizes.right *= factor
          }

          // 约束最小/最大值
          const minSize = 15
          const maxSize = 40

          if (newSizes.left < minSize) newSizes.left = minSize
          if (newSizes.right < minSize) newSizes.right = minSize
          if (newSizes.left > maxSize) newSizes.left = maxSize
          if (newSizes.right > maxSize) newSizes.right = maxSize

          // 重新计算 center
          newSizes.center = 100 - newSizes.left - newSizes.right

          return { panelSizes: newSizes }
        })
      },

      togglePanel: (panel) => {
        set((state) => ({
          panelCollapsed: { ...state.panelCollapsed, [panel]: !state.panelCollapsed[panel] }
        }))
      },

      setBreakpoint: (breakpoint) => {
        set({ breakpoint })
      },

      resetLayout: () => {
        set({
          panelSizes: defaultSizes,
          panelCollapsed: defaultCollapsed
        })
      }
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