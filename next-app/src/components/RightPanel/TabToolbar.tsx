'use client'

import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Search, Target, Copy, Languages } from "lucide-react"
import { toast } from "sonner"
import type { Segment } from "../../types"
import LanguageSwitcher from "./LanguageSwitcher"

interface TabToolbarProps {
  readonly onCenterActive: () => void
  readonly onOpenSearch: () => void
  readonly onOpenTranslate: () => void
  readonly segments: Segment[]
  readonly displayLanguage?: string
  readonly availableLanguages?: string[]
  readonly onLanguageChange?: (language: string) => void
  readonly getLanguageName?: (code: string) => string
  readonly autoScroll?: boolean
  readonly onAutoScrollChange?: (value: boolean) => void
}

/**
 * 阅读工具栏：左侧工具组（定位/搜索/翻译/复制），右侧阅读偏好（自动滚动 + 语言）。
 * 自动滚动开关从顶栏迁到此处——它控制的是这块阅读区，放在被控制对象旁边。
 */
export default function TabToolbar({
  onCenterActive,
  onOpenSearch,
  onOpenTranslate,
  segments,
  displayLanguage = 'original',
  availableLanguages = ['original'],
  onLanguageChange,
  getLanguageName = (code: string) => code,
  autoScroll,
  onAutoScrollChange,
}: Readonly<TabToolbarProps>) {
  const handleCopyText = async () => {
    const text = segments.map(seg => seg.sentence || "").join(" ")
    try {
      await navigator.clipboard.writeText(text)
      toast.success("已经成功复制")
    } catch (err) {
      console.error("复制失败:", err)
      toast.error("复制失败")
    }
  }

  return (
    <div className="flex items-center gap-1 px-3 py-2 border-b border-border flex-shrink-0">
      <Button
        variant="ghost"
        size="sm"
        onClick={onCenterActive}
        title="定位到当前句子"
        className="h-8 w-8 p-0 text-muted-foreground hover:text-foreground"
      >
        <Target className="h-4 w-4" />
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={onOpenSearch}
        title="搜索全文"
        className="h-8 w-8 p-0 text-muted-foreground hover:text-foreground"
      >
        <Search className="h-4 w-4" />
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={onOpenTranslate}
        title="翻译文稿"
        className="h-8 w-8 p-0 text-muted-foreground hover:text-foreground"
      >
        <Languages className="h-4 w-4" />
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={handleCopyText}
        title="复制全文"
        className="h-8 w-8 p-0 text-muted-foreground hover:text-foreground"
      >
        <Copy className="h-4 w-4" />
      </Button>

      {onAutoScrollChange && (
        <div className="flex items-center gap-2 ml-2 pl-3 border-l border-border">
          <Switch
            id="auto-scroll"
            checked={autoScroll ?? false}
            onCheckedChange={onAutoScrollChange}
          />
          <Label htmlFor="auto-scroll" className="text-xs text-muted-foreground cursor-pointer select-none">
            跟随播放
          </Label>
        </div>
      )}

      <div className="ml-auto">
        {onLanguageChange && (
          <LanguageSwitcher
            displayLanguage={displayLanguage}
            availableLanguages={availableLanguages}
            onLanguageChange={onLanguageChange}
            getLanguageName={getLanguageName}
          />
        )}
      </div>
    </div>
  )
}
