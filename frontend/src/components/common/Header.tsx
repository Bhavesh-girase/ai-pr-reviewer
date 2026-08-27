import { useLocation } from 'react-router-dom'
import { Menu, Search, Bell } from 'lucide-react'

interface HeaderProps {
  onOpenMobileMenu: () => void
}

export default function Header({ onOpenMobileMenu }: HeaderProps) {
  const location = useLocation()

  // Generate dynamic breadcrumb segments from active URL pathname
  const getBreadcrumbs = () => {
    const paths = location.pathname.split('/').filter(Boolean)
    if (paths.length === 0) return ['Workspace', 'Dashboard']
    return ['Workspace', ...paths.map((p) => {
      // Hide UUIDs / project IDs from raw breadcrumb view
      if (p.startsWith('proj_') || /^[0-9a-fA-F-]{36}$/.test(p)) {
        return 'Project Workspace'
      }
      return p.charAt(0).toUpperCase() + p.slice(1)
    })]
  }

  const breadcrumbs = getBreadcrumbs()

  return (
    <header className="h-16 border-b border-border bg-card/20 backdrop-blur-md flex items-center justify-between px-6 sticky top-0 z-40 w-full">
      {/* Left items: Navigation Breadcrumbs & Mobile trigger */}
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenMobileMenu}
          className="lg:hidden p-2 -ml-1 rounded-lg hover:bg-zinc-900 text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
          aria-label="Open mobile menu"
        >
          <Menu className="h-5 w-5" />
        </button>

        <div className="flex items-center gap-2 text-sm font-medium">
          {breadcrumbs.map((crumb, idx) => (
            <div key={idx} className="flex items-center gap-2">
              {idx > 0 && <span className="text-zinc-700">/</span>}
              <span
                className={
                  idx === breadcrumbs.length - 1
                    ? "text-white font-semibold"
                    : "text-muted-foreground"
                }
              >
                {crumb}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Right items: Global Actions, Connection Status & Mock Tools */}
      <div className="flex items-center gap-4">
        {/* Mock Search Bar for Command Palette styling */}
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border bg-zinc-950/40 text-muted-foreground hover:text-foreground hover:border-zinc-800 transition-all w-60">
          <Search className="h-3.5 w-3.5" />
          <span className="text-xs text-left flex-1 select-none">Search projects...</span>
          <kbd className="hidden sm:inline-flex h-4 select-none items-center gap-0.5 rounded border border-border bg-muted px-1.5 font-mono text-[9px] font-medium text-muted-foreground opacity-100">
            <span>⌘</span>K
          </kbd>
        </div>

        {/* Pulse Indicator: API Connection State */}
        <div className="flex items-center gap-2 border border-border bg-zinc-900/50 px-2.5 py-1 rounded-full">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-500">API Active</span>
        </div>

        {/* Notification Mock Button */}
        <button className="p-2 rounded-lg hover:bg-zinc-950/60 text-muted-foreground hover:text-white border border-transparent hover:border-border transition-all relative cursor-pointer">
          <Bell className="h-4.5 w-4.5" />
          <span className="absolute top-1.5 right-1.5 h-1.5 w-1.5 bg-indigo-500 rounded-full"></span>
        </button>
      </div>
    </header>
  )
}
