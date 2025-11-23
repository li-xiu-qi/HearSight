# 文稿Tab页滚动问题解决记录

## 问题描述

在 HearSight 前端应用中，右侧边栏有两个tab页：字幕分句和文稿。当用户在文稿tab页中滚动内容或点击字幕跳转视频时，会导致整个页面向上滚动，部分内容被header遮挡，影响用户体验。而字幕分句tab页则没有这个问题。

## 问题分析

### 根本原因
1. **组件实现差异**：
   - `SegmentsTab` 使用 `ScrollArea` 组件，提供独立的滚动容器
   - `TranscriptTab` 最初使用普通的 `div` + `overflow-y-auto`，滚动行为未被正确隔离

2. **滚动事件冒泡**：
   - 当 `TranscriptTab` 内容超出容器高度时，滚动事件会冒泡到父级容器
   - 导致整个 `AppPage` 容器滚动，内容被header遮挡

3. **自动滚动逻辑问题**：
   - `RightPanel` 中的自动滚动使用 `scrollIntoView()` 方法
   - 该方法会寻找最近的可滚动父元素，可能导致页面级别的滚动

## 解决步骤

### 1. 统一滚动组件实现
将 `TranscriptTab` 改为使用 `ScrollArea` 组件，与 `SegmentsTab` 保持一致：

```tsx
// 修改前
<div ref={ref} className="h-full overflow-y-auto">

// 修改后
<ScrollArea ref={ref} className="h-full overflow-hidden">
```

### 2. 修改自动滚动逻辑
替换 `scrollIntoView()` 为手动滚动计算：

```tsx
// 修改前
element?.scrollIntoView({ behavior: "smooth", block: "center" })

// 修改后
const scrollContainer = transcriptScrollRef.current?.querySelector('[data-radix-scroll-area-viewport]') as HTMLElement
if (element && scrollContainer) {
  const elementRect = element.getBoundingClientRect()
  const containerRect = scrollContainer.getBoundingClientRect()
  const scrollTop = scrollContainer.scrollTop
  const elementTop = elementRect.top - containerRect.top + scrollTop
  const containerHeight = scrollContainer.clientHeight
  const targetScrollTop = elementTop - containerHeight / 2 + element.offsetHeight / 2

  scrollContainer.scrollTo({
    top: targetScrollTop,
    behavior: 'smooth'
  })
}
```

### 3. 更新相关函数
同样修改 `useScrollHandlers` 中的 `centerActiveSegment` 函数，确保一致性。

## 技术细节

### ScrollArea 组件优势
- 提供独立的滚动上下文，防止滚动事件冒泡
- 内置的滚动条样式和行为
- 支持自定义滚动行为和样式

### 手动滚动计算原理
1. 获取目标元素和滚动容器的边界矩形
2. 计算元素相对于滚动容器的位置
3. 计算目标滚动位置（元素居中显示）
4. 使用 `scrollTo()` 方法进行平滑滚动

## 修改文件

- `frontend/src/components/RightPanel/TranscriptTab.tsx`：改为使用 ScrollArea 组件
- `frontend/src/components/RightPanel/RightPanel.tsx`：修改自动滚动逻辑
- `frontend/src/components/RightPanel/hooks/useScrollHandlers.ts`：更新 centerActiveSegment 函数

## 结果

通过以上修改：
- ✅ 文稿tab页的滚动被正确限制在组件内部
- ✅ 不再出现页面级别的滚动
- ✅ 字幕跳转时的自动滚动正常工作
- ✅ 用户体验得到改善

## 经验总结

1. **组件一致性**：相同功能的组件应该使用相同的实现方式
2. **滚动隔离**：使用专门的滚动组件可以有效防止滚动事件冒泡
3. **手动滚动控制**：在复杂布局中，`scrollIntoView()` 可能不是最佳选择
4. **测试不同场景**：滚动行为需要在不同tab页和交互场景下都进行测试</content>
<parameter name="filePath">c:\Users\ke\Downloads\HearSight\frontend\src\features\app\docs\文稿Tab页滚动问题解决记录.md