import { useRef, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Upload, X, FileVideo, FileAudio, Loader2 } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'

interface FileUploaderProps {
  onUploadSuccess: (data: { static_url: string; is_audio: boolean; placeholder_url?: string }) => void
  onUploadError: (error: string) => void
}

const FileUploader = ({ onUploadSuccess, onUploadError }: FileUploaderProps) => {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const isVideoFile = (fileName: string) => {
    const ext = fileName.toLowerCase().split('.').pop()
    return ['mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv', 'webm'].includes(ext || '')
  }

  const isAudioFile = (fileName: string) => {
    const ext = fileName.toLowerCase().split('.').pop()
    return ['mp3', 'wav', 'm4a', 'aac', 'flac', 'ogg', 'wma'].includes(ext || '')
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      if (isVideoFile(selectedFile.name) || isAudioFile(selectedFile.name)) {
        setFile(selectedFile)
      } else {
        onUploadError('不支持的文件格式，请上传视频或音频文件')
      }
    }
  }

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    const droppedFile = e.dataTransfer.files?.[0]
    if (droppedFile) {
      if (isVideoFile(droppedFile.name) || isAudioFile(droppedFile.name)) {
        setFile(droppedFile)
      } else {
        onUploadError('不支持的文件格式，请上传视频或音频文件')
      }
    }
  }

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: '上传失败' }))
        throw new Error(errorData.detail || '上传失败')
      }

      const result = await response.json()
      if (result.success) {
        onUploadSuccess(result.data)
        setFile(null)
        if (fileInputRef.current) {
          fileInputRef.current.value = ''
        }
      } else {
        throw new Error(result.message || '上传失败')
      }
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : '上传失败'
      onUploadError(errorMessage)
    } finally {
      setUploading(false)
    }
  }

  const handleRemove = () => {
    setFile(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
  }

  return (
    <Card className="w-full">
      <CardContent className="p-4">
        <div
          className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
            dragActive ? 'border-primary bg-primary/5' : 'border-slate-300 hover:border-slate-400'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          {!file ? (
            <div className="space-y-3">
              <div className="flex justify-center">
                <Upload className="h-10 w-10 text-slate-400" />
              </div>
              <div>
                <p className="text-sm text-slate-700 font-medium mb-1">
                  拖拽文件到此处或点击选择
                </p>
                <p className="text-xs text-slate-500">
                  支持视频格式: MP4, AVI, MOV, MKV等<br />
                  支持音频格式: MP3, WAV, M4A, AAC等
                </p>
              </div>
              <Button
                type="button"
                variant="outline"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
              >
                <Upload className="mr-2 h-4 w-4" />
                选择文件
              </Button>
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                accept="video/*,audio/*"
                onChange={handleFileChange}
              />
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center justify-center">
                {isVideoFile(file.name) ? (
                  <FileVideo className="h-10 w-10 text-blue-500" />
                ) : (
                  <FileAudio className="h-10 w-10 text-purple-500" />
                )}
              </div>
              <div>
                <p className="text-sm font-medium text-slate-700 mb-1">{file.name}</p>
                <p className="text-xs text-slate-500">{formatFileSize(file.size)}</p>
              </div>
              <div className="flex justify-center gap-2">
                <Button
                  onClick={handleUpload}
                  disabled={uploading}
                  size="sm"
                >
                  {uploading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      上传中
                    </>
                  ) : (
                    <>
                      <Upload className="mr-2 h-4 w-4" />
                      开始上传
                    </>
                  )}
                </Button>
                <Button
                  variant="outline"
                  onClick={handleRemove}
                  disabled={uploading}
                  size="sm"
                >
                  <X className="mr-2 h-4 w-4" />
                  移除
                </Button>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

export default FileUploader
