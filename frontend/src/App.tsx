import { useState } from 'react'
import './App.css'

function App() {
  const [url, setUrl] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<
    | { kind: 'BV' | 'av' | 'ep' | 'ss' | 'md'; id: string }
    | null
  >(null)

  const parseBilibiliUrl = (input: string) => {
    const trimmed = input.trim()
    if (!trimmed) return { error: '请输入链接' as const }

    // Basic http(s) validation
    if (!/^https?:\/\//i.test(trimmed)) {
      return { error: '请输入以 http(s):// 开头的有效链接' as const }
    }

    // b23 短链无法本地解析重定向，提示用户粘贴展开后的长链
    if (/^https?:\/\/b23\.tv\//i.test(trimmed)) {
      return { error: '检测到 b23 短链，请打开后粘贴展开后的 bilibili.com 长链接' as const }
    }

    // 仅接受 bilibili.com 主域名（含 www）
    if (!/^https?:\/\/(www\.)?bilibili\.com\//i.test(trimmed)) {
      return { error: '仅支持 bilibili.com 域名的链接' as const }
    }

    // 尝试匹配常见路径
    // 1) 视频: /video/BVxxxx 或 /video/av123456
    const mBV = trimmed.match(/\/video\/(BV[0-9A-Za-z]+)/)
    if (mBV) return { kind: 'BV' as const, id: mBV[1] }

    const mAv = trimmed.match(/\/video\/(av\d+)/)
    if (mAv) return { kind: 'av' as const, id: mAv[1] }

    // 2) 番剧/影视: /bangumi/play/ep123 或 /bangumi/play/ss456
    const mEp = trimmed.match(/\/bangumi\/play\/(ep\d+)/)
    if (mEp) return { kind: 'ep' as const, id: mEp[1] }

    const mSs = trimmed.match(/\/bangumi\/play\/(ss\d+)/)
    if (mSs) return { kind: 'ss' as const, id: mSs[1] }

    // 3) 媒体 ID: /bangumi/media/md789
    const mMd = trimmed.match(/\/bangumi\/media\/(md\d+)/)
    if (mMd) return { kind: 'md' as const, id: mMd[1] }

    return { error: '未能从链接中解析出 BV/av/ep/ss/md 信息，请检查链接是否正确' as const }
  }

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setResult(null)
    const parsed = parseBilibiliUrl(url)
    if ('error' in parsed) {
      setError(parsed.error)
    } else {
      setResult(parsed)
    }
  }

  return (
    <>
      <h1>哔哩哔哩链接解析</h1>
      <div className="card" style={{ textAlign: 'left' }}>
        <form onSubmit={onSubmit}>
          <label htmlFor="bili-url" style={{ display: 'block', marginBottom: 8 }}>
            请输入 bilibili.com 链接
          </label>
          <input
            id="bili-url"
            type="url"
            placeholder="例如：https://www.bilibili.com/video/BV1xx411c7mD"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            style={{
              width: '100%',
              padding: '10px 12px',
              borderRadius: 8,
              border: '1px solid #ccc',
              boxSizing: 'border-box',
              marginBottom: 12,
            }}
          />
          <div style={{ display: 'flex', gap: 12 }}>
            <button type="submit">解析</button>
            <button type="button" onClick={() => { setUrl(''); setError(null); setResult(null); }}>
              清空
            </button>
          </div>
        </form>

        {error && (
          <p style={{ color: '#e74c3c', marginTop: 12 }}>错误：{error}</p>
        )}

        {result && (
          <div style={{ marginTop: 16 }}>
            <p>
              解析结果：<strong>{result.kind}</strong> / <code>{result.id}</code>
            </p>
          </div>
        )}
      </div>
      <p className="read-the-docs">支持解析：BV、av、ep、ss、md。b23 短链请先展开。</p>
    </>
  )
}

export default App
