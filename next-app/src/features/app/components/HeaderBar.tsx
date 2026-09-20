'use client'

import type { FormEvent } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Loader2, Home, Menu, Upload, X } from "lucide-react"

interface HeaderBarProps {
  readonly inputUrl: string
  readonly submitting: boolean
  readonly leftPanelVisible: boolean
  readonly urlError: string | null
  readonly onSubmit: (event: FormEvent<HTMLFormElement>) => void
  readonly onInputUrlChange: (value: string) => void
  readonly onClear: () => void
  readonly onToggleLeftPanel: () => void
  readonly onNavigateHome: () => void
  readonly onOpenUpload: () => void
}

/**
 * 顶栏只保留三组：侧栏开关+标识 / 链接导入 / 上传与首页。
 * 自动滚动开关已迁至右栏工具栏（贴近它控制的阅读区）。
 */
function HeaderBar({
  inputUrl,
  submitting,
  leftPanelVisible,
  urlError,
  onSubmit,
  onInputUrlChange,
  onClear,
  onToggleLeftPanel,
  onNavigateHome,
  onOpenUpload,
}: HeaderBarProps) {
  return (
    <header className="bg-card border-b border-border px-4 flex-shrink-0">
      <div className="h-14 flex items-center gap-3">
        <div className="flex items-center gap-2 flex-shrink-0">
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggleLeftPanel}
            className="lg:hidden px-2"
            title={leftPanelVisible ? "收起侧栏" : "展开侧栏"}
          >
            {leftPanelVisible ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </Button>
          <span className="text-base font-semibold text-foreground tracking-tight hidden sm:block">HearSight</span>
        </div>

        <form onSubmit={onSubmit} className="flex-1 max-w-2xl flex items-center gap-2">
          <div className="relative flex-1">
            <Input
              type="text"
              placeholder="粘贴视频或播客链接，开始分析"
              value={inputUrl}
              onChange={(event) => onInputUrlChange(event.target.value)}
              className="pr-9"
              disabled={submitting}
            />
            {inputUrl && (
              <button
                type="button"
                onClick={onClear}
                title="清空输入"
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
          <Button type="submit" disabled={submitting || !inputUrl.trim()} size="sm" className="gap-1.5">
            {submitting ? (
              <>
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                分析中
              </>
            ) : (
              "分析"
            )}
          </Button>
        </form>

        <div className="flex items-center gap-1 flex-shrink-0">
          <Button
            variant="outline"
            size="sm"
            className="gap-1.5"
            onClick={onOpenUpload}
            title="上传本地音视频文件"
          >
            <Upload className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">上传</span>
          </Button>
          <Button variant="ghost" onClick={onNavigateHome} size="sm" className="gap-1.5 text-muted-foreground" title="返回首页">
            <Home className="h-3.5 w-3.5" />
            <span className="hidden md:inline">首页</span>
          </Button>
        </div>
      </div>
      {urlError && (
        <div className="pb-2">
          <p className="text-xs text-destructive">{urlError}</p>
        </div>
      )}
    </header>
  )
}

export default HeaderBar
