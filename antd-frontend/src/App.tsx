import { useEffect, useRef, useState } from 'react'
import { useLocation } from 'react-router-dom'
import './index.css'
import { Layout, Tag, message } from 'antd'
import { usePanelResize, useUrlHandler, useVideoSync, useDataLoader } from './hooks'
import LeftPanel from './components/LeftPanel'
import VideoPlayer from './components/VideoPlayer'
import RightPanel from './components/RightPanel'
import HeaderToolbar from './components/HeaderToolbar'
import UrlResultBar from './components/UrlResultBar'

const { Header, Footer } = Layout

// 创建一个全局变量来存储从HomePage传递的URL
let pendingUrl: string | null = null;

// 提供一个函数来设置待处理的URL
export const setPendingUrl = (url: string | null) => {
  pendingUrl = url;
};

function App() {
  const location = useLocation()
  const [autoScroll, setAutoScroll] = useState<boolean>(true) // 默认开启自动滚动
  
  // 全屏布局状态
  const [leftPanelVisible, setLeftPanelVisible] = useState(window.innerWidth > 768) // 在移动端默认隐藏左侧面板
  const [rightPanelVisible, setRightPanelVisible] = useState(window.innerWidth > 768) // 在移动端默认隐藏右侧面板
  
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

  // 响应式面板控制
  useEffect(() => {
    const handleResize = () => {
      const isDesktop = window.innerWidth > 768;
      if (isDesktop) {
        // 桌面端：显示面板
        setLeftPanelVisible(true);
        setRightPanelVisible(true);
      } else {
        // 移动端：隐藏面板
        setLeftPanelVisible(false);
        setRightPanelVisible(false);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);
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

  // 检查是否有待处理的URL
  useEffect(() => {
    if (pendingUrl) {
      setUrl(pendingUrl);
      message.info('URL已加载，请点击"解析"按钮开始处理');
      pendingUrl = null; // 清除待处理的URL
    }
  }, [setUrl]);

  // 窗口大小变化时更新最大宽度
  useEffect(() => {
    const handleResize = () => {
      // 注意：这里需要更新usePanelResize钩子来处理最大宽度变化
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // 处理表单提交（适配Ant Design Form的onFinish回调）
  const handleUrlSubmit = (values?: any) => {
    if (!url.trim()) {
      message.warning('请输入视频链接');
      return;
    }
    submitUrl(url)
      .then(() => {
        message.success('任务已提交');
      })
      .catch((error) => {
        console.error('提交URL失败:', error);
        message.error('提交URL失败: ' + (error.message || '未知错误'));
      });
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
        <div 
          className={`fullscreen-left-panel ${leftPanelVisible ? 'visible' : ''}`}
          style={{ 
            width: leftPanelVisible ? leftPanelResize.width : 0,
            minWidth: leftPanelVisible ? leftPanelResize.width : 0,
            maxWidth: leftPanelVisible ? leftPanelResize.width : 0,
            transform: leftPanelVisible ? 'translateX(0)' : 'translateX(-100%)',
            opacity: leftPanelVisible ? 1 : 0
          }}
        >
          {/* 拖拽手柄 */}
          <div 
            className={`panel-resize-handle left ${leftPanelResize.isResizing ? 'dragging' : ''}`}
            onMouseDown={leftPanelResize.startResizing}
            tabIndex={0}
            role="separator"
            aria-label="调整左侧面板宽度"
            aria-orientation="vertical"
            onKeyDown={(e) => {
              if (e.key === 'ArrowLeft') {
                e.preventDefault();
                // 减少宽度
                const newWidth = Math.max(leftPanelResize.width - 20, 280);
                // 这里需要手动更新宽度，暂时简化处理
              } else if (e.key === 'ArrowRight') {
                e.preventDefault();
                // 增加宽度
                const newWidth = Math.min(leftPanelResize.width + 20, window.innerWidth * 0.5);
                // 这里需要手动更新宽度，暂时简化处理
              }
            }}
          />
          <div className="panel-header">
            <span>历史记录</span>
            <button 
              type="button" 
              className="close-button"
              onClick={() => setLeftPanelVisible(false)}
              aria-label="关闭历史记录面板"
            >
              ×
            </button>
          </div>
          <div className="panel-content" role="region" aria-label="历史记录面板内容">
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
        
        {/* 移动端遮罩 */}
        {(leftPanelVisible || rightPanelVisible) && window.innerWidth <= 768 && (
          <div 
            className="mobile-overlay visible"
            onClick={() => {
              setLeftPanelVisible(false);
              setRightPanelVisible(false);
            }}
          />
        )}

        {/* 左侧面板展开按钮 */}
        {!leftPanelVisible && (
          <button 
            className="panel-toggle-btn left"
            onClick={() => setLeftPanelVisible(true)}
            title="展开左侧面板"
            aria-label="展开历史记录面板"
            aria-expanded={leftPanelVisible}
          >
            ▶
          </button>
        )}

        {/* 移动端遮罩 */}
        {(leftPanelVisible || rightPanelVisible) && window.innerWidth <= 768 && (
          <div 
            className="mobile-overlay visible"
            onClick={() => {
              setLeftPanelVisible(false);
              setRightPanelVisible(false);
            }}
            role="presentation"
            aria-hidden="true"
          />
        )}

        {/* 主视频区域 */}
        <div 
          className={`fullscreen-main ${leftPanelVisible ? 'with-left' : ''} ${rightPanelVisible ? 'with-right' : ''}`}
          style={{ 
            minWidth: minVideoWidth
          }}
          role="main"
          aria-label="视频播放区域"
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
            aria-label="展开AI分析面板"
            aria-expanded={rightPanelVisible}
          >
            ◀
          </button>
        )}
        
        {/* 右侧面板 */}
        <div 
          className={`fullscreen-right-panel ${rightPanelVisible ? 'visible' : ''}`}
          style={{ 
            width: rightPanelVisible ? rightPanelResize.width : 0,
            minWidth: rightPanelVisible ? rightPanelResize.width : 0,
            maxWidth: rightPanelVisible ? rightPanelResize.width : 0,
            transform: rightPanelVisible ? 'translateX(0)' : 'translateX(100%)',
            opacity: rightPanelVisible ? 1 : 0
          }}
        >
          {/* 拖拽手柄 */}
          <div 
            className={`panel-resize-handle right ${rightPanelResize.isResizing ? 'dragging' : ''}`}
            onMouseDown={rightPanelResize.startResizing}
            tabIndex={0}
            role="separator"
            aria-label="调整右侧面板宽度"
            aria-orientation="vertical"
            onKeyDown={(e) => {
              if (e.key === 'ArrowLeft') {
                e.preventDefault();
                // 减少宽度
              } else if (e.key === 'ArrowRight') {
                e.preventDefault();
                // 增加宽度
              }
            }}
          />
          <div className="panel-header">
            <span>AI</span>
            <button 
              type="button" 
              className="close-button"
              onClick={() => setRightPanelVisible(false)}
              aria-label="关闭AI分析面板"
            >
              ×
            </button>
          </div>
          <div className="panel-content" role="region" aria-label="AI分析面板内容">
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