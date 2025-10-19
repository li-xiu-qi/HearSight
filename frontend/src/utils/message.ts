import { toast } from "sonner"

export const message = {
  success: (content: string) => {
    toast.success(content)
  },
  error: (content: string) => {
    toast.error(content)
  },
  warning: (content: string) => {
    toast.warning(content)
  },
  info: (content: string) => {
    toast.info(content)
  },
}
