import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { Search, PlayCircle, FileText, BarChart, MessageSquare } from "lucide-react"
import { setPendingUrl } from "@/utils/pendingUrl"

function HomePage() {
  const [url, setUrl] = useState("")
  const navigate = useNavigate()

  const handleUrlSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (url.trim()) {
      setPendingUrl(url)
      navigate("/app")
    }
  }

  const handleGetStarted = () => {
    navigate("/app")
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* 顶部导航栏 */}
      <header className="bg-card border-b px-6 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto h-16 flex justify-between items-center">
          <h3 className="text-2xl font-semibold text-foreground m-0">HearSight</h3>
          <Button variant="ghost" onClick={() => navigate("/app")} className="hover:bg-accent">
            进入应用
          </Button>
        </div>
      </header>

      {/* 主要内容区域 */}
      <main className="flex-1">
        {/* 首屏区域 */}
        <section className="bg-gradient-to-br from-primary to-primary/80 text-primary-foreground py-20 px-6 text-center">
          <h1 className="text-5xl font-bold mb-4">HearSight</h1>
          <h3 className="text-2xl font-medium mb-6 text-primary-foreground/90">智能视频内容分析与理解工具</h3>
          <p className="text-lg max-w-3xl mx-auto mb-8 text-primary-foreground/85 leading-relaxed">
            HearSight 是一个强大的视频和音频内容分析工具，支持在线视频链接和本地文件上传，
            能够自动识别其中的语音内容，将其转换为文本，并提供智能分句、内容总结和智能问答功能，
            帮助您快速理解和分析媒体内容。
          </p>
          
          <form onSubmit={handleUrlSubmit} className="max-w-2xl mx-auto mb-8 flex gap-3 flex-wrap justify-center">
            <Input
              type="text"
              placeholder="请输入 B站、YouTube、小宇宙播客等平台的视频链接或上传本地文件"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="flex-1 min-w-[300px] h-12 bg-background text-foreground"
            />
            <Button type="submit" size="lg" className="h-12 bg-primary-foreground text-primary hover:bg-primary-foreground/90">
              <Search className="mr-2 h-4 w-4" />
              开始分析
            </Button>
          </form>
          
          <div className="mt-8">
            <Button 
              variant="outline" 
              size="lg" 
              onClick={handleGetStarted} 
              className="border-primary-foreground text-primary-foreground hover:bg-primary-foreground hover:text-primary bg-transparent"
            >
              <PlayCircle className="mr-2 h-4 w-4" />
              直接进入应用
            </Button>
          </div>
        </section>

        {/* 核心功能区域 */}
        <section className="py-16 px-6 max-w-7xl mx-auto bg-muted/30">
          <Separator className="mb-8" />
          <h2 className="text-3xl font-bold text-center mb-12 text-foreground">核心功能</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card className="text-center hover:-translate-y-1 transition-transform duration-300">
              <CardHeader>
                <div className="bg-primary/10 text-primary rounded-xl mx-auto w-fit p-5 mb-4">
                  <FileText className="h-10 w-10" />
                </div>
              </CardHeader>
              <CardContent>
                <CardTitle className="mb-3">语音转文字</CardTitle>
                <CardDescription className="text-base">
                  高精度语音识别技术，将媒体内容中的语音准确转换为文字
                </CardDescription>
              </CardContent>
            </Card>

            <Card className="text-center hover:-translate-y-1 transition-transform duration-300">
              <CardHeader>
                <div className="bg-primary/10 text-primary rounded-xl mx-auto w-fit p-5 mb-4">
                  <BarChart className="h-10 w-10" />
                </div>
              </CardHeader>
              <CardContent>
                <CardTitle className="mb-3">智能分句</CardTitle>
                <CardDescription className="text-base">
                  自动将长文本分割为语义完整的句子，便于理解和分析
                </CardDescription>
              </CardContent>
            </Card>

            <Card className="text-center hover:-translate-y-1 transition-transform duration-300">
              <CardHeader>
                <div className="bg-primary/10 text-primary rounded-xl mx-auto w-fit p-5 mb-4">
                  <MessageSquare className="h-10 w-10" />
                </div>
              </CardHeader>
              <CardContent>
                <CardTitle className="mb-3">智能问答</CardTitle>
                <CardDescription className="text-base">
                  基于AI技术的智能问答系统，可针对媒体内容进行提问和交互
                </CardDescription>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* 使用场景区域 */}
        <section className="py-16 px-6 bg-accent/30">
          <div className="max-w-7xl mx-auto">
            <Separator className="mb-8" />
            <h2 className="text-3xl font-bold text-center mb-12 text-foreground">适用场景</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <Card className="hover:-translate-y-1 transition-transform duration-300">
                <CardHeader>
                  <CardTitle>学习研究</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">快速提取视频课程、讲座中的关键信息，提高学习效率</p>
                </CardContent>
              </Card>

              <Card className="hover:-translate-y-1 transition-transform duration-300">
                <CardHeader>
                  <CardTitle>内容创作</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">为视频内容生成文字稿，便于编辑、翻译和二次创作</p>
                </CardContent>
              </Card>

              <Card className="hover:-translate-y-1 transition-transform duration-300">
                <CardHeader>
                  <CardTitle>会议记录</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">自动转写会议内容，生成结构化会议纪要</p>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

      </main>

      {/* 底部信息 */}
      <footer className="bg-card border-t text-muted-foreground text-center py-8 px-6 mt-auto">
        <div className="max-w-7xl mx-auto">
          <p className="m-0">HearSight &copy; {new Date().getFullYear()} - 智能视频内容分析工具</p>
        </div>
      </footer>
    </div>
  )
}

export default HomePage