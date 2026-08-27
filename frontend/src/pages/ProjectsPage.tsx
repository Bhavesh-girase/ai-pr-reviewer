import * as React from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getProjects, createProject, updateProject, deleteProject } from '@/api/projects'
import type { Project, CreateProjectInput } from '@/types/project'
import ProjectCard from '@/components/projects/ProjectCard'
import ProjectModal from '@/components/projects/ProjectModal'
import ProjectEmptyState from '@/components/projects/ProjectEmptyState'
import { Skeleton } from '@/components/ui/skeleton'
import { Plus, Search, Folder, RefreshCw } from 'lucide-react'
import { toast } from 'sonner'

export default function ProjectsPage() {
  const queryClient = useQueryClient()
  const [isModalOpen, setIsModalOpen] = React.useState(false)
  const [editingProject, setEditingProject] = React.useState<Project | null>(null)
  const [searchQuery, setSearchQuery] = React.useState('')

  // Fetch projects list with polling for non-terminal provisioning states
  const { data: projects = [], isLoading, isRefetching, refetch, error } = useQuery<Project[]>({
    queryKey: ['projects'],
    queryFn: getProjects,
    refetchInterval: (query) => {
      const data = query.state.data
      if (!data || !Array.isArray(data)) return false
      const isProvisioning = data.some((p) =>
        ['CREATING', 'CLONING', 'INDEXING'].includes(p.status)
      )
      return isProvisioning ? 3000 : false
    },
  })

  // Create Project Mutation
  const createMutation = useMutation({
    mutationFn: createProject,
    onSuccess: (newProj) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      const pName = newProj.project_name || newProj.name || 'Project'
      toast.success(`Started provisioning project "${pName}"`)
    },
    onError: (err: Error) => {
      toast.error(`Failed to create project: ${err.message}`)
    },
  })

  // Update Project Mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, input }: { id: string; input: Partial<CreateProjectInput> }) =>
      updateProject(id, input),
    onSuccess: (updatedProj) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      const pName = updatedProj.project_name || updatedProj.name || 'Project'
      toast.success(`Project "${pName}" updated`)
    },
    onError: (err: Error) => {
      toast.error(`Failed to update project: ${err.message}`)
    },
  })

  // Delete Project Mutation with Optimistic UI Update
  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteProject(id),
    onMutate: async (id: string) => {
      await queryClient.cancelQueries({ queryKey: ['projects'] })
      const previousProjects = queryClient.getQueryData<Project[]>(['projects'])

      const target = previousProjects?.find((p) => p.id === id)
      queryClient.setQueryData<Project[]>(['projects'], (old = []) =>
        old.filter((p) => p.id !== id)
      )

      return { previousProjects, target }
    },
    onSuccess: (_, __, context) => {
      const pName = context?.target?.project_name || context?.target?.name || 'Project'
      toast.success(`Deleted project "${pName}" and workspace files`)
    },
    onError: (err: Error, _, context) => {
      if (context?.previousProjects) {
        queryClient.setQueryData(['projects'], context.previousProjects)
      }
      toast.error(`Failed to delete project: ${err.message}`)
    },
  })

  const handleModalSubmit = async (data: CreateProjectInput) => {
    if (editingProject) {
      await updateMutation.mutateAsync({ id: editingProject.id, input: data })
    } else {
      await createMutation.mutateAsync(data)
    }
  }

  const handleOpenCreateModal = () => {
    setEditingProject(null)
    setIsModalOpen(true)
  }

  const handleOpenEditModal = (project: Project) => {
    setEditingProject(project)
    setIsModalOpen(true)
  }

  const handleDeleteProject = (project: Project) => {
    const pName = project.project_name || project.name || 'Project'
    if (window.confirm(`Are you sure you want to delete project "${pName}" and its storage files?`)) {
      deleteMutation.mutate(project.id)
    }
  }

  // Filter projects by search query
  const filteredProjects = projects.filter((p) => {
    const q = searchQuery.toLowerCase().trim()
    if (!q) return true
    const pName = (p.project_name || p.name || '').toLowerCase()
    const owner = (p.github_owner || p.repoOwner || '').toLowerCase()
    const repo = (p.github_repository || p.repoName || '').toLowerCase()
    const branch = (p.default_branch || p.defaultBranch || '').toLowerCase()
    return pName.includes(q) || owner.includes(q) || repo.includes(q) || branch.includes(q)
  })

  return (
    <div className="space-y-8 animate-fade-in text-left">
      {/* Top Header Section */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-zinc-900 pb-6">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded-lg bg-white flex items-center justify-center text-zinc-950 shadow-md">
              <Folder className="h-4.5 w-4.5" />
            </div>
            <h1 className="text-3xl font-bold tracking-tight text-white leading-none">Projects</h1>
          </div>
          <p className="text-xs text-zinc-400 mt-2">
            Provisioned workspaces for repository cloning, vector indexing, and AI reviews.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => refetch()}
            disabled={isRefetching}
            className="p-2 rounded-lg border border-zinc-800 bg-zinc-900 text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors cursor-pointer"
            title="Refresh projects list"
          >
            <RefreshCw className={`h-4 w-4 ${isRefetching ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={handleOpenCreateModal}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-white px-4 py-2.5 text-xs font-bold text-zinc-950 hover:bg-zinc-200 transition-all shadow-md cursor-pointer shrink-0"
          >
            <Plus className="h-4 w-4" />
            <span>+ New Project</span>
          </button>
        </div>
      </div>

      {/* Backend Error Notification */}
      {error && (
        <div className="p-4 rounded-xl bg-red-950/30 border border-red-900 text-red-300 text-xs flex justify-between items-center">
          <span>Failed to connect to backend database: {(error as Error).message}</span>
          <button onClick={() => refetch()} className="underline hover:text-white font-semibold">
            Retry
          </button>
        </div>
      )}

      {/* Main Content Area */}
      {isLoading ? (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="rounded-xl border border-zinc-800 p-5 space-y-4">
              <div className="flex justify-between items-center">
                <Skeleton className="h-6 w-3/4" />
                <Skeleton className="h-6 w-6 rounded-full" />
              </div>
              <Skeleton className="h-4 w-1/2" />
              <div className="flex gap-2 pt-2">
                <Skeleton className="h-5 w-20 rounded-full" />
                <Skeleton className="h-5 w-20 rounded-full" />
              </div>
              <Skeleton className="h-4 w-full pt-4" />
            </div>
          ))}
        </div>
      ) : projects.length === 0 ? (
        <ProjectEmptyState onCreateProject={handleOpenCreateModal} />
      ) : (
        <div className="space-y-6">
          {/* Search Bar */}
          <div className="flex items-center gap-3">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-zinc-500" />
              <input
                type="text"
                placeholder="Filter projects by name, owner, or repo..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-xl border border-zinc-800 bg-zinc-950/60 pl-9 pr-4 py-2 text-xs text-white placeholder-zinc-500 focus:border-indigo-500 focus:outline-none transition-colors"
              />
            </div>
            <span className="text-xs text-zinc-400 font-mono">
              {filteredProjects.length} {filteredProjects.length === 1 ? 'project' : 'projects'}
            </span>
          </div>

          {/* Cards Grid */}
          {filteredProjects.length === 0 ? (
            <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-8 text-center text-zinc-400 text-xs">
              No projects match "{searchQuery}"
            </div>
          ) : (
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {filteredProjects.map((project) => (
                <ProjectCard
                  key={project.id}
                  project={project}
                  onEdit={handleOpenEditModal}
                  onDelete={handleDeleteProject}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* New / Edit Project Modal */}
      <ProjectModal
        open={isModalOpen}
        onOpenChange={setIsModalOpen}
        onSubmit={handleModalSubmit}
        existingProjects={projects}
        editingProject={editingProject}
        isLoading={createMutation.isPending || updateMutation.isPending}
      />
    </div>
  )
}
