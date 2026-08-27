import { Component, type ErrorInfo, type ReactNode } from 'react'
import { AlertOctagon, RefreshCw, Home } from 'lucide-react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export default class ErrorBoundary extends Component<Props, State> {
  public override state: State = {
    hasError: false,
    error: null,
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public override componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught exception captured by React ErrorBoundary:', error, errorInfo)
  }

  private handleReload = () => {
    window.location.reload()
  }

  public override render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-zinc-950 flex items-center justify-center p-6 text-center select-none">
          <div className="max-w-md w-full border border-red-900/50 bg-gradient-to-b from-red-950/10 via-zinc-900/20 to-zinc-950 rounded-xl p-8 shadow-xl space-y-6">
            <div className="h-12 w-12 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-400 mx-auto animate-pulse">
              <AlertOctagon className="h-6 w-6" />
            </div>

            <div className="space-y-2">
              <h2 className="text-lg font-bold text-white tracking-tight">Application Crash Intercepted</h2>
              <p className="text-xs text-muted-foreground leading-relaxed">
                An unexpected runtime error occurred. The application state has been safely isolated to prevent browser crashing.
              </p>
            </div>

            {this.state.error && (
              <div className="bg-zinc-950 border border-border p-3.5 rounded-lg text-left max-h-32 overflow-y-auto">
                <pre className="text-[10px] font-mono text-red-300 leading-normal whitespace-pre-wrap select-text">
                  {this.state.error.toString()}
                </pre>
              </div>
            )}

            <div className="flex flex-col sm:flex-row gap-3 pt-2">
              <button
                onClick={this.handleReload}
                className="flex-1 inline-flex items-center justify-center gap-2 rounded-lg bg-white hover:bg-zinc-200 text-zinc-950 font-semibold py-2 text-xs transition-colors cursor-pointer"
                type="button"
              >
                <RefreshCw className="h-3.5 w-3.5 animate-spin-reverse" />
                Reload Application
              </button>
              <a
                href="/"
                className="flex-1 inline-flex items-center justify-center gap-2 rounded-lg bg-zinc-900 border border-border hover:bg-zinc-800 text-zinc-200 font-semibold py-2 text-xs transition-colors"
              >
                <Home className="h-3.5 w-3.5 text-zinc-400" />
                Go Back Home
              </a>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
