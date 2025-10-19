import { useState, useCallback, useRef, useEffect } from 'react';

interface UsePanelResizeProps {
  initialWidth: number;
  minWidth?: number;
  maxWidth: number;
  isRightPanel?: boolean; // 标识是否为右侧面板
  minVideoWidth?: number; // 视频区域最小宽度
  getSiblingPanelWidth?: () => number; // 获取兄弟面板宽度的函数
}

interface UsePanelResizeReturn {
  width: number;
  isResizing: boolean;
  startResizing: (e: React.MouseEvent) => void;
  stopResizing: () => void;
  maxWidth: number; // 添加maxWidth到返回值
}

export const usePanelResize = ({
  initialWidth,
  minWidth = 320, // 默认最小宽度为320px
  maxWidth: initialMaxWidth,
  isRightPanel = false, // 默认为左侧面板
  minVideoWidth = window.innerWidth * 0.3, // 视频区域最小宽度默认为视口宽度的30%
  getSiblingPanelWidth // 获取兄弟面板宽度的函数
}: UsePanelResizeProps): UsePanelResizeReturn => {
  const [width, setWidth] = useState(initialWidth);
  const [isResizing, setIsResizing] = useState(false);
  const [maxWidth, setMaxWidth] = useState(initialMaxWidth);
  const startXRef = useRef(0);
  const startWidthRef = useRef(0);

  const startResizing = useCallback((e: React.MouseEvent) => {
    setIsResizing(true);
    startXRef.current = e.clientX;
    startWidthRef.current = width;
    e.preventDefault();
  }, [width]);

  const stopResizing = useCallback(() => {
    setIsResizing(false);
  }, []);

  const updateWidth = useCallback((newWidth: number) => {
    setWidth(Math.min(Math.max(newWidth, minWidth), maxWidth));
  }, [minWidth, maxWidth]);

  // 窗口大小变化时更新最大宽度和视频最小宽度
  useEffect(() => {
    const handleResize = () => {
      const newMaxWidth = window.innerWidth * 0.5;
      setMaxWidth(newMaxWidth);
      // 如果当前宽度超过新的最大宽度，则调整当前宽度
      if (width > newMaxWidth) {
        setWidth(newMaxWidth);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [width]);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;
      
      const diff = e.clientX - startXRef.current;
      // 对于右侧面板，拖拽方向需要反转
      const actualDiff = isRightPanel ? -diff : diff;
      let newWidth = startWidthRef.current + actualDiff;
      
      // 计算考虑兄弟面板和视频区域约束后的最大宽度
      const siblingWidth = getSiblingPanelWidth ? getSiblingPanelWidth() : 0;
      const constrainedMaxWidth = Math.min(maxWidth, window.innerWidth - siblingWidth - minVideoWidth);
      
      // 面板宽度不能超过最大宽度
      newWidth = Math.min(Math.max(newWidth, minWidth), constrainedMaxWidth);
      
      updateWidth(newWidth);
    };

    const handleMouseUp = () => {
      if (isResizing) {
        stopResizing();
      }
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing, stopResizing, updateWidth, isRightPanel, minWidth, maxWidth, getSiblingPanelWidth, minVideoWidth]);

  return {
    width,
    isResizing,
    startResizing,
    stopResizing,
    maxWidth
  };
};