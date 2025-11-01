import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import { Toaster } from "sonner"
import "./index.css"
import Routes from "./routes.tsx"

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Routes />
    <Toaster
      position="top-center"
      richColors
      toastOptions={{ closeButton: true }}
    />
  </StrictMode>,
)
