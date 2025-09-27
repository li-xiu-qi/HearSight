import { useEffect, useRef, useState } from 'react'
import { useLocation } from 'react-router-dom'
import './index.css'
import { Layout, Typography, Button, Form, Input, Space, Alert, Tag, message } from 'antd'
import { MenuOutlined, CloseOutlined, SearchOutlined, ReloadOutlined, LeftOutlined, RightOutlined } from '@ant-design/icons'
import { extractFilename, seekVideoTo, parseBilibiliUrl } from './utils'
import { fetchJobs, fetchTranscripts, fetchTranscriptDetail, createJob } from './services/api'
import type { Segment, TranscriptMeta, JobItem, ParseResult } from './types'
import LeftPanel from './components/LeftPanel'
import VideoPlayer from './components/VideoPlayer'
import RightPanel from './components/RightPanel'

const { Header, Footer } = Layout
const { Title } = Typography

function App() {
  const location = useLocation()
  const [segments, setSegments] = useState<Array<Segment>>([])
  const [loading, setLoading] = useState(false)
  const [transcripts, setTranscripts] = useState<Array<TranscriptMeta>>([])
  const [jobs, setJobs] = useState<Array<JobItem>>([])
  const [videoSrc, setVideoSrc] = useState<string | null>(null)
  const [activeSegIndex, setActiveSegIndex] = useState<number | null>(null)
  const [activeTranscriptId, setActiveTranscriptId] = useState<number | null>(null)
  const [autoScroll, setAutoScroll] = useState<boolean>(true) // 默认开启自动滚动
  
  // 全屏布局状态
  const [leftPanelVisible, setLeftPanelVisible] = useState(true) // 默认显示历史记录面板
  const [rightPanelVisible, setRightPanelVisible] = useState(true) // 默认显示右侧面板
  const [url, setUrl] = useState('')
  const [urlError, setUrlError] = useState<string | null>(null)
  const [urlResult, setUrlResult] = useState<ParseResult | null>(null)
  const [submitting, setSubmitting] = useState(false)
  
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const segScrollRef = useRef<HTMLDivElement | null>(null)
  const histScrollRef = useRef<HTMLDivElement | null>(null)
  const prevActiveRef = useRef<number | null>(null)

  // 获取转写记录列表
  const loadTranscripts = async () => {
    try {
      const data = await fetchTranscripts()
      setTranscripts(Array.isArray(data.items) ? data.items : [])
    } catch (err: any) {
      console.error('获取转写记录失败:', err?.message || err)
    }
  }

  // 获取任务队列
  const loadJobs = async () => {
    try {
      const data = await fetchJobs()
      setJobs(data.items)
    } catch (err: any) {
      console.warn('获取任务队列失败:', err?.message || err)
    }
  }

  // 加载转写记录详情
  const loadTranscriptDetail = async (id: number) => {
    try {
      setLoading(true)
      const data = await fetchTranscriptDetail(id)
      const basename = extractFilename(data.media_path)
      if (basename) {
        setVideoSrc(`/static/${basename}`)
      }
      setSegments(Array.isArray(data.segments) ? data.segments : [])
      setActiveTranscriptId(id)
    } catch (err: any) {
      console.error('获取转写记录详情失败:', err?.message || err)
    } finally {
      setLoading(false)
    }
  }

  // 视频跳转
  const handleSeekTo = (timeMs: number) => {
    seekVideoTo(videoRef.current, timeMs)
  }

  // 处理URL提交
  const handleUrlSubmit = async () => {
    setUrlError(null)
    setUrlResult(null)
    
    const parsed = parseBilibiliUrl(url)
    if ('error' in parsed) {
      setUrlError(parsed.error)
      setUrlResult(parsed)
    } else {
      setUrlResult(parsed)
      try {
        setSubmitting(true)
        const data = await createJob(url)
        if (data && typeof data.job_id === 'number') {
          message.success(`任务已创建：#${data.job_id}`)
          // 立即刷新任务队列，避免等待下次轮询
          loadJobs()
        } else {
          message.warning('任务创建返回异常')
        }
      } catch (e: any) {
        setUrlError(e?.message || '创建任务出错')
        message.error(e?.message || '创建任务出错')
      } finally {
        setSubmitting(false)
      }
    }
  }

  // 清除URL输入
  const handleUrlClear = () => {
    setUrl('')
    setUrlError(null)
    setUrlResult(null)
  }

  // 当 activeTranscriptId 改变时，让历史列表滚动到该项
  useEffect(() => {
    if (activeTranscriptId == null) return
    const el = histScrollRef.current?.querySelector(`[data-transcript-id="${activeTranscriptId}"]`) as HTMLElement | null
    if (el) {
      try { 
        el.scrollIntoView({ behavior: 'smooth', block: 'center' }) 
      } catch { 
        el.scrollIntoView() 
      }
    }
  }, [activeTranscriptId])

  // 根据视频播放进度自动高亮对应分句并让其滚动到可见区域
  useEffect(() => {
    const v = videoRef.current
    if (!v) return

    const onTimeUpdate = () => {
      const ms = (v.currentTime || 0) * 1000
      let newIndex: number | null = null
      for (const s of segments) {
        const st = Number(s.start_time) || 0
        const et = Number(s.end_time) || 0
        if (ms >= st && ms < et) {
          newIndex = s.index
          break
        }
      }

      if (prevActiveRef.current !== newIndex) {
        prevActiveRef.current = newIndex
        setActiveSegIndex(newIndex)
        // 仅在开启自动滚动时让分句滚动到可见区域
        if (autoScroll && newIndex != null && segScrollRef.current) {
          // segScrollRef.current 现在直接指向 .segments-scroll 容器
          const scrollContainer = segScrollRef.current
          if (scrollContainer) {
            const el = scrollContainer.querySelector(`[data-seg-index="${newIndex}"]`) as HTMLElement | null
            if (el) {
              try { 
                el.scrollIntoView({ behavior: 'smooth', block: 'center' }) 
              } catch {}
            }
          } else {
            console.warn('自动滚动：未找到 .segments-scroll 容器')
          }
        }
      }
    }

    v.addEventListener('timeupdate', onTimeUpdate)
    return () => v.removeEventListener('timeupdate', onTimeUpdate)
  }, [segments, autoScroll])

  // 定期获取数据
  useEffect(() => {
    void loadTranscripts()
    const timer = setInterval(() => { void loadTranscripts() }, 5000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    void loadJobs()
    const timer = setInterval(() => { void loadJobs() }, 5000)
    return () => clearInterval(timer)
  }, [])

  // 检查URL参数，如果有的话自动加载视频
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search)
    const videoUrl = searchParams.get('url')
    if (videoUrl) {
      setUrl(videoUrl)
      // 可以在这里自动提交URL
      // handleUrlSubmit()
    }
  }, [location])

  return (
    <Layout className="fullscreen-layout">
      {/* 顶部工具栏 */}
      <Header className="fullscreen-header">
        <div className="header-left">
          <Title level={3} style={{ margin: 0, color: 'white' }}>HearSight</Title>
        </div>
        
        <div className="header-center">
          <Form layout="inline" onFinish={handleUrlSubmit}>
            <Form.Item style={{ marginBottom: 0 }}>
              <Input
                allowClear
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="请输入 bilibili.com 链接"
                style={{ width: 300 }}
              />
            </Form.Item>
            <Form.Item style={{ marginBottom: 0 }}>
              <Space>
                <Button type="primary" htmlType="submit" icon={<SearchOutlined />} loading={submitting}>
                  解析
                </Button>
                <Button icon={<ReloadOutlined />} onClick={handleUrlClear}>
                  清空
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </div>
        
        <div className="header-right">
          <Space>
            <Button 
              type={leftPanelVisible ? 'primary' : 'default'}
              icon={<LeftOutlined />}
              onClick={() => setLeftPanelVisible(!leftPanelVisible)}
            >
              历史记录
            </Button>
            <Button 
              type={rightPanelVisible ? 'primary' : 'default'}
              icon={<RightOutlined />}
              onClick={() => setRightPanelVisible(!rightPanelVisible)}
            >
              分句总结
            </Button>
          </Space>
        </div>
      </Header>
      
      {/* URL解析结果提示 */}
      {(urlError || urlResult) && (
        <div className="url-result-bar">
          {urlError && <Alert type="error" message={urlError} showIcon closable onClose={() => setUrlError(null)} />}
          {urlResult && !('error' in urlResult) && (
            <Alert
              type="success"
              message={`解析成功：${urlResult.kind} - ${urlResult.id}`}
              showIcon
              closable
              onClose={() => setUrlResult(null)}
            />
          )}
        </div>
      )}
      
      {/* 主内容区域 */}
      <div className="fullscreen-content">
        {/* 左侧面板 */}
        {leftPanelVisible && (
          <div className="fullscreen-left-panel">
            <div className="panel-header">
              <span>历史记录</span>
              <Button 
                type="text" 
                icon={<CloseOutlined />} 
                onClick={() => setLeftPanelVisible(false)}
                size="small"
              />
            </div>
            <div className="panel-content">
              <LeftPanel
                transcripts={transcripts}
                jobs={jobs}
                activeTranscriptId={activeTranscriptId}
                onLoadTranscript={loadTranscriptDetail}
                onJobsUpdate={loadJobs}
                onTranscriptsUpdate={loadTranscripts}
              />
            </div>
          </div>
        )}
        
        {/* 左侧面板展开按钮 */}
        {!leftPanelVisible && (
          <button 
            className="panel-toggle-btn left"
            onClick={() => setLeftPanelVisible(true)}
            title="展开左侧面板"
          >
            <RightOutlined />
          </button>
        )}
        
        {/* 主视频区域 */}
        <div className={`fullscreen-main ${leftPanelVisible ? 'with-left' : ''} ${rightPanelVisible ? 'with-right' : ''}`}>
          <VideoPlayer
            ref={videoRef}
            videoSrc={videoSrc}
            loading={loading}
          />
        </div>
        
        {/* 右侧面板展开按钮 */}
        {!rightPanelVisible && (
          <button 
            className="panel-toggle-btn right"
            onClick={() => setRightPanelVisible(true)}
            title="展开右侧面板"
          >
            <LeftOutlined />
          </button>
        )}
        
        {/* 右侧面板 */}
        {rightPanelVisible && (
          <div className="fullscreen-right-panel">
            <div className="panel-header">
              <span>分句与总结</span>
              <Button 
                type="text" 
                icon={<CloseOutlined />} 
                onClick={() => setRightPanelVisible(false)}
                size="small"
              />
            </div>
            <div className="panel-content">
              <RightPanel
                ref={segScrollRef}
                segments={segments}
                activeSegIndex={activeSegIndex}
                autoScroll={autoScroll}
                onSeekTo={handleSeekTo}
                onActiveSegmentChange={setActiveSegIndex}
                onAutoScrollChange={setAutoScroll}
              />
            </div>
          </div>
        )}
      </div>
      
      {/* 底部状态栏 */}
      <Footer className="fullscreen-footer">
        <div className="footer-content">
          <span>HearSight</span>
          {videoSrc && <Tag color="green">视频已加载</Tag>}
          {loading && <Tag color="blue">处理中...</Tag>}
          {segments.length > 0 && <Tag>{segments.length} 个分句</Tag>}
        </div>
      </Footer>
    </Layout>
  )
}

export default App
