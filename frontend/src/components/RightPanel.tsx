import React, { useState, forwardRef, type ForwardedRef } from 'react'
import {
  Card,
  Tabs,
  Button,
  Space,
  Empty,
  List,
  Alert,
} from 'antd'
import { 
  UpOutlined, 
  DownOutlined, 
  SyncOutlined, 
  PlayCircleOutlined 
} from '@ant-design/icons'
import type { Segment, Summary } from '../types'
import { formatTime } from '../utils'
import { generateSummary } from '../services/api'
import MarkdownRenderer from './MarkdownRenderer'

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
      if (!ref || typeof ref === 'function') return
      // ref 现在直接指向 segments-scroll 容器
      const scrollContainer = ref.current
      if (scrollContainer) {
        scrollContainer.scrollBy({ top: -160, left: 0, behavior: 'smooth' })
      }
    }

    const scrollDown = () => {
      if (!ref || typeof ref === 'function') return
      // ref 现在直接指向 segments-scroll 容器
      const scrollContainer = ref.current
      if (scrollContainer) {
        scrollContainer.scrollBy({ top: 160, left: 0, behavior: 'smooth' })
      }
    }

    const centerActiveSegment = () => {
      if (!ref || typeof ref === 'function' || activeSegIndex == null) return
      // ref 现在直接指向 segments-scroll 容器
      const scrollContainer = ref.current
      if (scrollContainer) {
        const el = scrollContainer.querySelector(`[data-seg-index="${activeSegIndex}"]`) as HTMLElement | null
        if (el) {
          try { 
            el.scrollIntoView({ behavior: 'smooth', block: 'center' }) 
          } catch {
            // fallback for older browsers
          }
        }
      }
    }

    return (
      <div className="fullscreen-right-panel-content">
        <Card 
          size="small" 
          className="right-grow-card" 
          bodyStyle={{ padding: 0, display: 'flex', flexDirection: 'column', minHeight: 0 }}
        >
          <Tabs
            size="small"
            defaultActiveKey="segments"
            style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}
            tabBarStyle={{ position: 'relative', zIndex: 60 }}
            onChange={(_key) => {
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
              <Tabs.TabPane tab="分句（点击跳转）" key="segments" forceRender>
                <div style={{ padding: 8, display: 'flex', flexDirection: 'column', minHeight: 0, flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                    <Button size="small" icon={<UpOutlined />} onClick={scrollUp} />
                    <Button size="small" icon={<DownOutlined />} onClick={scrollDown} />
                    <Button size="small" icon={<SyncOutlined />} onClick={centerActiveSegment}>
                      定位
                    </Button>
                    <div style={{ flex: 1 }} />
                    <Space>
                      <span style={{ color: '#8c8c8c', fontSize: 12 }}>自动滚动</span>
                      <Button 
                        size="small" 
                        type={autoScroll ? 'primary' : 'default'} 
                        onClick={() => onAutoScrollChange(!autoScroll)}
                      >
                        {autoScroll ? '开' : '关'}
                      </Button>
                    </Space>
                  </div>
                  <div className="segments-scroll" ref={ref}>
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
                </div>
              </Tabs.TabPane>
              <Tabs.TabPane tab="总结" key="summaries" forceRender>
                <div style={{ padding: 8, display: 'flex', flexDirection: 'column', minHeight: 0, flex: 1 }}>
                  <Button
                    size="small"
                    type="primary"
                    onClick={handleGenerateSummary}
                    loading={summariesLoading}
                  >
                    生成总结
                  </Button>

                  <div style={{ marginTop: 8 }}>
                    {summariesLoading && <div>生成中，请稍候…</div>}
                    {summariesError && <Alert type="error" message={summariesError} showIcon />}
                    {!summariesLoading && !summariesError && summaries.length === 0 && (
                      <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无总结，点击上方按钮生成" />
                    )}
                    {!summariesLoading && summaries.length > 0 && (
                      <List
                        itemLayout="vertical"
                        dataSource={summaries}
                        renderItem={(item: Summary) => (
                          <List.Item>
                            <List.Item.Meta
                              title={item.topic || '(无主题)'}
                              description={`时间: ${formatTime(item.start_time || 0)} ~ ${formatTime(item.end_time || 0)}`}
                            />
                            <div style={{ whiteSpace: 'pre-wrap' }}>
                              <MarkdownRenderer>{item.summary || ''}</MarkdownRenderer>
                            </div>
                          </List.Item>
                        )}
                      />
                    )}
                  </div>
                </div>
              </Tabs.TabPane>
          </Tabs>
        </Card>
      </div>
    )
  }
)

RightPanel.displayName = 'RightPanel'

export default RightPanel