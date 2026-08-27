import { useState } from 'react'
import {
  CheckCircle2,
  AlertCircle,
  Loader2,
  KeyRound,
  ShieldCheck,
  ExternalLink,
  Unlink,
  RefreshCw,
  Eye,
  EyeOff
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useGitHubIntegration } from '@/hooks/useGitHubIntegration'
import { motion, AnimatePresence } from 'framer-motion'

function GithubIcon({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
    </svg>
  )
}


export default function GitHubIntegrationCard() {
  const {
    status,
    loading,
    testing,
    connecting,
    disconnecting,
    error,
    successMessage,
    testResult,
    testConnection,
    connectAccount,
    disconnectAccount,
    clearMessages
  } = useGitHubIntegration()

  const [token, setToken] = useState('')
  const [showToken, setShowToken] = useState(false)
  const [isReplacing, setIsReplacing] = useState(false)
  const [showDisconnectConfirm, setShowDisconnectConfirm] = useState(false)

  const handleTest = async (e: React.FormEvent) => {
    e.preventDefault()
    await testConnection(token)
  }

  const handleConnectSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const success = await connectAccount(token)
    if (success) {
      setToken('')
      setIsReplacing(false)
    }
  }

  const handleConfirmDisconnect = async () => {
    const success = await disconnectAccount()
    if (success) {
      setShowDisconnectConfirm(false)
      setIsReplacing(false)
      setToken('')
    }
  }

  if (loading) {
    return (
      <div className="bg-card border border-border/80 rounded-xl p-8 flex items-center justify-center min-h-[300px]">
        <div className="flex flex-col items-center gap-3 text-muted-foreground">
          <Loader2 className="h-7 w-7 animate-spin text-white" />
          <span className="text-sm font-medium">Checking GitHub integration status...</span>
        </div>
      </div>
    )
  }

  const isConnectedState = status.connected && !isReplacing

  return (
    <div className="bg-card border border-border/80 rounded-xl shadow-lg overflow-hidden">
      {/* Header Banner */}
      <div className="px-6 py-5 border-b border-border flex items-center justify-between bg-zinc-950/40">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-lg bg-zinc-900 border border-border flex items-center justify-center shrink-0 shadow-inner">
            <GithubIcon className="h-5 w-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h3 className="text-base font-semibold text-white">GitHub Integration</h3>
              {status.connected && (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Connected
                </span>
              )}
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              Connect your GitHub account ONCE using a Personal Access Token (PAT). Future projects automatically use this account.
            </p>
          </div>
        </div>
      </div>

      {/* Body Content */}
      <div className="p-6 space-y-6">
        {/* Status Banners */}
        <AnimatePresence mode="wait">
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className="p-4 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive flex items-start gap-3 text-sm"
            >
              <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
              <div className="flex-1">
                <span className="font-semibold block">Integration Error</span>
                <span>{error}</span>
              </div>
              <button
                onClick={clearMessages}
                className="text-xs text-destructive/80 hover:text-destructive underline cursor-pointer"
              >
                Dismiss
              </button>
            </motion.div>
          )}

          {successMessage && !error && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-start gap-3 text-sm"
            >
              <CheckCircle2 className="h-5 w-5 shrink-0 mt-0.5" />
              <div className="flex-1">
                <span className="font-semibold block">Success</span>
                <span>{successMessage}</span>
              </div>
              <button
                onClick={clearMessages}
                className="text-xs text-emerald-400/80 hover:text-emerald-400 underline cursor-pointer"
              >
                Dismiss
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* CONNECTED DISPLAY STATE */}
        {isConnectedState ? (
          <div className="space-y-6 animate-fade-in">
            {/* Account Card */}
            <div className="p-5 rounded-xl bg-zinc-950/60 border border-border flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                {status.avatar_url ? (
                  <img
                    src={status.avatar_url}
                    alt={status.username || 'GitHub Avatar'}
                    className="h-14 w-14 rounded-full border-2 border-border object-cover shadow-md"
                  />
                ) : (
                  <div className="h-14 w-14 rounded-full bg-zinc-900 border border-border flex items-center justify-center">
                    <GithubIcon className="h-7 w-7 text-white" />
                  </div>
                )}
                <div>
                  <h4 className="text-base font-bold text-white flex items-center gap-2">
                    {status.name || status.username}
                  </h4>
                  <a
                    href={`https://github.com/${status.username}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs font-mono text-muted-foreground hover:text-primary flex items-center gap-1 mt-0.5 transition-colors"
                  >
                    @{status.username}
                    <ExternalLink className="h-3 w-3" />
                  </a>
                  <div className="mt-2 flex items-center gap-1.5 text-[11px] text-emerald-400 font-medium">
                    <ShieldCheck className="h-3.5 w-3.5" />
                    Personal Access Token Encrypted & Saved
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-3 self-end md:self-auto">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setIsReplacing(true)
                    clearMessages()
                  }}
                  className="gap-2 text-xs border-border hover:bg-zinc-900 text-white cursor-pointer"
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                  Replace Token
                </Button>

                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => setShowDisconnectConfirm(true)}
                  disabled={disconnecting}
                  className="gap-2 text-xs cursor-pointer"
                >
                  {disconnecting ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Unlink className="h-3.5 w-3.5" />
                  )}
                  Disconnect
                </Button>
              </div>
            </div>

            {/* Disconnect confirmation modal overlay */}
            {showDisconnectConfirm && (
              <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/30 space-y-3">
                <div className="flex items-center gap-2 text-sm font-semibold text-destructive">
                  <AlertCircle className="h-4 w-4" />
                  Disconnect GitHub Account?
                </div>
                <p className="text-xs text-muted-foreground">
                  Are you sure you want to remove your connected GitHub credential? Future projects will require you to re-connect a GitHub token.
                </p>
                <div className="flex items-center gap-3 pt-1">
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={handleConfirmDisconnect}
                    disabled={disconnecting}
                    className="text-xs cursor-pointer"
                  >
                    {disconnecting && <Loader2 className="h-3 w-3 animate-spin mr-1" />}
                    Confirm Disconnect
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowDisconnectConfirm(false)}
                    className="text-xs text-muted-foreground hover:text-white cursor-pointer"
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            )}
          </div>
        ) : (
          /* NOT CONNECTED / REPLACE TOKEN FORM STATE */
          <form onSubmit={handleConnectSubmit} className="space-y-5">
            {isReplacing && (
              <div className="flex items-center justify-between text-xs text-muted-foreground bg-zinc-950/40 p-3 rounded-lg border border-border">
                <span>Updating existing GitHub connection for <strong>@{status.username}</strong></span>
                <button
                  type="button"
                  onClick={() => setIsReplacing(false)}
                  className="text-primary hover:underline cursor-pointer"
                >
                  Cancel
                </button>
              </div>
            )}

            <div className="space-y-2">
              <label htmlFor="github-token" className="text-xs font-semibold text-white flex items-center justify-between">
                <span className="flex items-center gap-1.5">
                  <KeyRound className="h-3.5 w-3.5 text-zinc-400" />
                  GitHub Personal Access Token
                </span>
                <a
                  href="https://github.com/settings/tokens/new?scopes=repo,read:user"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[11px] text-zinc-400 hover:text-white transition-colors flex items-center gap-1"
                >
                  Generate Token on GitHub
                  <ExternalLink className="h-3 w-3" />
                </a>
              </label>

              <div className="relative">
                <Input
                  id="github-token"
                  type={showToken ? 'text' : 'password'}
                  placeholder="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  className="pr-10 font-mono text-xs bg-zinc-950 border-border focus-visible:ring-1 focus-visible:ring-white"
                  autoComplete="off"
                />
                <button
                  type="button"
                  onClick={() => setShowToken(!showToken)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-white transition-colors cursor-pointer"
                  aria-label={showToken ? "Hide token" : "Show token"}
                >
                  {showToken ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>

              <p className="text-[11px] text-muted-foreground leading-relaxed">
                Requires <code className="px-1 py-0.5 rounded bg-zinc-900 text-zinc-300 font-mono">repo</code> and <code className="px-1 py-0.5 rounded bg-zinc-900 text-zinc-300 font-mono">read:user</code> scopes. The token will be encrypted before storage and is never displayed again after saving.
              </p>
            </div>

            {/* Test Preview Banner */}
            {testResult && (
              <div className="p-3.5 rounded-lg bg-zinc-950 border border-emerald-500/30 flex items-center justify-between gap-3 animate-fade-in">
                <div className="flex items-center gap-3">
                  <img
                    src={testResult.avatar}
                    alt={testResult.username}
                    className="h-9 w-9 rounded-full border border-border object-cover"
                  />
                  <div>
                    <div className="text-xs font-bold text-white">{testResult.name}</div>
                    <div className="text-[11px] font-mono text-zinc-400">@{testResult.username}</div>
                  </div>
                </div>
                <span className="text-[10px] uppercase tracking-wider font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded border border-emerald-500/20">
                  Valid Token
                </span>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex items-center gap-3 pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={handleTest}
                disabled={testing || connecting || !token.trim()}
                className="gap-2 text-xs border-border hover:bg-zinc-900 text-white cursor-pointer"
              >
                {testing ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <ShieldCheck className="h-3.5 w-3.5" />}
                Test Connection
              </Button>

              <Button
                type="submit"
                disabled={connecting || testing || !token.trim()}
                className="gap-2 text-xs bg-white text-zinc-950 hover:bg-zinc-200 font-semibold cursor-pointer shadow-md"
              >
                {connecting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <CheckCircle2 className="h-3.5 w-3.5" />}
                {isReplacing ? 'Update GitHub Token' : 'Connect GitHub'}
              </Button>
            </div>
          </form>
        )}

        {/* Security Disclosure Footer */}
        <div className="pt-4 border-t border-border/60 flex items-center gap-2 text-[11px] text-muted-foreground">
          <ShieldCheck className="h-4 w-4 text-emerald-400 shrink-0" />
          <span>
            <strong>Bank-grade Security:</strong> Personal Access Tokens are encrypted using AES-256 Fernet symmetric cryptography in the backend and decrypted strictly during GitHub API executions.
          </span>
        </div>
      </div>
    </div>
  )
}
