import {
  BookOpen,
  ChevronLeft,
  ChevronRight,
  Home,
  Moon,
  Sun,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, Outlet, useLocation } from 'react-router-dom'
import { ApiConnectionError, useCourses } from '@/api/client'
import { CommandPalette, CommandTrigger } from '@/components/CommandPalette'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useCommandPalette } from '@/hooks/useCommandPalette'

type LayoutContext = {
  apiDown?: boolean
  refetchCourses?: () => void
  isFetching?: boolean
}

const SHELL_ICON = 22

const navLinkClass = (active: boolean) =>
  `flex items-center gap-3.5 rounded-xl px-4 py-3 min-h-[3.25rem] text-[length:var(--shell-nav-size)] font-medium transition-all no-underline ${
    active
      ? 'bg-[var(--accent)] text-[var(--foreground)] font-semibold shadow-[var(--shadow-sm)]'
      : 'text-[var(--muted-foreground)] hover:bg-[var(--accent)] hover:text-[var(--foreground)]'
  }`

export function Layout() {
  const location = useLocation()
  const { data, isError, error, isFetching, refetch } = useCourses()
  const { open: cmdOpen, setOpen: setCmdOpen } = useCommandPalette()
  const [collapsed, setCollapsed] = useState(false)
  const [dark, setDark] = useState(
    () =>
      localStorage.getItem('theme') === 'dark' ||
      (!localStorage.getItem('theme') &&
        window.matchMedia('(prefers-color-scheme: dark)').matches),
  )

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    localStorage.setItem('theme', dark ? 'dark' : 'light')
  }, [dark])

  const apiDown = isError && error instanceof ApiConnectionError
  const sidebarWidth = collapsed
    ? 'var(--sidebar-collapsed-width)'
    : 'var(--sidebar-width)'

  return (
    <div className="app-shell min-h-screen flex bg-[var(--background)] text-[var(--foreground)]">
      <aside
        className="shrink-0 flex flex-col border-r border-[var(--border)] bg-[var(--sidebar)] shadow-[var(--shadow-sm)] transition-[width] duration-200"
        style={{ width: sidebarWidth }}
      >
        <div className="h-[var(--header-height)] px-5 flex items-center justify-between border-b border-[var(--border-subtle)]">
          <Link
            to="/"
            className="flex items-center gap-3.5 no-underline text-inherit min-w-0"
            title="Study Review"
          >
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-[var(--foreground)] text-[var(--card)] shadow-[var(--shadow-sm)]">
              <BookOpen size={SHELL_ICON} strokeWidth={2.5} />
            </div>
            {!collapsed && (
              <span className="text-[length:var(--text-xl)] font-semibold tracking-tight truncate">
                Study Review
              </span>
            )}
          </Link>
          {!collapsed && (
            <Button
              variant="ghost"
              size="icon"
              className="h-12 w-12 shrink-0"
              onClick={() => setCollapsed(true)}
              aria-label="收起侧栏"
            >
              <ChevronLeft size={SHELL_ICON} />
            </Button>
          )}
        </div>

        {collapsed && (
          <div className="px-3 py-3 border-b border-[var(--border-subtle)]">
            <Button
              variant="ghost"
              size="icon"
              className="h-12 w-12 w-full"
              onClick={() => setCollapsed(false)}
              aria-label="展开侧栏"
            >
              <ChevronRight size={SHELL_ICON} />
            </Button>
          </div>
        )}

        <nav className="flex-1 p-4 space-y-1.5 overflow-y-auto">
          <Link
            to="/"
            className={navLinkClass(location.pathname === '/')}
            title={collapsed ? '今日复习' : undefined}
          >
            <Home size={SHELL_ICON} className="shrink-0" />
            {!collapsed && <span>今日复习</span>}
          </Link>

          {data?.courses && data.courses.length > 0 && !collapsed && (
            <p className="px-4 pt-6 pb-2 type-muted uppercase tracking-wider font-semibold text-[length:var(--text-base)]">
              课程
            </p>
          )}

          {data?.courses?.map((course) => (
            <Link
              key={course.course_id}
              to={`/course/${course.course_id}`}
              className={navLinkClass(location.pathname.includes(course.course_id))}
              title={collapsed ? course.name : undefined}
            >
              {!collapsed ? (
                <>
                  <span className="truncate flex-1">{course.name}</span>
                  {course.due_items_count > 0 && (
                    <Badge
                      variant="secondary"
                      className="ml-auto shrink-0 tabular-nums text-[length:var(--text-base)] px-2.5 py-1 bg-[var(--warning)]/12 text-[var(--warning)] border-0"
                    >
                      {course.due_items_count}
                    </Badge>
                  )}
                </>
              ) : (
                <span className="mx-auto text-[length:var(--text-base)] font-semibold">
                  {course.name.slice(0, 1)}
                </span>
              )}
            </Link>
          ))}

          {apiDown && !collapsed && (
            <p className="mx-2 mt-4 rounded-xl border border-[var(--destructive)]/20 bg-[var(--destructive)]/5 px-4 py-3 text-[length:var(--text-base)] text-[var(--destructive)]">
              API 离线
            </p>
          )}
        </nav>

        <div className="p-4 border-t border-[var(--border-subtle)]">
          <Button
            variant="ghost"
            size={collapsed ? 'icon' : 'lg'}
            className={
              collapsed
                ? 'h-12 w-12'
                : 'w-full justify-start h-12 text-[length:var(--shell-nav-size)]'
            }
            onClick={() => setDark((v) => !v)}
            title={dark ? '浅色模式' : '暗色模式'}
          >
            {dark ? <Sun size={SHELL_ICON} /> : <Moon size={SHELL_ICON} />}
            {!collapsed && (dark ? '浅色模式' : '暗色模式')}
          </Button>
        </div>
      </aside>

      <main className="flex-1 min-w-0 flex flex-col overflow-hidden">
        <header className="shrink-0 z-10 h-[var(--header-height)] flex items-center border-b border-[var(--border)] bg-[var(--card)]/85 backdrop-blur-md px-6 lg:px-10">
          <div className="w-full max-w-5xl mx-auto flex items-center gap-6">
            <CommandTrigger onClick={() => setCmdOpen(true)} />
            <div className="ml-auto flex items-center gap-4 type-muted text-[length:var(--text-lg)]">
              {isFetching && !apiDown && <span>同步中</span>}
              <span className="hidden md:inline font-medium">
                {new Date().toLocaleDateString('zh-CN', {
                  month: 'short',
                  day: 'numeric',
                  weekday: 'short',
                })}
              </span>
            </div>
          </div>
        </header>

        <div className="flex-1 overflow-auto">
          <div className="p-6 lg:p-8 max-w-5xl mx-auto w-full">
            <Outlet
              context={
                {
                  apiDown,
                  refetchCourses: refetch,
                  isFetching,
                } satisfies LayoutContext
              }
            />
          </div>
        </div>
      </main>

      <CommandPalette open={cmdOpen} onOpenChange={setCmdOpen} />
    </div>
  )
}
