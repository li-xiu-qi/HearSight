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

  const data = result.data
  // 验证返回的 data 是否为可用图片，允许 data URL、http(s) 或静态图片路径
  if (typeof data !== 'string') {
    throw new Error('缩略图数据不是字符串')
  }

  const isDataUrl = data.startsWith('data:image/')
  const isHttpUrl = data.startsWith('http://') || data.startsWith('https://')
  const isStaticPath = data.startsWith('/static/')
  // 检查静态路径是否为图片扩展名
  const imageExtMatch = /\.(jpg|jpeg|png|webp|gif)$/i.test(data)

  if (isDataUrl || isHttpUrl || (isStaticPath && imageExtMatch)) {
    return data
  }

  // 不支持的返回格式：记录并抛出错误
  // Unexpected thumbnail data value will be ignored and throw an error at caller
  throw new Error('缩略图数据格式不受支持')
}