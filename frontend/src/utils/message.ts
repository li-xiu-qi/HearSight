import { toast } from "sonner"

export const message = {
  success: (content: string) => {
    toast.success(content, { dismissible: true })
  },
  error: (content: string) => {
    toast.error(content, { dismissible: true })
  },
  warning: (content: string) => {
    toast.warning(content, { dismissible: true })
  },
  info: (content: string) => {
    toast.info(content, { dismissible: true })
  },
}
