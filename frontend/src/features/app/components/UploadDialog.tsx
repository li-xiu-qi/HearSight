import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import FileUploader from "@/components/FileUploader"

interface UploadDialogProps {
  readonly open: boolean
  readonly onOpenChange: (open: boolean) => void
  readonly onUploadSuccess: (data: { static_url: string; is_audio: boolean; placeholder_url?: string }) => void
  readonly onUploadError: (message: string) => void
}

function UploadDialog({ open, onOpenChange, onUploadSuccess, onUploadError }: UploadDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>上传视频或音频文件</DialogTitle>
        </DialogHeader>
        <FileUploader onUploadSuccess={onUploadSuccess} onUploadError={onUploadError} />
      </DialogContent>
    </Dialog>
  )
}

export default UploadDialog
