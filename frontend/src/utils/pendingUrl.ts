let pendingUrl: string | null = null

export const setPendingUrl = (url: string | null) => {
  pendingUrl = url
}

export const getPendingUrl = () => {
  const url = pendingUrl
  pendingUrl = null
  return url
}