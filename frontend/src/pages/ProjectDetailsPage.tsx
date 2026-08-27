import * as React from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getProjectById, deleteProject, syncProjectRepository } from '@/api/projects'
import type { Project } from '@/types/project'
import { Skeleton } from '@/components/ui/skeleton'
import WorkspaceHeader from '@/components/workspace/WorkspaceHeader'
import HealthCard from '@/components/workspace/HealthCard'
import RepositoryCard from '@/components/workspace/RepositoryCard'
import AIEngineCard from '@/components/workspace/AIEngineCard'
import VectorCard from '@/components/workspace/VectorCard'
import ActivityTimeline from '@/components/workspace/ActivityTimeline'
import DeveloperPanel from '@/components/workspace/DeveloperPanel'
import InsightsDashboard from '@/components/workspace/InsightsDashboard'
import { ReviewList } from '@/components/reviews/ReviewList'
import { PullRequestList } from '@/components/pull_requests/PullRequestList'
import { WebhookConfigCard } from '@/components/workspace/WebhookConfigCard'
import {
  ChevronRight,
  GitPullRequest,
  History,
  LayoutDashboard,
  BarChart3,
  Folder,
  Settings,
  Terminal,
  Trash2,
  AlertCircle,
  ArrowLeft,
  ShieldCheck,
  Key,
} from 'lucide-react'
import { toast } from 'sonner'

interface ProjectDetailsPageProps {
  defaultTab?: 'overview' | 'pulls' | 'reviews' | 'insights' | 'repository' | 'settings'
}

export default function ProjectDetailsPage({ defaultTab = 'overview' }: ProjectDetailsPageProps) {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  // Tab State: Overview | Pull Requests | Reviews | Insights | Repository | Settings
  const [activeTab, setActiveTab] = React.useState<
    'overview' | 'pulls' | 'reviews' | 'insights' | 'repository' | 'settings'
  >(defaultTab)

  // Developer Mode Toggle (Default: OFF)
  const [devMode, setDevMode] = React.useState<boolean>(() => {
    const saved = localStorage.getItem('developer-mode-enabled')
    return saved ? JSON.parse(saved) : false
  })

  const toggleDevMode = (enabled: boolean) => {
    setDevMode(enabled)
    localStorage.setItem('developer-mode-enabled', JSON.stringify(enabled))
    toast.info(enabled ? 'Developer Mode Enabled' : 'Developer Mode Disabled')
  }

  // Fetch single project data with polling during active provisioning or syncing
  const { data: project, isLoading, error } = useQuery<Project>({
    queryKey: ['project', projectId],
    queryFn: () => getProjectById(projectId || ''),
    enabled: !!projectId,
    refetchInterval: (query) => {
      const data = query.state.data
      if (data && (['CREATING', 'CLONING', 'INDEXING'].includes(data.status) || data.sync_status === 'SYNCING')) {
        return 2500
      }
      return false
    },
  })

  // Sync Repository mutation
  const syncMutation = useMutation({
    mutationFn: (id: string) => syncProjectRepository(id),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['project', projectId] })
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      queryClient.invalidateQueries({ queryKey: ['pullRequests', projectId] })
      toast.success(data.message || 'Repository synchronized successfully!')
    },
    onError: (err: Error) => {
      toast.error(`Failed to sync repository: ${err.message}`)
    },
  })

  // Delete Project mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteProject(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      toast.success('Project deleted successfully')
      navigate('/projects')
    },
    onError: (err: Error) => {
      toast.error(`Failed to delete project: ${err.message}`)
    },
  })

  const handleTriggerSync = () => {
    if (project) {
      syncMutation.mutate(project.id)
    }
  }

  const handleDeleteProject = () => {
    if (!project) return
    const name = project.project_name || project.name || 'Project'
    if (window.confirm(`Are you sure you want to delete project "${name}"? This action cannot be undone.`)) {
      deleteMutation.mutate(project.id)
    }
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-6 animate-fade-in text-left">
        <div className="flex items-center gap-2 text-xs text-zinc-500">
          <Skeleton className="h-4 w-12" />
          <ChevronRight className="h-3 w-3" />
          <Skeleton className="h-4 w-24" />
        </div>
        <div className="flex justify-between items-center border-b border-zinc-900 pb-6">
          <div className="space-y-2">
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-4 w-96" />
          </div>
          <Skeleton className="h-10 w-28 rounded-lg" />
        </div>
        <div className="grid gap-6 md:grid-cols-3">
          <Skeleton className="h-48 md:col-span-2 rounded-xl" />
          <Skeleton className="h-48 rounded-xl" />
        </div>
      </div>
    )
  }

  // Error state
  if (error || !project) {
    return (
      <div className="rounded-xl border border-red-950 bg-red-950/10 p-6 text-center select-none text-left max-w-md mx-auto mt-12 space-y-4">
        <AlertCircle className="h-9 w-9 text-red-400 mx-auto" />
        <h3 className="font-bold text-white text-base">Project Not Found</h3>
        <p className="text-xs text-red-300 leading-relaxed">
          {(error as Error)?.message || 'The project could not be found or you do not have permission to view it.'}
        </p>
        <button
          onClick={() => navigate('/projects')}
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-zinc-900 border border-zinc-800 px-4 py-2 text-xs font-semibold text-white hover:bg-zinc-800 transition-colors cursor-pointer w-full"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Projects</span>
        </button>
      </div>
    )
  }

  const name = project.project_name || project.name || 'Untitled Project'
  const owner = project.github_owner || project.repoOwner || 'owner'
  const repo = project.github_repository || project.repoName || 'repo'
  const branch = project.default_branch || project.defaultBranch || 'main'
  const authType = project.auth_type || project.authType || 'connected_account'

  return (
    <div className="space-y-6 animate-fade-in text-left">
      {/* Breadcrumbs Navigation */}
      <div className="flex items-center gap-2 text-xs text-zinc-400">
        <Link to="/projects" className="hover:text-white transition-colors">
          Projects
        </Link>
        <ChevronRight className="h-3.5 w-3.5 text-zinc-600" />
        <span className="text-zinc-300 font-semibold">{name}</span>
      </div>

      {/* Premium Workspace Header */}
      <WorkspaceHeader
        project={project}
        onBack={() => navigate('/projects')}
        onSync={handleTriggerSync}
        isSyncing={syncMutation.isPending}
      />

      {/* Main Tabs Navigation */}
      <div className="flex border-b border-zinc-900 overflow-x-auto gap-2">
        <button
          onClick={() => setActiveTab('overview')}
          className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition-all cursor-pointer whitespace-nowrap flex items-center gap-1.5 ${
            activeTab === 'overview'
              ? 'border-indigo-500 text-white bg-indigo-500/5'
              : 'border-transparent text-zinc-400 hover:text-zinc-200'
          }`}
        >
          <LayoutDashboard className="h-3.5 w-3.5" />
          <span>Overview</span>
        </button>

        <button
          onClick={() => setActiveTab('pulls')}
          className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition-all cursor-pointer whitespace-nowrap flex items-center gap-1.5 ${
            activeTab === 'pulls'
              ? 'border-indigo-500 text-white bg-indigo-500/5'
              : 'border-transparent text-zinc-400 hover:text-zinc-200'
          }`}
        >
          <GitPullRequest className="h-3.5 w-3.5" />
          <span>Pull Requests</span>
        </button>

        <button
          onClick={() => setActiveTab('reviews')}
          className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition-all cursor-pointer whitespace-nowrap flex items-center gap-1.5 ${
            activeTab === 'reviews'
              ? 'border-indigo-500 text-white bg-indigo-500/5'
              : 'border-transparent text-zinc-400 hover:text-zinc-200'
          }`}
        >
          <History className="h-3.5 w-3.5" />
          <span>Reviews</span>
        </button>

        <button
          onClick={() => setActiveTab('insights')}
          className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition-all cursor-pointer whitespace-nowrap flex items-center gap-1.5 ${
            activeTab === 'insights'
              ? 'border-indigo-500 text-white bg-indigo-500/5'
              : 'border-transparent text-zinc-400 hover:text-zinc-200'
          }`}
        >
          <BarChart3 className="h-3.5 w-3.5" />
          <span>Insights</span>
        </button>

        <button
          onClick={() => setActiveTab('repository')}
          className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition-all cursor-pointer whitespace-nowrap flex items-center gap-1.5 ${
            activeTab === 'repository'
              ? 'border-indigo-500 text-white bg-indigo-500/5'
              : 'border-transparent text-zinc-400 hover:text-zinc-200'
          }`}
        >
          <Folder className="h-3.5 w-3.5" />
          <span>Repository</span>
        </button>

        <button
          onClick={() => setActiveTab('settings')}
          className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition-all cursor-pointer whitespace-nowrap flex items-center gap-1.5 ${
            activeTab === 'settings'
              ? 'border-indigo-500 text-white bg-indigo-500/5'
              : 'border-transparent text-zinc-400 hover:text-zinc-200'
          }`}
        >
          <Settings className="h-3.5 w-3.5" />
          <span>Settings</span>
        </button>
      </div>

      {/* Developer Panel Overlay (Only visible when Developer Mode is ON) */}
      {devMode && <DeveloperPanel project={project} />}

      {/* Tab Content */}
      <div className="pt-2 animate-fade-in">
        {/* OVERVIEW TAB */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2">
              <HealthCard project={project} />
              <RepositoryCard project={project} />
              <AIEngineCard />
              <VectorCard project={project} />
            </div>
            <ActivityTimeline project={project} />
          </div>
        )}

        {/* PULL REQUESTS TAB */}
        {activeTab === 'pulls' && <PullRequestList project={project} />}

        {/* REVIEWS TAB */}
        {activeTab === 'reviews' && project && <ReviewList project={project} />}

        {/* INSIGHTS TAB */}
        {activeTab === 'insights' && project && <InsightsDashboard project={project} />}

        {/* REPOSITORY TAB */}
        {activeTab === 'repository' && (
          <div className="space-y-6">
            <RepositoryCard project={project} />
            <VectorCard project={project} />
          </div>
        )}

        {/* SETTINGS TAB */}
        {activeTab === 'settings' && (
          <div className="space-y-6 max-w-4xl">
            {/* General Project Settings */}
            <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-6 space-y-4">
              <h3 className="text-sm font-semibold text-white border-b border-zinc-900 pb-3">
                General Project Settings
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                <div className="space-y-1">
                  <span className="text-[10px] uppercase font-bold text-zinc-500">Project Name</span>
                  <p className="text-white font-semibold">{name}</p>
                </div>
                <div className="space-y-1">
                  <span className="text-[10px] uppercase font-bold text-zinc-500">Repository</span>
                  <p className="text-white font-mono font-semibold">{owner}/{repo}</p>
                </div>
                <div className="space-y-1">
                  <span className="text-[10px] uppercase font-bold text-zinc-500">Default Branch</span>
                  <p className="text-white font-mono font-semibold">{branch}</p>
                </div>
                <div className="space-y-1">
                  <span className="text-[10px] uppercase font-bold text-zinc-500">Auth Method</span>
                  <p className="text-white font-semibold flex items-center gap-1.5">
                    {authType === 'custom_token' ? (
                      <>
                        <Key className="h-3.5 w-3.5 text-amber-400" />
                        <span>Custom Token</span>
                      </>
                    ) : (
                      <>
                        <ShieldCheck className="h-3.5 w-3.5 text-indigo-400" />
                        <span>Connected GitHub Account</span>
                      </>
                    )}
                  </p>
                </div>
              </div>
            </div>

            {/* GitHub Webhook Configuration */}
            <WebhookConfigCard project={project} />

            {/* Developer Mode Toggle */}
            <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-zinc-900 pb-3">
                <div className="flex items-center gap-2">
                  <Terminal className="h-4 w-4 text-amber-400" />
                  <div>
                    <h3 className="text-sm font-semibold text-white">Developer Mode</h3>
                    <p className="text-xs text-zinc-400 mt-0.5">
                      Display project UUIDs, local filesystem clone paths, ChromaDB vector paths, and diagnostics.
                    </p>
                  </div>
                </div>

                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={devMode}
                    onChange={(e) => toggleDevMode(e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-zinc-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-zinc-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
                </label>
              </div>

              <p className="text-xs text-zinc-400 leading-relaxed">
                Developer Mode is currently <strong className={devMode ? 'text-amber-400' : 'text-zinc-400'}>{devMode ? 'ENABLED' : 'DISABLED'}</strong>.
              </p>
            </div>

            {/* Danger Zone: Delete Project */}
            <div className="rounded-xl border border-red-950/60 bg-red-950/10 p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-red-900/40 pb-3">
                <div>
                  <h3 className="text-sm font-semibold text-white">Danger Zone</h3>
                  <p className="text-xs text-red-300 mt-0.5">
                    Irreversibly delete this project record, local repository clone, and vector store data.
                  </p>
                </div>
                <button
                  onClick={handleDeleteProject}
                  disabled={deleteMutation.isPending}
                  className="inline-flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-xs font-bold text-white hover:bg-red-500 transition-colors shadow-sm disabled:opacity-50 cursor-pointer shrink-0"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  <span>Delete Project</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
