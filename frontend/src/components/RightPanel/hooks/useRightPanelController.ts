import { useEffect, useState } from "react"
import type { Segment, TranscriptMeta } from "@/types"
import type { ChatMessage } from "../ChatView"
import { fetchTranscripts } from "@/services/transcriptService"
import {
  useScrollHandlers,
  useSegmentHandlers,
  useSearchHandlers,
  useSummaryHandlers,
  useTranslateHandlers,
  useLanguageSwitch,
} from "."
import { useTranslationLanguages } from "./useTranslationLanguages"

interface UseRightPanelControllerParams {
  readonly segments: Segment[]
  readonly onActiveSegmentChange: (index: number) => void
  readonly onSeekTo: (timeMs: number) => void
  readonly transcriptId?: number
  readonly onTranslateComplete?: () => void
}

export const useRightPanelController = ({
  segments,
  onActiveSegmentChange,
  onSeekTo,
  transcriptId,
  onTranslateComplete,
}: UseRightPanelControllerParams) => {
  const [activeTab, setActiveTab] = useState("segments")
  const [searchModalOpen, setSearchModalOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState("")
  const [searchResults, setSearchResults] = useState<Segment[]>([])
  const [displaySegments, setDisplaySegments] = useState<Segment[]>(segments)
  const [translateDialogOpen, setTranslateDialogOpen] = useState(false)
  const [availableTranscripts, setAvailableTranscripts] = useState<TranscriptMeta[]>([])

  const {
    segmentsScrollRef,
    transcriptScrollRef,
    centerActiveSegment,
  } = useScrollHandlers()
  const { handleSegmentClick } = useSegmentHandlers(onActiveSegmentChange, onSeekTo)
  const { performSearch } = useSearchHandlers(displaySegments)
  const {
    summaries,
    summariesLoading,
    summariesError,
    handleGenerateSummary,
    handleLoadSavedSummaries,
    hasSavedSummaries,
  } = useSummaryHandlers()
  const {
    displayLanguage,
    availableLanguages,
    getLanguageName,
    addLanguage,
    switchLanguage,
  } = useLanguageSwitch()
  const {
    translateProgress,
    showProgressPanel,
    setShowProgressPanel,
    handleStartTranslate,
    handleRetryTranslate,
    hasSavedTranslations,
    savedLanguages,
    loadSavedTranslations,
  } = useTranslateHandlers(
    onTranslateComplete,
    (updatedSegments, targetLanguage) => {
      setDisplaySegments(updatedSegments)
      if (targetLanguage && targetLanguage.trim()) {
        addLanguage(targetLanguage)
        switchLanguage(targetLanguage)
      }
    }
  )

  useEffect(() => {
    setDisplaySegments(segments)
  }, [segments])

  // 加载可用的转写记录
  useEffect(() => {
    const loadTranscripts = async () => {
      try {
        const response = await fetchTranscripts()
        setAvailableTranscripts(response.items)
      } catch (error) {
        console.error('加载转写记录失败:', error)
      }
    }
    loadTranscripts()
  }, [])

  // 当 transcriptId 变化时自动加载已保存的总结
  useEffect(() => {
    if (!transcriptId) {
      return
    }
    handleLoadSavedSummaries(transcriptId)
  }, [transcriptId, handleLoadSavedSummaries])

  useTranslationLanguages({ segments, addLanguage })

  const executeSearch = () => {
    const results = performSearch(searchTerm, displayLanguage)
    setSearchResults(results)
  }

  const triggerSummaryGeneration = () => {
    if (!transcriptId) {
      console.warn('Transcript ID is missing')
      return
    }
    handleGenerateSummary(displaySegments, transcriptId)
  }

  return {
    activeTab,
    setActiveTab,
    searchModalOpen,
    setSearchModalOpen,
    searchTerm,
    setSearchTerm,
    searchResults,
    executeSearch,
    displaySegments,
    handleSegmentClick,
    summaries,
    summariesLoading,
    summariesError,
    triggerSummaryGeneration,
    hasSavedSummaries,
    translateDialogOpen,
    setTranslateDialogOpen,
    displayLanguage,
    availableLanguages,
    getLanguageName,
    switchLanguage,
    translateProgress,
    showProgressPanel,
    setShowProgressPanel,
    handleStartTranslate,
    handleRetryTranslate,
    hasSavedTranslations,
    savedLanguages,
    loadSavedTranslations,
    segmentsScrollRef,
    transcriptScrollRef,
    centerActiveSegment,
    handleLoadSavedSummaries,
    availableTranscripts,
  }
}
