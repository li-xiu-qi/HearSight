'use client'

import { Loader2, CheckCircle2, XCircle, Clock } from 'lucide-react'

export const useStatusHelpers = () => {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'downloading':
        return <Loader2 className="h-3 w-3 animate-spin text-primary" />
      case 'processing':
        return <Loader2 className="h-3 w-3 animate-spin text-primary" />
      case 'success':
        return <CheckCircle2 className="h-3 w-3 text-success" />
      case 'failed':
        return <XCircle className="h-3 w-3 text-destructive" />
      default:
        return <Clock className="h-3 w-3 text-muted-foreground" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'downloading':
        return 'bg-primary/10 text-primary'
      case 'processing':
        return 'bg-primary/10 text-primary'
      case 'success':
        return 'bg-success/10 text-success'
      case 'failed':
        return 'bg-destructive/10 text-destructive'
      default:
        return 'bg-muted text-muted-foreground'
    }
  }

  return { getStatusIcon, getStatusColor }
}
