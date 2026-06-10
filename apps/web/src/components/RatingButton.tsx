import { Button } from '@/components/ui/button'
import { RATINGS, type Rating } from '@/lib/schemas'
import { cn } from '@/lib/utils'

const RATING_META: Record<
  Rating,
  { hint: string; selectedClass: string }
> = {
  忘了: {
    hint: '1 天后复查',
    selectedClass:
      'border-[var(--destructive)] bg-[var(--destructive)]/10 text-[var(--destructive)]',
  },
  困难: {
    hint: '1 天后复查',
    selectedClass:
      'border-[var(--warning)] bg-[var(--warning)]/10 text-[var(--warning)]',
  },
  还行: {
    hint: '3 天后复查',
    selectedClass: 'border-[var(--primary)] bg-[var(--primary)]/10 text-[var(--primary)]',
  },
  很熟: {
    hint: '7 天后复查',
    selectedClass:
      'border-[var(--success)] bg-[var(--success)]/10 text-[var(--success)]',
  },
}

interface RatingButtonGroupProps {
  value?: Rating | null
  onSelect: (rating: Rating) => void
  disabled?: boolean
}

export function RatingButtonGroup({
  value,
  onSelect,
  disabled,
}: RatingButtonGroupProps) {
  return (
    <div
      className="grid grid-cols-2 sm:grid-cols-4 gap-2"
      role="radiogroup"
      aria-label="自评掌握程度"
    >
      {RATINGS.map((rating) => {
        const meta = RATING_META[rating]
        const selected = value === rating
        return (
          <Button
            key={rating}
            type="button"
            role="radio"
            aria-checked={selected}
            aria-label={`${rating}，${meta.hint}`}
            variant="outline"
            disabled={disabled}
            className={cn(
              'h-auto flex-col py-2.5 gap-0.5 transition-all duration-150 hover:scale-[1.02] active:scale-[0.98]',
              selected && cn('ring-2 ring-[var(--ring)] scale-[1.02]', meta.selectedClass),
            )}
            onClick={() => onSelect(rating)}
          >
            <span className="font-medium">{rating}</span>
            <span className="type-muted">{meta.hint}</span>
          </Button>
        )
      })}
    </div>
  )
}
