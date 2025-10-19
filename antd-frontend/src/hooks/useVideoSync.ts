import { useEffect, useRef } from 'react';
import { seekVideoTo } from '../utils';

interface UseVideoSyncProps {
  segments: any[];
  autoScroll: boolean;
  segScrollRef: React.RefObject<HTMLDivElement>;
  setActiveSegIndex: (index: number | null) => void;
  videoRef: React.RefObject<HTMLVideoElement>;
}

export const useVideoSync = ({
  segments,
  autoScroll,
  segScrollRef,
  setActiveSegIndex,
  videoRef
}: UseVideoSyncProps) => {
  const prevActiveRef = useRef<number | null>(null);

  // 根据视频播放进度自动高亮对应分句并让其滚动到可见区域
  useEffect(() => {
    const v = videoRef.current;
    if (!v) return;

    const onTimeUpdate = () => {
      const ms = (v.currentTime || 0) * 1000;
      let newIndex: number | null = null;
      for (const s of segments) {
        const st = Number(s.start_time) || 0;
        const et = Number(s.end_time) || 0;
        if (ms >= st && ms < et) {
          newIndex = s.index;
          break;
        }
      }

      if (prevActiveRef.current !== newIndex) {
        prevActiveRef.current = newIndex;
        setActiveSegIndex(newIndex);
        // 仅在开启自动滚动时让分句滚动到可见区域
        if (autoScroll && newIndex != null && segScrollRef.current) {
          // segScrollRef.current 现在直接指向 .segments-scroll 容器
          const scrollContainer = segScrollRef.current;
          if (scrollContainer) {
            const el = scrollContainer.querySelector(`[data-seg-index="${newIndex}"]`) as HTMLElement | null;
            if (el) {
              try { 
                el.scrollIntoView({ behavior: 'smooth', block: 'center' }); 
              } catch {}
            }
          } else {
            console.warn('自动滚动：未找到 .segments-scroll 容器');
          }
        }
      }
    };

    v.addEventListener('timeupdate', onTimeUpdate);
    return () => v.removeEventListener('timeupdate', onTimeUpdate);
  }, [segments, autoScroll, segScrollRef, setActiveSegIndex]);

  // 视频跳转
  const handleSeekTo = (timeMs: number) => {
    seekVideoTo(videoRef.current, timeMs);
  };

  return {
    handleSeekTo
  };
};