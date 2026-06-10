import {
  ArrowRight,
  BookMarked,
  Clock,
  Layers,
  Play,
} from 'lucide-react'
import { Link, useOutletContext } from 'react-router-dom'
import { ApiConnectionError, useCourses, useDueToday } from '@/api/client'
import { ApiBanner } from '@/components/ApiBanner'
import { EmptyState } from '@/components/EmptyState'
import { DashboardSkeleton } from '@/components/Skeleton'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

type LayoutContext = {
  apiDown?: boolean
  refetchCourses?: () => void
  isFetching?: boolean
}

export function Dashboard() {
  const { refetchCourses, isFetching } = useOutletContext<LayoutContext>()
  const {
    data: coursesData,
    isLoading,
    isError,
    error,
    refetch,
  } = useCourses()
  const { data: dueData } = useDueToday()
  const courses = coursesData?.courses ?? []
  const dueCourses = dueData?.courses ?? []
  const totalDue = dueCourses.reduce((sum, c) => sum + c.items.length, 0)

  if (isLoading) return <DashboardSkeleton />

  if (isError && error instanceof ApiConnectionError) {
    return (
      <ApiBanner
        onRetry={() => {
          void refetch()
          refetchCourses?.()
        }}
        isRetrying={isFetching}
      />
    )
  }

  if (courses.length === 0) {
    return (
      <EmptyState
        title="还没有扫描到课程"
        description="后端已连接，但课程目录为空。请重启 API 后刷新。"
        action={
          <Button
            onClick={() => {
              void refetch()
              refetchCourses?.()
            }}
          >
            刷新课程列表
          </Button>
        }
      />
    )
  }

  const focusCourse =
    courses.find((c) => c.due_items_count > 0) ?? courses[0]
  const hasDue = totalDue > 0
  const materialTotal = courses.reduce((s, c) => s + c.materials_count, 0)

  return (
    <div className="space-y-8 anim-in">
      <section className="hero-panel">
        <div className="relative space-y-3">
          <span className="badge-pill">今晚</span>
          <h1 className="type-page text-[length:var(--text-2xl)]">
            {hasDue ? `复习 ${totalDue} 项到期内容` : '开始一轮诊断答题'}
          </h1>
          <p className="type-muted max-w-lg">
            {hasDue
              ? `优先处理 ${focusCourse.name}，做完再生成计划查漏补缺。`
              : '分析重点 → 生成计划 → 一题一答 → 错题自动安排复查。'}
          </p>
          <div className="flex flex-wrap items-center gap-3 pt-1">
            <Button asChild size="lg">
              <Link to={`/course/${focusCourse.course_id}/quiz`}>
                <Play size={16} fill="currentColor" />
                {hasDue ? '开始复习' : '开始答题'}
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg">
              <Link to={`/course/${focusCourse.course_id}/plan`}>
                查看计划
                <ArrowRight size={15} />
              </Link>
            </Button>
          </div>
        </div>
      </section>

      <div className="grid gap-3 sm:grid-cols-3">
        {[
          { icon: Layers, label: '课程', value: courses.length, warn: false },
          { icon: Clock, label: '今日到期', value: totalDue, warn: hasDue },
          { icon: BookMarked, label: '资料', value: materialTotal, warn: false },
        ].map(({ icon: Icon, label, value, warn }) => (
          <div key={label} className="stat-tile">
            <div className="stat-tile-label">
              <Icon size={15} />
              <span>{label}</span>
            </div>
            <p
              className={`stat-tile-value tabular-nums ${warn ? 'text-[var(--warning)]' : ''}`}
            >
              {value}
            </p>
          </div>
        ))}
      </div>

      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="type-section">今日待复习</h2>
          {hasDue && (
            <Badge variant="secondary" className="tabular-nums">
              {totalDue}
            </Badge>
          )}
        </div>

        {dueCourses.length === 0 ? (
          <Card className="p-6 text-center">
            <p className="type-muted">今天没有到期项，可以直接做新题。</p>
          </Card>
        ) : (
          <Card className="overflow-hidden p-0 shadow-[var(--shadow-sm)]">
            {dueCourses.flatMap((course) =>
              course.items.slice(0, 5).map((item) => (
                <Link
                  key={item.id}
                  to={`/course/${course.course_id}/quiz`}
                  className="list-row no-underline text-inherit border-0 rounded-none border-b border-[var(--border-subtle)] last:border-b-0"
                >
                  <span className="shrink-0 w-[4.5rem] type-muted tabular-nums text-[length:var(--text-xs)]">
                    {item.due}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="font-medium text-[var(--foreground)]">
                      {item.topic}
                    </span>
                    <span className="type-muted block truncate mt-0.5">
                      {item.prompt.slice(0, 80)}
                      {item.prompt.length > 80 ? '…' : ''}
                    </span>
                  </span>
                  <ArrowRight
                    size={15}
                    className="shrink-0 text-[var(--muted-foreground)]"
                  />
                </Link>
              )),
            )}
          </Card>
        )}
      </section>

      <section>
        <h2 className="type-section mb-3">课程</h2>
        <Card className="overflow-hidden p-0 shadow-[var(--shadow-sm)]">
          {courses.map((course) => (
            <Link
              key={course.course_id}
              to={`/course/${course.course_id}`}
              className="list-row no-underline text-inherit border-0 rounded-none border-b border-[var(--border-subtle)] last:border-b-0"
            >
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[var(--muted)] text-[var(--foreground)] font-semibold text-[length:var(--text-sm)]">
                {course.name.slice(0, 1).toUpperCase()}
              </div>
              <div className="min-w-0 flex-1">
                <p className="font-medium truncate">{course.name}</p>
                <p className="type-muted">{course.materials_count} 份资料</p>
              </div>
              {course.due_items_count > 0 && (
                <Badge
                  variant="secondary"
                  className="shrink-0 tabular-nums bg-[var(--warning)]/12 text-[var(--warning)] border-0"
                >
                  {course.due_items_count} 待复习
                </Badge>
              )}
              <ArrowRight
                size={15}
                className="shrink-0 text-[var(--muted-foreground)]"
              />
            </Link>
          ))}
        </Card>
      </section>
    </div>
  )
}
