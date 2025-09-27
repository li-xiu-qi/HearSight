import React from 'react'
import { Button, Space } from 'antd'
import { UpOutlined, DownOutlined, SyncOutlined, SearchOutlined } from '@ant-design/icons'
import './styles/SegmentsToolbar.css'

interface SegmentsToolbarProps {
  onScrollUp: () => void
  onScrollDown: () => void
  onCenterActive: () => void
  onOpenSearch: () => void
  autoScroll: boolean
  onAutoScrollChange: (enabled: boolean) => void
}

const SegmentsToolbar: React.FC<SegmentsToolbarProps> = ({
  onScrollUp,
  onScrollDown,
  onCenterActive,
  onOpenSearch,
  autoScroll,
  onAutoScrollChange
}) => {
  return (
    <div className="segments-toolbar">
      <div className="segments-toolbar-inner">
        <Button size="small" icon={<UpOutlined />} onClick={onScrollUp} />
        <Button size="small" icon={<DownOutlined />} onClick={onScrollDown} />
        <Button size="small" icon={<SyncOutlined />} onClick={onCenterActive}>
          定位
        </Button>
        <Button size="small" icon={<SearchOutlined />} onClick={onOpenSearch}>
          搜索
        </Button>
        <div style={{ flex: 1 }} />
        <div className="auto-scroll-group">
          <span className="toolbar-label">自动滚动</span>
          <Button
            size="small"
            type={autoScroll ? 'primary' : 'default'}
            onClick={() => onAutoScrollChange(!autoScroll)}
          >
            {autoScroll ? '开' : '关'}
          </Button>
        </div>
      </div>
    </div>
  )
}

export default SegmentsToolbar