import { FileText } from 'lucide-react'
import { useParams } from 'react-router-dom'
import { useMaterials } from '@/api/client'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'

const TYPE_VARIANT: Record<string, 'default' | 'secondary' | 'destructive'> = {
  past_exam: 'destructive',
  mock_exam: 'destructive',
  slides: 'default',
  teacher_focus: 'secondary',
  homework_answer: 'secondary',
  notes: 'secondary',
}

export function Materials() {
  const { id = '' } = useParams()
  const { data, isLoading } = useMaterials(id)

  if (isLoading) {
    return (
      <div className="space-y-4 max-w-3xl">
        <Skeleton className="h-8 w-40" />
        <Skeleton className="h-48 w-full" />
      </div>
    )
  }

  const files = data?.files ?? []

  return (
    <div className="max-w-3xl space-y-4 anim-in">
      <header>
        <h1 className="type-page">课程资料</h1>
        <p className="type-muted mt-1">{files.length} 个文件</p>
      </header>

      {files.length === 0 ? (
        <p className="type-muted py-6">暂无资料，请通过 CLI 或 API 上传。</p>
      ) : (
        <Card className="divide-y divide-[var(--border)] overflow-hidden p-0">
          {files.map((file) => (
            <div
              key={file.id}
              className="list-row border-0 rounded-none justify-between"
            >
              <div className="flex min-w-0 items-center gap-2.5 flex-1">
                <FileText
                  size={15}
                  className="shrink-0 text-[var(--muted-foreground)]"
                />
                <span className="type-mono truncate">{file.name}</span>
              </div>
              <Badge
                variant={TYPE_VARIANT[file.material_type] ?? 'secondary'}
                className="shrink-0"
              >
                {file.material_type}
              </Badge>
              <span className="type-muted shrink-0 w-16 text-right text-[length:var(--text-xs)]">
                {file.status}
              </span>
            </div>
          ))}
        </Card>
      )}
    </div>
  )
}
