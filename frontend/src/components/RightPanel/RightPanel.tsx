import {
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
} from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import type { Segment, Summary } from "../../types"
import { generateSummary } from "../../services/api"
import ChatView, { type ChatMessage } from "./ChatView"
import SegmentsTab from "./SegmentsTab"
import TranscriptTab from "./TranscriptTab"
import SummariesTab from "./SummariesTab"
import TabToolbar from "./TabToolbar"
import SearchDialog from "./SearchDialog"

type ScrollElement = HTMLDivElement | null

interface RightPanelProps {
  readonly segments: Segment[]
  readonly activeSegIndex: number | null
  readonly autoScroll: boolean
  readonly onSeekTo: (timeMs: number) => void
  readonly onActiveSegmentChange: (index: number) => void
  readonly transcriptId?: number
}

const RightPanel = forwardRef<ScrollElement, RightPanelProps>(
  ({ segments, activeSegIndex, autoScroll, onSeekTo, onActiveSegmentChange, transcriptId }, ref) => {
    const [activeTab, setActiveTab] = useState("segments")
    const [searchModalOpen, setSearchModalOpen] = useState(false)
    const [searchTerm, setSearchTerm] = useState("")
    const [searchResults, setSearchResults] = useState<Segment[]>([])
    const [summaries, setSummaries] = useState<Summary[]>([])
    const [summariesLoading, setSummariesLoading] = useState(false)
    const [summariesError, setSummariesError] = useState<string | null>(null)
    const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
    const [chatLoading, setChatLoading] = useState(false)
    const [chatError, setChatError] = useState<string | null>(null)

    const segmentsScrollRef = useRef<HTMLDivElement | null>(null)
    const transcriptScrollRef = useRef<HTMLDivElement | null>(null)

    useImperativeHandle<HTMLDivElement | null, HTMLDivElement | null>(
      ref,
      () => segmentsScrollRef.current,
      []
    )

    const handleSegmentClick = (segment: Segment) => {
      onActiveSegmentChange(segment.index)
      onSeekTo(segment.start_time)
    }

    const scrollUp = () => {
      if (activeTab === "segments") {
        segmentsScrollRef.current?.scrollBy({ top: -160, behavior: "smooth" })
      } else if (activeTab === "transcript") {
        transcriptScrollRef.current?.scrollBy({ top: -160, behavior: "smooth" })
      }
    }

    const scrollDown = () => {
      if (activeTab === "segments") {
        segmentsScrollRef.current?.scrollBy({ top: 160, behavior: "smooth" })
      } else if (activeTab === "transcript") {
        transcriptScrollRef.current?.scrollBy({ top: 160, behavior: "smooth" })
      }
    }

    const centerActiveSegment = () => {
      if (activeSegIndex == null) return
      if (activeTab === "segments") {
        const el = segmentsScrollRef.current?.querySelector(
          `[data-seg-index="${activeSegIndex}"]`
        ) as HTMLElement | null
        el?.scrollIntoView({ behavior: "smooth", block: "center" })
      } else if (activeTab === "transcript") {
        const el = transcriptScrollRef.current?.querySelector(
          `[data-seg-index="${activeSegIndex}"]`
        ) as HTMLElement | null
        el?.scrollIntoView({ behavior: "smooth", block: "center" })
      }
    }

    const performSearch = useCallback(() => {
      if (!searchTerm.trim()) {
        setSearchResults([])
        return
      }
      const term = searchTerm.toLowerCase()
      const results = segments.filter((seg) => seg.sentence?.toLowerCase().includes(term))
      setSearchResults(results)
    }, [searchTerm, segments])

    const handleGenerateSummary = async () => {
      setSummariesError(null)
      setSummaries([])

      if (segments.length === 0) {
        setSummariesError("没有可用分句")
        return
      }

      setSummariesLoading(true)
      try {
        const data = await generateSummary(segments)
        const items = Array.isArray(data.summaries) ? data.summaries : []
        setSummaries(items)
      } catch (err: unknown) {
        setSummariesError((err as Error)?.message || "调用总结接口失败")
      } finally {
        setSummariesLoading(false)
      }
    }

    useEffect(() => {
      if (!autoScroll || activeSegIndex == null || activeTab !== "transcript") return
      const el = transcriptScrollRef.current?.querySelector(
        `[data-seg-index="${activeSegIndex}"]`
      ) as HTMLElement | null
      el?.scrollIntoView({ behavior: "smooth", block: "center" })
    }, [activeSegIndex, autoScroll, activeTab])

    return (
      <div className="h-full flex flex-col overflow-hidden">
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
              onScrollUp={scrollUp}
              onScrollDown={scrollDown}
              onCenterActive={centerActiveSegment}
              onOpenSearch={() => setSearchModalOpen(true)}
              segments={segments}
            />
          )}

          <div className="flex-1 min-h-0 overflow-hidden">
            <TabsContent value="segments" className="h-full m-0 data-[state=inactive]:hidden">
              <SegmentsTab
                ref={segmentsScrollRef}
                segments={segments}
                activeSegIndex={activeSegIndex}
                onSegmentClick={handleSegmentClick}
              />
            </TabsContent>

            <TabsContent value="transcript" className="h-full m-0 data-[state=inactive]:hidden">
              <TranscriptTab
                ref={transcriptScrollRef}
                segments={segments}
                activeSegIndex={activeSegIndex}
                onSegmentClick={handleSegmentClick}
              />
            </TabsContent>

            <TabsContent value="summaries" className="h-full m-0 data-[state=inactive]:hidden">
              <SummariesTab
                summaries={summaries}
                loading={summariesLoading}
                error={summariesError}
                onGenerate={handleGenerateSummary}
                onSeekTo={onSeekTo}
                transcriptId={transcriptId}
              />
            </TabsContent>

            <TabsContent value="chat" className="h-full m-0 data-[state=inactive]:hidden">
              <ChatView
                segments={segments}
                messages={chatMessages}
                loading={chatLoading}
                error={chatError}
                onMessagesChange={setChatMessages}
                onLoadingChange={setChatLoading}
                onErrorChange={setChatError}
                transcriptId={transcriptId}
              />
            </TabsContent>
          </div>
        </Tabs>

        <SearchDialog
          open={searchModalOpen}
          onOpenChange={setSearchModalOpen}
          searchTerm={searchTerm}
          onSearchTermChange={setSearchTerm}
          onSubmit={performSearch}
          results={searchResults}
          onSelect={(segment) => {
            handleSegmentClick(segment)
            setSearchModalOpen(false)
          }}
        />
      </div>
    )
  }
)

RightPanel.displayName = "RightPanel"

export default RightPanel
