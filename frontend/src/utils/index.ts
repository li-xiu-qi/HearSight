/* eslint-disable @typescript-eslint/no-explicit-any */
import type { ParseResult } from '../types'

export const parseUrl = (input: string): ParseResult => {
  const trimmed = input.trim()
  if (!trimmed) return { error: '请输入链接' }

  // 自动补全协议
  // 大小写不敏感地检查协议
  const hasProtocol = /^https?:\/\//i.test(trimmed);
  const withProtocol = hasProtocol ? trimmed : `https://${trimmed}`

  // 支持的平台
  const supportedPlatforms = [
    { name: 'B站', pattern: /^(https?:\/\/)?(www\.)?bilibili\.com\//i, domain: 'bilibili.com' },
    { name: 'B站短链', pattern: /^(https?:\/\/)?b23\.tv\//i, domain: 'b23.tv' },
    { name: 'YouTube', pattern: /^(https?:\/\/)?(www\.)?youtube\.com\//i, domain: 'youtube.com' },
    { name: 'YouTube短链', pattern: /^(https?:\/\/)?youtu\.be\//i, domain: 'youtu.be' },
    { name: '小宇宙播客', pattern: /^(https?:\/\/)?(www\.)?xiaoyuzhoufm\.com\//i, domain: 'xiaoyuzhoufm.com' }
  ]

  // 同时检查原始输入和补全协议后的URL
  const platform = supportedPlatforms.find(p => 
    p.pattern.test(trimmed) || p.pattern.test(withProtocol)
  )
  if (!platform) {
    return { error: '不支持的平台，仅支持 B站、YouTube、小宇宙播客等平台的链接' }
  }

  // 对于B站，解析具体ID
  if (platform.domain === 'bilibili.com' || platform.domain === 'b23.tv') {
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

    return { error: '未能从 B站链接中解析出 BV/av/ep/ss/md 信息，请检查链接是否正确' }
  }

  // 对于其他平台，直接返回URL作为ID
  return { kind: 'url', id: withProtocol, platform: platform.name }
}

export const parseBilibiliUrl = (input: string): ParseResult => {
  return parseUrl(input)
}

export const formatTime = (ms: number): string => {
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

export const seekVideoTo = (videoElement: HTMLVideoElement | null, timeMs: number): void => {
  const v = videoElement
  if (!v) return
  
  const targetMs = Math.max(0, Number(timeMs) || 0)
  let target = targetMs / 1000
  
  if (!Number.isFinite(v.duration) || v.readyState < 1) {
    const handler = () => {
      const dur = Number.isFinite(v.duration) ? v.duration : undefined
      if (dur) target = Math.min(Math.max(0, target), Math.max(0, dur - 0.05))
      if (typeof (v as any).fastSeek === 'function') {
        try { (v as any).fastSeek(target) } catch { v.currentTime = target }
      } else {
        v.currentTime = target
      }
      v.play().catch(() => {})
    }
    v.addEventListener('loadedmetadata', handler, { once: true } as any)
    return
  }
  
  const dur = Number.isFinite(v.duration) ? v.duration : undefined
  if (dur) target = Math.min(Math.max(0, target), Math.max(0, dur - 0.05))
  if (typeof (v as any).fastSeek === 'function') {
    try { (v as any).fastSeek(target) } catch { v.currentTime = target }
  } else {
    if (Math.abs(v.currentTime - target) > 0.03) {
      v.currentTime = target
    }
  }
  v.play().catch(() => {})
}

export const extractFilename = (path: string): string => {
  return path.split('\\').pop()?.split('/').pop() || path
}
