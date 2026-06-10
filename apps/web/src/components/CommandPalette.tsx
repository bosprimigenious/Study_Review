import {
  BarChart3,
  BookOpen,
  ClipboardList,
  FileStack,
  Home,
  Play,
} from 'lucide-react'
import { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useCourses } from '@/api/client'
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandShortcut,
} from '@/components/ui/command'
import {
  Dialog,
  DialogCloseButton,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

type CommandPaletteProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const navigate = useNavigate()
  const { data } = useCourses()
  const courses = data?.courses ?? []

  const go = useCallback(
    (path: string) => {
      onOpenChange(false)
      void navigate(path)
    },
    [navigate, onOpenChange],
  )

  const primaryCourse =
    courses.find((c) => c.due_items_count > 0) ?? courses[0]

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="overflow-hidden p-0">
        <DialogTitle>命令面板</DialogTitle>
        <DialogHeader>
          <span className="text-[length:var(--text-xl)] font-semibold text-[var(--foreground)]">
            快速导航
          </span>
          <DialogCloseButton />
        </DialogHeader>
        <Command>
          <CommandInput placeholder="搜索课程或动作…" />
          <CommandList>
            <CommandEmpty>没有匹配项</CommandEmpty>

            <CommandGroup heading="动作">
              <CommandItem onSelect={() => go('/')}>
                <Home size={20} />
                今日复习
              </CommandItem>
              {primaryCourse && (
                <CommandItem
                  onSelect={() => go(`/course/${primaryCourse.course_id}/quiz`)}
                >
                  <Play size={20} />
                  开始答题 — {primaryCourse.name}
                  <CommandShortcut>↵</CommandShortcut>
                </CommandItem>
              )}
            </CommandGroup>

            {courses.map((course) => (
              <CommandGroup key={course.course_id} heading={course.name}>
                <CommandItem
                  onSelect={() => go(`/course/${course.course_id}`)}
                >
                  <BookOpen size={20} />
                  课程概览
                </CommandItem>
                <CommandItem
                  onSelect={() => go(`/course/${course.course_id}/quiz`)}
                >
                  <Play size={20} />
                  答题
                </CommandItem>
                <CommandItem
                  onSelect={() => go(`/course/${course.course_id}/plan`)}
                >
                  <ClipboardList size={20} />
                  复习计划
                </CommandItem>
                <CommandItem
                  onSelect={() => go(`/course/${course.course_id}/materials`)}
                >
                  <FileStack size={20} />
                  资料
                </CommandItem>
                <CommandItem
                  onSelect={() => go(`/course/${course.course_id}/analysis`)}
                >
                  <BarChart3 size={20} />
                  试卷分析
                </CommandItem>
              </CommandGroup>
            ))}
          </CommandList>
        </Command>
      </DialogContent>
    </Dialog>
  )
}

export function CommandTrigger({ onClick }: { onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex h-[3.25rem] w-full max-w-xl items-center gap-3.5 rounded-xl border border-[var(--border)] bg-[var(--card)] px-5 text-[length:var(--text-lg)] text-[var(--muted-foreground)] transition-colors hover:border-[color-mix(in_srgb,var(--foreground)_15%,var(--border))] hover:bg-[var(--accent)] shadow-[var(--shadow-sm)]"
    >
      <span className="flex-1 text-left">搜索或跳转…</span>
      <span className="kbd hidden sm:inline-flex">⌘K</span>
    </button>
  )
}
