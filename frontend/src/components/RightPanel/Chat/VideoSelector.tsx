import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

interface VideoSelectorProps {
  readonly availableTranscripts: any[]
  readonly selectedTranscriptIds: number[]
  readonly onSelectionChange: (ids: number[]) => void
}

export default function VideoSelector({
  availableTranscripts,
  selectedTranscriptIds,
  onSelectionChange,
}: VideoSelectorProps) {
  const handleTranscriptChange = (value: string) => {
    const transcriptId = parseInt(value)
    if (selectedTranscriptIds.includes(transcriptId)) {
      onSelectionChange(selectedTranscriptIds.filter(id => id !== transcriptId))
    } else {
      onSelectionChange([...selectedTranscriptIds, transcriptId])
    }
  }

  const getFileName = (transcript: any) => {
    return transcript.video_path ?
      transcript.video_path.split(/[/\\]/).pop() :
      transcript.audio_path?.split(/[/\\]/).pop() || `视频 ${transcript.id}`
  }

  const getSelectedNames = () => {
    if (selectedTranscriptIds.length === 0) return "未选择视频"
    if (selectedTranscriptIds.length === 1) {
      const transcript = availableTranscripts.find(t => t.id === selectedTranscriptIds[0])
      return transcript ? getFileName(transcript) : "未知视频"
    }
    return `已选择 ${selectedTranscriptIds.length} 个视频`
  }

  return (
    <div className="space-y-2">
      <Label className="text-sm font-medium">选择用于问答的视频</Label>
      <div className="flex items-center gap-2">
        <Select onValueChange={handleTranscriptChange}>
          <SelectTrigger className="flex-1">
            <SelectValue placeholder={getSelectedNames()} />
          </SelectTrigger>
          <SelectContent>
            {availableTranscripts.map((transcript) => (
              <SelectItem 
                key={transcript.id} 
                value={transcript.id.toString()}
              >
                {getFileName(transcript)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <div className="text-sm text-slate-500">
          ({selectedTranscriptIds.length}/{availableTranscripts.length})
        </div>
      </div>
      {selectedTranscriptIds.length === 0 && (
        <p className="text-sm text-slate-500">未选择视频，将在全部视频范围内进行问答</p>
      )}
      {selectedTranscriptIds.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {selectedTranscriptIds.map(id => {
            const transcript = availableTranscripts.find(t => t.id === id)
            return transcript ? (
              <div 
                key={id} 
                className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded flex items-center"
              >
                <span className="max-w-[120px] truncate">{getFileName(transcript)}</span>
                <button 
                  onClick={() => onSelectionChange(selectedTranscriptIds.filter(selId => selId !== id))}
                  className="ml-1 hover:bg-blue-200 rounded-full w-4 h-4 flex items-center justify-center"
                >
                  ×
                </button>
              </div>
            ) : null
          })}
        </div>
      )}
    </div>
  )
}