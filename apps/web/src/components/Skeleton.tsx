import { Card, CardContent } from '@/components/ui/card'
import { Skeleton as UiSkeleton } from '@/components/ui/skeleton'

export function DashboardSkeleton() {
  return (
    <div className="space-y-8">
      <UiSkeleton className="h-48 w-full rounded-2xl" />
      <div className="grid gap-4 sm:grid-cols-3">
        <UiSkeleton className="h-28 rounded-xl" />
        <UiSkeleton className="h-28 rounded-xl" />
        <UiSkeleton className="h-28 rounded-xl" />
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <UiSkeleton className="h-36 rounded-xl" />
        <UiSkeleton className="h-36 rounded-xl" />
      </div>
    </div>
  )
}

export function CardSkeleton() {
  return (
    <Card>
      <CardContent className="p-6 space-y-3">
        <UiSkeleton className="h-6 w-2/3" />
        <UiSkeleton className="h-4 w-full" />
        <UiSkeleton className="h-4 w-4/5" />
      </CardContent>
    </Card>
  )
}
