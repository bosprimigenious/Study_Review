import { Inbox } from 'lucide-react'
import type { ReactNode } from 'react'
import { Card, CardContent } from '@/components/ui/card'

interface EmptyStateProps {
  title: string
  description: string
  action?: ReactNode
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <Card className="flex flex-col items-center justify-center p-10 text-center max-w-md mx-auto">
      <CardContent className="flex flex-col items-center p-0">
        <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-[var(--muted)] text-[var(--muted-foreground)] mb-4">
          <Inbox size={22} strokeWidth={1.5} />
        </div>
        <h2 className="type-section mb-2">{title}</h2>
        <p className="type-muted leading-relaxed max-w-sm mb-6">
          {description}
        </p>
        {action}
      </CardContent>
    </Card>
  )
}
