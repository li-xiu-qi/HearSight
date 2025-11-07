import { useEffect, useState } from "react"
import type { Segment } from "@/types"
import type { ChatMessage } from "../ChatView"
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
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [chatLoading, setChatLoading] = useState(false)
  const [chatError, setChatError] = useState<string | null>(null)
  const [translateDialogOpen, setTranslateDialogOpen] = useState(false)

  const {
    segmentsScrollRef,
    transcriptScrollRef,
    scrollUp,
    scrollDown,
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
    chatMessages,
    setChatMessages,
    chatLoading,
    setChatLoading,
    chatError,
    setChatError,
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
    scrollUp,
    scrollDown,
    centerActiveSegment,
    handleLoadSavedSummaries,
  }
}
