import React from 'react'
import { Modal, Input, List, Empty, Button } from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import type { Segment } from '../../types'
import { formatTime } from '../../utils'
import './styles/SearchModal.css'

interface SearchModalProps {
  visible: boolean
  searchTerm: string
  searchResults: Segment[]
  onSearchTermChange: (term: string) => void
  onSearch: () => void
  onClose: () => void
  onJumpToResult: (segment: Segment) => void
}

const SearchModal: React.FC<SearchModalProps> = ({
  visible,
  searchTerm,
  searchResults,
  onSearchTermChange,
  onSearch,
  onClose,
  onJumpToResult
}) => {
  return (
    <Modal
      title="搜索分句"
      open={visible}
      onCancel={onClose}
      footer={null}
      width={600}
    >
      <div style={{ marginBottom: 16 }}>
        <Input
          placeholder="输入要搜索的关键词"
          value={searchTerm}
          onChange={(e) => onSearchTermChange(e.target.value)}
          onPressEnter={onSearch}
          suffix={
            <Button 
              type="primary" 
              icon={<SearchOutlined />} 
              size="small" 
              onClick={onSearch}
            />
          }
        />
      </div>
      
      {searchResults.length > 0 ? (
        <List
          bordered
          dataSource={searchResults}
          renderItem={(segment: Segment) => (
            <List.Item 
              style={{ cursor: 'pointer' }}
              onClick={() => onJumpToResult(segment)}
            >
              <div>
                <div style={{ marginBottom: 4 }}>
                  <span style={{ fontSize: 12, color: '#8c8c8c' }}>
                    {formatTime(segment.start_time)} ~ {formatTime(segment.end_time)}
                    {segment.spk_id && ` | SPK ${segment.spk_id}`}
                  </span>
                </div>
                <div>
                  {segment.sentence}
                </div>
              </div>
            </List.Item>
          )}
        />
      ) : searchTerm ? (
        <Empty description="未找到匹配的分句" />
      ) : null}
    </Modal>
  )
}

export default SearchModal