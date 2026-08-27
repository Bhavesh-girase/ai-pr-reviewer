import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { Project } from '@/types/project'
import {
  getProjectWebhookStatus,
  registerProjectWebhook,
  retryProjectWebhook,
  deleteProjectWebhook,
  syncProjectPullRequests,
} from '@/api/webhooks'
import {
  Webhook,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Loader2,
  PauseCircle,
  Copy,
  Check,
  ShieldCheck,
  Zap,
} from 'lucide-react'
import { toast } from 'sonner'

interface WebhookConfigCardProps {
  project: Project
}

export const WebhookConfigCard: React.FC<WebhookConfigCardProps> = ({ project }) => {
  const queryClient = useQueryClient()
  const [copiedUrl, setCopiedUrl] = useState(false)

  // Query live webhook status
  const { data: webhookStatus, isLoading, refetch } = useQuery({
    queryKey: ['projectWebhookStatus', project.id],
    queryFn: () => getProjectWebhookStatus(project.id),
    staleTime: 10000,
  })

  // Register Webhook mutation
  const registerMutation = useMutation({
    mutationFn: () => registerProjectWebhook(project.id),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['projectWebhookStatus', project.id] })
      queryClient.invalidateQueries({ queryKey: ['pullRequests', project.id] })
      queryClient.invalidateQueries({ queryKey: ['project', project.id] })
      toast.success(data.message || 'Webhook registered successfully!')
    },
    onError: (err: Error) => {
      toast.error(`Registration failed: ${err.message}`)
    },
  })

  // Retry Webhook mutation
  const retryMutation = useMutation({
    mutationFn: () => retryProjectWebhook(project.id),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['projectWebhookStatus', project.id] })
      queryClient.invalidateQueries({ queryKey: ['pullRequests', project.id] })
      toast.success(data.message || 'Webhook re-registered successfully!')
    },
    onError: (err: Error) => {
      toast.error(`Retry failed: ${err.message}`)
    },
  })

  // Delete Webhook mutation
  const deleteMutation = useMutation({
    mutationFn: () => deleteProjectWebhook(project.id),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['projectWebhookStatus', project.id] })
      queryClient.invalidateQueries({ queryKey: ['project', project.id] })
      toast.info(data.message || 'Webhook disabled.')
    },
    onError: (err: Error) => {
      toast.error(`Failed to disable webhook: ${err.message}`)
    },
  })

  // Manual PR Sync mutation
  const syncPrsMutation = useMutation({
    mutationFn: () => syncProjectPullRequests(project.id),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['pullRequests', project.id] })
      toast.success(data.message || `Synchronized ${data.synced_prs_count} pull requests!`)
    },
    onError: (err: Error) => {
      toast.error(`Sync failed: ${err.message}`)
    },
  })

  const status = webhookStatus?.webhook_status || project.webhook_status || 'NOT_REGISTERED'
  const isRegistered = status === 'ACTIVE'
  const isFailed = status === 'FAILED'
  const isRegistering = status === 'REGISTERING' || registerMutation.isPending || retryMutation.isPending
  const isSyncing = syncPrsMutation.isPending

  const handleCopyUrl = () => {
    if (webhookStatus?.webhook_url) {
      navigator.clipboard.writeText(webhookStatus.webhook_url)
      setCopiedUrl(true)
      setTimeout(() => setCopiedUrl(false), 2000)
    }
  }

  const renderStatusBadge = () => {
    switch (status) {
      case 'ACTIVE':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="h-3 w-3" />
            <span>Active</span>
          </span>
        )
      case 'REGISTERING':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <Loader2 className="h-3 w-3 animate-spin" />
            <span>Registering</span>
          </span>
        )
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-red-500/10 text-red-400 border border-red-500/20">
            <AlertTriangle className="h-3 w-3" />
            <span>Registration Failed</span>
          </span>
        )
      case 'DISABLED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <PauseCircle className="h-3 w-3" />
            <span>Disabled</span>
          </span>
        )
      case 'NOT_REGISTERED':
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-zinc-800 text-zinc-400 border border-zinc-700">
            <span>Not Registered</span>
          </span>
        )
    }
  }

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-6 space-y-5 shadow-sm text-left">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-zinc-900 pb-3 flex-wrap gap-2">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <Webhook className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">GitHub Webhook Integration</h3>
            <p className="text-xs text-zinc-400 mt-0.5">
              Event-driven synchronization for Pull Requests and repository updates.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {renderStatusBadge()}
          <button
            onClick={() => refetch()}
            disabled={isLoading}
            className="p-1 rounded-md text-zinc-500 hover:text-zinc-300 hover:bg-zinc-900 transition-colors cursor-pointer"
            title="Refresh Webhook Status"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin text-indigo-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* Details Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
        {/* Webhook URL Display */}
        <div className="space-y-1 sm:col-span-2">
          <span className="text-[10px] uppercase font-bold text-zinc-500">Receiver Endpoint URL</span>
          <div className="flex items-center gap-2 bg-zinc-900/90 border border-zinc-800 rounded-lg px-3 py-2">
            <code className="font-mono text-zinc-300 text-[11px] truncate flex-1 select-all">
              {webhookStatus?.webhook_url || 'https://api.yourdomain.com/webhooks/github'}
            </code>
            <button
              onClick={handleCopyUrl}
              className="text-zinc-400 hover:text-white p-1 rounded transition-colors cursor-pointer"
              title="Copy Webhook URL"
            >
              {copiedUrl ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
            </button>
          </div>
        </div>

        {/* Timestamps */}
        <div className="space-y-1">
          <span className="text-[10px] uppercase font-bold text-zinc-500">Registered On</span>
          <p className="text-zinc-300 font-mono">
            {webhookStatus?.webhook_registered_at
              ? new Date(webhookStatus.webhook_registered_at).toLocaleString()
              : 'Not registered yet'}
          </p>
        </div>

        <div className="space-y-1">
          <span className="text-[10px] uppercase font-bold text-zinc-500">Last Received Event</span>
          <p className="text-zinc-300 font-mono">
            {webhookStatus?.last_webhook_event_at
              ? new Date(webhookStatus.last_webhook_event_at).toLocaleString()
              : 'No events received yet'}
          </p>
        </div>
      </div>

      {/* Security Info Banner */}
      <div className="flex items-start gap-2.5 p-3 rounded-lg bg-zinc-900/40 border border-zinc-850 text-xs text-zinc-400">
        <ShieldCheck className="h-4 w-4 text-indigo-400 shrink-0 mt-0.5" />
        <p className="leading-relaxed text-[11px]">
          HMAC-SHA256 signatures are verified for all incoming events. Webhook secrets are cryptographically generated and encrypted using AES-256 on the backend.
        </p>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-between pt-2 border-t border-zinc-900 flex-wrap gap-2">
        <div className="flex items-center gap-2">
          {/* Manual PR Sync button */}
          <button
            onClick={() => syncPrsMutation.mutate()}
            disabled={isSyncing}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-xs font-semibold text-zinc-200 transition-colors cursor-pointer disabled:opacity-50"
          >
            {isSyncing ? (
              <Loader2 className="h-3.5 w-3.5 text-indigo-400 animate-spin" />
            ) : (
              <RefreshCw className="h-3.5 w-3.5 text-zinc-400" />
            )}
            <span>{isSyncing ? 'Syncing PRs...' : 'Sync Pull Requests'}</span>
          </button>
        </div>

        <div className="flex items-center gap-2">
          {/* Register / Retry / Disable button */}
          {isRegistered ? (
            <button
              onClick={() => {
                if (window.confirm('Are you sure you want to unregister and disable the GitHub webhook for this repository?')) {
                  deleteMutation.mutate()
                }
              }}
              disabled={deleteMutation.isPending}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-zinc-900 hover:bg-red-950/40 border border-zinc-800 hover:border-red-900/50 text-xs font-semibold text-zinc-400 hover:text-red-400 transition-colors cursor-pointer disabled:opacity-50"
            >
              {deleteMutation.isPending ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <PauseCircle className="h-3.5 w-3.5" />
              )}
              <span>Disable Webhook</span>
            </button>
          ) : isFailed ? (
            <button
              onClick={() => retryMutation.mutate()}
              disabled={isRegistering}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-xs font-bold text-white transition-colors cursor-pointer disabled:opacity-50"
            >
              {isRegistering ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin text-white" />
              ) : (
                <RefreshCw className="h-3.5 w-3.5" />
              )}
              <span>Retry Registration</span>
            </button>
          ) : (
            <button
              onClick={() => registerMutation.mutate()}
              disabled={isRegistering}
              className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-bold text-white shadow-sm shadow-indigo-600/20 transition-all cursor-pointer hover:scale-105 disabled:opacity-50"
            >
              {isRegistering ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin text-white" />
              ) : (
                <Zap className="h-3.5 w-3.5" />
              )}
              <span>Register Webhook</span>
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
