import { useState } from 'react'
import { Layout, Typography, Button, Form, Input, Space, Card, Row, Col, Divider } from 'antd'
import { SearchOutlined, PlayCircleOutlined, FileTextOutlined, BarChartOutlined, CommentOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import './styles/HomePage.css'

const { Header, Content, Footer } = Layout
const { Title, Paragraph } = Typography

function HomePage() {
  const [url, setUrl] = useState('')
  const navigate = useNavigate()

  const handleUrlSubmit = (values: any) => {
    // 这里可以添加URL验证逻辑
    // 然后导航到主应用页面
    navigate('/app')
  }

  const handleGetStarted = () => {
    navigate('/app')
  }

  return (
    <Layout className="homepage-layout">
      {/* 顶部导航栏 */}
      <Header className="homepage-header">
        <div className="header-content">
          <Title level={3} style={{ margin: 0, color: 'white' }}>HearSight</Title>
          <Space>
            <Button type="text" onClick={() => navigate('/app')} style={{ color: 'white' }}>
              进入应用
            </Button>
          </Space>
        </div>
      </Header>

      {/* 主要内容区域 - 采用上下线性布局 */}
      <Content className="homepage-content">
        {/* 首屏区域 */}
        <section className="hero-section">
          <Title level={1} className="hero-title">HearSight</Title>
          <Title level={3} className="hero-subtitle">智能视频内容分析与理解平台</Title>
          <Paragraph className="hero-description">
            HearSight 是一个强大的视频内容分析工具，能够自动识别视频中的语音内容，
            将其转换为文本，并提供智能分句、内容总结和智能问答功能，帮助您快速理解和分析视频内容。
          </Paragraph>
          
          <Form 
            layout="inline" 
            onFinish={handleUrlSubmit}
            className="url-input-form"
          >
            <Form.Item
              name="url"
              rules={[{ required: true, message: '请输入视频链接!' }]}
              style={{ flex: 1, minWidth: 300 }}
            >
              <Input
                size="large"
                placeholder="请输入 bilibili.com 视频链接"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                style={{ width: '100%' }}
              />
            </Form.Item>
            <Form.Item>
              <Button 
                type="primary" 
                size="large" 
                htmlType="submit" 
                icon={<SearchOutlined />}
              >
                开始分析
              </Button>
            </Form.Item>
          </Form>
          
          <div className="cta-section">
            <Button 
              type="default" 
              size="large" 
              onClick={handleGetStarted}
              icon={<PlayCircleOutlined />}
            >
              直接进入应用
            </Button>
          </div>
        </section>

        {/* 核心功能区域 */}
        <section className="features-section">
          <Divider>核心功能</Divider>
          <Row gutter={[16, 16]} justify="center">
            <Col xs={24} sm={12} lg={8}>
              <Card 
                className="feature-card"
                cover={<div className="feature-icon"><FileTextOutlined /></div>}
              >
                <Card.Meta
                  title="语音转文字"
                  description="高精度语音识别技术，将视频中的语音内容准确转换为文字"
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={8}>
              <Card 
                className="feature-card"
                cover={<div className="feature-icon"><BarChartOutlined /></div>}
              >
                <Card.Meta
                  title="智能分句"
                  description="自动将长文本分割为语义完整的句子，便于理解和分析"
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={8}>
              <Card 
                className="feature-card"
                cover={<div className="feature-icon"><CommentOutlined /></div>}
              >
                <Card.Meta
                  title="智能问答"
                  description="基于AI技术的智能问答系统，可针对视频内容进行提问和交互"
                />
              </Card>
            </Col>
          </Row>
        </section>

        {/* 使用场景区域 */}
        <section className="use-cases-section">
          <Divider>适用场景</Divider>
          <Row gutter={[16, 16]} justify="center">
            <Col xs={24} md={12} lg={8}>
              <Card className="use-case-card">
                <Title level={4}>学习研究</Title>
                <Paragraph>
                  快速提取视频课程、讲座中的关键信息，提高学习效率
                </Paragraph>
              </Card>
            </Col>
            <Col xs={24} md={12} lg={8}>
              <Card className="use-case-card">
                <Title level={4}>内容创作</Title>
                <Paragraph>
                  为视频内容生成文字稿，便于编辑、翻译和二次创作
                </Paragraph>
              </Card>
            </Col>
            <Col xs={24} md={12} lg={8}>
              <Card className="use-case-card">
                <Title level={4}>会议记录</Title>
                <Paragraph>
                  自动转写会议内容，生成结构化会议纪要
                </Paragraph>
              </Card>
            </Col>
          </Row>
        </section>

        {/* 常见问题区域 */}
        <section className="faq-section">
          <Divider>常见问题</Divider>
          <Row gutter={[16, 16]} justify="center">
            <Col xs={24} lg={12}>
              <Card title="HearSight支持哪些视频平台？">
                <Paragraph>
                  目前HearSight主要支持Bilibili平台的视频分析，我们正在努力扩展对更多平台的支持。
                </Paragraph>
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title="转写准确率如何？">
                <Paragraph>
                  我们使用了先进的语音识别技术，对于清晰的普通话音频，准确率可达95%以上。
                  对于有背景音乐、杂音或方言的情况，准确率可能会有所下降。
                </Paragraph>
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title="处理一个视频需要多长时间？">
                <Paragraph>
                  处理时间取决于视频的长度和当前系统负载，通常5-10分钟的视频需要2-5分钟处理时间。
                </Paragraph>
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title="是否支持导出转写结果？">
                <Paragraph>
                  是的，您可以在分析完成后导出文本内容，支持多种格式包括TXT、SRT等。
                </Paragraph>
              </Card>
            </Col>
          </Row>
        </section>
      </Content>

      {/* 底部信息 */}
      <Footer className="homepage-footer">
        <div className="footer-content">
          <Paragraph>HearSight &copy; {new Date().getFullYear()} - 智能视频内容分析平台</Paragraph>
        </div>
      </Footer>
    </Layout>
  )
}

export default HomePage