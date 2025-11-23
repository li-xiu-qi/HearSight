export const startDownload = async (
  url: string,
  jobId: number,
  sessdata?: string,
  playlist?: boolean,
  quality?: string
) => {
  const response = await fetch('/api/download', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      url,
      job_id: jobId,
      sessdata: sessdata || '',
      playlist: playlist || false,
      quality: quality || 'best',
      workers: 1,
    })
  })
  
  if (!response.ok) {
    throw new Error(`启动下载失败：${response.status}`)
  }
  
  return response.json()
}