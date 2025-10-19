import React from 'react';
import { Typography, Form, Input, Space, Button } from 'antd';
import { SearchOutlined, ReloadOutlined, LeftOutlined, RightOutlined } from '@ant-design/icons';

const { Title } = Typography;

interface HeaderToolbarProps {
  url: string;
  setUrl: (url: string) => void;
  submitting: boolean;
  handleUrlSubmit: (e?: React.FormEvent) => void;
  handleUrlClear: () => void;
  leftPanelVisible: boolean;
  rightPanelVisible: boolean;
  setLeftPanelVisible: (visible: boolean) => void;
  setRightPanelVisible: (visible: boolean) => void;
}

const HeaderToolbar: React.FC<HeaderToolbarProps> = ({
  url,
  setUrl,
  submitting,
  handleUrlSubmit,
  handleUrlClear,
  leftPanelVisible,
  rightPanelVisible,
  setLeftPanelVisible,
  setRightPanelVisible
}) => {
  return (
    <>
      <div className="header-left">
        <Title level={3} style={{ margin: 0, color: 'white' }}>HearSight</Title>
      </div>
      
      <div className="header-center">
        <Form layout="inline" onFinish={handleUrlSubmit}>
          <Form.Item style={{ marginBottom: 0 }}>
            <Input
              allowClear
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="请输入 bilibili.com 链接"
              style={{ width: 300 }}
            />
          </Form.Item>
          <Form.Item style={{ marginBottom: 0 }}>
            <Space>
              <Button type="primary" htmlType="submit" icon={<SearchOutlined />} loading={submitting}>
                解析
              </Button>
              <Button icon={<ReloadOutlined />} onClick={handleUrlClear}>
                清空
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </div>
      
      <div className="header-right">
        <Space>
          <Button 
            type={leftPanelVisible ? 'primary' : 'default'}
            icon={<LeftOutlined />}
            onClick={() => setLeftPanelVisible(!leftPanelVisible)}
          >
            历史记录
          </Button>
          <Button 
            type={rightPanelVisible ? 'primary' : 'default'}
            icon={<RightOutlined />}
            onClick={() => setRightPanelVisible(!rightPanelVisible)}
          >
            AI智能问答
          </Button>
        </Space>
      </div>
    </>
  );
};

export default HeaderToolbar;