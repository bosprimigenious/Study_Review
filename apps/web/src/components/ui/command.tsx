import { Command as CommandPrimitive } from 'cmdk'
import { Search } from 'lucide-react'
import * as React from 'react'
import { cn } from '@/lib/utils'

const Command = React.forwardRef<
  React.ComponentRef<typeof CommandPrimitive>,
  React.ComponentPropsWithoutRef<typeof CommandPrimitive>
>(({ className, ...props }, ref) => (
  <CommandPrimitive
    ref={ref}
    className={cn(
      'flex h-full w-full flex-col overflow-hidden rounded-xl bg-[var(--popover)] text-[var(--popover-foreground)]',
      className,
    )}
    {...props}
  />
))
Command.displayName = CommandPrimitive.displayName

function CommandInput({
  className,
  ...props
}: React.ComponentPropsWithoutRef<typeof CommandPrimitive.Input>) {
  return (
    <div
      className="flex items-center gap-3 border-b border-[var(--border)] px-5 py-1"
      cmdk-input-wrapper=""
    >
      <Search size={22} className="shrink-0 text-[var(--muted-foreground)]" />
      <CommandPrimitive.Input
        className={cn(
          'flex h-14 w-full bg-transparent text-[length:var(--text-lg)] outline-none placeholder:text-[var(--muted-foreground)] disabled:cursor-not-allowed disabled:opacity-50',
          className,
        )}
        {...props}
      />
    </div>
  )
}

function CommandList({
  className,
  ...props
}: React.ComponentPropsWithoutRef<typeof CommandPrimitive.List>) {
  return (
    <CommandPrimitive.List
      className={cn('max-h-[24rem] overflow-y-auto overflow-x-hidden p-2', className)}
      {...props}
    />
  )
}

function CommandEmpty({
  ...props
}: React.ComponentPropsWithoutRef<typeof CommandPrimitive.Empty>) {
  return (
    <CommandPrimitive.Empty
      className="py-10 text-center text-[length:var(--text-base)] text-[var(--muted-foreground)]"
      {...props}
    />
  )
}

function CommandGroup({
  className,
  ...props
}: React.ComponentPropsWithoutRef<typeof CommandPrimitive.Group>) {
  return (
    <CommandPrimitive.Group
      className={cn(
        'overflow-hidden p-1.5 text-[var(--foreground)] [&_[cmdk-group-heading]]:px-3 [&_[cmdk-group-heading]]:py-3 [&_[cmdk-group-heading]]:text-[length:var(--text-lg)] [&_[cmdk-group-heading]]:font-semibold [&_[cmdk-group-heading]]:text-[var(--foreground)]',
        className,
      )}
      {...props}
    />
  )
}

function CommandItem({
  className,
  ...props
}: React.ComponentPropsWithoutRef<typeof CommandPrimitive.Item>) {
  return (
    <CommandPrimitive.Item
      className={cn(
        'relative flex cursor-pointer select-none items-center gap-3 rounded-lg px-3 py-3 min-h-[3rem] text-[length:var(--text-lg)] outline-none aria-selected:bg-[var(--accent)] aria-selected:text-[var(--accent-foreground)] data-[disabled=true]:pointer-events-none data-[disabled=true]:opacity-50',
        className,
      )}
      {...props}
    />
  )
}

function CommandShortcut({ className, ...props }: React.HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn('ml-auto kbd text-[length:var(--text-sm)]', className)}
      {...props}
    />
  )
}

export {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandShortcut,
}
