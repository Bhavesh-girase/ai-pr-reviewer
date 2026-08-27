import { type ComponentType, useState, useEffect } from 'react'
import { cn } from '@/lib/utils'
import { ArrowUpRight, ArrowDownRight } from 'lucide-react'

// Define the type for the icon prop (Lucide icons are ComponentTypes with SVGProps)
interface LucideIconProps {
  className?: string
}

interface MetricCardProps {
  title: string
  value: string | number
  icon: ComponentType<LucideIconProps>
  description?: string
  trend?: string
  trendType?: 'up' | 'down' | 'neutral'
  className?: string
}

export default function MetricCard({
  title,
  value,
  icon: Icon,
  description,
  trend,
  trendType = 'neutral',
  className,
}: MetricCardProps) {
  const [displayValue, setDisplayValue] = useState<string | number>(0)

  useEffect(() => {
    const end = typeof value === 'number' ? value : parseInt(value.toString(), 10)
    if (isNaN(end) || end === 0) {
      setDisplayValue(value)
      return
    }

    let start = 0
    const duration = 500 // 500ms duration
    const steps = 25
    const stepTime = duration / steps
    const increment = end / steps

    const timer = setInterval(() => {
      start += increment
      if (start >= end) {
        clearInterval(timer)
        setDisplayValue(end)
      } else {
        setDisplayValue(Math.floor(start))
      }
    }, stepTime)

    return () => clearInterval(timer)
  }, [value])

  return (
    <div
      className={cn(
        "rounded-xl border border-border bg-card/45 p-6 shadow-sm hover:border-zinc-800 hover:bg-zinc-950/20 transition-all duration-300 group flex flex-col justify-between min-h-[140px] select-none",
        className
      )}
    >
      {/* Top row: Title and Icon */}
      <div className="flex items-center justify-between gap-4">
        <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-400">
          {title}
        </span>
        <div className="p-2 rounded-lg bg-zinc-900/60 border border-border group-hover:border-zinc-700 transition-colors">
          <Icon className="h-4 w-4 text-zinc-400 group-hover:text-white transition-colors" />
        </div>
      </div>

      {/* Middle row: Big Metric Value */}
      <div className="mt-3.5 flex items-baseline gap-2">
        <span className="text-3xl font-bold tracking-tight text-white select-all">
          {displayValue}
        </span>
        
        {/* Trend Indicator */}
        {trend && (
          <span
            className={cn(
              "inline-flex items-center gap-0.5 text-xs font-semibold px-1.5 py-0.5 rounded",
              trendType === 'up' && "text-emerald-400 bg-emerald-950/20 border border-emerald-900/40",
              trendType === 'down' && "text-red-400 bg-red-950/20 border border-red-900/40",
              trendType === 'neutral' && "text-zinc-400 bg-zinc-900 border border-zinc-800"
            )}
          >
            {trendType === 'up' && <ArrowUpRight className="h-3 w-3 shrink-0" />}
            {trendType === 'down' && <ArrowDownRight className="h-3 w-3 shrink-0" />}
            <span>{trend}</span>
          </span>
        )}
      </div>

      {/* Bottom row: Helper Description */}
      {description && (
        <p className="mt-2 text-xs text-zinc-500 leading-normal">
          {description}
        </p>
      )}
    </div>
  )
}
export type { MetricCardProps }
