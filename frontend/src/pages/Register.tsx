import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Terminal, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

export default function Register() {
  const { signUp } = useAuth()
  const navigate = useNavigate()

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const getFriendlyErrorMessage = (errorMsg: string) => {
    const msg = errorMsg.toLowerCase()
    if (msg.includes('already registered') || msg.includes('already exists')) {
      return 'An account with this email already exists.'
    }
    if (msg.includes('should be at least 6 characters') || msg.includes('weak password')) {
      return 'Password must be at least 6 characters long.'
    }
    if (msg.includes('network') || msg.includes('fetch')) {
      return 'Network error occurred. Please check your internet connection.'
    }
    return errorMsg || 'An unexpected error occurred. Please try again.'
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name || !email || !password) {
      setError('Please fill in all fields.')
      return
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters long.')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const data = await signUp({
        email,
        password,
        options: {
          data: {
            name,
          },
        },
      })

      // If email verification is disabled, Supabase logs the user in immediately
      if (data?.session) {
        navigate('/', { replace: true })
      } else {
        // If email verification is enabled, we show a success checkmark
        setSuccess(true)
      }
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
            <h1 className="text-2xl font-bold tracking-tight text-white">Create an account</h1>
            <p className="text-xs text-muted-foreground mt-1.5 select-none">
              Get started with automated AI reviews
            </p>
          </div>
        </div>

        {success ? (
          /* Success Screen */
          <div className="space-y-6 text-center py-4 animate-fade-in">
            <div className="flex justify-center">
              <CheckCircle2 className="h-12 w-12 text-emerald-500 opacity-90" />
            </div>
            <div className="space-y-2">
              <h2 className="text-lg font-bold text-white tracking-tight">Check your email</h2>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Registration successful! We sent a confirmation link to <span className="text-zinc-200 font-semibold">{email}</span>. Please click the link to activate your account.
              </p>
            </div>
            <Button onClick={() => navigate('/login')} className="w-full mt-4">
              Proceed to Login
            </Button>
          </div>
        ) : (
          /* Register Form */
          <>
            {/* Error Callout */}
            {error && (
              <div className="flex items-start gap-2.5 bg-destructive/10 border border-destructive/25 text-destructive text-xs rounded-lg p-3">
                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                <span className="leading-normal">{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label htmlFor="name" className="text-xs font-semibold text-zinc-300">
                  Full Name
                </label>
                <Input
                  id="name"
                  type="text"
                  placeholder="John Doe"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  disabled={loading}
                  required
                  className="w-full"
                />
              </div>

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
                <label htmlFor="password" className="text-xs font-semibold text-zinc-300">
                  Password
                </label>
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
                className="w-full mt-2 cursor-pointer flex justify-center items-center"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin text-zinc-950" />
                    <span>Creating account...</span>
                  </>
                ) : (
                  'Create Account'
                )}
              </Button>
            </form>

            {/* Link Footer */}
            <div className="text-center pt-2 border-t border-border/40">
              <p className="text-xs text-muted-foreground">
                Already have an account?{' '}
                <Link to="/login" className="text-white hover:underline font-medium">
                  Sign in
                </Link>
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
