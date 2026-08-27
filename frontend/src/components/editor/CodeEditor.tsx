import { useEffect, useRef } from 'react'
import { DiffEditor, type Monaco } from '@monaco-editor/react'
import { Loader2 } from 'lucide-react'

interface CodeEditorProps {
  filename: string
  originalCode: string
  modifiedCode: string
  issueLines: number[]
  isLoading: boolean
  focusLine?: number | null
}

const getLanguageFromFilename = (filename: string): string => {
  const ext = filename.split('.').pop()?.toLowerCase();
  switch (ext) {
    case 'js':
    case 'jsx':
      return 'javascript';
    case 'ts':
    case 'tsx':
      return 'typescript';
    case 'py':
      return 'python';
    case 'json':
      return 'json';
    case 'md':
      return 'markdown';
    case 'html':
      return 'html';
    case 'css':
      return 'css';
    default:
      return 'plaintext';
  }
}

export default function CodeEditor({
  filename,
  originalCode,
  modifiedCode,
  issueLines,
  isLoading,
  focusLine,
}: CodeEditorProps) {
  const editorRef = useRef<any>(null)
  const monacoRef = useRef<Monaco | null>(null)
  const decorationsRef = useRef<any>(null)

  // Handle line highlight decorations dynamically when modifiedCode or issueLines change
  useEffect(() => {
    const editor = editorRef.current
    const monaco = monacoRef.current

    if (editor && monaco) {
      // Clear previous decorations if any
      if (decorationsRef.current) {
        decorationsRef.current.clear()
      }

      // Create new decorations for issue lines
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

      // Center the first issue line in the viewport on file load
      if (issueLines.length > 0) {
        editor.revealLineInCenter(issueLines[0])
      }
    }
  }, [modifiedCode, issueLines])

  // Scroll, focus, and trigger a temporary yellow line-flash animation on selected issues
  useEffect(() => {
    const editor = editorRef.current
    const monaco = monacoRef.current
    if (editor && monaco && focusLine && focusLine > 0) {
      editor.revealLineInCenter(focusLine)
      editor.setPosition({ lineNumber: focusLine, column: 1 })
      editor.focus()

      // Render a temporary flashing decoration on the focused line
      const flashCollection = editor.createDecorationsCollection([
        {
          range: new monaco.Range(focusLine, 1, focusLine, 1),
          options: {
            isWholeLine: true,
            className: 'monaco-line-flash',
            marginClassName: 'monaco-line-flash-margin',
          },
        },
      ])

      // Auto-clear the flash animation after 2.2 seconds
      const timer = setTimeout(() => {
        flashCollection.clear()
      }, 2200)

      return () => {
        clearTimeout(timer)
        flashCollection.clear()
      }
    }
  }, [focusLine])

  const handleEditorDidMount = (editor: any, monaco: Monaco) => {
    // Attach handlers specifically to Monaco's modified editor pane (the Head/PR pane)
    const modifiedEditor = editor.getModifiedEditor()
    editorRef.current = modifiedEditor
    monacoRef.current = monaco

    // Set initial decorations if issueLines already exist
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
      decorationsRef.current = modifiedEditor.createDecorationsCollection(decorations)
      modifiedEditor.revealLineInCenter(issueLines[0])
    }
  }

  const options = {
    readOnly: true,
    domReadOnly: true,
    minimap: { enabled: false },
    scrollBeyondLastLine: false,
    fontSize: 13,
    fontFamily: "Fira Code, Menlo, Monaco, Consolas, monospace",
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
    renderSideBySide: true, // Side-by-side split layout
  }

  return (
    <div className="flex flex-col border border-border bg-[#09090b] rounded-xl overflow-hidden h-full w-full relative select-none">
      {/* Self-contained styling overrides for Monaco highlight decorations and bright diff tags */}
      <style>{`
        /* AI Issue line decorations */
        .monaco-issue-line-highlight {
          background-color: rgba(239, 68, 68, 0.09) !important;
          border-left: 3.5px solid #f43f5e !important;
        }
        .monaco-issue-margin-highlight {
          border-left: 3.5px solid #f43f5e !important;
          background-color: rgba(239, 68, 68, 0.09) !important;
        }

        /* Temp Scroll-To Line Flash animations */
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

        /* Override Monaco default side-by-side diff colors for greater contrast */
        .monaco-diff-editor .inserted,
        .monaco-diff-editor .inserted-text,
        .monaco-editor .inserted-line,
        .monaco-editor .inserted-text {
          background-color: rgba(34, 197, 94, 0.22) !important;
        }
        .monaco-diff-editor .removed,
        .monaco-diff-editor .removed-text,
        .monaco-editor .removed-line,
        .monaco-editor .removed-text {
          background-color: rgba(239, 68, 68, 0.22) !important;
        }

        /* Tighten margins bg styling */
        .monaco-editor .margin {
          background-color: #09090b !important;
        }
      `}</style>

      {/* Editor Header */}
      <div className="h-10 border-b border-border bg-card/30 flex items-center justify-between px-4 shrink-0 select-none">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-indigo-500" />
          <span className="text-xs font-mono text-zinc-300 truncate max-w-xs">{filename}</span>
        </div>
        <div className="text-[9px] text-zinc-500 uppercase tracking-widest font-bold font-sans">
          code review • side-by-side diff
        </div>
      </div>

      {/* Editor Content Area */}
      <div className="flex-1 relative min-h-0 bg-[#09090b]">
        {isLoading ? (
          <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-zinc-950/80 gap-3">
            <Loader2 className="h-6 w-6 text-indigo-400 animate-spin" />
            <span className="text-xs text-muted-foreground">Reading file content...</span>
          </div>
        ) : (
          <DiffEditor
            height="100%"
            original={originalCode}
            modified={modifiedCode}
            language={getLanguageFromFilename(filename)}
            theme="vs-dark"
            options={options}
            onMount={handleEditorDidMount}
            loading={
              <div className="flex flex-col items-center justify-center gap-2">
                <Loader2 className="h-5 w-5 text-zinc-400 animate-spin" />
                <span className="text-xs text-zinc-500">Loading IDE...</span>
              </div>
            }
          />
        )}
      </div>
    </div>
  )
}
export type { CodeEditorProps }
