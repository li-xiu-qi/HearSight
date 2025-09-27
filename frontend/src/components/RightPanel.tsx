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
  SearchModal, 
  SegmentsToolbar, 
  TranscriptToolbar 
} from './RightPanelComponents'
import './RightPanelComponents/styles/RightPanelComponents.css'

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
        
        // 后端可能返回两种格式：直接的数组或 { summaries: [...] }
        let items: any[] = []
        if (Array.isArray(data)) {
          items = data
        } else if (Array.isArray(data.summaries)) {
          items = data.summaries
        }

        // 规范化每条 summary：若 summary 字段本身包含 code fence JSON 或是 JSON 字符串，解析并替换为真实 summary 字符串
        const normalize = (item: any) => {
          const result = { ...item }
          let s = String(result.summary || '')
          
          // 如果是代码块包裹（```json\n{...}```），提取内部并尝试解析 JSON
          const codeFenceMatch = s.match(/```(?:json)?\s*\n([\s\S]*)\n```/i)
          if (codeFenceMatch) {
            const inner = codeFenceMatch[1].trim()
            try {
              const obj = JSON.parse(inner)
              if (obj && typeof obj.summary === 'string') {
                result.summary = obj.summary
                if (!result.topic && obj.topic) result.topic = obj.topic
                return result
              }
              // 如果 obj 本身是字符串或其他，则回退为 inner
              result.summary = inner
              return result
            } catch (e) {
              // 解析失败则使用 inner 文本
              result.summary = inner
              return result
            }
          }

          // 如果 summary 看起来像一个 JSON 字符串（以 { 开头），尝试解析
          if (s.trim().startsWith('{')) {
            try {
              const obj = JSON.parse(s)
              if (obj && typeof obj.summary === 'string') {
                result.summary = obj.summary
                if (!result.topic && obj.topic) result.topic = obj.topic
              } else {
                // 如果不是期望结构，则转为漂亮的 JSON 文本
                result.summary = JSON.stringify(obj, null, 2)
              }
            } catch (e) {
              // ignore
            }
          }
          return result
        }

        setSummaries(items.map(normalize))
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
              <SummaryView
                summaries={summaries}
                summariesLoading={summariesLoading}
                summariesError={summariesError}
                segments={segments}
                onGenerateSummary={handleGenerateSummary}
              />
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