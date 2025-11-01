export interface TranslateProgress {
  status: 'idle' | 'detecting' | 'translating' | 'done' | 'error'
  progress: number
  message: string
  detectionInfo?: string
  targetLanguage?: string
  newTranscriptId?: number
}
