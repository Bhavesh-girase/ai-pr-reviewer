import { useState, useEffect, useCallback } from 'react'
import {
  getGitHubStatus,
  testGitHubConnection,
  connectGitHubAccount,
  disconnectGitHubAccount,
  type GitHubStatus,
  type GitHubTestResult
} from '@/api/githubSettings'

export function useGitHubIntegration() {
  const [status, setStatus] = useState<GitHubStatus>({
    connected: false,
    username: null,
    avatar_url: null,
    name: null
  })
  const [loading, setLoading] = useState<boolean>(true)
  const [testing, setTesting] = useState<boolean>(false)
  const [connecting, setConnecting] = useState<boolean>(false)
  const [disconnecting, setDisconnecting] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [testResult, setTestResult] = useState<GitHubTestResult | null>(null)

  const fetchStatus = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getGitHubStatus()
      setStatus(data)
    } catch (err: any) {
      console.error('Failed to load GitHub status:', err)
      setError(err.message || 'Failed to load GitHub connection status')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchStatus()
  }, [fetchStatus])

  const handleTestConnection = async (token: string) => {
    if (!token.trim()) {
      setError('Please enter a GitHub Personal Access Token.')
      return false
    }
    setTesting(true)
    setError(null)
    setSuccessMessage(null)
    setTestResult(null)
    try {
      const result = await testGitHubConnection(token)
      setTestResult(result)
      setSuccessMessage(`Token verified! Connected as @${result.username}`)
      return true
    } catch (err: any) {
      setError(err.message || 'Failed to test connection to GitHub.')
      return false
    } finally {
      setTesting(false)
    }
  }

  const handleConnect = async (token: string) => {
    if (!token.trim()) {
      setError('Please enter a GitHub Personal Access Token.')
      return false
    }
    setConnecting(true)
    setError(null)
    setSuccessMessage(null)
    try {
      const result = await connectGitHubAccount(token)
      setStatus({
        connected: true,
        username: result.username,
        avatar_url: result.avatar_url,
        name: result.name
      })
      setSuccessMessage('GitHub account connected successfully!')
      setTestResult(null)
      return true
    } catch (err: any) {
      setError(err.message || 'Failed to connect GitHub account.')
      return false
    } finally {
      setConnecting(false)
    }
  }

  const handleDisconnect = async () => {
    setDisconnecting(true)
    setError(null)
    setSuccessMessage(null)
    try {
      await disconnectGitHubAccount()
      setStatus({
        connected: false,
        username: null,
        avatar_url: null,
        name: null
      })
      setSuccessMessage('GitHub account disconnected.')
      setTestResult(null)
      return true
    } catch (err: any) {
      setError(err.message || 'Failed to disconnect GitHub account.')
      return false
    } finally {
      setDisconnecting(false)
    }
  }

  const clearMessages = () => {
    setError(null)
    setSuccessMessage(null)
  }

  return {
    status,
    loading,
    testing,
    connecting,
    disconnecting,
    error,
    successMessage,
    testResult,
    refetchStatus: fetchStatus,
    testConnection: handleTestConnection,
    connectAccount: handleConnect,
    disconnectAccount: handleDisconnect,
    clearMessages
  }
}
