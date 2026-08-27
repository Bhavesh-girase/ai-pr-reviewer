import { RouterProvider } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import { router } from './routes'
import { AuthProvider } from '@/context/AuthProvider'

// Initialize the TanStack Query Client for managing server state
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
      <Toaster 
        position="bottom-right" 
        theme="dark" 
        closeButton 
        richColors
        toastOptions={{
          style: {
            background: '#0e0e11',
            border: '1px solid #1f1f23',
            color: '#fafafa',
          },
        }}
      />
    </QueryClientProvider>
  )
}
