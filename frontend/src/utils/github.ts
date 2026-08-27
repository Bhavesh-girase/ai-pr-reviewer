import { type ReviewIssue } from '@/types/review'

/**
 * Parses a GitHub Pull Request URL and extracts the owner, repository name, and pull request number.
 * Supported formats:
 * - https://github.com/owner/repo/pull/number
 * - http://github.com/owner/repo/pull/number
 * - github.com/owner/repo/pull/number
 */
export function parseGitHubPrUrl(url: string): { owner: string; repo: string; pullNumber: number } | null {
  try {
    const trimmed = url.trim()
    if (!trimmed) return null

    const regex = /github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/i
    const match = trimmed.match(regex)

    if (match) {
      const owner = match[1]
      const repo = match[2]
      const pullNumber = parseInt(match[3], 10)

      if (owner && repo && !isNaN(pullNumber)) {
        return { owner, repo, pullNumber }
      }
    }
  } catch (e) {
    console.error('Failed parsing GitHub PR URL:', e)
  }
  return null
}

/**
 * Attempts to retrieve raw file content from GitHub public repositories.
 */
export async function fetchFileContentFromGitHub(
  owner: string,
  repo: string,
  filename: string
): Promise<string | null> {
  try {
    const url = `https://raw.githubusercontent.com/${owner}/${repo}/main/${filename}`
    const response = await fetch(url)
    if (response.ok) {
      return await response.text()
    }
  } catch (error) {
    console.warn('Network or CORS block while fetching file content, falling back to mock generator.', error)
  }
  return null
}

/**
 * Generates syntactically correct mock code based on file extension
 * and weaves annotations directly into the lines of the detected issues.
 */
export function generateMockCode(filename: string, issues: ReviewIssue[]): string {
  const ext = filename.split('.').pop()?.toLowerCase() || ''
  const lines: string[] = []

  // Create standard file templates
  if (ext === 'tsx' || ext === 'jsx') {
    lines.push(
      "import { useState, useEffect } from 'react'",
      "",
      "interface AppProps {",
      "  title?: string",
      "}",
      "",
      "export default function AppComponent({ title = 'AI Code Reviewer' }: AppProps) {",
      "  const [active, setActive] = useState<boolean>(false)",
      "  const [logs, setLogs] = useState<string[]>([])",
      "",
      "  useEffect(() => {",
      "    console.log('Component initialized')",
      "  }, [])",
      "",
      "  const handleProcess = () => {",
      "    try {",
      "      setActive(true)",
      "      setLogs(prev => [...prev, 'Process started'])",
      "    } catch (err) {",
      "      console.error(err)",
      "    }",
      "  }",
      "",
      "  return (",
      "    <div className=\"flex flex-col gap-4 p-6 border rounded-lg bg-card text-card-foreground shadow\">",
      "      <h3 className=\"text-lg font-bold\">{title}</h3>",
      "      <p className=\"text-xs text-muted-foreground\">Review suggestions are highlighted.</p>",
      "      <button onClick={handleProcess} className=\"px-4 py-2 rounded bg-primary text-primary-foreground\">",
      "        Trigger Process",
      "      </button>",
      "    </div>",
      "  )",
      "}"
    )
  } else if (ext === 'ts' || ext === 'js') {
    lines.push(
      "/**",
      " * Core business logic utilities",
      " */",
      "",
      "export function parsePayload(data: unknown) {",
      "  if (!data) return null",
      "  return JSON.stringify(data)",
      "}",
      "",
      "export async function executeTask(taskId: string): Promise<boolean> {",
      "  console.log('Executing background task:', taskId)",
      "  try {",
      "    const res = await fetch(`/api/tasks/${taskId}`)",
      "    return res.ok",
      "  } catch (error) {",
      "    console.error('Task execution failed:', error)",
      "    return false",
      "  }",
      "}",
      "",
      "export function formatCurrency(value: number): string {",
      "  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value)",
      "}",
      "",
      "export const API_VERSION = 'v1'"
    )
  } else if (ext === 'css') {
    lines.push(
      "/* Global layout configuration */",
      ":root {",
      "  --bg-color: #09090b;",
      "  --text-color: #fafafa;",
      "  --primary-color: #6366f1;",
      "}",
      "",
      "body {",
      "  background-color: var(--bg-color);",
      "  color: var(--text-color);",
      "  font-family: system-ui, sans-serif;",
      "  margin: 0;",
      "}",
      "",
      ".card-container {",
      "  display: flex;",
      "  flex-direction: column;",
      "  border: 1px solid #27272a;",
      "  padding: 1.5rem;",
      "  border-radius: 0.5rem;",
      "}"
    )
  } else {
    // Fallback for config/JSON files
    lines.push(
      "{",
      "  \"name\": \"ai-pr-reviewer-config\",",
      "  \"version\": \"1.0.0\",",
      "  \"private\": true,",
      "  \"engines\": {",
      "    \"node\": \">=18.0.0\"",
      "  },",
      "  \"settings\": {",
      "    \"theme\": \"dark\",",
      "    \"features\": [\"summaries\", \"file-tree\", \"annotations\"]",
      "  }",
      "}"
    )
  }

  // Inject issue descriptors on specific line numbers
  issues.forEach((issue) => {
    if (issue.line !== null && issue.line > 0) {
      const idx = issue.line - 1
      while (lines.length <= idx) {
        lines.push("")
      }
      
      let commentStyle = '//'
      if (ext === 'css') {
        commentStyle = '/*'
      }

      const issueLabel = ext === 'css'
        ? `  ${commentStyle} ISSUE [${issue.severity}]: ${issue.title} */`
        : `  ${commentStyle} ISSUE [${issue.severity}]: ${issue.title}`

      if (lines[idx].trim() === "") {
        lines[idx] = issueLabel
      } else {
        lines[idx] = `${lines[idx]} ${issueLabel}`
      }
    }
  })

  return lines.join('\n')
}
