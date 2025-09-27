import React, { useState, forwardRef, type ForwardedRef, useCallback, useRef, useEffect } from 'react'
import {
  Card,
  Tabs,
  Button,
  Space,
  Empty,
  List,
  Alert,
  Modal,
  Input,
} from 'antd'
import { 
  UpOutlined, 
  DownOutlined, 
  SyncOutlined, 
  PlayCircleOutlined,
  SearchOutlined
} from '@ant-design/icons'
import type { Segment, Summary } from '../types'
import { formatTime } from '../utils'
import { generateSummary } from '../services/api'
import MarkdownRenderer from './MarkdownRenderer'
import { 
  SummaryView, 
  ChatView,  // 添加ChatView导入
  SearchModal, 
  SegmentsToolbar, 
  TranscriptToolbar 
} from './RightPanelComponents'
import type { ChatMessage } from './RightPanelComponents/ChatView'
import './RightPanelComponents/styles/RightPanelComponents.css' // 添加导入CSS文件

interface RightPanelProps {
  segments: Segment[]
  activeSegIndex: number | null
  autoScroll: boolean
  onSeekTo: (timeMs: number) => void
  onActiveSegmentChange: (index: number) => void
  onAutoScrollChange: (enabled: boolean) => void
}

const RightPanel = forwardRef<HTMLDivElement, RightPanelProps>(
  ({ 
    segments, 
    activeSegIndex, 
    autoScroll, 
    onSeekTo, 
    onActiveSegmentChange, 
    onAutoScrollChange 
  }, ref: ForwardedRef<HTMLDivElement>) => {
  const [summaries, setSummaries] = useState<Summary[]>([])
    const [summariesLoading, setSummariesLoading] = useState(false)
    const [summariesError, setSummariesError] = useState<string | null>(null)
    const [searchModalVisible, setSearchModalVisible] = useState(false)
    const [searchTerm, setSearchTerm] = useState('')
    const [searchResults, setSearchResults] = useState<Segment[]>([])
  const [activeTab, setActiveTab] = useState<string>('segments')
  const transcriptScrollRef = useRef<HTMLDivElement | null>(null)
  
  // 添加ChatView的状态
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [chatLoading, setChatLoading] = useState(false)
  const [chatError, setChatError] = useState<string | null>(null)

  // 添加事件监听器处理时间跳转
  useEffect(() => {
    const handleSeekToTime = (event: CustomEvent) => {
      const timeMs = event.detail;
      if (onSeekTo) {
        onSeekTo(timeMs);
      }
    };

    // 添加事件监听器
    window.addEventListener('seekToTime', handleSeekToTime as EventListener);
    
    // 清理事件监听器
    return () => {
      window.removeEventListener('seekToTime', handleSeekToTime as EventListener);
    };
  }, [onSeekTo]);

    const handleGenerateSummary = async () => {
      setSummariesError(null)
      setSummaries([])
      
      if (!segments || segments.length === 0) {
        setSummariesError('没有可用的分句，请先打开某个转写记录')
        return
      }
      
      setSummariesLoading(true)
      try {
        const data = await generateSummary(segments)
        
        // 后端返回的是 { summaries: [...] } 格式
        let items: Summary[] = []
        if (data && Array.isArray(data.summaries)) {
          // 确保每个项目都有必要的字段
          items = data.summaries.map(item => ({
            topic: item.topic || '',
            summary: item.summary || '',
            start_time: item.start_time,
            end_time: item.end_time
          }))
        }

        setSummaries(items)
      } catch (err: any) {
        setSummariesError(err?.message || '调用总结接口失败')
      } finally {
        setSummariesLoading(false)
      }
    }

    const handleSegmentClick = (segment: Segment) => {
      onActiveSegmentChange(segment.index)
      onSeekTo(segment.start_time)
    }

    const scrollUp = () => {
      // 分句视图
      if (activeTab === 'segments') {
        if (!ref || typeof ref === 'function') return
        const scrollContainer = ref.current
        scrollContainer?.scrollBy({ top: -160, left: 0, behavior: 'smooth' })
        return
      }
      // 文稿视图
      if (activeTab === 'transcript') {
        const c = transcriptScrollRef.current
        c?.scrollBy({ top: -160, left: 0, behavior: 'smooth' })
      }
    }

    const scrollDown = () => {
      if (activeTab === 'segments') {
        if (!ref || typeof ref === 'function') return
        const scrollContainer = ref.current
        scrollContainer?.scrollBy({ top: 160, left: 0, behavior: 'smooth' })
        return
      }
      if (activeTab === 'transcript') {
        const c = transcriptScrollRef.current
        c?.scrollBy({ top: 160, left: 0, behavior: 'smooth' })
      }
    }

    const centerActiveSegment = () => {
      if (activeSegIndex == null) return
      // 根据当前 tab 选择滚动容器
      if (activeTab === 'segments') {
        if (!ref || typeof ref === 'function') return
        const scrollContainer = ref.current
        if (scrollContainer) {
          const el = scrollContainer.querySelector(`[data-seg-index="${activeSegIndex}"]`) as HTMLElement | null
          if (el) {
            try { el.scrollIntoView({ behavior: 'smooth', block: 'center' }) } catch {}
          }
        }
      } else if (activeTab === 'transcript') {
        const scrollContainer = transcriptScrollRef.current
        if (scrollContainer) {
          const el = scrollContainer.querySelector(`[data-seg-index="${activeSegIndex}"]`) as HTMLElement | null
          if (el) {
            try { el.scrollIntoView({ behavior: 'smooth', block: 'center' }) } catch {}
          }
        }
      }
    }

    // 当 activeSegIndex 或 tab / autoScroll 改变时，自动滚动文稿视图
    useEffect(() => {
      if (!autoScroll || activeSegIndex == null) return
      if (activeTab !== 'transcript') return
      const scrollContainer = transcriptScrollRef.current
      if (!scrollContainer) return
      const el = scrollContainer.querySelector(`[data-seg-index="${activeSegIndex}"]`) as HTMLElement | null
      if (el) {
        try { el.scrollIntoView({ behavior: 'smooth', block: 'center' }) } catch {}
      }
    }, [activeSegIndex, autoScroll, activeTab])

    // 打开搜索模态框
    const openSearchModal = () => {
      setSearchModalVisible(true)
      setSearchTerm('')
      setSearchResults([])
    }

    // 关闭搜索模态框
    const closeSearchModal = () => {
      setSearchModalVisible(false)
      setSearchTerm('')
      setSearchResults([])
    }

    // 执行搜索
    const performSearch = useCallback(() => {
      if (!searchTerm.trim()) {
        setSearchResults([])
        return
      }

      const term = searchTerm.toLowerCase().trim()
      const results = segments.filter(segment => 
        segment.sentence && segment.sentence.toLowerCase().includes(term)
      )

      setSearchResults(results)
    }, [searchTerm, segments])

    // 跳转到搜索结果
    const jumpToSearchResult = (segment: Segment) => {
      closeSearchModal()
      handleSegmentClick(segment)
    }

    return (
      <div className="fullscreen-right-panel-content">
        <Card 
          size="small" 
          className="right-grow-card" 
          bodyStyle={{ padding: 0, display: 'flex', flexDirection: 'column', minHeight: 0 }}
        >
          {/* 固定的Tabs导航栏 */}
          <div className="fixed-tabs-container">
            <Tabs
              size="small"
              activeKey={activeTab}
              style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}
              tabBarStyle={{ margin: 0 }}
              onChange={(key) => {
                setActiveTab(key)
                // ensure tab content gets a chance to layout; useful when TabPane was lazily rendered
                setTimeout(() => {
                  try {
                    if (ref && typeof ref !== 'function' && ref.current) {
                      // ref 现在直接指向 segments-scroll 容器
                      const segmentsScroll = ref.current
                      if (segmentsScroll) {
                        segmentsScroll.scrollTop = segmentsScroll.scrollTop
                      }
                    }
                  } catch {}
                }, 30)
              }}
            >
              <Tabs.TabPane tab="字幕分句" key="segments" forceRender />
              <Tabs.TabPane tab="文稿" key="transcript" forceRender />
              <Tabs.TabPane tab="总结" key="summaries" forceRender />
              <Tabs.TabPane tab="问答" key="chat" forceRender />  // 添加聊天Tab
            </Tabs>
          </div>
          
          {/* 固定的工具栏 */}
          <div className="fixed-toolbar-container">
            {activeTab === 'segments' && (
              <SegmentsToolbar
                onScrollUp={scrollUp}
                onScrollDown={scrollDown}
                onCenterActive={centerActiveSegment}
                onOpenSearch={openSearchModal}
                autoScroll={autoScroll}
                onAutoScrollChange={onAutoScrollChange}
              />
            )}
            {activeTab === 'transcript' && (
              <TranscriptToolbar
                onScrollUp={scrollUp}
                onScrollDown={scrollDown}
                onCenterActive={centerActiveSegment}
                onOpenSearch={openSearchModal}
                autoScroll={autoScroll}
                onAutoScrollChange={onAutoScrollChange}
              />
            )}
          </div>
          
          {/* 可滚动的内容区域 */}
          <div className="scrollable-content-container">
            {activeTab === 'segments' && (
              <div ref={ref} className="segments-scroll" style={{ flex: 1, minHeight: 0, overflowY: 'auto' }}>
                {segments.length === 0 ? (
                  <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无分句" />
                ) : (
                  <List
                    split={false}
                    dataSource={segments}
                    renderItem={(segment: Segment) => {
                      const isActive = activeSegIndex === segment.index
                      return (
                        <List.Item 
                          className="segment-item" 
                          style={{ paddingLeft: 0, paddingRight: 0 }} 
                          data-seg-index={segment.index}
                        >
                          <div
                            role="button"
                            tabIndex={0}
                            className={`segment-btn is-div ${isActive ? 'active' : ''}`}
                            onClick={() => handleSegmentClick(segment)}
                            title={`跳转到 ${formatTime(segment.start_time)} (${Math.floor(Number(segment.start_time) || 0)} ms)`}
                          >
                            <span className="segment-icon">
                              <PlayCircleOutlined />
                            </span>
                            <div className="seg-card">
                              <div className="seg-head">
                                <span className="seg-time">
                                  {formatTime(segment.start_time)}
                                  <span className="segment-time-sep">~</span>
                                  {formatTime(segment.end_time)}
                                </span>
                                {segment.spk_id && (
                                  <span className="seg-spk">SPK {segment.spk_id}</span>
                                )}
                              </div>
                              <div className="seg-body">{segment.sentence || '(空)'}</div>
                            </div>
                          </div>
                        </List.Item>
                      )
                    }}
                  />
                )}
              </div>
            )}
            
            {activeTab === 'transcript' && (
              <div ref={transcriptScrollRef} className="transcript-scroll" style={{ flex: 1, minHeight: 0, overflowY: 'auto' }}>
                {segments.length === 0 ? (
                  <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无内容" />
                ) : (
                  <div className="transcript-body">
                    {segments.map(seg => {
                      const isActive = activeSegIndex === seg.index
                      return (
                        <span
                          key={seg.index}
                          data-seg-index={seg.index}
                          onClick={() => handleSegmentClick(seg)}
                          className={`transcript-seg ${isActive ? 'active' : ''}`}
                        >
                          <span className="transcript-text">{seg.sentence || '(空)'}</span>
                        </span>
                      )
                    })}
                  </div>
                )}
              </div>
            )}
            
            {activeTab === 'summaries' && (
              <div className="summaries-scroll" style={{ flex: 1, minHeight: 0, overflowY: 'auto', padding: 8 }}>
                <SummaryView
                  summaries={summaries}
                  summariesLoading={summariesLoading}
                  summariesError={summariesError}
                  segments={segments}
                  onGenerateSummary={handleGenerateSummary}
                  onSeekTo={onSeekTo} // 添加跳转到时间的回调函数
                />
              </div>
            )}
            
            {activeTab === 'chat' && (  // 添加聊天Tab内容
              <div className="chat-scroll" style={{ flex: 1, minHeight: 0, overflowY: 'auto' }}>
                <ChatView
                  segments={segments}
                  messages={chatMessages}
                  loading={chatLoading}
                  error={chatError}
                  onMessagesChange={setChatMessages}
                  onLoadingChange={setChatLoading}
                  onErrorChange={setChatError}
                />
              </div>
            )}
          </div>
        </Card>

        <SearchModal
          visible={searchModalVisible}
          searchTerm={searchTerm}
          searchResults={searchResults}
          onSearchTermChange={setSearchTerm}
          onSearch={performSearch}
          onClose={closeSearchModal}
          onJumpToResult={jumpToSearchResult}
        />
      </div>
    )
  }
)

RightPanel.displayName = 'RightPanel'

export default RightPanel