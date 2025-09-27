import { useEffect, useRef, useState } from 'react'
import { useLocation } from 'react-router-dom'
import './index.css'
import { Layout, Tag } from 'antd'
import { usePanelResize, useUrlHandler, useVideoSync, useDataLoader } from './hooks'
import LeftPanel from './components/LeftPanel'
import VideoPlayer from './components/VideoPlayer'
import RightPanel from './components/RightPanel'
import HeaderToolbar from './components/HeaderToolbar'
import UrlResultBar from './components/UrlResultBar'

const { Header, Footer } = Layout

function App() {
  const location = useLocation()
  const [autoScroll, setAutoScroll] = useState<boolean>(true) // 默认开启自动滚动
  
  // 全屏布局状态
  const [leftPanelVisible, setLeftPanelVisible] = useState(true) // 默认显示历史记录面板
  const [rightPanelVisible, setRightPanelVisible] = useState(true) // 默认显示右侧面板
  
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const segScrollRef = useRef<HTMLDivElement | null>(null)
  const histScrollRef = useRef<HTMLDivElement | null>(null)

  // 使用URL处理钩子
  const { 
    url, 
    setUrl, 
    urlError, 
    setUrlError,
    urlResult, 
    setUrlResult,
    submitting, 
    handleUrlSubmit: submitUrl, 
    handleUrlClear 
  } = useUrlHandler();

  // 使用数据加载钩子
  const { 
    segments, 
    loading, 
    transcripts, 
    jobs, 
    videoSrc, 
    activeTranscriptId, 
    loadTranscriptDetail, 
    loadJobs, 
    loadTranscripts,
    setVideoSrc,
    setActiveTranscriptId,
    setSegments
  } = useDataLoader();

  const [activeSegIndex, setActiveSegIndex] = useState<number | null>(null);
  const { handleSeekTo } = useVideoSync({
    segments,
    autoScroll,
    segScrollRef,
    setActiveSegIndex,
    videoRef
  });

  // 计算视频区域的最小宽度（视口宽度的30%）
  const minVideoWidth = window.innerWidth * 0.3;

  // 面板拖拽调整宽度
  const leftPanelResize = usePanelResize({
    initialWidth: 320,
    maxWidth: window.innerWidth * 0.5, // 最大宽度为视口宽度的50%
    minVideoWidth, // 传递视频最小宽度
    getSiblingPanelWidth: () => rightPanelVisible ? rightPanelResize.width : 0 // 获取兄弟面板宽度
  });

  const rightPanelResize = usePanelResize({
    initialWidth: 320,
    maxWidth: window.innerWidth * 0.5, // 最大宽度为视口宽度的50%
    isRightPanel: true, // 指定为右侧面板
    minVideoWidth, // 传递视频最小宽度
    getSiblingPanelWidth: () => leftPanelVisible ? leftPanelResize.width : 0 // 获取兄弟面板宽度
  });

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

  // 检查URL参数，如果有的话自动加载视频
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search)
    const videoUrl = searchParams.get('url')
    if (videoUrl) {
      setUrl(videoUrl)
      // 可以在这里自动提交URL
      // handleUrlSubmit()
    }
  }, [location, setUrl])

  // 窗口大小变化时更新最大宽度
  useEffect(() => {
    const handleResize = () => {
      // 注意：这里需要更新usePanelResize钩子来处理最大宽度变化
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const handleUrlSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    submitUrl(url);
  };

  return (
    <Layout className="fullscreen-layout">
      {/* 顶部工具栏 */}
      <Header className="fullscreen-header">
        <HeaderToolbar
          url={url}
          setUrl={setUrl}
          submitting={submitting}
          handleUrlSubmit={handleUrlSubmit}
          handleUrlClear={handleUrlClear}
          leftPanelVisible={leftPanelVisible}
          rightPanelVisible={rightPanelVisible}
          setLeftPanelVisible={setLeftPanelVisible}
          setRightPanelVisible={setRightPanelVisible}
        />
      </Header>
      
      {/* URL解析结果提示 */}
      <UrlResultBar
        urlError={urlError}
        urlResult={urlResult}
        setUrlError={setUrlError}
        setUrlResult={setUrlResult}
      />
      
      {/* 主内容区域 */}
      <div className="fullscreen-content">
        {/* 左侧面板 */}
        {leftPanelVisible && (
          <div 
            className="fullscreen-left-panel"
            style={{ 
              width: leftPanelResize.width,
              minWidth: leftPanelResize.width,
              maxWidth: leftPanelResize.width
            }}
          >
            {/* 拖拽手柄 */}
            <div 
              className="panel-resize-handle left"
              onMouseDown={leftPanelResize.startResizing}
            />
            <div className="panel-header">
              <span>历史记录</span>
              <button 
                type="button" 
                className="close-button"
                onClick={() => setLeftPanelVisible(false)}
              >
                ×
              </button>
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
            ▶
          </button>
        )}
        
        {/* 主视频区域 */}
        <div 
          className={`fullscreen-main ${leftPanelVisible ? 'with-left' : ''} ${rightPanelVisible ? 'with-right' : ''}`}
          style={{ 
            minWidth: minVideoWidth
          }}
        >
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
            ◀
          </button>
        )}
        
        {/* 右侧面板 */}
        {rightPanelVisible && (
          <div 
            className="fullscreen-right-panel"
            style={{ 
              width: rightPanelResize.width,
              minWidth: rightPanelResize.width,
              maxWidth: rightPanelResize.width
            }}
          >
            {/* 拖拽手柄 */}
            <div 
              className="panel-resize-handle right"
              onMouseDown={rightPanelResize.startResizing}
            />
            <div className="panel-header">
              <span>AI</span>
              <button 
                type="button" 
                className="close-button"
                onClick={() => setRightPanelVisible(false)}
              >
                ×
              </button>
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