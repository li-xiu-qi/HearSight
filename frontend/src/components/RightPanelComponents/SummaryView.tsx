import React from 'react'
import { List, Empty, Alert, Button, Space } from 'antd'
import type { Segment, Summary } from '../../types'
import { formatTime } from '../../utils'
import MarkdownRenderer from '../MarkdownRenderer'
import './styles/SummaryView.css'
import { PlayCircleOutlined } from '@ant-design/icons'

interface SummaryViewProps {
  summaries: Summary[]
  summariesLoading: boolean
  summariesError: string | null
  segments: Segment[]
  onGenerateSummary: () => void
  onSeekTo?: (timeMs: number) => void // 添加跳转到时间的回调函数
}

const SummaryView: React.FC<SummaryViewProps> = ({
  summaries,
  summariesLoading,
  summariesError,
  segments,
  onGenerateSummary,
  onSeekTo // 接收跳转到时间的回调函数
}) => {
  // 跳转到指定时间位置
  const handleJumpToTime = (timeMs: number) => {
    if (onSeekTo) {
      onSeekTo(timeMs)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: 0, height: '100%' }}>
      <div style={{ padding: 'var(--spacing-sm) var(--spacing-sm) var(--spacing-md) var(--spacing-sm)', borderBottom: '1px solid var(--color-border-light)' }}>
        <Button
          size="small"
          type="primary"
          onClick={onGenerateSummary}
          loading={summariesLoading}
        >
          生成总结
        </Button>
      </div>

      <div className="summaries-scroll" style={{ flex: 1, minHeight: 0, overflowY: 'auto', padding: 'var(--spacing-sm)' }}>
        {summariesLoading && <div>生成中，请稍候…</div>}
        {summariesError && <Alert type="error" message={summariesError} showIcon />}
        {!summariesLoading && !summariesError && summaries.length === 0 && (
          <div className="empty-state">
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} />
            <div className="empty-title">暂无内容总结</div>
            <div className="empty-description">
              点击上方的"生成总结"按钮，AI将为您分析视频内容并生成结构化摘要。
            </div>
          </div>
        )}
        {!summariesLoading && summaries.length > 0 && (
          <List
            itemLayout="vertical"
            dataSource={summaries}
            renderItem={(item: Summary) => (
              <List.Item>
                <List.Item.Meta
                  title={item.topic || '(无主题)'}
                  description={
                    <Space size="middle">
                      <span>时间: {formatTime(item.start_time || 0)} ~ {formatTime(item.end_time || 0)}</span>
                      {item.start_time !== undefined && (
                        <Button 
                          type="link" 
                          size="small" 
                          icon={<PlayCircleOutlined />}
                          onClick={() => handleJumpToTime(item.start_time!)}
                          style={{ padding: 0 }}
                        >
                          跳转到对应位置
                        </Button>
                      )}
                    </Space>
                  }
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
  )
}

export default SummaryView