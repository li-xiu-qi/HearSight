import { useMemo } from "react"
import MarkdownIt from "markdown-it"

interface MarkdownRendererProps {
  readonly children: string
  readonly className?: string
}

export default function MarkdownRenderer({ children, className }: Readonly<MarkdownRendererProps>) {
  const md = useMemo(() => {
    return new MarkdownIt({
      html: true,
      linkify: true,
      typographer: true,
      breaks: true,
    })
  }, [])

  const htmlContent = useMemo(() => {
    return md.render(children || "")
  }, [md, children])

  return (
    <div
      className={className}
      dangerouslySetInnerHTML={{ __html: htmlContent }}
      style={{
        lineHeight: "1.6",
        wordBreak: "break-word",
      }}
    />
  )
}
