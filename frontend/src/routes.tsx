import { createBrowserRouter, RouterProvider } from "react-router-dom"
import HomePage from "./HomePage/HomePage"
import App from "./App"

const router = createBrowserRouter([
  {
    path: "/",
    element: <HomePage />,
  },
  {
    path: "/app",
    element: <App />,
  },
])

export default function Routes() {
  return <RouterProvider router={router} />
}
