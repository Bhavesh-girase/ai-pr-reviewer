 import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { Terminal, Loader2, AlertCircle } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

export default function Login() {
  const { signIn } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Redirect path after authentication
  const from = (location.state as any)?.from?.pathname || '/'

  const getFriendlyErrorMessage = (errorMsg: string) => {
    const msg = errorMsg.toLowerCase()
    if (msg.includes('invalid login credentials') || msg.includes('invalid credentials') || msg.includes('email not confirmed')) {
      return 'Invalid email or password.'
    }
    if (msg.includes('network') || msg.includes('fetch')) {
      return 'Network error occurred. Please check your internet connection.'
    }
    return errorMsg || 'An unexpected error occurred. Please try again.'
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email || !password) {
      setError('Please fill in all fields.')
      return
    }

    setLoading(true)
    setError(null)

    try {
      await signIn({ email, password })
      navigate(from, { replace: true })
    } catch (err: any) {
      setError(getFriendlyErrorMessage(err.message || 'Unknown error'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#09090b] flex flex-col justify-center items-center px-4 relative overflow-hidden">
      {/* Dynamic background highlights */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-zinc-900/10 rounded-full blur-3xl -z-10 pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-zinc-950/20 rounded-full blur-3xl -z-10 pointer-events-none" />

      {/* Main card */}
      <div className="w-full max-w-md bg-card/30 backdrop-blur-md border border-border p-8 rounded-xl shadow-2xl space-y-6">
        {/* Brand Header */}
        <div className="flex flex-col items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-white flex items-center justify-center shadow-lg">
            <Terminal className="h-5.5 w-5.5 text-zinc-950" />
          </div>
          <div className="text-center">
            <h1 className="text-2xl font-bold tracking-tight text-white">Welcome back</h1>
            <p className="text-xs text-muted-foreground mt-1.5 select-none">
              Sign in to manage and review your codebase issues
            </p>
          </div>
        </div>

        {/* Error Callout */}
        {error && (
          <div className="flex items-start gap-2.5 bg-destructive/10 border border-destructive/25 text-destructive text-xs rounded-lg p-3">
            <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
            <span className="leading-normal">{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label htmlFor="email" className="text-xs font-semibold text-zinc-300">
              Email Address
            </label>
            <Input
              id="email"
              type="email"
              placeholder="name@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
              required
              className="w-full"
            />
          </div>

          <div className="space-y-1.5">
            <div className="flex justify-between items-center">
              <label htmlFor="password" className="text-xs font-semibold text-zinc-300">
                Password
              </label>
            </div>
            <Input
              id="password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              required
              className="w-full"
            />
          </div>

          <Button
            type="submit"
            disabled={loading}
            className="w-full mt-2 cursor-pointer flex justify-center items-center animate-fade-in"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin text-zinc-950" />
                <span>Signing in...</span>
              </>
            ) : (
              'Sign In'
            )}
          </Button>
        </form>

        {/* Link Footer */}
        <div className="text-center pt-2 border-t border-border/40">
          <p className="text-xs text-muted-foreground">
            Don't have an account?{' '}
            <Link to="/register" className="text-white hover:underline font-medium">
              Create an account
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
