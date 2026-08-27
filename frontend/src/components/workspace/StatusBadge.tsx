import type { ProjectStatus } from '@/types/project'
import { Badge } from '@/components/ui/badge'
import { CheckCircle2, RefreshCw, AlertCircle, Clock, Loader2 } from 'lucide-react'

interface StatusBadgeProps {
  status: ProjectStatus
  errorMessage?: string
}

export default function StatusBadge({ status, errorMessage }: StatusBadgeProps) {
  switch (status) {
    case 'READY':
      return (
        <Badge variant="success">
          <CheckCircle2 className="h-3 w-3" />
          <span>Workspace Ready</span>
        </Badge>
      )
    case 'INDEXING':
      return (
        <Badge variant="info">
          <RefreshCw className="h-3 w-3 animate-spin" />
          <span>Building AI Workspace</span>
        </Badge>
      )
    case 'CLONING':
      return (
        <Badge variant="warning">
          <Loader2 className="h-3 w-3 animate-spin" />
          <span>Preparing Repository</span>
        </Badge>
      )
    case 'CREATING':
      return (
        <Badge variant="secondary">
          <Clock className="h-3 w-3 animate-pulse" />
          <span>Provisioning Workspace</span>
        </Badge>
      )
    case 'FAILED':
    default:
      return (
        <Badge variant="destructive" title={errorMessage || 'Provisioning failed'}>
          <AlertCircle className="h-3 w-3" />
          <span>Attention Required</span>
        </Badge>
      )
  }
}
