import { ChevronDown } from 'lucide-react'
import { useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import type { GradingResult } from '@/lib/schemas'
import { cn } from '@/lib/utils'

const config = {
  correct: {
    border: 'border-l-[var(--success)]',
    bg: 'bg-emerald-500/5',
    icon: '✓',
    label: '正确',
    badge: 'success' as const,
  },
  partial: {
    border: 'border-l-[var(--warning)]',
    bg: 'bg-amber-500/5',
    icon: '△',
    label: '部分正确',
    badge: 'warning' as const,
  },
  wrong: {
    border: 'border-l-[var(--destructive)]',
    bg: 'bg-red-500/5',
    icon: '✗',
    label: '错误',
    badge: 'destructive' as const,
  },
} as const

interface ScoreCardProps {
  result: GradingResult
}

export function ScoreCard({ result }: ScoreCardProps) {
  const style = config[result.verdict]
  const [followUpOpen, setFollowUpOpen] = useState(false)

  return (
    <Card className={cn('border-l-4 anim-in', style.border, style.bg)}>
      <CardContent className="p-6 pt-6">
        <div className="flex items-center gap-3 mb-4">
          <span
            className="flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--card)] text-lg shadow-sm"
            aria-hidden
          >
            {style.icon}
          </span>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold">{style.label}</span>
              <Badge variant={style.badge}>{result.score_hint}</Badge>
            </div>
          </div>
        </div>

        {result.omissions.length > 0 && (
          <div className="mb-4">
            <p className="type-muted font-medium uppercase tracking-wide mb-2">
              遗漏要点
            </p>
            <ul className="type-muted space-y-2">
              {result.omissions.map((item) => (
                <li key={item} className="flex gap-2">
                  <span className="text-[var(--destructive)]">·</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        )}

        {result.better_answer && (
          <p className="type-muted leading-relaxed">
            <span className="font-medium text-[var(--foreground)]">更稳答法：</span>
            {result.better_answer}
          </p>
        )}

        {result.follow_up_question && (
          <Collapsible
            open={followUpOpen}
            onOpenChange={setFollowUpOpen}
            className="mt-4 pt-4 border-t border-[var(--border)]"
          >
            <CollapsibleTrigger className="flex w-full items-center justify-between font-medium type-muted hover:text-[var(--foreground)]">
              追问（点击展开）
              <ChevronDown
                className={cn('h-4 w-4 transition-transform', followUpOpen && 'rotate-180')}
              />
            </CollapsibleTrigger>
            <CollapsibleContent className="collapsible-content pt-3 type-muted leading-relaxed overflow-hidden">
              {result.follow_up_question}
            </CollapsibleContent>
          </Collapsible>
        )}
      </CardContent>
    </Card>
  )
}
