import { Link } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { Navigate } from 'react-router-dom'
import {
  Terminal,
  ArrowRight,
  GitBranch,
  Database,
  MessageSquareCode,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import heroImg from '@/assets/hero-illustration.png'

export default function LandingPage() {
  const { user, loading } = useAuth()

  if (!loading && user) {
    return <Navigate to="/dashboard" replace />
  }

  return (
    <div className="min-h-screen bg-[#09090b] text-foreground overflow-x-hidden">
      {/* ─── Ambient background glows ─── */}
      <div className="pointer-events-none fixed inset-0 -z-10">
        <div className="absolute -top-40 -left-40 h-[600px] w-[600px] rounded-full bg-blue-600/[0.04] blur-[120px]" />
        <div className="absolute top-1/3 right-0 h-[500px] w-[500px] rounded-full bg-violet-600/[0.03] blur-[120px]" />
      </div>

      {/* ─── Navigation ─── */}
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

          <div className="flex items-center gap-3">
            <Link to="/login">
              <Button variant="ghost" size="sm" className="text-zinc-400 hover:text-white">
                Sign In
              </Button>
            </Link>
            <Link to="/register">
              <Button size="sm" className="px-5">
                Get Started
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* ─── Hero Section — full background image ─── */}
      <section className="relative w-full overflow-hidden">
        {/* Background image using img tag for reliability */}
        <img
          src={heroImg}
          alt=""
          aria-hidden="true"
          className="absolute inset-0 h-full w-full object-cover object-right"
        />

        {/* Dark gradient overlay — heavier on left for text readability, fades to reveal image on right */}
        <div className="absolute inset-0 bg-gradient-to-r from-[#09090b] via-[#09090b]/85 to-[#09090b]/30" />
        {/* Bottom fade to seamlessly blend into the next section */}
        <div className="absolute inset-x-0 bottom-0 h-32 bg-gradient-to-t from-[#09090b] to-transparent" />

        <div className="relative z-10 mx-auto max-w-6xl px-6 pt-24 pb-28 lg:pt-32 lg:pb-36">
          {/* Content — left-aligned */}
          <div className="max-w-xl">
            <p
              className="mb-4 text-lg font-semibold tracking-wide text-transparent bg-clip-text inline-block"
              style={{
                fontFamily: "'Playfair Display', 'Georgia', serif",
                fontStyle: 'italic',
                backgroundImage: 'linear-gradient(135deg, #93c5fd, #c4b5fd, #67e8f9)',
              }}
            >
              Crafted for Devs
            </p>

            <h1 className="text-4xl font-extrabold leading-[1.12] tracking-tight text-white sm:text-5xl lg:text-[3.25rem]">
              Your Codebase, Contextually Understood.{' '}
              <span className="bg-gradient-to-r from-blue-400 via-violet-400 to-cyan-400 bg-clip-text text-transparent">
                AI Pull Requests,
              </span>{' '}
              Elevated.
            </h1>

            <p className="mt-5 max-w-lg text-[15px] leading-relaxed text-zinc-300/80">
              Go beyond simple checks. Get actionable, developer-centric feedback
              that understands the entirety of your codebase context, and helps you
              ship faster.
            </p>

            <div className="mt-8 flex flex-col items-start gap-3 sm:flex-row">
              <Link to="/register">
                <Button size="lg" className="gap-2 px-8 text-sm font-semibold shadow-lg shadow-white/5">
                  Get Started Free
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <Link to="/login">
                <Button variant="outline" size="lg" className="gap-2 px-8 text-sm border-zinc-600 hover:border-zinc-400 bg-transparent backdrop-blur-sm">
                  Learn More
                </Button>
              </Link>
            </div>
          </div>

        </div>
      </section>

      {/* ─── 3-Step Setup ─── */}
      <section className="mx-auto max-w-6xl px-6 pb-24">
        <h2 className="text-center text-2xl font-bold tracking-tight text-white sm:text-3xl mb-12">
          Your 3-Step Setup
        </h2>

        <div className="grid gap-5 sm:grid-cols-3">
          {steps.map((step) => (
            <div
              key={step.title}
              className="group relative rounded-2xl border border-zinc-800/80 bg-zinc-900/40 p-7 backdrop-blur-sm transition-all duration-300 hover:border-zinc-700 hover:bg-zinc-900/70 flex flex-col"
            >
              {/* Icon */}
              <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-xl bg-zinc-800/60 border border-zinc-700/50 group-hover:border-blue-500/30 group-hover:bg-zinc-800 transition-all duration-300 mx-auto">
                <step.icon className="h-6 w-6 text-blue-400/80 group-hover:text-blue-300 transition-colors duration-300" />
              </div>

              <h3 className="text-sm font-bold text-white text-center">
                {step.title}
              </h3>
              <p className="mt-2 text-xs leading-relaxed text-zinc-500 text-center flex-1">
                {step.description}
              </p>

              {/* CTA button */}
              <div className="mt-5 text-center">
                <Link to={step.link}>
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-xs border-zinc-700 hover:border-zinc-500 hover:bg-zinc-800"
                  >
                    {step.cta}
                  </Button>
                </Link>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ─── Bottom CTA ─── */}
      <section className="mx-auto max-w-6xl px-6 pb-20">
        <div className="relative overflow-hidden rounded-2xl border border-zinc-800/60 bg-gradient-to-br from-zinc-900/80 via-zinc-900/60 to-zinc-950/80 px-8 py-14 text-center">
          <h2 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
            Ready to Supercharge Your Workflow?
          </h2>
          <p className="mx-auto mt-3 max-w-md text-sm text-zinc-500">
            Join teams shipping higher-quality code, faster — with AI-powered reviews
            that actually understand your codebase.
          </p>
          <div className="mt-8">
            <Link to="/register">
              <Button
                size="lg"
                className="gap-2 px-10 text-sm font-semibold shadow-lg shadow-white/5"
              >
                Start Reviewing
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* ─── Footer ─── */}
      <footer className="border-t border-border/40 bg-zinc-950/60">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 py-8 sm:flex-row">
          <div className="flex items-center gap-2.5">
            <div className="flex h-6 w-6 items-center justify-center rounded-md bg-white">
              <Terminal className="h-3 w-3 text-zinc-950" />
            </div>
            <span className="flex flex-col gap-0.5 leading-none" aria-label="RepoVela - AI PR Reviewer">
              <span className="text-xs font-semibold text-zinc-300">RepoVela</span>
              <span className="text-[8px] font-medium uppercase tracking-[0.12em] text-zinc-500">
                AI PR Reviewer
              </span>
            </span>
          </div>
          <p className="text-xs text-zinc-600 select-none">
            &copy; {new Date().getFullYear()} RepoVela. Built with ❤️ for developers.
          </p>
        </div>
      </footer>
    </div>
  )
}

/* ─── Data ─── */

const steps = [
  {
    icon: GitBranch,
    title: 'Connect Repo',
    description:
      'Link your GitHub repository in seconds using a personal access token or GitHub App.',
    cta: "Connect Repo",
    link: '/register',
  },
  {
    icon: Database,
    title: 'Codebase Indexed',
    description:
      'Our hybrid RAG pipeline clones, parses, and indexes your code into a vector store for deep context.',
    cta: 'Codebase Indexed',
    link: '/register',
  },
  {
    icon: MessageSquareCode,
    title: 'Automated Review',
    description:
      'Every pull request is automatically reviewed with contextual, actionable feedback in minutes.',
    cta: 'Automated Review',
    link: '/register',
  },
]
