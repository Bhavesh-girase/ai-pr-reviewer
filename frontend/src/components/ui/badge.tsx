import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold tracking-wide transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
  {
    variants: {
      variant: {
        default: 'bg-zinc-800 text-zinc-100 border border-zinc-700',
        success: 'bg-emerald-950/70 text-emerald-400 border border-emerald-800/60',
        warning: 'bg-amber-950/70 text-amber-400 border border-amber-800/60',
        destructive: 'bg-red-950/70 text-red-400 border border-red-800/60',
        secondary: 'bg-zinc-900 text-zinc-300 border border-zinc-800',
        info: 'bg-indigo-950/70 text-indigo-300 border border-indigo-800/60',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}

export { Badge, badgeVariants }
