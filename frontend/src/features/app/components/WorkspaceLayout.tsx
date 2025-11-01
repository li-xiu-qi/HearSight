import type { ReactNode } from "react"

interface WorkspaceLayoutProps {
  readonly leftPanelVisible: boolean
  readonly rightPanelVisible: boolean
  readonly leftPanel: ReactNode
  readonly centerPanel: ReactNode
  readonly rightPanel: ReactNode
}

function WorkspaceLayout({
  leftPanelVisible,
  rightPanelVisible,
  leftPanel,
  centerPanel,
  rightPanel,
}: WorkspaceLayoutProps) {
  return (
    <div className="flex-1 flex overflow-hidden">
      {leftPanelVisible && (
        <div className="w-80 border-r border-slate-200 bg-white overflow-hidden">
          {leftPanel}
        </div>
      )}
      <div className="flex-1 p-4 overflow-auto">
        {centerPanel}
      </div>
      {rightPanelVisible && (
        <div className="w-96 border-l border-slate-200 bg-white overflow-hidden">
          {rightPanel}
        </div>
      )}
    </div>
  )
}

export default WorkspaceLayout
