import { useState, useEffect } from 'react'
import { Outlet, Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, Folder, Settings, X, Terminal, LogOut } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import Sidebar from '@/components/common/Sidebar'
import Header from '@/components/common/Header'
import PageWrapper from '@/components/common/PageWrapper'
import { cn } from '@/lib/utils'
import { AnimatePresence, motion } from 'framer-motion'

export default function AppLayout() {
  const location = useLocation()
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
  
  // Collapse state for sidebar (Desktop layout only)
  const [isCollapsed, setIsCollapsed] = useState<boolean>(() => {
    const saved = localStorage.getItem('sidebar-collapsed')
    return saved ? JSON.parse(saved) : false
  })

  // Open state for mobile hamburger menu drawer overlay
  const [isMobileOpen, setIsMobileOpen] = useState<boolean>(false)

  // Sync collapsible choice to localStorage for user preference persistence
  useEffect(() => {
    localStorage.setItem('sidebar-collapsed', JSON.stringify(isCollapsed))
  }, [isCollapsed])

  // Automatically close mobile menu drawer on active URL location changes
  useEffect(() => {
    setIsMobileOpen(false)
  }, [location.pathname])

  const mobileNavItems = [
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
    <div className="flex min-h-screen bg-background text-foreground">
      {/* 1. Desktop permanent / collapsible sidebar */}
      <Sidebar isCollapsed={isCollapsed} onToggle={() => setIsCollapsed(!isCollapsed)} />

      {/* 2. Mobile sidebar Drawer using framer-motion overlay */}
      <AnimatePresence>
        {isMobileOpen && (
          <>
            {/* Dark dim backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.4 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsMobileOpen(false)}
              className="fixed inset-0 bg-black z-50 lg:hidden"
            />
            {/* Sliding drawer panel */}
            <motion.div
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 240 }}
              className="fixed top-0 bottom-0 left-0 w-72 bg-card border-r border-border z-50 p-6 flex flex-col justify-between lg:hidden"
            >
              <div>
                {/* Brand Header */}
                <div className="flex items-center justify-between mb-8">
                  <div className="flex items-center gap-2.5">
                    <div className="h-8 w-8 rounded-lg bg-white flex items-center justify-center shadow-md">
                      <Terminal className="h-4.5 w-4.5 text-zinc-950" />
                    </div>
                    <span className="font-bold text-white text-sm">RepoVela</span>
                  </div>
                  <button
                    onClick={() => setIsMobileOpen(false)}
                    className="p-1.5 rounded-lg hover:bg-zinc-900 border border-transparent hover:border-border text-muted-foreground hover:text-white transition-colors cursor-pointer"
                    aria-label="Close menu"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>

                {/* Mobile Drawer navigation links */}
                <nav className="space-y-1.5">
                  {mobileNavItems.map((item) => {
                    const Icon = item.icon
                    const isActive = location.pathname === item.path
                    return (
                      <Link
                        key={item.path}
                        to={item.path}
                        className={cn(
                          "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
                          isActive
                            ? "bg-zinc-900 border border-border text-white shadow-sm"
                            : "text-muted-foreground hover:text-white hover:bg-zinc-950/40"
                        )}
                      >
                        <Icon className="h-4.5 w-4.5" />
                        <span>{item.name}</span>
                      </Link>
                    )
                  })}
                </nav>
              </div>

              {/* Drawer footer profile */}
              <div className="border-t border-border/60 pt-4 flex items-center justify-between gap-2">
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
                  <LogOut className="h-4.5 w-4.5" />
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* 3. Right main workspace area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Header onOpenMobileMenu={() => setIsMobileOpen(true)} />
        <main className="flex-1 overflow-y-auto px-6 py-8 flex flex-col justify-between">
          <div className="max-w-7xl mx-auto w-full flex-1">
            <AnimatePresence mode="wait">
              <PageWrapper key={location.pathname}>
                <Outlet />
              </PageWrapper>
            </AnimatePresence>
          </div>

          {/* Portfolio tech stack footer */}
          <footer className="mt-8 pt-4 border-t border-border/40 text-center select-none shrink-0">
            <span className="text-[9px] font-mono text-zinc-600 tracking-widest uppercase">
              AI • Hybrid Search • CrossEncoder Reranker • FastAPI • ChromaDB
            </span>
          </footer>
        </main>
      </div>
    </div>
  )
}
