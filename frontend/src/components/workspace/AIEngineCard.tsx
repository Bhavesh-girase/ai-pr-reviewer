import { Cpu, CheckCircle2, Bot, Layers, Search, Database } from 'lucide-react'

export default function AIEngineCard() {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-950/45 p-5 space-y-4 shadow-sm">
      <div className="flex items-center justify-between border-b border-zinc-900 pb-3">
        <div className="flex items-center gap-2">
          <Cpu className="h-4.5 w-4.5 text-indigo-400" />
          <h3 className="text-sm font-semibold text-white">AI Engine Configuration</h3>
        </div>
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-950/60 text-emerald-400 border border-emerald-800/60">
          <CheckCircle2 className="h-3 w-3" />
          <span>Operational</span>
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
        <div className="space-y-1">
          <span className="text-[10px] uppercase font-bold text-zinc-500 flex items-center gap-1">
            <Bot className="h-3 w-3 text-indigo-400" />
            <span>LLM Model</span>
          </span>
          <p className="text-white font-semibold">AI</p>
        </div>

        <div className="space-y-1">
          <span className="text-[10px] uppercase font-bold text-zinc-500 flex items-center gap-1">
            <Layers className="h-3 w-3 text-emerald-400" />
            <span>Embedding Model</span>
          </span>
          <p className="text-white font-semibold">AI Embeddings</p>
        </div>

        <div className="space-y-1">
          <span className="text-[10px] uppercase font-bold text-zinc-500 flex items-center gap-1">
            <Search className="h-3 w-3 text-amber-400" />
            <span>Retriever Strategy</span>
          </span>
          <p className="text-white font-semibold">Hybrid (BM25 + Vector Search)</p>
        </div>

        <div className="space-y-1">
          <span className="text-[10px] uppercase font-bold text-zinc-500 flex items-center gap-1">
            <Layers className="h-3 w-3 text-indigo-400" />
            <span>Reranking Pipeline</span>
          </span>
          <p className="text-white font-semibold">CrossEncoder Re-ranker</p>
        </div>

        <div className="space-y-1">
          <span className="text-[10px] uppercase font-bold text-zinc-500 flex items-center gap-1">
            <Database className="h-3 w-3 text-cyan-400" />
            <span>Vector Database</span>
          </span>
          <p className="text-white font-semibold">ChromaDB Multi-Tenant</p>
        </div>

        <div className="space-y-1">
          <span className="text-[10px] uppercase font-bold text-zinc-500">Pipeline Status</span>
          <p className="text-emerald-400 font-semibold flex items-center gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400"></span>
            <span>Healthy & Ready</span>
          </p>
        </div>
      </div>
    </div>
  )
}
