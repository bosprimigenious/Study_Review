import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'
import * as React from 'react'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-[length:var(--text-base)] font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)] disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default:
          'bg-[var(--primary)] text-[var(--primary-foreground)] shadow-[var(--shadow-sm)] hover:bg-[var(--primary-hover)] hover:shadow-[var(--shadow-md)] active:scale-[0.98] transition-all duration-150',
        secondary:
          'bg-[var(--secondary)] text-[var(--secondary-foreground)] hover:bg-[color-mix(in_srgb,var(--secondary)_90%,var(--foreground))]',
        outline:
          'border border-[var(--border)] bg-transparent hover:bg-[var(--accent)]',
        ghost: 'hover:bg-[var(--accent)] text-[var(--muted-foreground)]',
        destructive:
          'bg-[var(--destructive)] text-[var(--destructive-foreground)] hover:opacity-90',
      },
      size: {
        default: 'h-12 px-6 text-[length:var(--text-lg)]',
        sm: 'h-11 rounded-lg px-4 text-[length:var(--text-base)]',
        lg: 'h-14 rounded-xl px-7 text-[length:var(--text-xl)]',
        icon: 'h-12 w-12',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button'
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  },
)
Button.displayName = 'Button'

export { Button }
