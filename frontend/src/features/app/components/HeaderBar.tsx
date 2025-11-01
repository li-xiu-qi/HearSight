import type { FormEvent } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Loader2, Home, Menu, X, Upload } from "lucide-react"

interface HeaderBarProps {
  readonly inputUrl: string
  readonly submitting: boolean
  readonly autoScroll: boolean
  readonly leftPanelVisible: boolean
  readonly urlError: string | null
  readonly onSubmit: (event: FormEvent<HTMLFormElement>) => void
  readonly onInputUrlChange: (value: string) => void
  readonly onClear: () => void
  readonly onAutoScrollChange: (value: boolean) => void
  readonly onToggleLeftPanel: () => void
  readonly onNavigateHome: () => void
  readonly onOpenUpload: () => void
}

function HeaderBar({
  inputUrl,
  submitting,
  autoScroll,
  leftPanelVisible,
  urlError,
  onSubmit,
  onInputUrlChange,
  onClear,
  onAutoScrollChange,
  onToggleLeftPanel,
  onNavigateHome,
  onOpenUpload,
}: HeaderBarProps) {
  return (
    <header className="bg-white border-b border-slate-200 px-4 sticky top-0 z-50 shadow-sm">
      <div className="h-14 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggleLeftPanel}
            className="lg:hidden"
          >
            {leftPanelVisible ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </Button>
          <h3 className="text-lg font-semibold text-slate-900">HearSight</h3>
        </div>
        <form onSubmit={onSubmit} className="flex-1 max-w-2xl flex items-center gap-2">
          <Input
            type="text"
            placeholder="输入 bilibili.com 视频链接"
            value={inputUrl}
            onChange={(event) => onInputUrlChange(event.target.value)}
            className="flex-1"
            disabled={submitting}
          />
          <Button type="submit" disabled={submitting} size="sm">
            {submitting ? (
              <>
                <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                提交
              </>
            ) : (
              "提交"
            )}
          </Button>
          {inputUrl && (
            <Button
              type="button"
              variant="outline"
              onClick={onClear}
              disabled={submitting}
              size="sm"
            >
              清除
            </Button>
          )}
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="gap-1.5"
            onClick={onOpenUpload}
          >
            <Upload className="h-4 w-4" />
            <span className="hidden sm:inline">上传</span>
          </Button>
        </form>
        <div className="flex items-center gap-3">
          <div className="hidden md:flex items-center gap-2">
            <Switch
              id="auto-scroll"
              checked={autoScroll}
              onCheckedChange={onAutoScrollChange}
            />
            <Label htmlFor="auto-scroll" className="text-sm cursor-pointer">
              自动滚动
            </Label>
          </div>
          <Button variant="ghost" onClick={onNavigateHome} size="sm" className="gap-1.5">
            <Home className="h-4 w-4" />
            <span className="hidden sm:inline">首页</span>
          </Button>
        </div>
      </div>
      {urlError && (
        <div className="pb-2">
          <p className="text-xs text-red-600">{urlError}</p>
        </div>
      )}
    </header>
  )
}

export default HeaderBar
