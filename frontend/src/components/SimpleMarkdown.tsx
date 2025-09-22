import React from 'react';

interface SimpleMarkdownProps {
  children: string;
  className?: string;
}

export const SimpleMarkdown: React.FC<SimpleMarkdownProps> = ({ children, className }) => {
  const renderMarkdown = (text: string) => {
    // 简单的markdown渲染
    let html = text
      // 代码块
      .replace(/```[\s\S]*?```/g, (match) => {
        const code = match.slice(3, -3).trim();
        return `<pre><code>${code}</code></pre>`;
      })
      // 内联代码
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      // 粗体
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      // 斜体
      .replace(/\*([^*]+)\*/g, '<em>$1</em>')
      // 换行
      .replace(/\n/g, '<br />');
    
    return html;
  };

  return (
    <div 
      className={className}
      dangerouslySetInnerHTML={{ __html: renderMarkdown(children) }}
      style={{
        lineHeight: '1.6',
        wordBreak: 'break-word'
      }}
    />
  );
};

export default SimpleMarkdown;