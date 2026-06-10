import { cva, type VariantProps } from 'class-variance-authority'
import * as React from 'react'
import { cn } from '@/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center rounded-lg border px-3 py-1 text-[length:var(--text-base)] font-medium transition-colors',
  {
    variants: {
      variant: {
        default:
          'border-transparent bg-[var(--muted)] text-[var(--foreground)]',
        secondary:
          'border-transparent bg-[var(--secondary)] text-[var(--secondary-foreground)]',
        outline: 'text-[var(--foreground)] border-[var(--border)]',
        success:
          'border-transparent bg-[var(--success)]/10 text-[var(--success)]',
        warning:
          'border-transparent bg-[var(--warning)]/10 text-[var(--warning)]',
        destructive:
          'border-transparent bg-[var(--destructive)]/10 text-[var(--destructive)]',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  },
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}

export { Badge }
