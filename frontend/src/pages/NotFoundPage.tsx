import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { FileQuestion, Home } from 'lucide-react'

export default function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] text-center px-4 select-none">
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: 'easeOut' }}
        className="max-w-md w-full border border-border bg-gradient-to-b from-zinc-950 via-zinc-900/10 to-zinc-950 rounded-xl p-8 shadow-xl space-y-6"
      >
        {/* Error icon header */}
        <div className="h-14 w-14 rounded-full bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mx-auto animate-bounce">
          <FileQuestion className="h-7 w-7" />
        </div>

        {/* Text descriptions */}
        <div className="space-y-2">
          <span className="text-[10px] font-bold uppercase tracking-widest text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 px-2 py-0.5 rounded-full">
            404 Error
          </span>
          <h1 className="text-2xl font-extrabold tracking-tight text-white mt-3">
            Page Not Found
          </h1>
          <p className="text-xs text-zinc-400 leading-relaxed max-w-sm mx-auto font-normal">
            Sorry, we couldn’t find the page you are looking for. It might have been moved or doesn't exist anymore.
          </p>
        </div>

        {/* Back Link buttons */}
        <div className="pt-2">
          <Link
            to="/"
            className="w-full inline-flex items-center justify-center gap-2 rounded-lg bg-white hover:bg-zinc-200 text-zinc-950 font-semibold py-2.5 text-xs transition-colors duration-200 shadow cursor-pointer"
          >
            <Home className="h-3.5 w-3.5" />
            Return to Dashboard
          </Link>
        </div>
      </motion.div>
    </div>
  )
}
