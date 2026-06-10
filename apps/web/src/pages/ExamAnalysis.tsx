import { Link, useParams } from 'react-router-dom'
import { useAnalysis, useAnalyzeExam, useGenerateQuestions } from '@/api/client'
import { EmptyState } from '@/components/EmptyState'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

export function ExamAnalysis() {
  const { id = '' } = useParams()
  const { data, isLoading, isError } = useAnalysis(id)
  const analyze = useAnalyzeExam(id)
  const generate = useGenerateQuestions(id)

  if (isLoading) return <p className="type-muted">加载分析…</p>

  if (isError || !data) {
    return (
      <EmptyState
        title="还没有试卷分析"
        description="上传样题/往年题后，点击分析提取优先级和 evidence。"
        action={
          <Button disabled={analyze.isPending} onClick={() => analyze.mutate()}>
            {analyze.isPending ? '分析中…' : '开始分析'}
          </Button>
        }
      />
    )
  }

  const sorted = [...data.priorities].sort((a, b) => b.weight - a.weight)

  return (
    <div className="max-w-3xl space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="type-page">试卷分析</h1>
          <p className="type-muted mt-1">
            {data.priorities_count} 条优先级 · 置信度 {data.confidence}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            disabled={generate.isPending}
            onClick={() => generate.mutate(5)}
          >
            生成变式题
          </Button>
          <Button asChild>
            <Link to={`/course/${id}/quiz`}>去答题</Link>
          </Button>
        </div>
      </header>

      <div className="space-y-3">
        {sorted.map((priority) => (
          <Card key={priority.topic} className="card-interactive p-4 anim-in">
            <div className="flex items-center justify-between mb-2">
              <h2 className="font-medium">{priority.topic}</h2>
              <span className="type-muted">权重 {priority.weight}/5</span>
            </div>
            {priority.chapter && (
              <p className="type-muted mb-2">{priority.chapter}</p>
            )}
            <div className="h-1.5 rounded-full bg-[var(--muted)] mb-3">
              <div
                className="h-full rounded-full bg-[var(--primary)] transition-all duration-700 ease-out"
                style={{ width: `${(priority.weight / 5) * 100}%` }}
              />
            </div>
            <p className="mb-2">{priority.recommended_action}</p>
            <ul className="type-muted space-y-1">
              {priority.evidence.map((item) => (
                <li key={item.source_file}>
                  {item.source_file} — {item.reason}
                </li>
              ))}
            </ul>
          </Card>
        ))}
      </div>
    </div>
  )
}
