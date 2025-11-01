import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger } from '@/components/ui/dialog'
import { Pencil, Loader2 } from 'lucide-react'
import { message } from '@/utils/message'

interface FileRenameDialogProps {
  oldFilename: string
  onRenameSuccess?: (newFilename: string) => void
}

const FileRenameDialog = ({ oldFilename, onRenameSuccess }: FileRenameDialogProps) => {
  const [open, setOpen] = useState(false)
  const [newFilename, setNewFilename] = useState(oldFilename)
  const [renaming, setRenaming] = useState(false)

  const handleOpenChange = (isOpen: boolean) => {
    setOpen(isOpen)
    if (isOpen) {
      setNewFilename(oldFilename)
    }
  }

  const handleRename = async () => {
    if (!newFilename.trim()) {
      message.error('文件名不能为空')
      return
    }

    if (newFilename === oldFilename) {
      message.warning('文件名未更改')
      setOpen(false)
      return
    }

    setRenaming(true)
    try {
      const response = await fetch('/api/upload/rename', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          old_filename: oldFilename,
          new_filename: newFilename,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: '重命名失败' }))
        throw new Error(errorData.detail || '重命名失败')
      }

      const result = await response.json()
      if (result.success) {
        message.success(result.message || '重命名成功')
        setOpen(false)
        onRenameSuccess?.(result.data.new_filename)
      } else {
        throw new Error(result.message || '重命名失败')
      }
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : '重命名失败'
      message.error(errorMessage)
    } finally {
      setRenaming(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <button className="w-full text-left px-2 py-1.5 flex items-center gap-2 hover:bg-slate-50 rounded">
          <Pencil className="h-4 w-4" />
          <span>重命名</span>
        </button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>重命名文件</DialogTitle>
        </DialogHeader>
        <div className="py-4">
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-slate-700 mb-2 block">
                原文件名
              </label>
              <Input value={oldFilename} disabled className="bg-slate-50" />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700 mb-2 block">
                新文件名
              </label>
              <Input
                value={newFilename}
                onChange={(e) => setNewFilename(e.target.value)}
                placeholder="请输入新文件名"
                disabled={renaming}
              />
              <p className="text-xs text-slate-500 mt-1">
                注意：不能更改文件扩展名
              </p>
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)} disabled={renaming}>
            取消
          </Button>
          <Button onClick={handleRename} disabled={renaming}>
            {renaming ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                重命名中
              </>
            ) : (
              '确认'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default FileRenameDialog
