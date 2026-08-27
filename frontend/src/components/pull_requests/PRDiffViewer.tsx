import React, { useState, useEffect, useRef } from 'react'
import Editor, { DiffEditor, type Monaco } from '@monaco-editor/react'
import type { PullRequestFile } from '@/types/pullRequest'
import {
  FileCode,
  FileDiff,
  Eye,
  AlertCircle,
  Loader2,
  Copy,
  Check,
} from 'lucide-react'

interface PRDiffViewerProps {
  file: PullRequestFile | null
  rawDiff?: string | null
  isLoading?: boolean
  issueLines?: number[]
  focusLine?: number | null
}

const getLanguageFromFilename = (filename: string): string => {
  const ext = filename.split('.').pop()?.toLowerCase() || ''
  switch (ext) {
    case 'js':
    case 'jsx':
      return 'javascript'
    case 'ts':
    case 'tsx':
      return 'typescript'
    case 'py':
      return 'python'
    case 'json':
      return 'json'
    case 'md':
      return 'markdown'
    case 'html':
      return 'html'
    case 'css':
      return 'css'
    case 'go':
      return 'go'
    case 'rs':
      return 'rust'
    case 'sql':
      return 'sql'
    case 'yml':
    case 'yaml':
      return 'yaml'
    case 'sh':
      return 'shell'
    default:
      return 'plaintext'
  }
}

/**
 * Reconstructs simple before/after approximations from GitHub unified patch lines
 * for the dedicated Before and After tab views.
 */
function reconstructFromPatch(patch: string): { before: string; after: string } {
  const beforeLines: string[] = []
  const afterLines: string[] = []

  const lines = patch.split('\n')
  for (const line of lines) {
    if (line.startsWith('@@')) {
      continue
    } else if (line.startsWith('+')) {
      afterLines.push(line.slice(1))
    } else if (line.startsWith('-')) {
      beforeLines.push(line.slice(1))
    } else {
      const context = line.startsWith(' ') ? line.slice(1) : line
      beforeLines.push(context)
      afterLines.push(context)
    }
  }

  return {
    before: beforeLines.join('\n'),
    after: afterLines.join('\n'),
  }
}

export const PRDiffViewer: React.FC<PRDiffViewerProps> = ({
  file,
  rawDiff,
  isLoading = false,
  issueLines = [],
  focusLine = null,
}) => {
  // Tabs: 'diff' (unified patch diff) | 'split' (side-by-side diff) | 'after' (head version) | 'before' (base version)
  const [activeViewTab, setActiveViewTab] = useState<'diff' | 'split' | 'after' | 'before'>('diff')
  const [copied, setCopied] = useState(false)

  const editorRef = useRef<any>(null)
  const monacoRef = useRef<Monaco | null>(null)
  const decorationsRef = useRef<any>(null)

  const filename = file?.filename || 'No file selected'
  const patch = file?.patch || ''
  const hasPatch = Boolean(patch && patch.trim().length > 0)
  const { before: baseCode, after: headCode } = React.useMemo(() => {
    return hasPatch ? reconstructFromPatch(patch) : { before: '', after: '' }
  }, [patch, hasPatch])

  // Handle line highlight decorations for AI issue lines
  useEffect(() => {
    const editor = editorRef.current
    const monaco = monacoRef.current

    if (editor && monaco) {
      if (decorationsRef.current) {
        decorationsRef.current.clear()
      }

      if (issueLines.length > 0) {
        const decorations = issueLines
          .filter((line) => line > 0)
          .map((line) => ({
            range: new monaco.Range(line, 1, line, 1),
            options: {
              isWholeLine: true,
              className: 'monaco-issue-line-highlight',
              marginClassName: 'monaco-issue-margin-highlight',
            },
          }))
        decorationsRef.current = editor.createDecorationsCollection(decorations)
        editor.revealLineInCenter(issueLines[0])
      }
    }
  }, [issueLines, activeViewTab, file])

  // Handle focus line flash animation
  useEffect(() => {
    const editor = editorRef.current
    const monaco = monacoRef.current

    if (editor && monaco && focusLine && focusLine > 0) {
      editor.revealLineInCenter(focusLine)
      editor.setPosition({ lineNumber: focusLine, column: 1 })
      editor.focus()

      const flash = editor.createDecorationsCollection([
        {
          range: new monaco.Range(focusLine, 1, focusLine, 1),
          options: {
            isWholeLine: true,
            className: 'monaco-line-flash',
            marginClassName: 'monaco-line-flash-margin',
          },
        },
      ])

      const timer = setTimeout(() => {
        flash.clear()
      }, 2200)

      return () => {
        clearTimeout(timer)
        flash.clear()
      }
    }
  }, [focusLine, activeViewTab])

  const handleEditorMount = (editor: any, monaco: Monaco) => {
    editorRef.current = editor
    monacoRef.current = monaco
  }

  const handleDiffEditorMount = (editor: any, monaco: Monaco) => {
    editorRef.current = editor.getModifiedEditor()
    monacoRef.current = monaco
  }

  const handleCopyDiff = () => {
    const content = activeViewTab === 'diff' ? (patch || rawDiff || '') : (activeViewTab === 'after' ? headCode : baseCode)
    navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const monacoOptions = {
    readOnly: true,
    domReadOnly: true,
    minimap: { enabled: false },
    scrollBeyondLastLine: false,
    fontSize: 12.5,
    fontFamily: 'Fira Code, Menlo, Monaco, Consolas, monospace',
    lineHeight: 20,
    renderLineHighlight: 'all' as const,
    folding: true,
    lineNumbers: 'on' as const,
    wordWrap: 'on' as const,
    contextmenu: false,
    scrollbar: {
      verticalScrollbarSize: 8,
      horizontalScrollbarSize: 8,
    },
  }

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-[520px] bg-[#09090b] rounded-xl border border-zinc-850 gap-3">
        <Loader2 className="h-7 w-7 text-indigo-400 animate-spin" />
        <span className="text-xs text-zinc-400">Loading Pull Request diff from GitHub...</span>
      </div>
    )
  }

  if (!file && !rawDiff) {
    return (
      <div className="flex flex-col items-center justify-center h-[520px] bg-[#09090b] rounded-xl border border-zinc-850 p-6 text-center space-y-3">
        <FileCode className="h-10 w-10 text-zinc-700" />
        <h4 className="text-sm font-bold text-zinc-300">No Changed File Selected</h4>
        <p className="text-xs text-zinc-500 max-w-sm">
          Select a file from the changed files list on the left to inspect its live GitHub PR diff.
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col border border-zinc-850 bg-[#09090b] rounded-xl overflow-hidden h-full min-h-[550px] w-full text-left">
      {/* Monaco Styling Overrides */}
      <style>{`
        .monaco-issue-line-highlight {
          background-color: rgba(239, 68, 68, 0.12) !important;
          border-left: 3.5px solid #f43f5e !important;
        }
        .monaco-issue-margin-highlight {
          border-left: 3.5px solid #f43f5e !important;
          background-color: rgba(239, 68, 68, 0.12) !important;
        }
        @keyframes flash-yellow {
          0% { background-color: rgba(234, 179, 8, 0.42); }
          100% { background-color: transparent; }
        }
        .monaco-line-flash {
          animation: flash-yellow 2.2s cubic-bezier(0.16, 1, 0.3, 1) forwards !important;
          border-left: 3.5px solid #eab308 !important;
        }
        .monaco-line-flash-margin {
          border-left: 3.5px solid #eab308 !important;
          animation: flash-yellow 2.2s cubic-bezier(0.16, 1, 0.3, 1) forwards !important;
        }
        .monaco-diff-editor .inserted,
        .monaco-diff-editor .inserted-text {
          background-color: rgba(34, 197, 94, 0.22) !important;
        }
        .monaco-diff-editor .removed,
        .monaco-diff-editor .removed-text {
          background-color: rgba(239, 68, 68, 0.22) !important;
        }
      `}</style>

      {/* Diff Header Bar */}
      <div className="border-b border-zinc-850 bg-zinc-950 px-4 py-2.5 flex flex-wrap items-center justify-between gap-3 shrink-0">
        {/* Left: Filename & Status Badge */}
        <div className="flex items-center gap-2.5 min-w-0">
          <FileDiff className="h-4 w-4 text-indigo-400 shrink-0" />
          <span className="font-mono text-xs font-bold text-white truncate max-w-sm">
            {filename}
          </span>
          {file && (
            <div className="flex items-center gap-1.5 text-[11px] font-mono shrink-0">
              <span className="text-emerald-400 font-bold">+{file.additions}</span>
              <span className="text-red-400 font-bold">-{file.deletions}</span>
            </div>
          )}
        </div>

        {/* Right: View Mode Tabs & Copy Button */}
        <div className="flex items-center gap-2">
          <div className="flex items-center bg-zinc-900 border border-zinc-800 rounded-lg p-0.5 text-xs">
            <button
              onClick={() => setActiveViewTab('diff')}
              className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition-all cursor-pointer flex items-center gap-1 ${
                activeViewTab === 'diff'
                  ? 'bg-indigo-600 text-white shadow-xs'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <FileDiff className="h-3 w-3" />
              <span>PR Diff</span>
            </button>

            <button
              onClick={() => setActiveViewTab('split')}
              disabled={!hasPatch}
              className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition-all cursor-pointer flex items-center gap-1 disabled:opacity-40 ${
                activeViewTab === 'split'
                  ? 'bg-indigo-600 text-white shadow-xs'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <Eye className="h-3 w-3" />
              <span>Side-by-Side</span>
            </button>

            <button
              onClick={() => setActiveViewTab('after')}
              disabled={!hasPatch}
              className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition-all cursor-pointer disabled:opacity-40 ${
                activeViewTab === 'after'
                  ? 'bg-indigo-600 text-white shadow-xs'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              After (Head)
            </button>

            <button
              onClick={() => setActiveViewTab('before')}
              disabled={!hasPatch}
              className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition-all cursor-pointer disabled:opacity-40 ${
                activeViewTab === 'before'
                  ? 'bg-indigo-600 text-white shadow-xs'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              Before (Base)
            </button>
          </div>

          <button
            onClick={handleCopyDiff}
            title="Copy diff to clipboard"
            className="p-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-400 hover:text-white transition-colors cursor-pointer"
          >
            {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
          </button>
        </div>
      </div>

      {/* Editor Content Area */}
      <div className="flex-1 relative min-h-[480px] bg-[#09090b]">
        {!hasPatch && !rawDiff ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center space-y-3">
            <AlertCircle className="h-8 w-8 text-amber-500" />
            <h4 className="text-sm font-bold text-white">Diff Unavailable for this File</h4>
            <p className="text-xs text-zinc-400 max-w-sm leading-relaxed">
              GitHub does not provide a patch for this file. This usually occurs for binary files, submodule commits, or changes exceeding GitHub&apos;s patch size limit.
            </p>
          </div>
        ) : activeViewTab === 'split' ? (
          <DiffEditor
            height="100%"
            original={baseCode}
            modified={headCode}
            language={getLanguageFromFilename(filename)}
            theme="vs-dark"
            options={{ ...monacoOptions, renderSideBySide: true }}
            onMount={handleDiffEditorMount}
            loading={
              <div className="flex items-center justify-center h-full gap-2 text-xs text-zinc-500">
                <Loader2 className="h-4 w-4 animate-spin text-zinc-400" />
                <span>Loading side-by-side diff...</span>
              </div>
            }
          />
        ) : activeViewTab === 'diff' ? (
          <Editor
            height="100%"
            value={patch || rawDiff || ''}
            language="diff"
            theme="vs-dark"
            options={monacoOptions}
            onMount={handleEditorMount}
            loading={
              <div className="flex items-center justify-center h-full gap-2 text-xs text-zinc-500">
                <Loader2 className="h-4 w-4 animate-spin text-zinc-400" />
                <span>Loading patch diff...</span>
              </div>
            }
          />
        ) : activeViewTab === 'after' ? (
          <Editor
            height="100%"
            value={headCode}
            language={getLanguageFromFilename(filename)}
            theme="vs-dark"
            options={monacoOptions}
            onMount={handleEditorMount}
          />
        ) : (
          <Editor
            height="100%"
            value={baseCode}
            language={getLanguageFromFilename(filename)}
            theme="vs-dark"
            options={monacoOptions}
            onMount={handleEditorMount}
          />
        )}
      </div>
    </div>
  )
}
