import { Loader2, CheckCircle2, XCircle, Clock } from 'lucide-react'

export const useStatusHelpers = () => {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'downloading':
        return <Loader2 className="h-3 w-3 animate-spin text-blue-600" />
      case 'processing':
        return <Loader2 className="h-3 w-3 animate-spin text-purple-600" />
      case 'success':
        return <CheckCircle2 className="h-3 w-3 text-green-600" />
      case 'failed':
        return <XCircle className="h-3 w-3 text-red-600" />
      default:
        return <Clock className="h-3 w-3 text-slate-400" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'downloading':
        return 'bg-blue-100 text-blue-700'
      case 'processing':
        return 'bg-purple-100 text-purple-700'
      case 'success':
        return 'bg-green-100 text-green-700'
      case 'failed':
        return 'bg-red-100 text-red-700'
      default:
        return 'bg-slate-100 text-slate-600'
    }
  }

  return { getStatusIcon, getStatusColor }
}
