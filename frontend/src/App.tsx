import { useEffect, useRef, useState } from 'react'
import './index.css'
import {
  Layout,
  Typography,
  Form,
  Input,
  Button,
  Space,
  Card,
  List,
  Alert,
  Tag,
  Empty,
  message,
  Tabs,
} from 'antd'
import { PlayCircleOutlined, ReloadOutlined, SearchOutlined, UpOutlined, DownOutlined, SyncOutlined, UploadOutlined } from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'

const { Header, Footer } = Layout
const { Title, Text } = Typography

function App() {
  const [url, setUrl] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<
    | { kind: 'BV' | 'av' | 'ep' | 'ss' | 'md'; id: string }
    | null
  >(null)
  const [videoSrc, setVideoSrc] = useState<string | null>(null)
  type Segment = {
    index: number
    spk_id: string | null
    sentence: string
    start_time: number
    end_time: number
  }

  const fetchJobs = async () => {
    try {
      const [p1, p2] = await Promise.all([
        fetch('/api/jobs?status=pending&limit=50&offset=0'),
        fetch('/api/jobs?status=running&limit=50&offset=0'),
      ])
      if (!p1.ok) throw new Error(`获取待处理任务失败：${p1.status}`)
      if (!p2.ok) throw new Error(`获取进行中任务失败：${p2.status}`)
      const j1 = await p1.json()
      const j2 = await p2.json()
      const items: JobItem[] = [
        ...(Array.isArray(j1.items) ? j1.items : []),
        ...(Array.isArray(j2.items) ? j2.items : []),
      ]
      // 去重并按 id 升序/创建时间升序方便观察排队
      const map = new Map<number, JobItem>()
      for (const it of items) map.set(Number(it.id), it)
      const arr = Array.from(map.values()).sort((a, b) => Number(a.id) - Number(b.id))
      setJobs(arr)
    } catch (err: any) {
      // 仅记录，不打断 UI
      console.warn(err?.message || err)
    }
  }

  

  
  type TranscriptMeta = { id: number; media_path: string; created_at: string; segment_count: number }
  type JobItem = {
    id: number
    url: string
    status: 'pending' | 'running' | 'success' | 'failed' | string
    created_at?: string | null
    started_at?: string | null
    finished_at?: string | null
    result?: any
    error?: string | null
  }

  const [segments, setSegments] = useState<Array<Segment>>([])
  const [summaries, setSummaries] = useState<Array<any>>([])
  const [summariesLoading, setSummariesLoading] = useState(false)
  const [summariesError, setSummariesError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [transcripts, setTranscripts] = useState<Array<TranscriptMeta>>([])
  const [jobs, setJobs] = useState<Array<JobItem>>([])
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const segScrollRef = useRef<HTMLDivElement | null>(null)
  const histScrollRef = useRef<HTMLDivElement | null>(null)
  const [activeSegIndex, setActiveSegIndex] = useState<number | null>(null)
  const [activeTranscriptId, setActiveTranscriptId] = useState<number | null>(null)
  const [autoScroll, setAutoScroll] = useState<boolean>(false)
  const [submitting, setSubmitting] = useState(false)
  const prevActiveRef = useRef<number | null>(null)

  // 侧边栏固定显示（已移除折叠逻辑）

  const parseBilibiliUrl = (input: string) => {
    const trimmed = input.trim()
    if (!trimmed) return { error: '请输入链接' as const }

    if (!/^https?:\/\/(www\.)?bilibili\.com\//i.test(trimmed)) {
      return { error: '仅支持 bilibili.com 域名的链接' as const }
    }

    const mBV = trimmed.match(/\/video\/(BV[0-9A-Za-z]+)/)
    if (mBV) return { kind: 'BV' as const, id: mBV[1] }

    const mAv = trimmed.match(/\/video\/(av\d+)/)
    if (mAv) return { kind: 'av' as const, id: mAv[1] }

    const mEp = trimmed.match(/\/bangumi\/play\/(ep\d+)/)
    if (mEp) return { kind: 'ep' as const, id: mEp[1] }

    const mSs = trimmed.match(/\/bangumi\/play\/(ss\d+)/)
    if (mSs) return { kind: 'ss' as const, id: mSs[1] }

    const mMd = trimmed.match(/\/bangumi\/media\/(md\d+)/)
    if (mMd) return { kind: 'md' as const, id: mMd[1] }

    return { error: '未能从链接中解析出 BV/av/ep/ss/md 信息，请检查链接是否正确' as const }
  }

  const handleSubmit = async () => {
    setError(null)
    setResult(null)
    setSegments([])
    setVideoSrc(null)
    const parsed = parseBilibiliUrl(url)
    if ('error' in parsed) {
      setError(parsed.error ?? '解析失败')
    } else {
      setResult(parsed)
      try {
        setSubmitting(true)
        const resp = await fetch('/api/jobs', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url })
        })
        if (!resp.ok) throw new Error(`创建任务失败：${resp.status}`)
        const data = await resp.json()
        if (data && typeof data.job_id === 'number') {
          message.success(`任务已创建：#${data.job_id}`)
          // 立即刷新任务队列，避免等待下次轮询
          void fetchJobs()
        } else {
          message.warning('任务创建返回异常')
        }
      } catch (e: any) {
        setError(e?.message || '创建任务出错')
        message.error(e?.message || '创建任务出错')
      } finally {
        setSubmitting(false)
      }
    }
  }

  

  const fetchTranscripts = async () => {
    try {
      const resp = await fetch('/api/transcripts?limit=50&offset=0')
      if (!resp.ok) throw new Error(`获取列表失败：${resp.status}`)
      const data = await resp.json()
      setTranscripts(Array.isArray(data.items) ? data.items : [])
    } catch (err: any) {
      setError(err?.message || '获取列表出错')
    } finally {
      // no-op
    }
  }

  const loadTranscriptDetail = async (id: number) => {
    try {
      setLoading(true)
      const resp = await fetch(`/api/transcripts/${id}`)
      if (!resp.ok) throw new Error(`获取详情失败：${resp.status}`)
      const data = await resp.json()
      const basename = data.media_path?.split('\\').pop()?.split('/').pop()
      if (basename) setVideoSrc(`/static/${basename}`)
      setSegments(Array.isArray(data.segments) ? data.segments : [])
      // mark this transcript as active in the history list
      setActiveTranscriptId(id)
    } catch (err: any) {
      setError(err?.message || '获取详情出错')
    } finally {
      setLoading(false)
    }
  }

  // 当 activeTranscriptId 改变时，让历史列表滚动到该项
  useEffect(() => {
    if (activeTranscriptId == null) return
    const el = histScrollRef.current?.querySelector(`[data-transcript-id="${activeTranscriptId}"]`) as HTMLElement | null
    if (el) {
      try { el.scrollIntoView({ behavior: 'smooth', block: 'center' }) } catch { el.scrollIntoView() }
    }
  }, [activeTranscriptId])

  // fmtTime: 接受毫秒为输入，返回 mm:ss 格式
  const fmtTime = (ms: number) => {
  // 统一将传入值视为毫秒（ms）并转换为秒用于显示
  const msec = Math.max(0, Math.floor(Number(ms) || 0))
  const totalSec = Math.floor(msec / 1000)
  const m2 = Math.floor(totalSec / 60)
  const s2 = Math.floor(totalSec % 60)
  const mm = String(m2).padStart(2, '0')
  const ss = String(s2).padStart(2, '0')
  return `${mm}:${ss}`
  }

  const seekTo = (t: number) => {
    const v = videoRef.current
    if (!v) return
    // 统一把传入时间当作毫秒(ms)，转换为秒供 video.currentTime 使用
    let targetMs = Math.max(0, Number(t) || 0)
    let target = targetMs / 1000
    // 就绪前先等待元数据，避免设置 currentTime 失败
    if (!isFinite(v.duration) || v.readyState < 1) {
      const handler = () => {
        const dur = isFinite(v.duration) ? v.duration : undefined
        if (dur) target = Math.min(Math.max(0, target), Math.max(0, dur - 0.05))
        if (typeof (v as any).fastSeek === 'function') {
          try { (v as any).fastSeek(target) } catch { v.currentTime = target }
        } else {
          v.currentTime = target
        }
        void v.play()
      }
      v.addEventListener('loadedmetadata', handler, { once: true } as any)
      return
    }
    // 元数据已就绪，优先使用 fastSeek
    const dur = isFinite(v.duration) ? v.duration : undefined
    if (dur) target = Math.min(Math.max(0, target), Math.max(0, dur - 0.05))
    if (typeof (v as any).fastSeek === 'function') {
      try { (v as any).fastSeek(target) } catch { v.currentTime = target }
    } else {
      if (Math.abs(v.currentTime - target) > 0.03) {
        v.currentTime = target
      }
    }
    void v.play()
  }

  useEffect(() => {
    void fetchTranscripts()
    const timer = setInterval(() => { void fetchTranscripts() }, 5000)
    return () => clearInterval(timer)
  }, [])

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
          const el = segScrollRef.current.querySelector(`[data-seg-index="${newIndex}"]`) as HTMLElement | null
          if (el) {
            try { el.scrollIntoView({ behavior: 'smooth', block: 'center' }) } catch {}
          }
        }
      }
    }

    v.addEventListener('timeupdate', onTimeUpdate)
    return () => v.removeEventListener('timeupdate', onTimeUpdate)
  }, [segments, videoRef.current, autoScroll])

  useEffect(() => {
    void fetchJobs()
    const t = setInterval(() => { void fetchJobs() }, 5000)
    return () => clearInterval(t)
  }, [])

  return (
    <Layout style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Header style={{ background: 'transparent', padding: '0 16px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ width: '100%', maxWidth: 1440 }}>
          <Title level={2} style={{ margin: '8px 0' }}>HearSight</Title>
        </div>
      </Header>
  <div className={`three-col`}>
        {/* 左侧列 */}
  <div className="three-col__left">
          <div className="sider-inner">
            <Card size="small" title="解析链接" style={{ marginBottom: 12 }} bodyStyle={{ overflowX: 'hidden' }}>
              <Form layout="vertical" size="middle" onFinish={handleSubmit}>
                <Form.Item label="请输入 bilibili.com 链接" required>
                  <Input
                    allowClear
                    value={url}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setUrl(e.target.value)}
                    placeholder="例如：https://www.bilibili.com/video/BV1LL8hzBEZr"
                  />
                </Form.Item>
                <Form.Item>
                    <Space wrap>
                    <Button type="primary" htmlType="submit" icon={<SearchOutlined />} loading={submitting}>解析</Button>
                    <Button icon={<ReloadOutlined />} onClick={() => { setUrl(''); setError(null); setResult(null); setSegments([]); setVideoSrc(null); }}>清空</Button>
                  </Space>
                </Form.Item>
                {error && (<Alert type="error" message={error} showIcon style={{ marginTop: 4 }} />)}
                {result && (
                  <Text type="secondary" style={{ marginTop: 6, display: 'inline-block' }}>
                    解析结果：<Tag color="blue">{result.kind}</Tag> <code>{result.id}</code>
                  </Text>
                )}
              </Form>
            </Card>

            <Card size="small" style={{ marginBottom: 12 }} className="left-grow-card" bodyStyle={{ padding: 0, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
              <Tabs defaultActiveKey="processed" size="small" centered>
                <Tabs.TabPane tab="已处理" key="processed" forceRender>
                  <div style={{ padding: 8, display: 'flex', flexDirection: 'column', minHeight: 0, flex: 1 }}>
                    {transcripts.length === 0 ? (
                      <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无记录" />
                    ) : (
                      <div className="hist-scroll" ref={histScrollRef}>
                        <List
                          split={false}
                          size="small"
                          dataSource={transcripts}
                          renderItem={(it: TranscriptMeta) => {
                            const basename = it.media_path.split('\\').pop()?.split('/').pop() || it.media_path
                            return (
                              <List.Item className={`hist-item ${activeTranscriptId === it.id ? 'hist-item-active' : ''}`} data-transcript-id={it.id}>
                                <div className={`hist-main ${activeTranscriptId === it.id ? 'hist-main-active' : ''}`}>
                                  <div className="hist-row">
                                    <div className="hist-title" title={basename}>{basename}</div>
                                    <Button className="hist-open" size="small" type="link" onClick={() => loadTranscriptDetail(it.id)}>打开</Button>
                                  </div>
                                  <div className="hist-meta">ID {it.id} · {it.segment_count} 段 · {it.created_at}</div>
                                </div>
                              </List.Item>
                            )
                          }}
                        />
                      </div>
                    )}
                  </div>
                </Tabs.TabPane>
                <Tabs.TabPane tab="任务队列" key="tasks" forceRender>
                  <div style={{ padding: 8 }}>
                    {jobs.length === 0 ? (
                      <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无任务" />
                    ) : (
                      <div className="hist-scroll">
                        <List
                          split={false}
                          size="small"
                          dataSource={jobs}
                          renderItem={(it: JobItem) => {
                            const shortUrl = (it.url || '').replace(/^https?:\/\//, '')
                            const color = it.status === 'running' ? 'blue' : (it.status === 'pending' ? 'default' : (it.status === 'failed' ? 'red' : 'green'))
                            return (
                              <List.Item className="hist-item">
                                <div className="hist-main">
                                  <div className="hist-row">
                                    <div className="hist-title" title={it.url}>{shortUrl}</div>
                                    <Tag color={color}>{it.status}</Tag>
                                  </div>
                                  <div className="hist-meta"># {it.id} · {it.created_at || it.started_at || ''}</div>
                                </div>
                              </List.Item>
                            )
                          }}
                        />
                      </div>
                    )}
                  </div>
                </Tabs.TabPane>
              </Tabs>
            </Card>
          </div>
        </div>

        {/* 中间列 */}
        <div className="three-col__center">
          <Card title="播放器" extra={videoSrc && <Tag color="green">可播放</Tag>}>
            {videoSrc ? (
              <div style={{ width: '100%', aspectRatio: '16 / 9', background: '#000', borderRadius: 8, overflow: 'hidden' }}>
                <video
                  ref={videoRef}
                  src={videoSrc}
                  controls
                  style={{ width: '100%', height: '100%', objectFit: 'contain', background: '#000' }}
                  preload="metadata"
                />
              </div>
            ) : (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无视频" />
            )}
            {loading && <Text style={{ marginTop: 8, display: 'block' }}>处理中，请稍候…（首次识别会较慢）</Text>}
          </Card>
        </div>

        {/* 右侧列 */}
  <div className="three-col__right">
          <div className="sider-inner">
            <Card size="small" className="right-grow-card" bodyStyle={{ padding: 0, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
              <Tabs
                size="small"
                defaultActiveKey="segments"
                style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}
                tabBarStyle={{ position: 'relative', zIndex: 60 }}
                onChange={(_key) => {
                  // ensure tab content gets a chance to layout; useful when TabPane was lazily rendered
                  setTimeout(() => {
                    try {
                      if (segScrollRef.current) segScrollRef.current.scrollTop = segScrollRef.current.scrollTop
                      if (histScrollRef.current) histScrollRef.current.scrollTop = histScrollRef.current.scrollTop
                    } catch {}
                  }, 30)
                }}
              >
                <Tabs.TabPane tab="分句（点击跳转）" key="segments" forceRender>
                  <div style={{ padding: 8, display: 'flex', flexDirection: 'column', minHeight: 0, flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                      <Button size="small" icon={<UpOutlined />} onClick={() => {
                        // 手动向上滚动
                        if (!segScrollRef.current) return
                        segScrollRef.current.scrollBy({ top: -160, left: 0, behavior: 'smooth' })
                      }} />
                      <Button size="small" icon={<DownOutlined />} onClick={() => {
                        if (!segScrollRef.current) return
                        segScrollRef.current.scrollBy({ top: 160, left: 0, behavior: 'smooth' })
                      }} />
                      <Button size="small" icon={<SyncOutlined />} onClick={() => {
                        // 手动将当前 activeSegIndex 居中
                        if (!segScrollRef.current || activeSegIndex == null) return
                        const el = segScrollRef.current.querySelector(`[data-seg-index="${activeSegIndex}"]`) as HTMLElement | null
                        if (el) try { el.scrollIntoView({ behavior: 'smooth', block: 'center' }) } catch {}
                      }}>定位</Button>
                      <div style={{ flex: 1 }} />
                      <Space>
                        <span style={{ color: '#8c8c8c', fontSize: 12 }}>自动滚动</span>
                        <Button size="small" type={autoScroll ? 'primary' : 'default'} onClick={() => setAutoScroll(!autoScroll)}>{autoScroll ? '开' : '关'}</Button>
                      </Space>
                    </div>
                    <div className="segments-scroll" ref={segScrollRef}>
                      {segments.length === 0 ? (
                        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无分句" />
                      ) : (
                        <List
                          split={false}
                          dataSource={segments}
                          renderItem={(s: Segment) => {
                            const isActive = activeSegIndex === s.index
                            return (
                              <List.Item className="segment-item" style={{ paddingLeft: 0, paddingRight: 0 }} data-seg-index={s.index}>
                                <div
                                  role="button"
                                  tabIndex={0}
                                  className={`segment-btn is-div ${isActive ? 'active' : ''}`}
                                  onClick={() => { setActiveSegIndex(s.index); seekTo(s.start_time) }}
                                  title={`跳转到 ${fmtTime(s.start_time)} (${Math.floor(Number(s.start_time) || 0)} ms)`}
                                >
                                  <span className="segment-icon"><PlayCircleOutlined /></span>
                                  <div className="seg-card">
                                    <div className="seg-head">
                                      <span className="seg-time">{fmtTime(s.start_time)}<span className="segment-time-sep">~</span>{fmtTime(s.end_time)}</span>
                                      {s.spk_id && <span className="seg-spk">SPK {s.spk_id}</span>}
                                    </div>
                                    <div className="seg-body">{s.sentence || '(空)'}</div>
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
                      onClick={async () => {
                        setSummariesError(null)
                        setSummaries([])
                        if (!segments || segments.length === 0) {
                          setSummariesError('没有可用的分句，请先打开某个转写记录')
                          return
                        }
                        setSummariesLoading(true)
                        try {
                          const resp = await fetch('/api/summarize', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ segments })
                          })
                          if (!resp.ok) throw new Error(`summarize failed: ${resp.status}`)
                          const data = await resp.json()
                          // 后端可能返回两种格式：直接的数组或 { summaries: [...] }
                          let items: any[] = []
                          if (Array.isArray(data)) items = data
                          else if (Array.isArray(data.summaries)) items = data.summaries

                          // 规范化每条 summary：若 summary 字段本身包含 code fence JSON 或是 JSON 字符串，解析并替换为真实 summary 字符串
                          const normalize = (it: any) => {
                            const res = { ...it }
                            let s = String(res.summary || '')
                            // 如果是代码块包裹（```json\n{...}```），提取内部并尝试解析 JSON
                            const codeFenceMatch = s.match(/```(?:json)?\s*\n([\s\S]*)\n```/i)
                            if (codeFenceMatch) {
                              const inner = codeFenceMatch[1].trim()
                              try {
                                const obj = JSON.parse(inner)
                                if (obj && typeof obj.summary === 'string') {
                                  res.summary = obj.summary
                                  if (!res.topic && obj.topic) res.topic = obj.topic
                                  return res
                                }
                                // 如果 obj 本身是字符串或其他，则回退为 inner
                                res.summary = inner
                                return res
                              } catch (e) {
                                // 解析失败则使用 inner 文本
                                res.summary = inner
                                return res
                              }
                            }

                            // 如果 summary 看起来像一个 JSON 字符串（以 { 开头），尝试解析
                            if (s.trim().startsWith('{')) {
                              try {
                                const obj = JSON.parse(s)
                                if (obj && typeof obj.summary === 'string') {
                                  res.summary = obj.summary
                                  if (!res.topic && obj.topic) res.topic = obj.topic
                                } else {
                                  // 如果不是期望结构，则转为漂亮的 JSON 文本
                                  res.summary = JSON.stringify(obj, null, 2)
                                }
                              } catch (e) {
                                // ignore
                              }
                            }
                            return res
                          }

                          setSummaries(items.map(normalize))
                        } catch (err: any) {
                          setSummariesError(err?.message || '调用总结接口失败')
                        } finally {
                          setSummariesLoading(false)
                        }
                      }}
                    >生成总结</Button>

                    <div style={{ marginTop: 8 }}>
                      {summariesLoading && <Text>生成中，请稍候…</Text>}
                      {summariesError && <Alert type="error" message={summariesError} showIcon />}
                      {!summariesLoading && !summariesError && summaries.length === 0 && (
                        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无总结，点击上方按钮生成" />
                      )}
                      {!summariesLoading && summaries.length > 0 && (
                        <List
                          itemLayout="vertical"
                          dataSource={summaries}
                          renderItem={(it: any) => (
                            <List.Item>
                              <List.Item.Meta
                                title={it.topic || '(无主题)'}
                                description={`时间: ${fmtTime((it.start_time || 0))} ~ ${fmtTime((it.end_time || 0))}`}
                              />
                              <div style={{ whiteSpace: 'pre-wrap' }}>
                                <ReactMarkdown>{it.summary || ''}</ReactMarkdown>
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
        </div>
      </div>
      <Footer style={{ textAlign: 'center' }}>
  HearSight
      </Footer>
    </Layout>
  )
}

export default App
