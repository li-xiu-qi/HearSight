import type { ParseResult } from '../types'

/**
 * 解析 Bilibili URL，提取视频ID
 */
export const parseBilibiliUrl = (input: string): ParseResult => {
  const trimmed = input.trim()
  if (!trimmed) return { error: '请输入链接' }

  if (!/^https?:\/\/(www\.)?bilibili\.com\//i.test(trimmed)) {
    return { error: '仅支持 bilibili.com 域名的链接' }
  }

  const mBV = trimmed.match(/\/video\/(BV[0-9A-Za-z]+)/)
  if (mBV) return { kind: 'BV', id: mBV[1] }

  const mAv = trimmed.match(/\/video\/(av\d+)/)
  if (mAv) return { kind: 'av', id: mAv[1] }

  const mEp = trimmed.match(/\/bangumi\/play\/(ep\d+)/)
  if (mEp) return { kind: 'ep', id: mEp[1] }

  const mSs = trimmed.match(/\/bangumi\/play\/(ss\d+)/)
  if (mSs) return { kind: 'ss', id: mSs[1] }

  const mMd = trimmed.match(/\/bangumi\/media\/(md\d+)/)
  if (mMd) return { kind: 'md', id: mMd[1] }

  return { error: '未能从链接中解析出 BV/av/ep/ss/md 信息，请检查链接是否正确' }
}

/**
 * 格式化时间：接受毫秒为输入，返回 hh:mm:ss 或 mm:ss 格式
 */
export const formatTime = (ms: number): string => {
  // 统一将传入值视为毫秒（ms）并转换为秒用于显示
  const msec = Math.max(0, Math.floor(Number(ms) || 0))
  const totalSec = Math.floor(msec / 1000)
  const h = Math.floor(totalSec / 3600)
  const m = Math.floor((totalSec % 3600) / 60)
  const s = Math.floor(totalSec % 60)
  
  const mm = String(m).padStart(2, '0')
  const ss = String(s).padStart(2, '0')
  
  if (h > 0) {
    const hh = String(h).padStart(2, '0')
    return `${hh}:${mm}:${ss}`
  }
  return `${mm}:${ss}`
}

/**
 * 视频跳转到指定时间
 */
export const seekVideoTo = (videoElement: HTMLVideoElement | null, timeMs: number): void => {
  const v = videoElement
  if (!v) return
  
  // 统一把传入时间当作毫秒(ms)，转换为秒供 video.currentTime 使用
  let targetMs = Math.max(0, Number(timeMs) || 0)
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

/**
 * 从路径中提取文件名
 */
export const extractFilename = (path: string): string => {
  return path.split('\\').pop()?.split('/').pop() || path
}