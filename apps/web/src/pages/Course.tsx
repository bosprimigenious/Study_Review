import {
  ArrowRight,
  BarChart3,
  ClipboardList,
  FileStack,
  Play,
  Sparkles,
} from 'lucide-react'
import { Link, useParams } from 'react-router-dom'
import {
  useAnalyzeExam,
  useCourses,
  useGenerateQuestions,
  useMakePlan,
} from '@/api/client'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

const actions = [
  { to: 'materials', icon: FileStack, label: '资料列表', desc: '课件与样题' },
  { to: 'analysis', icon: BarChart3, label: '试卷分析', desc: '优先级与 evidence' },
  { to: 'plan', icon: ClipboardList, label: '复习计划', desc: '90 分钟救火' },
] as const

export function Course() {
  const { id = '' } = useParams()
  const { data } = useCourses()
  const course = data?.courses.find((item) => item.course_id === id)
  const analyze = useAnalyzeExam(id)
  const generate = useGenerateQuestions(id)
  const plan = useMakePlan(id)

  if (!course) {
    return <p className="type-muted">课程不存在或 API 未返回数据</p>
  }

  return (
    <div className="space-y-8 max-w-4xl anim-in">
      <header>
        <Badge variant="secondary" className="mb-4">
          {course.stage}
        </Badge>
        <h1 className="type-page">{course.name}</h1>
        <p className="type-muted mt-3">
          资料 {course.materials_count} 份
          {course.due_items_count > 0 && (
            <>
              {' '}
              ·{' '}
              <span className="text-[var(--warning)] font-medium">
                {course.due_items_count} 项待复习
              </span>
            </>
          )}
        </p>
      </header>

      <Link
        to={`/course/${id}/quiz`}
        className="hero-panel flex items-center gap-5 no-underline text-inherit card-interactive"
      >
        <div className="relative flex h-14 w-14 shrink-0 items-center justify-center rounded-xl bg-[var(--primary)] text-[var(--primary-foreground)] shadow-[var(--shadow-md)]">
          <Play size={24} fill="currentColor" />
        </div>
        <div className="relative min-w-0 flex-1">
          <p className="font-semibold text-[length:var(--text-xl)]">开始答题</p>
          <p className="type-muted mt-0.5">一题一答 · 自动判分 · 错题落盘</p>
        </div>
        <ArrowRight size={22} className="relative shrink-0 text-[var(--muted-foreground)]" />
      </Link>

      <div className="grid gap-4 sm:grid-cols-3">
        {actions.map(({ to, icon: Icon, label, desc }) => (
          <Link
            key={to}
            to={`/course/${id}/${to}`}
            className="stat-tile card-interactive no-underline text-inherit"
          >
            <Icon size={22} className="text-[var(--muted-foreground)]" />
            <p className="font-semibold text-[length:var(--text-lg)]">{label}</p>
            <p className="type-muted">{desc}</p>
          </Link>
        ))}
      </div>

      <Card className="p-6 shadow-[var(--shadow-sm)]">
        <div className="flex items-center gap-2.5 mb-5">
          <Sparkles size={20} className="text-[var(--muted-foreground)]" />
          <h2 className="type-section">快速操作</h2>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button disabled={analyze.isPending} onClick={() => analyze.mutate()}>
            {analyze.isPending ? '分析中…' : '分析试卷'}
          </Button>
          <Button
            variant="outline"
            disabled={generate.isPending}
            onClick={() => generate.mutate(5)}
          >
            {generate.isPending ? '生成中…' : '生成 5 道变式题'}
          </Button>
          <Button
            variant="outline"
            disabled={plan.isPending}
            onClick={() => plan.mutate()}
          >
            {plan.isPending ? '规划中…' : '生成 90 分钟计划'}
          </Button>
        </div>
      </Card>
    </div>
  )
}
