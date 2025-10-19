import React from 'react'
import {
  Card,
  Empty,
  Tabs,
  List,
  Tag,
  Button,
  Typography,
  Dropdown,
  message,
} from 'antd'
import { MoreOutlined } from '@ant-design/icons'
import type { MenuProps } from 'antd'
import type { TranscriptMeta, JobItem } from '../types'
import { extractFilename } from '../utils'
import { deleteTranscriptComplete } from '../services/api'
import './RightPanelComponents/styles/HistoryView.css'

const { Text } = Typography

interface LeftPanelProps {
  transcripts: TranscriptMeta[]
  jobs: JobItem[]
  activeTranscriptId: number | null
  onLoadTranscript: (id: number) => void
  onJobsUpdate: () => void
  onTranscriptsUpdate: () => void  // 新增：用于刷新转写记录列表
}

const LeftPanel: React.FC<LeftPanelProps> = ({
  transcripts,
  jobs,
  activeTranscriptId,
  onLoadTranscript,
  onJobsUpdate,
  onTranscriptsUpdate,
}) => {

  // 删除转写记录（包含视频文件和数据库记录）
  const handleDeleteTranscript = (transcriptId: number, filename: string) => {
    console.log('开始删除操作:', { transcriptId, filename })
    
    // 直接执行删除，不使用确认对话框（临时测试）
    console.log('直接执行删除操作（测试模式）')
    
    deleteTranscriptComplete(transcriptId)
      .then(result => {
        console.log('删除结果:', result)
        if (result.success) {
          message.success(result.message || '删除成功')
          onTranscriptsUpdate() // 刷新列表
        } else {
          message.warning(result.message || '删除失败')
        }
      })
      .catch(error => {
        console.error('删除错误:', error)
        message.error(error?.message || '删除失败')
      })
  }

  return (
    <div className="fullscreen-left-panel-content">
      <Card 
        size="small" 
        className="left-grow-card" 
        styles={{ body: { padding: 0, display: 'flex', flexDirection: 'column', minHeight: 0 } }}
      >
        <Tabs 
          defaultActiveKey="processed" 
          size="small" 
          centered
          items={[
            {
              key: 'processed',
              label: '已处理',
              forceRender: true,
              children: (
                <div style={{ padding: 'var(--spacing-sm)', display: 'flex', flexDirection: 'column', minHeight: 0, flex: 1 }}>
                  {transcripts.length === 0 ? (
                    <div className="empty-state">
                      <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} />
                      <div className="empty-title">暂无处理记录</div>
                      <div className="empty-description">
                        您还没有处理过任何视频。在上方输入视频URL开始分析吧！
                      </div>
                    </div>
                  ) : (
                    <div className="hist-scroll">
                      <List
                        split={false}
                        size="small"
                        dataSource={transcripts}
                        renderItem={(item: TranscriptMeta) => {
                          const basename = extractFilename(item.media_path)
                          const isActive = activeTranscriptId === item.id
                          
                          // 下拉菜单项
                          const handleMenuClick = (key: string) => {
                            console.log('菜单点击事件触发:', key, { transcriptId: item.id, basename })
                            
                            if (key === 'deleteTranscript') {
                              console.log('准备执行删除操作')
                              handleDeleteTranscript(item.id, basename)
                            }
                          }
                          
                          const menuItems: MenuProps['items'] = [
                            {
                              key: 'deleteTranscript',
                              label: '删除记录',
                              danger: true,
                            },
                          ]
                          
                          return (
                            <List.Item 
                              className={`hist-item ${isActive ? 'hist-item-active' : ''}`} 
                              data-transcript-id={item.id}
                            >
                              <div className={`hist-main ${isActive ? 'hist-main-active' : ''}`}>
                                <div className="hist-row">
                                  <div 
                                    className="hist-title" 
                                    title={basename}
                                    style={{ cursor: 'pointer' }}
                                    onClick={() => onLoadTranscript(item.id)}
                                  >
                                    {basename}
                                  </div>
                                  <div className="hist-action-area">
                                    <Dropdown 
                                      menu={{ 
                                        items: menuItems,
                                        onClick: ({ key }) => {
                                          console.log('Dropdown onClick 触发:', key)
                                          handleMenuClick(key)
                                        }
                                      }}
                                      trigger={['click']}
                                      placement="bottomRight"
                                    >
                                      <Button 
                                        type="text" 
                                        size="small" 
                                        icon={<MoreOutlined />}
                                        onClick={(e) => {
                                          console.log('更多按钮被点击')
                                          e.stopPropagation()
                                          e.preventDefault()
                                        }}
                                      />
                                    </Dropdown>
                                  </div>
                                </div>
                                <div className="hist-meta">
                                  ID {item.id} · {item.segment_count} 段 · {item.created_at}
                                </div>
                              </div>
                            </List.Item>
                          )
                        }}
                      />
                    </div>
                  )}
                </div>
              )
            },
            {
              key: 'tasks',
              label: '处理情况',
              forceRender: true,
              children: (
                <div style={{ padding: 'var(--spacing-sm)' }}>
                  {jobs.length === 0 ? (
                    <div className="empty-state">
                      <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} />
                      <div className="empty-title">暂无处理任务</div>
                      <div className="empty-description">
                        当前没有正在处理的视频。提交视频URL后，处理进度会显示在这里。
                      </div>
                    </div>
                  ) : (
                    <div className="hist-scroll">
                      <List
                        split={false}
                        size="small"
                        dataSource={jobs}
                        renderItem={(item: JobItem) => {
                          const shortUrl = (item.url || '').replace(/^https?:\/\//, '')
                          const color = item.status === 'running' 
                            ? 'blue' 
                            : (item.status === 'pending' 
                              ? 'default' 
                              : (item.status === 'failed' ? 'red' : 'green'))
                          return (
                            <List.Item className="hist-item">
                              <div className="hist-main">
                                <div className="hist-row">
                                  <div className="hist-title" title={item.url}>
                                    {shortUrl}
                                  </div>
                                  <div className="hist-action-area">
                                    <Tag color={color}>{item.status}</Tag>
                                  </div>
                                </div>
                                <div className="hist-meta">
                                  # {item.id} · {item.created_at || item.started_at || ''}
                                </div>
                              </div>
                            </List.Item>
                          )
                        }}
                      />
                    </div>
                  )}
                </div>
              )
            }
          ]}
        />
      </Card>
    </div>
  )
}

export default LeftPanel