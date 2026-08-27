import * as React from 'react'
import {
  Dialog,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
} from '@/components/ui/dialog'
import type { Project, CreateProjectInput, AuthType } from '@/types/project'
import { Folder, GitBranch, Key, AlertCircle, Loader2 } from 'lucide-react'

// Local Github icon SVG component to avoid lucide import inconsistencies
function GithubIcon({ className = "h-4 w-4" }: { className?: string }) {
  return (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
    </svg>
  )
}

interface ProjectModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSubmit: (data: CreateProjectInput) => Promise<void>
  existingProjects: Project[]
  editingProject?: Project | null
  isLoading?: boolean
}

export default function ProjectModal({
  open,
  onOpenChange,
  onSubmit,
  existingProjects,
  editingProject,
  isLoading = false,
}: ProjectModalProps) {
  const [name, setName] = React.useState('')
  const [repoOwner, setRepoOwner] = React.useState('')
  const [repoName, setRepoName] = React.useState('')
  const [defaultBranch, setDefaultBranch] = React.useState('main')
  const [authType, setAuthType] = React.useState<AuthType>('connected_account')
  const [customToken, setCustomToken] = React.useState('')

  const [errors, setErrors] = React.useState<Record<string, string>>({})

  // Populate fields if editing
  React.useEffect(() => {
    if (editingProject) {
      setName(editingProject.project_name || editingProject.name || '')
      setRepoOwner(editingProject.github_owner || editingProject.repoOwner || '')
      setRepoName(editingProject.github_repository || editingProject.repoName || '')
      setDefaultBranch(editingProject.default_branch || editingProject.defaultBranch || 'main')
      setAuthType(editingProject.auth_type || editingProject.authType || 'connected_account')
      setCustomToken(editingProject.custom_token || editingProject.customToken || '')
    } else {
      setName('')
      setRepoOwner('')
      setRepoName('')
      setDefaultBranch('main')
      setAuthType('connected_account')
      setCustomToken('')
    }
    setErrors({})
  }, [editingProject, open])

  // Validation logic
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!name.trim()) {
      newErrors.name = 'Project name is required'
    } else {
      const isDuplicate = existingProjects.some(
        (p) =>
          (p.project_name || p.name || '').toLowerCase() === name.trim().toLowerCase() &&
          p.id !== editingProject?.id
      )
      if (isDuplicate) {
        newErrors.name = 'A project with this name already exists'
      }
    }

    if (!repoOwner.trim()) {
      newErrors.repoOwner = 'Repository owner is required'
    } else if (!/^[a-zA-Z0-9_.-]+$/.test(repoOwner.trim())) {
      newErrors.repoOwner = 'Invalid format for repository owner'
    }

    if (!repoName.trim()) {
      newErrors.repoName = 'Repository name is required'
    } else if (!/^[a-zA-Z0-9_.-]+$/.test(repoName.trim())) {
      newErrors.repoName = 'Invalid format for repository name'
    }

    if (!defaultBranch.trim()) {
      newErrors.defaultBranch = 'Default branch is required'
    }

    if (authType === 'custom_token' && !customToken.trim() && !editingProject) {
      newErrors.customToken = 'GitHub Token is required when custom token authentication is selected'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validateForm()) return

    await onSubmit({
      project_name: name.trim(),
      github_owner: repoOwner.trim(),
      github_repository: repoName.trim(),
      default_branch: defaultBranch.trim() || 'main',
      auth_type: authType,
      custom_token: authType === 'custom_token' ? customToken.trim() : undefined,
    })

    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogClose onClick={() => onOpenChange(false)} />
      
      <DialogHeader>
        <div className="flex items-center gap-2.5 mb-1">
          <div className="h-8 w-8 rounded-lg bg-zinc-900 border border-zinc-800 flex items-center justify-center text-white">
            <Folder className="h-4 w-4" />
          </div>
          <DialogTitle>
            {editingProject ? 'Edit Project' : 'Create New Project'}
          </DialogTitle>
        </div>
        <DialogDescription>
          {editingProject
            ? 'Update your repository connection settings and credentials.'
            : 'Provision a new project workspace, clone source code, and create vector search indexes.'}
        </DialogDescription>
      </DialogHeader>

      <form onSubmit={handleSubmit} className="space-y-4 mt-4 text-left">
        {/* Project Name */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-zinc-300 flex items-center gap-1">
            <span>Project Name</span>
            <span className="text-red-400">*</span>
          </label>
          <input
            type="text"
            placeholder="e.g. Main SaaS Backend"
            value={name}
            onChange={(e) => {
              setName(e.target.value)
              if (errors.name) setErrors((prev) => ({ ...prev, name: '' }))
            }}
            className="w-full rounded-lg border border-zinc-800 bg-zinc-900/60 px-3 py-2 text-xs text-white placeholder-zinc-500 focus:border-indigo-500 focus:outline-none transition-colors"
          />
          {errors.name && (
            <p className="text-[11px] text-red-400 flex items-center gap-1 mt-1">
              <AlertCircle className="h-3 w-3" />
              <span>{errors.name}</span>
            </p>
          )}
        </div>

        {/* Repository Owner & Name Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-zinc-300 flex items-center gap-1">
              <span>Repository Owner</span>
              <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              placeholder="e.g. facebook"
              value={repoOwner}
              onChange={(e) => {
                setRepoOwner(e.target.value)
                if (errors.repoOwner) setErrors((prev) => ({ ...prev, repoOwner: '' }))
              }}
              className="w-full rounded-lg border border-zinc-800 bg-zinc-900/60 px-3 py-2 text-xs text-white placeholder-zinc-500 focus:border-indigo-500 focus:outline-none transition-colors"
            />
            {errors.repoOwner && (
              <p className="text-[11px] text-red-400 flex items-center gap-1 mt-1">
                <AlertCircle className="h-3 w-3" />
                <span>{errors.repoOwner}</span>
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-zinc-300 flex items-center gap-1">
              <span>Repository Name</span>
              <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              placeholder="e.g. react"
              value={repoName}
              onChange={(e) => {
                setRepoName(e.target.value)
                if (errors.repoName) setErrors((prev) => ({ ...prev, repoName: '' }))
              }}
              className="w-full rounded-lg border border-zinc-800 bg-zinc-900/60 px-3 py-2 text-xs text-white placeholder-zinc-500 focus:border-indigo-500 focus:outline-none transition-colors"
            />
            {errors.repoName && (
              <p className="text-[11px] text-red-400 flex items-center gap-1 mt-1">
                <AlertCircle className="h-3 w-3" />
                <span>{errors.repoName}</span>
              </p>
            )}
          </div>
        </div>

        {/* Default Branch */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-zinc-300 flex items-center gap-1">
            <GitBranch className="h-3.5 w-3.5 text-zinc-400" />
            <span>Default Branch</span>
            <span className="text-red-400">*</span>
          </label>
          <input
            type="text"
            placeholder="e.g. main"
            value={defaultBranch}
            onChange={(e) => {
              setDefaultBranch(e.target.value)
              if (errors.defaultBranch) setErrors((prev) => ({ ...prev, defaultBranch: '' }))
            }}
            className="w-full rounded-lg border border-zinc-800 bg-zinc-900/60 px-3 py-2 text-xs text-white placeholder-zinc-500 focus:border-indigo-500 focus:outline-none transition-colors"
          />
          {errors.defaultBranch && (
            <p className="text-[11px] text-red-400 flex items-center gap-1 mt-1">
              <AlertCircle className="h-3 w-3" />
              <span>{errors.defaultBranch}</span>
            </p>
          )}
        </div>

        {/* Authentication selection */}
        <div className="space-y-2 pt-2 border-t border-zinc-900">
          <label className="text-xs font-semibold text-zinc-300 block">
            Authentication Method
          </label>
          
          <div className="space-y-2">
            <label className="flex items-start gap-3 p-3 rounded-lg border border-zinc-800 bg-zinc-900/40 hover:bg-zinc-900/80 transition-colors cursor-pointer">
              <input
                type="radio"
                name="authType"
                value="connected_account"
                checked={authType === 'connected_account'}
                onChange={() => setAuthType('connected_account')}
                className="mt-0.5 text-indigo-500 focus:ring-indigo-500 bg-zinc-950 border-zinc-700"
              />
              <div>
                <div className="flex items-center gap-1.5 text-xs font-semibold text-white">
                  <GithubIcon className="h-3.5 w-3.5 text-indigo-400" />
                  <span>Use Connected GitHub Account</span>
                </div>
                <p className="text-[11px] text-zinc-400 mt-0.5">
                  Authenticate using your OAuth access grant linked in Settings.
                </p>
              </div>
            </label>

            <label className="flex items-start gap-3 p-3 rounded-lg border border-zinc-800 bg-zinc-900/40 hover:bg-zinc-900/80 transition-colors cursor-pointer">
              <input
                type="radio"
                name="authType"
                value="custom_token"
                checked={authType === 'custom_token'}
                onChange={() => setAuthType('custom_token')}
                className="mt-0.5 text-indigo-500 focus:ring-indigo-500 bg-zinc-950 border-zinc-700"
              />
              <div>
                <div className="flex items-center gap-1.5 text-xs font-semibold text-white">
                  <Key className="h-3.5 w-3.5 text-amber-400" />
                  <span>Use Custom GitHub Token</span>
                </div>
                <p className="text-[11px] text-zinc-400 mt-0.5">
                  Supply a repository-scoped Personal Access Token (PAT).
                </p>
              </div>
            </label>
          </div>
        </div>

        {/* Custom GitHub Token field */}
        {authType === 'custom_token' && (
          <div className="space-y-1.5 animate-fade-in pl-1">
            <label className="text-xs font-semibold text-zinc-300 flex items-center gap-1">
              <span>GitHub Token</span>
              <span className="text-red-400">*</span>
            </label>
            <input
              type="password"
              placeholder="ghp_************************************"
              value={customToken}
              onChange={(e) => {
                setCustomToken(e.target.value)
                if (errors.customToken) setErrors((prev) => ({ ...prev, customToken: '' }))
              }}
              className="w-full rounded-lg border border-zinc-800 bg-zinc-900/60 px-3 py-2 text-xs font-mono text-white placeholder-zinc-500 focus:border-amber-500 focus:outline-none transition-colors"
            />
            {errors.customToken && (
              <p className="text-[11px] text-red-400 flex items-center gap-1 mt-1">
                <AlertCircle className="h-3 w-3" />
                <span>{errors.customToken}</span>
              </p>
            )}
          </div>
        )}

        <DialogFooter>
          <button
            type="button"
            onClick={() => onOpenChange(false)}
            className="rounded-lg border border-zinc-800 bg-zinc-900 px-4 py-2 text-xs font-semibold text-zinc-300 hover:bg-zinc-800 transition-colors cursor-pointer"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isLoading}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-white px-4 py-2 text-xs font-bold text-zinc-950 hover:bg-zinc-200 transition-colors shadow-sm disabled:opacity-50 cursor-pointer"
          >
            {isLoading && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            <span>{editingProject ? 'Save Changes' : 'Provision Project'}</span>
          </button>
        </DialogFooter>
      </form>
    </Dialog>
  )
}
