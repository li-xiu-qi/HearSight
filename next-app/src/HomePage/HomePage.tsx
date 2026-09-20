'use client'

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ArrowRight, Link2, Upload } from "lucide-react"
import { setPendingUrl } from "@/utils/pendingUrl"

const CAPABILITIES = [
  { title: "转写", desc: "句级时间戳 + 说话人分离" },
  { title: "摘要", desc: "段落级结构化总结" },
  { title: "翻译", desc: "多语言对照保存" },
  { title: "问答", desc: "基于原文的检索式回答" },
]

function HomePage() {
  const [url, setUrl] = useState("")
  const navigate = useRouter()

  const handleUrlSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (url.trim()) {
      setPendingUrl(url)
      navigate.push("/app")
    }
  }

  return (
    <div className="min-h-dvh flex flex-col bg-background">
      {/* 顶部：细导航 */}
      <header className="border-b border-border px-6">
        <div className="max-w-6xl mx-auto h-14 flex justify-between items-center">
          <span className="text-base font-semibold text-foreground tracking-tight">HearSight</span>
          <Button variant="ghost" size="sm" onClick={() => navigate.push("/app")} className="gap-1.5 text-muted-foreground">
            进入工作台
            <ArrowRight className="h-3.5 w-3.5" />
          </Button>
        </div>
      </header>

      {/* 首屏：左定位文案，右导入面板。无渐变、无居中大字堆叠 */}
      <main className="flex-1 max-w-6xl mx-auto w-full px-6 py-16 lg:py-24 grid lg:grid-cols-[1fr_28rem] gap-12 lg:gap-16 items-start">
        <section>
          <div className="border-l-2 border-primary pl-5 mb-8">
            <h1 className="text-3xl lg:text-4xl font-bold text-foreground tracking-tight mb-3">
              把音视频变成可检索的知识
            </h1>
            <p className="text-base text-muted-foreground leading-7 max-w-xl">
              粘贴链接或上传文件，自动转写为带时间戳的文稿，再做摘要、翻译和问答。全程本地处理，数据不出这台机器。
            </p>
          </div>
          <dl className="grid sm:grid-cols-2 gap-x-8 gap-y-5 max-w-xl">
            {CAPABILITIES.map((c) => (
              <div key={c.title} className="border-t border-border pt-3">
                <dt className="text-sm font-medium text-foreground mb-0.5">{c.title}</dt>
                <dd className="text-sm text-muted-foreground">{c.desc}</dd>
              </div>
            ))}
          </dl>
        </section>

        {/* 导入面板：首页唯一动作 */}
        <section className="rounded-lg border border-border bg-card p-6 lg:sticky lg:top-20">
          <h2 className="text-sm font-medium text-foreground mb-4">开始分析</h2>
          <form onSubmit={handleUrlSubmit} className="space-y-3">
            <div className="relative">
              <Link2 className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
              <Input
                type="text"
                placeholder="粘贴视频或播客链接"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="pl-9 h-11"
              />
            </div>
            <Button type="submit" className="w-full h-11" disabled={!url.trim()}>
              开始分析
            </Button>
          </form>
          <div className="flex items-center gap-3 my-5">
            <span className="flex-1 border-t border-border" />
            <span className="text-xs text-muted-foreground">或</span>
            <span className="flex-1 border-t border-border" />
          </div>
          <Button
            variant="outline"
            className="w-full h-11 gap-2"
            onClick={() => navigate.push("/app")}
          >
            <Upload className="h-4 w-4" />
            上传本地文件
          </Button>
          <p className="text-xs text-muted-foreground mt-5 leading-5">
            支持常见视频平台与播客链接，以及 MP4、MP3、WAV、M4A 等本地格式。
          </p>
        </section>
      </main>

      <footer className="border-t border-border text-xs text-muted-foreground py-5 px-6">
        <div className="max-w-6xl mx-auto">HearSight · 本地优先的音视频分析</div>
      </footer>
    </div>
  )
}

export default HomePage
