import { Button } from "@/components/ui/button"
import { ChevronDown, ChevronUp, Search, Target, Copy } from "lucide-react"
import { toast } from "sonner"
import type { Segment } from "../../types"

interface TabToolbarProps {
  readonly onScrollUp: () => void
  readonly onScrollDown: () => void
  readonly onCenterActive: () => void
  readonly onOpenSearch: () => void
  readonly segments: Segment[]
}

export default function TabToolbar({
  onScrollUp,
  onScrollDown,
  onCenterActive,
  onOpenSearch,
  segments,
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
    <div className="flex items-center gap-2 px-3 py-2 border-b bg-slate-50 flex-shrink-0">
      <Button variant="ghost" size="sm" onClick={onScrollUp}>
        <ChevronUp className="h-4 w-4" />
      </Button>
      <Button variant="ghost" size="sm" onClick={onScrollDown}>
        <ChevronDown className="h-4 w-4" />
      </Button>
      <Button variant="ghost" size="sm" onClick={onCenterActive}>
        <Target className="h-4 w-4" />
      </Button>
      <Button variant="ghost" size="sm" onClick={onOpenSearch}>
        <Search className="h-4 w-4" />
      </Button>
      <Button variant="ghost" size="sm" onClick={handleCopyText}>
        <Copy className="h-4 w-4" />
      </Button>
    </div>
  )
}
