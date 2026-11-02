import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Folder, Settings, ChevronLeft, ChevronRight, Terminal, LogOut } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuth } from '@/hooks/useAuth'

interface SidebarProps {
  isCollapsed: boolean
  onToggle: () => void
}

export default function Sidebar({ isCollapsed, onToggle }: SidebarProps) {
  const { user, signOut } = useAuth()
  
  const displayName = user?.user_metadata?.name || 'User'
  const email = user?.email || ''
  
  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2)
  }
  const initials = getInitials(displayName)

  const navItems = [
    {
      name: 'Dashboard',
      path: '/',
      icon: LayoutDashboard,
    },
    {
      name: 'Projects',
      path: '/projects',
      icon: Folder,
    },
    {
      name: 'Settings',
      path: '/settings',
      icon: Settings,
    },
  ]


  return (
    <aside
      className={cn(
        "hidden lg:flex flex-col border-r border-border bg-card/30 backdrop-blur-md transition-all duration-300 ease-in-out h-screen sticky top-0",
        isCollapsed ? "w-16" : "w-64"
      )}
    >
      {/* Header Section */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-border">
        <div className={cn("flex items-center gap-2.5 overflow-hidden", isCollapsed && "justify-center w-full")}>
          <div className="h-8 w-8 rounded-lg bg-white flex items-center justify-center shrink-0 shadow-md">
            <Terminal className="h-4.5 w-4.5 text-zinc-950" />
          </div>
          {!isCollapsed && (
            <span className="font-bold text-white tracking-tight text-sm whitespace-nowrap animate-fade-in">
              RepoVela
            </span>
          )}
        </div>
        
        {!isCollapsed && (
          <button
            onClick={onToggle}
            className="p-1.5 rounded-lg border border-border bg-card text-muted-foreground hover:text-foreground hover:bg-accent transition-all cursor-pointer"
            aria-label="Collapse sidebar"
          >
            <ChevronLeft className="h-3.5 w-3.5" />
          </button>
        )}
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 py-6 px-3 space-y-1.5 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.path}
              to={item.path}
              aria-label={item.name}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 group relative",
                  isActive
                    ? "bg-zinc-900 border border-border/80 text-white shadow-sm"
                    : "text-muted-foreground hover:text-foreground hover:bg-zinc-950/40"
                )
              }
            >
              <Icon className="h-4.5 w-4.5 shrink-0 transition-transform group-hover:scale-105" />
              {!isCollapsed && (
                <span className="whitespace-nowrap animate-fade-in">{item.name}</span>
              )}
              {isCollapsed && (
                <div className="absolute left-14 scale-0 group-hover:scale-100 transition-all duration-150 origin-left bg-zinc-950 border border-border text-white text-xs font-medium px-2.5 py-1.5 rounded shadow-xl whitespace-nowrap z-50 pointer-events-none">
                  {item.name}
                </div>
              )}
            </NavLink>
          )
        })}
      </nav>

      {/* Expand Toggle (only when collapsed) */}
      {isCollapsed && (
        <div className="p-3 border-t border-border/60 flex justify-center">
          <button
            onClick={onToggle}
            className="p-1.5 rounded-lg border border-border bg-card text-muted-foreground hover:text-foreground hover:bg-accent transition-all cursor-pointer"
            aria-label="Expand sidebar"
          >
            <ChevronRight className="h-3.5 w-3.5" />
          </button>
        </div>
      )}

      {/* Footer Profile Block */}
      <div className="p-4 border-t border-border/60 mt-auto">
        {isCollapsed ? (
          <button
            onClick={() => signOut()}
            className="w-full flex justify-center p-2 rounded-lg text-muted-foreground hover:text-destructive hover:bg-zinc-950/40 transition-colors group relative cursor-pointer"
            aria-label="Sign Out"
          >
            <LogOut className="h-4.5 w-4.5" />
            <div className="absolute left-14 scale-0 group-hover:scale-100 transition-all duration-150 origin-left bg-zinc-950 border border-border text-white text-xs font-medium px-2.5 py-1.5 rounded shadow-xl whitespace-nowrap z-50 pointer-events-none">
              Sign Out
            </div>
          </button>
        ) : (
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-3 overflow-hidden">
              <div className="h-8 w-8 rounded-full bg-zinc-800 border border-border flex items-center justify-center text-xs font-semibold text-white shrink-0">
                {initials}
              </div>
              <div className="overflow-hidden">
                <div className="text-xs font-semibold text-white truncate">{displayName}</div>
                <div className="text-[10px] text-muted-foreground truncate">{email}</div>
              </div>
            </div>
            <button
              onClick={() => signOut()}
              className="p-1.5 rounded-lg text-muted-foreground hover:text-destructive hover:bg-zinc-900 border border-transparent hover:border-border transition-all cursor-pointer shrink-0"
              aria-label="Sign Out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        )}
      </div>
    </aside>
  )
}
