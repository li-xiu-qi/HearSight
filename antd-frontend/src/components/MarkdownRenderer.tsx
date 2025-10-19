import React, { useMemo } from 'react'
import MarkdownIt from 'markdown-it'

interface MarkdownRendererProps {
  children: string
  className?: string
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ children, className }) => {
  const md = useMemo(() => {
    return new MarkdownIt({
      html: true,        // 允许 HTML 标签
      linkify: true,     // 自动识别链接
      typographer: true, // 智能引号和其他排版功能
      breaks: true,      // 将换行符转换为 <br>
    })
  }, [])

  const htmlContent = useMemo(() => {
    return md.render(children || '')
  }, [md, children])

  return (
    <div 
      className={className}
      dangerouslySetInnerHTML={{ __html: htmlContent }}
      style={{
        lineHeight: '1.6',
        wordBreak: 'break-word'
      }}
    />
  )
}

export default MarkdownRenderer