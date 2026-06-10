import { Link, useParams } from 'react-router-dom'
import { useMakePlan, usePlan } from '@/api/client'
import { EmptyState } from '@/components/EmptyState'
import { Button } from '@/components/ui/button'

export function PlanPage() {
  const { id = '' } = useParams()
  const { data, isLoading, isError } = usePlan(id)
  const makePlan = useMakePlan(id)

  if (isLoading) return <p className="type-muted">加载计划…</p>

  if (isError || !data?.plan_md) {
    return (
      <EmptyState
        title="还没有复习计划"
        description="先生成 90 分钟保底计划，计划会基于试卷分析和当前进度。"
        action={
          <Button disabled={makePlan.isPending} onClick={() => makePlan.mutate()}>
            {makePlan.isPending ? '生成中…' : '生成计划'}
          </Button>
        }
      />
    )
  }

  return (
    <div className="max-w-3xl space-y-6">
      <header className="flex items-center justify-between gap-4">
        <h1 className="type-page">复习计划</h1>
        <Button asChild>
          <Link to={`/course/${id}/quiz`}>现在开始答题</Link>
        </Button>
      </header>
      <article className="max-w-none whitespace-pre-wrap rounded-lg border border-[var(--border)] p-5 leading-relaxed">
        {data.plan_md}
      </article>
    </div>
  )
}
