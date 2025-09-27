import React from 'react'
import { List, Empty, Alert, Button } from 'antd'
import type { Segment, Summary } from '../../types'
import { formatTime } from '../../utils'
import MarkdownRenderer from '../MarkdownRenderer'
import './styles/SummaryView.css'

interface SummaryViewProps {
  summaries: Summary[]
  summariesLoading: boolean
  summariesError: string | null
  segments: Segment[]
  onGenerateSummary: () => void
}

const SummaryView: React.FC<SummaryViewProps> = ({
  summaries,
  summariesLoading,
  summariesError,
  segments,
  onGenerateSummary
}) => {
  return (
    <div style={{ padding: 8, display: 'flex', flexDirection: 'column', minHeight: 0, flex: 1 }}>
      <Button
        size="small"
        type="primary"
        onClick={onGenerateSummary}
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
  )
}

export default SummaryView