import { useAuth } from '@/hooks/useAuth'
import GitHubIntegrationCard from '@/components/settings/GitHubIntegrationCard'
import { User, Mail, Shield, Settings, Check } from 'lucide-react'

export default function SettingsPage() {
  const { user } = useAuth()

  const displayName = user?.user_metadata?.name || 'Developer Account'
  const email = user?.email || 'user@example.com'

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2)
  }

  return (
    <div className="space-y-8 max-w-5xl mx-auto pb-12 animate-fade-in">
      {/* Page Header */}
      <div>
        <div className="flex items-center gap-2.5 text-xs text-muted-foreground font-mono uppercase tracking-wider mb-1">
          <Settings className="h-3.5 w-3.5" />
          <span>Account & Integrations</span>
        </div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Settings</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Manage your account profile, security credentials, and GitHub integrations.
        </p>
      </div>

      {/* User Profile Overview Card */}
      <div className="bg-card border border-border/80 rounded-xl p-6 shadow-md">
        <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <User className="h-4 w-4 text-zinc-400" />
          User Profile
        </h3>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="h-14 w-14 rounded-full bg-zinc-900 border-2 border-border flex items-center justify-center text-lg font-bold text-white shadow-inner">
              {getInitials(displayName)}
            </div>
            <div>
              <h2 className="text-base font-bold text-white">{displayName}</h2>
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground mt-0.5">
                <Mail className="h-3.5 w-3.5" />
                <span>{email}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 bg-zinc-950 px-3.5 py-2 rounded-lg border border-border text-xs text-muted-foreground">
            <Shield className="h-4 w-4 text-emerald-400" />
            <span>Supabase Authenticated Session</span>
            <Check className="h-3.5 w-3.5 text-emerald-400 ml-1" />
          </div>
        </div>
      </div>

      {/* GitHub Integration Section */}
      <GitHubIntegrationCard />
    </div>
  )
}
