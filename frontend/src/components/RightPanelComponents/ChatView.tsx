import React, { useState, useRef, useEffect } from 'react'
import { Input, Button, List, Avatar, Space, Alert, Spin } from 'antd'
import { SendOutlined, PlayCircleOutlined, DeleteOutlined } from '@ant-design/icons'
import type { Segment, ChatResponse } from '../../types'  // 使用type导入
import { chatWithSegments } from '../../services/api'  // 只导入函数
import { formatTime } from '../../utils'
import MarkdownRenderer from '../MarkdownRenderer'
import './styles/ChatView.css'

interface ChatViewProps {
    segments: Segment[]
    messages?: ChatMessage[]
    loading?: boolean
    error?: string | null
    onMessagesChange?: (messages: ChatMessage[]) => void
    onLoadingChange?: (loading: boolean) => void
    onErrorChange?: (error: string | null) => void
}

export interface ChatMessage {
    id: string
    type: 'user' | 'ai'
    content: string
    timestamp: number
}

const ChatView: React.FC<ChatViewProps> = ({ 
    segments,
    messages: externalMessages,
    loading: externalLoading,
    error: externalError,
    onMessagesChange,
    onLoadingChange,
    onErrorChange
}) => {
    const [inputValue, setInputValue] = useState('')
    const [internalMessages, setInternalMessages] = useState<ChatMessage[]>([])
    const [internalLoading, setInternalLoading] = useState(false)
    const [internalError, setInternalError] = useState<string | null>(null)
    const messagesEndRef = useRef<HTMLDivElement>(null)
    
    // 使用外部状态或内部状态
    const messages = externalMessages !== undefined ? externalMessages : internalMessages
    const loading = externalLoading !== undefined ? externalLoading : internalLoading
    const error = externalError !== undefined ? externalError : internalError
    
    // 设置状态的函数
    const setMessages = onMessagesChange || setInternalMessages
    const setLoading = onLoadingChange || setInternalLoading
    const setError = onErrorChange || setInternalError

    // 滚动到底部
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages])

    const handleSend = async () => {
        if (!inputValue.trim() || loading) return

        // 添加用户消息
        const userMessage: ChatMessage = {
            id: `user-${Date.now()}`,
            type: 'user',
            content: inputValue,
            timestamp: Date.now()
        }

        // 确保正确更新消息状态
        const newMessages = [...messages, userMessage];
        setMessages(newMessages);
        setInputValue('')
        
        // 设置加载状态
        setLoading(true)
        setError(null)

        try {
            // 调用后端API
            const response: ChatResponse = await chatWithSegments(segments, inputValue)

            // 添加AI回复
            const aiMessage: ChatMessage = {
                id: `ai-${Date.now()}`,
                type: 'ai',
                content: response.answer || '抱歉，我没有理解您的问题。',
                timestamp: Date.now()
            }

            // 确保正确更新消息状态
            setMessages([...newMessages, aiMessage])
        } catch (err: any) {
            setError(err?.message || '聊天失败，请稍后重试')
            // 添加错误消息
            const errorMessage: ChatMessage = {
                id: `error-${Date.now()}`,
                type: 'ai',
                content: '抱歉，回答失败，请稍后重试。',
                timestamp: Date.now()
            }
            setMessages([...newMessages, errorMessage])
        } finally {
            setLoading(false)
        }
    }

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            handleSend()
        }
    }

    // 解析内容中的时间戳并生成跳转函数
    const renderMessageContent = (content: string) => {
        // 匹配时间戳格式 [数字-数字] 或 [数字.数字-数字.数字]，支持多位数字
        const timeRegex = /\[(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)\]/g
        const parts = content.split(/(\[\d+(?:\.\d+)?-\d+(?:\.\d+)?\])/g)
        
        return parts.map((part, index) => {
            const timeMatch = part.match(/\[(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)\]/)
            if (timeMatch) {
                const startTime = parseFloat(timeMatch[1])
                const endTime = parseFloat(timeMatch[2])
                // 后端返回的时间已经是以毫秒为单位，直接使用
                const startTimeMs = startTime
                const endTimeMs = endTime
                return (
                    <Space key={index} size="middle">
                        <Button 
                            type="link" 
                            size="small" 
                            icon={<PlayCircleOutlined />}
                            onClick={() => {
                                // 跳转到对应时间的逻辑
                                window.dispatchEvent(new CustomEvent('seekToTime', { detail: startTimeMs }))
                            }}
                            style={{ padding: 0 }}
                            title={`时间: ${formatTime(startTimeMs)} ~ ${formatTime(endTimeMs)}`} // 鼠标悬浮时显示时间信息
                        >
                            跳转到对应位置
                        </Button>
                    </Space>
                )
            }
            // 对于非时间戳部分，使用MarkdownRenderer渲染，并保持与总结部分一致的样式
            return (
                <span key={index} className="chat-markdown-content">
                    <MarkdownRenderer>{part}</MarkdownRenderer>
                </span>
            )
        })
    }

    // 清空对话历史
    const handleClearChat = () => {
        setMessages([])
        if (onErrorChange) {
            setError(null)
        } else {
            setError(null)
        }
    }

    return (
        <div className="chat-container">
            {error && <Alert type="error" message={error} showIcon style={{ marginBottom: 8 }} />}

            <div className="messages-container">
                {messages.length === 0 ? (
                    <div className="empty-chat">
                        <p>欢迎使用视频内容问答功能</p>
                        <p>请输入您的问题，AI将基于视频字幕内容为您解答</p>
                    </div>
                ) : (
                    // 修改这里，添加头像来区分用户和AI消息
                    <div className="messages-content">
                        {messages.map((message) => (
                            <div key={message.id} className={`message-item ${message.type}`}>
                                <Avatar
                                    size="small"
                                    style={{
                                        backgroundColor: message.type === 'user' ? '#1890ff' : '#52c41a',
                                        marginRight: 8,
                                        verticalAlign: 'middle'
                                    }}
                                >
                                    {message.type === 'user' ? '我' : 'AI'}
                                </Avatar>
                                <span className="message-content">
                                    {renderMessageContent(message.content)}
                                </span>
                            </div>
                        ))}
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <div className="input-container">
                <div className="clear-chat-button">
                    <Button 
                        icon={<DeleteOutlined />}
                        onClick={handleClearChat}
                        disabled={messages.length === 0}
                        size="small"
                    >
                        清空对话
                    </Button>
                </div>
                <Input.TextArea
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onPressEnter={handleKeyPress}
                    placeholder="请输入您的问题..."
                    autoSize={{ minRows: 2, maxRows: 4 }}
                    disabled={loading}
                />
                <Button
                    type="primary"
                    icon={<SendOutlined />}
                    onClick={handleSend}
                    loading={loading}
                    disabled={!inputValue.trim() || loading}
                    style={{ marginTop: 8 }}
                >
                    发送
                </Button>
            </div>
        </div>
    )
}

export default ChatView