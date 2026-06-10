import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface QuizCardProps {
  flipped: boolean
  front: ReactNode
  back: ReactNode
}

export function QuizCard({ flipped, front, back }: QuizCardProps) {
  return (
    <div className="perspective-[1200px] w-full">
      <div
        className={cn(
          'flip-inner relative w-full min-h-[300px] transform-3d',
          flipped && 'rotate-y-180',
        )}
      >
        <div className="absolute inset-0 backface-hidden rounded-xl border border-[var(--border)] bg-[var(--card)] p-5 shadow-[var(--shadow-md)]">
          {front}
        </div>
        <div className="absolute inset-0 backface-hidden rotate-y-180 rounded-xl border border-[var(--border)] bg-[var(--card)] p-5 shadow-[var(--shadow-md)]">
          {back}
        </div>
      </div>
    </div>
  )
}
