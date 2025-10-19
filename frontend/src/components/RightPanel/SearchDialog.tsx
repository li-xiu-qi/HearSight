import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import type { Segment } from "../../types"
import { formatTime } from "../../utils"

interface SearchDialogProps {
  readonly open: boolean
  readonly onOpenChange: (open: boolean) => void
  readonly searchTerm: string
  readonly onSearchTermChange: (value: string) => void
  readonly onSubmit: () => void
  readonly results: Segment[]
  readonly onSelect: (segment: Segment) => void
}

export default function SearchDialog({
  open,
  onOpenChange,
  searchTerm,
  onSearchTermChange,
  onSubmit,
  results,
  onSelect,
}: Readonly<SearchDialogProps>) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>搜索字幕</DialogTitle>
        </DialogHeader>
        <div className="space-y-3">
          <div className="flex gap-2">
            <Input
              placeholder="输入搜索关键词"
              value={searchTerm}
              onChange={(e) => onSearchTermChange(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && onSubmit()}
            />
            <Button onClick={onSubmit} size="sm">
              搜索
            </Button>
          </div>
          <ScrollArea className="h-80">
            {results.length === 0 ? (
              <div className="text-center py-10 text-sm text-slate-500">
                {searchTerm ? "未找到结果" : "请输入关键词"}
              </div>
            ) : (
              <div className="space-y-2">
                {results.map((seg) => (
                  <button
                    key={seg.index}
                    type="button"
                    aria-label={`跳转到 ${formatTime(seg.start_time)}`}
                    onClick={() => onSelect(seg)}
                    className="w-full text-left p-2 hover:bg-slate-50 cursor-pointer rounded text-sm"
                  >
                    <div className="text-xs text-slate-500 mb-1">
                      {formatTime(seg.start_time)}
                    </div>
                    <div>{seg.sentence}</div>
                  </button>
                ))}
              </div>
            )}
          </ScrollArea>
        </div>
      </DialogContent>
    </Dialog>
  )
}
