import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Folder, GitBranch, ShieldCheck, Activity, BarChart3, ArrowRight, FolderPlus, Database, Layers } from 'lucide-react'
import MetricCard from '@/components/dashboard/MetricCard'
import { getProjects } from '@/api/projects'
import type { Project } from '@/types/project'

export default function DashboardPage() {
  // Fetch projects list for real database metrics
  const { data: projects = [], isLoading } = useQuery<Project[]>({
    queryKey: ['projects'],
    queryFn: getProjects,
  })

  // Calculate metrics directly from PostgreSQL
  const totalProjects = projects.length
  const connectedProjects = projects.filter((p) => (p.auth_type || p.authType) === 'connected_account').length
  const readyProjects = projects.filter((p) => p.status === 'READY').length
  const provisioningProjects = projects.filter((p) => ['CREATING', 'CLONING', 'INDEXING'].includes(p.status)).length

  const hasProjects = totalProjects > 0

  return (
    <div className="space-y-8 animate-fade-in text-left">
      {/* Page Header and CTA */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white leading-none">Dashboard</h1>
          <p className="text-xs text-zinc-400 mt-2 select-none">
            Monitor provisioned workspaces, vector databases, and indexing pipelines.
          </p>
        </div>
        
        {hasProjects && (
          <Link
            to="/projects"
            className="inline-flex items-center gap-2 rounded-lg bg-zinc-900 border border-zinc-800 px-3.5 py-2 text-xs font-semibold text-white hover:bg-zinc-850 transition-colors"
          >
            <span>View All Projects</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        )}
      </div>

      {/* Welcome Banner: Visible when no projects have been registered */}
      {!hasProjects && !isLoading && (
        <div className="rounded-xl border border-zinc-800 bg-gradient-to-r from-zinc-950 via-zinc-900/35 to-zinc-950 p-6 md:p-8 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-6 select-none animate-fade-in">
          <div className="space-y-2 max-w-xl">
            <h2 className="text-lg font-bold text-white tracking-tight leading-none">Get Started with Projects</h2>
            <p className="text-xs text-zinc-400 leading-relaxed mt-2.5">
              Add a repository as a Project to provision source code storage, index vector embeddings into ChromaDB, and enable automated AI reviews.
            </p>
          </div>
          <Link
            to="/projects"
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-white px-4 py-2.5 text-xs font-bold text-zinc-950 hover:bg-zinc-200 transition-all shadow-md shrink-0 cursor-pointer"
          >
            <FolderPlus className="h-4 w-4" />
            <span>Provision Your First Project</span>
          </Link>
        </div>
      )}

      {/* Grid of Metric Cards */}
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4 select-all">
        <MetricCard
          title="Total Workspaces"
          value={isLoading ? '...' : totalProjects.toString()}
          icon={Folder}
          description="Provisioned PostgreSQL projects"
          trend={hasProjects ? `${totalProjects} active` : undefined}
        />
        <MetricCard
          title="Connected Auth"
          value={isLoading ? '...' : connectedProjects.toString()}
          icon={Layers}
          description="OAuth & PAT credential tunnels"
          trend={hasProjects ? `${connectedProjects} verified` : undefined}
          trendType={connectedProjects > 0 ? 'up' : 'neutral'}
        />
        <MetricCard
          title="Ready Workspaces"
          value={isLoading ? '...' : readyProjects.toString()}
          icon={ShieldCheck}
          description="Vectorized codebase workspaces"
          trend={hasProjects ? `${readyProjects} ready` : undefined}
          trendType={readyProjects > 0 ? 'up' : 'neutral'}
          className={readyProjects > 0 ? "border-indigo-950/40 bg-indigo-950/5 hover:border-indigo-900" : ""}
        />
        <MetricCard
          title="Active Provisioning"
          value={isLoading ? '...' : provisioningProjects.toString()}
          icon={GitBranch}
          description="Cloning & vectorizing pipelines"
          trend={provisioningProjects > 0 ? 'Provisioning...' : 'Idle'}
          trendType={provisioningProjects > 0 ? 'neutral' : 'neutral'}
          className={provisioningProjects > 0 ? "border-amber-950 bg-amber-950/5 hover:border-amber-900" : ""}
        />
      </div>

      {/* Analytics Charts Grid */}
      <div className="space-y-4">
        <div className="flex items-center gap-2 border-b border-zinc-900 pb-3 select-none">
          <BarChart3 className="h-4.5 w-4.5 text-zinc-400" />
          <h3 className="text-sm font-semibold text-white">Visual Overview</h3>
        </div>

        {hasProjects ? (
          <div className="grid gap-6 md:grid-cols-2">
            {/* Status distribution panel */}
            <div className="rounded-xl border border-zinc-800 bg-zinc-950/45 p-6 shadow-sm flex flex-col justify-between overflow-hidden">
              <div>
                <h4 className="text-sm font-medium text-zinc-200">Repository Credentials</h4>
                <p className="text-xs text-zinc-500 mt-0.5 mb-4">Authorization methods used across projects</p>
              </div>
              
              <div className="space-y-4 py-3">
                <div className="space-y-1">
                  <div className="flex justify-between text-xs font-semibold select-none">
                    <span className="text-zinc-300">Connected Account</span>
                    <span className="text-zinc-500 font-mono">
                      {projects.filter((p) => (p.auth_type || p.authType) === 'connected_account').length}
                    </span>
                  </div>
                  <div className="h-1.5 w-full bg-zinc-950 border border-zinc-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-indigo-500 rounded-full"
                      style={{
                        width: `${
                          (projects.filter((p) => (p.auth_type || p.authType) === 'connected_account').length / totalProjects) * 100
                        }%`,
                      }}
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="flex justify-between text-xs font-semibold select-none">
                    <span className="text-zinc-300">Custom Tokens</span>
                    <span className="text-zinc-500 font-mono">
                      {projects.filter((p) => (p.auth_type || p.authType) === 'custom_token').length}
                    </span>
                  </div>
                  <div className="h-1.5 w-full bg-zinc-950 border border-zinc-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-amber-500 rounded-full"
                      style={{
                        width: `${
                          (projects.filter((p) => (p.auth_type || p.authType) === 'custom_token').length / totalProjects) * 100
                        }%`,
                      }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Indexing status panel */}
            <div className="rounded-xl border border-zinc-800 bg-zinc-950/45 p-6 shadow-sm flex flex-col justify-between overflow-hidden">
              <div>
                <h4 className="text-sm font-medium text-zinc-200">Provisioning & Index Readiness</h4>
                <p className="text-xs text-zinc-500 mt-0.5 mb-5">Current status breakdown from PostgreSQL</p>
              </div>
              
              <div className="space-y-3 flex-1 flex flex-col justify-center">
                <div className="flex justify-between items-center text-xs text-zinc-400 py-1 border-b border-zinc-900/60">
                  <span className="flex items-center gap-1.5">
                    <span className="h-2 w-2 rounded-full bg-indigo-400"></span>
                    <span>Ready</span>
                  </span>
                  <span className="font-mono text-white">{readyProjects}</span>
                </div>
                <div className="flex justify-between items-center text-xs text-zinc-400 py-1 border-b border-zinc-900/60">
                  <span className="flex items-center gap-1.5">
                    <span className="h-2 w-2 rounded-full bg-amber-400 animate-pulse"></span>
                    <span>Provisioning</span>
                  </span>
                  <span className="font-mono text-white">{provisioningProjects}</span>
                </div>
                <div className="flex justify-between items-center text-xs text-zinc-400 py-1">
                  <span className="flex items-center gap-1.5">
                    <span className="h-2 w-2 rounded-full bg-red-400"></span>
                    <span>Failed</span>
                  </span>
                  <span className="font-mono text-white">
                    {projects.filter((p) => p.status === 'FAILED').length}
                  </span>
                </div>
              </div>
            </div>
          </div>
        ) : (
          /* Visual Empty State */
          <div className="rounded-xl border border-zinc-800 bg-zinc-950/10 p-8 text-center flex flex-col items-center justify-center min-h-[220px] animate-fade-in select-none">
            <Database className="h-9 w-9 text-zinc-800 mb-3" />
            <h4 className="font-semibold text-white text-sm">No Database Projects Found</h4>
            <p className="text-xs text-zinc-500 mt-1.5 max-w-xs leading-relaxed">
              Create a project to provision a local repository clone and ChromaDB vector database.
            </p>
          </div>
        )}
      </div>

      {/* Active Workspaces Overview */}
      {hasProjects && (
        <div className="rounded-xl border border-zinc-800 bg-zinc-950/20 p-6 space-y-4 animate-fade-in select-none">
          <div className="flex items-center gap-2 border-b border-zinc-900 pb-3">
            <Activity className="h-4.5 w-4.5 text-zinc-400" />
            <h3 className="text-sm font-semibold text-white">Multi-Tenant Workspaces</h3>
          </div>
          
          <div className="space-y-3">
            <p className="text-xs text-zinc-400 leading-relaxed">
              Connected to Supabase PostgreSQL database. Monitoring <span className="text-white font-medium">{totalProjects} provisioned projects</span>.
            </p>
            <div className="pt-1">
              <Link
                to="/projects"
                className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition-colors flex items-center gap-1.5"
              >
                <span>Go to Projects Manager</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
