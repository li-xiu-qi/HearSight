export const fetchThumbnail = async (
  transcriptId: number,
  startTime: number,
  endTime: number,
  width: number = 320
): Promise<string> => {
  const response = await fetch(
    `/api/thumbnails/${transcriptId}?start_time=${startTime}&end_time=${endTime}&width=${width}`
  )
  
  if (!response.ok) {
    throw new Error(`获取缩略图失败：${response.status}`)
  }
  
  const result = await response.json()
  if (!result.success || !result.data) {
    throw new Error('缩略图数据格式错误')
  }
  
  return result.data
}