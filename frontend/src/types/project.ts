export type ProjectStatus = 'CREATING' | 'CLONING' | 'INDEXING' | 'READY' | 'FAILED'
export type ProjectSyncStatus = 'READY' | 'SYNCING' | 'SYNC_FAILED' | string
export type AuthType = 'connected_account' | 'custom_token'

export interface Project {
  id: string
  user_id?: string
  project_name: string
  github_owner: string
  github_repository: string
  default_branch: string
  auth_type: AuthType
  custom_token?: string
  clone_path?: string
  chroma_path?: string
  current_commit_hash?: string
  last_indexed_at?: string
  last_synced_at?: string
  status: ProjectStatus
  sync_status?: ProjectSyncStatus
  sync_error_message?: string | null
  last_sync_started_at?: string | null
  last_sync_completed_at?: string | null
  github_webhook_id?: number | null
  webhook_status?: 'NOT_REGISTERED' | 'REGISTERING' | 'ACTIVE' | 'FAILED' | 'DISABLED' | string
  webhook_registered_at?: string | null
  last_webhook_event_at?: string | null
  error_message?: string
  created_at?: string
  updated_at?: string

  // Optional Frontend Display Aliases
  name?: string
  repoOwner?: string
  repoName?: string
  defaultBranch?: string
  authType?: AuthType
  customToken?: string
  createdAt?: string
  lastSyncTime?: string
}

export interface ProjectSyncResponse {
  status: string
  current_commit?: string | null
  last_synced_at?: string | null
  last_indexed_at?: string | null
  changed_files_count: number
  message: string
}

export interface ProjectSyncStatusResponse {
  project_id: string
  status: string
  sync_status: string
  current_commit_hash?: string | null
  last_synced_at?: string | null
  last_indexed_at?: string | null
  last_sync_started_at?: string | null
  last_sync_completed_at?: string | null
  sync_error_message?: string | null
  is_syncing: boolean
}

export interface CreateProjectInput {
  project_name: string
  github_owner: string
  github_repository: string
  default_branch: string
  auth_type: AuthType
  custom_token?: string
}

export interface UpdateProjectInput {
  project_name?: string
  github_owner?: string
  github_repository?: string
  default_branch?: string
  auth_type?: AuthType
  custom_token?: string
}
