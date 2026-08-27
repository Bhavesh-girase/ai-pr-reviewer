import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { Loader2 } from 'lucide-react'

export default function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return (
      <div className="flex h-screen w-screen flex-col items-center justify-center bg-zinc-950 text-foreground">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-white opacity-80" />
          <div className="text-sm font-mono text-zinc-400 select-none animate-pulse">
            Authenticating Session...
          </div>
        </div>
      </div>
    )
  }

  if (!user) {
    // Save current location to redirect back after successful login
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <>{children}</>
}
