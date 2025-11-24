import { forwardRef, useEffect, useImperativeHandle } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import type { Segment } from "@/types"
import SessionBasedChat from "./SessionBasedChat"
import SegmentsTab from "./SegmentsTab"
import TranscriptTab from "./TranscriptTab"
import SummariesTab from "./SummariesTab"
import TabToolbar from "./TabToolbar"
import SearchDialog from "./SearchDialog"
import TranslateDialog from "./TranslateDialog"
import TranslateProgressPanel from "./TranslateProgressPanel"
import { useRightPanelController } from "./hooks"

type ScrollElement = HTMLDivElement | null

interface RightPanelProps {
  readonly segments: Segment[]
  readonly activeSegIndex: number | null
  readonly autoScroll: boolean
  readonly onSeekTo: (timeMs: number, transcriptId?: number) => void
  readonly onActiveSegmentChange: (index: number) => void
  readonly transcriptId?: number
  readonly mediaType?: string
  readonly onTranslateComplete?: () => void
}

const RightPanel = forwardRef<ScrollElement, RightPanelProps>(
  ({ segments, activeSegIndex, autoScroll, onSeekTo, onActiveSegmentChange, transcriptId, mediaType, onTranslateComplete }, ref) => {
    const {
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
      segmentsScrollRef,
      transcriptScrollRef,
      centerActiveSegment,
      availableTranscripts,
    } = useRightPanelController({
      segments,
      onActiveSegmentChange,
      onSeekTo,
      transcriptId,
      onTranslateComplete,
    })

    useImperativeHandle<HTMLDivElement | null, HTMLDivElement | null>(
      ref,
      () => segmentsScrollRef.current,
      [segmentsScrollRef]
    )

    useEffect(() => {
      if (!autoScroll || activeSegIndex == null || activeTab !== "transcript") {
        return
      }
      // 对于TranscriptTab，使用ScrollArea，需要找到正确的滚动容器
      const scrollContainer = transcriptScrollRef.current?.querySelector('[data-radix-scroll-area-viewport]') as HTMLElement | null
      const element = scrollContainer?.querySelector(
        `[data-seg-index="${activeSegIndex}"]`
      ) as HTMLElement | null
      if (element && scrollContainer) {
        // 计算元素相对于滚动容器的位置
        const elementRect = element.getBoundingClientRect()
        const containerRect = scrollContainer.getBoundingClientRect()
        const scrollTop = scrollContainer.scrollTop
        const elementTop = elementRect.top - containerRect.top + scrollTop
        const containerHeight = scrollContainer.clientHeight
        const targetScrollTop = elementTop - containerHeight / 2 + element.offsetHeight / 2

        scrollContainer.scrollTo({
          top: targetScrollTop,
          behavior: 'smooth'
        })
      }
    }, [activeSegIndex, autoScroll, activeTab, transcriptScrollRef])

    return (
      <div className="h-[90vh] flex flex-col overflow-hidden">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col gap-0 overflow-hidden">
          <div className="flex-shrink-0">
            <TabsList className="w-full justify-start rounded-none border-b">
              <TabsTrigger value="segments">字幕分句</TabsTrigger>
              <TabsTrigger value="transcript">文稿</TabsTrigger>
              <TabsTrigger value="summaries">总结</TabsTrigger>
              <TabsTrigger value="chat">问答</TabsTrigger>
            </TabsList>
          </div>

          {(activeTab === "segments" || activeTab === "transcript") && (
            <TabToolbar
              onCenterActive={() => centerActiveSegment(activeSegIndex, activeTab)}
              onOpenSearch={() => setSearchModalOpen(true)}
              onOpenTranslate={() => setTranslateDialogOpen(true)}
              segments={displaySegments}
              displayLanguage={displayLanguage}
              availableLanguages={availableLanguages}
              onLanguageChange={switchLanguage}
              getLanguageName={getLanguageName}
            />
          )}

          <div className="flex-1 min-h-0">
            <TabsContent value="segments" className="h-full m-0 data-[state=inactive]:hidden">
              <SegmentsTab
                ref={segmentsScrollRef}
                segments={displaySegments}
                activeSegIndex={activeSegIndex}
                onSegmentClick={handleSegmentClick}
                displayLanguage={displayLanguage}
              />
            </TabsContent>

            <TabsContent value="transcript" className="h-full m-0 data-[state=inactive]:hidden">
              <TranscriptTab
                ref={transcriptScrollRef}
                segments={displaySegments}
                activeSegIndex={activeSegIndex}
                onSegmentClick={handleSegmentClick}
                displayLanguage={displayLanguage}
              />
            </TabsContent>

            <TabsContent value="summaries" className="h-full m-0 data-[state=inactive]:hidden">
              <SummariesTab
                summaries={summaries}
                loading={summariesLoading}
                error={summariesError}
                onGenerate={triggerSummaryGeneration}
                onSeekTo={onSeekTo}
                transcriptId={transcriptId}
                hasSavedSummaries={hasSavedSummaries}
                mediaType={mediaType}
              />
            </TabsContent>

            <TabsContent value="chat" className="h-full m-0 data-[state=inactive]:hidden">
              <SessionBasedChat availableTranscripts={availableTranscripts} mediaType={mediaType} currentTranscriptId={transcriptId} onSeekTo={onSeekTo} />
            </TabsContent>
          </div>
        </Tabs>

        <SearchDialog
          open={searchModalOpen}
          onOpenChange={setSearchModalOpen}
          searchTerm={searchTerm}
          onSearchTermChange={setSearchTerm}
          onSubmit={executeSearch}
          results={searchResults}
          onSelect={(segment) => {
            handleSegmentClick(segment)
            setSearchModalOpen(false)
          }}
          displayLanguage={displayLanguage}
        />

        <TranslateDialog
          open={translateDialogOpen}
          onOpenChange={setTranslateDialogOpen}
          transcriptId={transcriptId}
          segments={segments}
          onStartTranslate={(language, forceRetranslate) => handleStartTranslate(transcriptId, language, forceRetranslate)}
          isTranslating={translateProgress.status === "translating"}
        />

        {showProgressPanel && (
          <TranslateProgressPanel
            state={translateProgress}
            onClose={() => setShowProgressPanel(false)}
            onRetry={() => handleRetryTranslate(transcriptId)}
          />
        )}
      </div>
    )
  }
)

RightPanel.displayName = "RightPanel"

export default RightPanel
