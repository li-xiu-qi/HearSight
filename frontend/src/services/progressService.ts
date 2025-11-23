export const getDownloadProgress = async (jobId: number) => {
  const response = await fetch(`/api/progress/download/${jobId}`)
  
  if (!response.ok) {
    throw new Error(`获取下载进度失败：${response.status}`)
  }
  
  return response.json()
}

export const getTaskProgress = async (jobId: number) => {
  const response = await fetch(`/api/progress/task/${jobId}`)
  
  if (!response.ok) {
    throw new Error(`获取任务进度失败：${response.status}`)
  }
  
  return response.json()
}