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
import { PlayCircleOutlined, ReloadOutlined, SearchOutlined, MenuFoldOutlined, MenuUnfoldOutlined } from '@ant-design/icons'

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
  const [loading, setLoading] = useState(false)
  const [transcripts, setTranscripts] = useState<Array<TranscriptMeta>>([])
  const [jobs, setJobs] = useState<Array<JobItem>>([])
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const segScrollRef = useRef<HTMLDivElement | null>(null)
  const [activeSegIndex, setActiveSegIndex] = useState<number | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const prevActiveRef = useRef<number | null>(null)

  // 手动控制左右侧栏折叠
  const [leftCollapsed, setLeftCollapsed] = useState(false)
  const [rightCollapsed, setRightCollapsed] = useState(false)

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
    } catch (err: any) {
      setError(err?.message || '获取详情出错')
    } finally {
      setLoading(false)
    }
  }

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
        if (newIndex != null && segScrollRef.current) {
          const el = segScrollRef.current.querySelector(`[data-seg-index="${newIndex}"]`) as HTMLElement | null
          if (el) {
            try { el.scrollIntoView({ behavior: 'smooth', block: 'center' }) } catch {}
          }
        }
      }
    }

    v.addEventListener('timeupdate', onTimeUpdate)
    return () => v.removeEventListener('timeupdate', onTimeUpdate)
  }, [segments, videoRef.current])

  useEffect(() => {
    void fetchJobs()
    const t = setInterval(() => { void fetchJobs() }, 5000)
    return () => clearInterval(t)
  }, [])

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: 'transparent', padding: '0 16px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ width: '100%', maxWidth: 1440 }}>
          <Title level={2} style={{ margin: '8px 0' }}>HearSight</Title>
        </div>
      </Header>
      <div className={`three-col ${leftCollapsed ? 'left-collapsed' : ''} ${rightCollapsed ? 'right-collapsed' : ''}`}>
        {/* 左侧列 */}
        <div className="three-col__left">
          <button className="collapse-btn collapse-btn--left" onClick={() => setLeftCollapsed(!leftCollapsed)}>
            {leftCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          </button>
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

            <Card size="small" style={{ marginBottom: 12 }} bodyStyle={{ padding: 0 }}>
              <Tabs defaultActiveKey="processed" size="small" centered>
                <Tabs.TabPane tab="已处理" key="processed">
                  <div style={{ padding: 8 }}>
                    {transcripts.length === 0 ? (
                      <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无记录" />
                    ) : (
                      <div className="hist-scroll">
                        <List
                          split={false}
                          size="small"
                          dataSource={transcripts}
                          renderItem={(it: TranscriptMeta) => {
                            const basename = it.media_path.split('\\').pop()?.split('/').pop() || it.media_path
                            return (
                              <List.Item className="hist-item">
                                <div className="hist-main">
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
                <Tabs.TabPane tab="任务队列" key="tasks">
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
          <button className="collapse-btn collapse-btn--right" onClick={() => setRightCollapsed(!rightCollapsed)}>
            {rightCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          </button>
          <div className="sider-inner">
            <Card size="small" title="分句（点击跳转）" bodyStyle={{ padding: 8, overflowX: 'hidden' }}>
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
