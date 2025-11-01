import { useCallback } from 'react'
import type { Segment } from '../../../types'

export const useSearchHandlers = (segments: Segment[]) => {
  const performSearch = useCallback(
    (searchTerm: string, displayLanguage: string = 'original') => {
      if (!searchTerm.trim()) {
        return []
      }
      const term = searchTerm.toLowerCase()

      return segments.filter((seg) => {
        let contentToSearch = ''

        if (displayLanguage === 'original') {
          contentToSearch = seg.sentence || ''
        } else {
          // 检查translation字段（对象格式）
          if (seg.translation && typeof seg.translation === 'object' && seg.translation[displayLanguage]) {
            contentToSearch = seg.translation[displayLanguage] || ''
          }
          // 如果没有找到翻译内容，回退到原文
          else {
            contentToSearch = seg.sentence || ''
          }
        }

        return contentToSearch.toLowerCase().includes(term)
      })
    },
    [segments]
  )

  return { performSearch }
}
