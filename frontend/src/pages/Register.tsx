import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Terminal, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import heroImg from '@/assets/hero-illustration.png'

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
    <div className="min-h-screen bg-[#09090b] text-foreground flex flex-col relative overflow-x-hidden">
      {/* ─── Ambient background glows ─── */}
      <div className="pointer-events-none fixed inset-0 -z-10">
        <div className="absolute -top-40 -left-40 h-[600px] w-[600px] rounded-full bg-blue-600/[0.04] blur-[120px]" />
        <div className="absolute top-1/3 right-0 h-[500px] w-[500px] rounded-full bg-violet-600/[0.03] blur-[120px]" />
      </div>

      {/* ─── Navigation — seamless with Landing Page ─── */}
      <nav className="sticky top-0 z-50 border-b border-border/50 bg-[#09090b]/80 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white shadow-md group-hover:shadow-lg transition-shadow duration-300">
              <Terminal className="h-4 w-4 text-zinc-950" />
            </div>
            <span className="flex flex-col gap-1 leading-none" aria-label="RepoVela - AI PR Reviewer">
              <span className="text-base font-extrabold tracking-tight text-white sm:text-lg">RepoVela</span>
              <span className="text-[9px] font-medium uppercase tracking-[0.14em] text-zinc-400">
                AI PR Reviewer
              </span>
            </span>
          </Link>
        </div>
      </nav>

      {/* ─── Main Section — full background blend matching hero ─── */}
      <div className="relative flex-1 w-full overflow-hidden flex items-center min-h-[calc(100vh-4rem)]">
        {/* Background image using hero-illustration.png */}
        <img
          src={heroImg}
          alt=""
          aria-hidden="true"
          className="absolute inset-0 h-full w-full object-cover object-right pointer-events-none"
        />

        {/* Dark gradient overlay — heavier on left for form readability, reveals illustration on right */}
        <div className="absolute inset-0 bg-gradient-to-r from-[#09090b] via-[#09090b]/90 to-[#09090b]/40 pointer-events-none" />

        {/* Content — aligned on max-w-6xl grid matching landing page hero */}
        <div className="relative z-10 mx-auto w-full max-w-6xl px-6 py-12 lg:py-16">
          <div className="max-w-md">
            {success ? (
              /* ── Success Screen ── */
              <div className="space-y-6 py-4">
                <div className="flex justify-start">
                  <CheckCircle2 className="h-14 w-14 text-emerald-500 opacity-90" />
                </div>
                <div className="space-y-2">
                  <h2 className="text-2xl font-bold text-white tracking-tight">
                    Check your email
                  </h2>
                  <p className="text-sm text-zinc-400 leading-relaxed">
                    Registration successful! We sent a confirmation link to{' '}
                    <span className="text-zinc-200 font-semibold">{email}</span>.
                    Please click the link to activate your account.
                  </p>
                </div>
                <Button onClick={() => navigate('/login')} className="w-full h-11">
                  Proceed to Login
                </Button>
              </div>
            ) : (
              <>
                {/* Header Badge */}
                <p
                  className="mb-3 text-sm font-semibold tracking-wide text-transparent bg-clip-text inline-block"
                  style={{
                    fontFamily: "'Playfair Display', 'Georgia', serif",
                    fontStyle: 'italic',
                    backgroundImage: 'linear-gradient(135deg, #93c5fd, #c4b5fd, #67e8f9)',
                  }}
                >
                  Get Started
                </p>

                <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white mb-2">
                  Create your account
                </h1>
                <p className="text-sm text-zinc-400 mb-8 leading-relaxed">
                  Get started with automated AI-powered code reviews.
                </p>

                {/* Error Callout */}
                {error && (
                  <div className="flex items-start gap-2.5 bg-destructive/10 border border-destructive/25 text-destructive text-xs rounded-lg p-3 mb-6">
                    <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                    <span className="leading-normal">{error}</span>
                  </div>
                )}

                {/* Form */}
                <form onSubmit={handleSubmit} className="space-y-5">
                  <div className="space-y-2">
                    <label htmlFor="name" className="text-sm font-semibold text-zinc-300">
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
                      className="w-full h-11 bg-zinc-900/60 border-zinc-800 text-white placeholder:text-zinc-600 focus:border-zinc-500 focus:ring-zinc-700 backdrop-blur-sm"
                    />
                  </div>

                  <div className="space-y-2">
                    <label htmlFor="email" className="text-sm font-semibold text-zinc-300">
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
                      className="w-full h-11 bg-zinc-900/60 border-zinc-800 text-white placeholder:text-zinc-600 focus:border-zinc-500 focus:ring-zinc-700 backdrop-blur-sm"
                    />
                  </div>

                  <div className="space-y-2">
                    <label htmlFor="password" className="text-sm font-semibold text-zinc-300">
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
                      className="w-full h-11 bg-zinc-900/60 border-zinc-800 text-white placeholder:text-zinc-600 focus:border-zinc-500 focus:ring-zinc-700 backdrop-blur-sm"
                    />
                  </div>

                  <Button
                    type="submit"
                    disabled={loading}
                    className="w-full h-11 mt-3 cursor-pointer flex justify-center items-center text-sm font-semibold"
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

                {/* Footer link */}
                <p className="mt-8 text-sm text-zinc-400">
                  Already have an account?{' '}
                  <Link to="/login" className="text-white hover:underline font-medium underline underline-offset-4">
                    Sign in
                  </Link>
                </p>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
