import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import App from './App'
import HomePage from './HomePage/HomePage'

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

export default router