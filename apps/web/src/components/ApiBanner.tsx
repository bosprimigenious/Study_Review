import { AlertCircle, RefreshCw, Terminal } from 'lucide-react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'

interface ApiBannerProps {
  onRetry: () => void
  isRetrying?: boolean
}

export function ApiBanner({ onRetry, isRetrying }: ApiBannerProps) {
  return (
    <Alert variant="destructive" className="mb-8">
      <AlertCircle className="h-5 w-5" />
      <AlertTitle>后端未连接</AlertTitle>
      <AlertDescription className="space-y-4">
        <p>
          页面卡在「加载中」是因为 FastAPI 没在跑。请先启动后端，再刷新页面。
        </p>
        <Card>
          <CardContent className="p-3 type-mono type-muted overflow-x-auto">
            <div className="flex items-center gap-2 text-[var(--foreground)] mb-2 font-sans font-medium">
              <Terminal size={14} /> 终端 1 — API
            </div>
            <div>cd Study_Review</div>
            <div>python -m uvicorn services.api.app:app --reload --port 8000</div>
            <div className="mt-3 flex items-center gap-2 text-[var(--foreground)] font-sans font-medium">
              <Terminal size={14} /> 终端 2 — 前端
            </div>
            <div>cd apps\web && npm run dev</div>
          </CardContent>
        </Card>
        <Button disabled={isRetrying} onClick={onRetry}>
          <RefreshCw size={16} className={isRetrying ? 'animate-spin' : ''} />
          {isRetrying ? '连接中…' : '重新连接'}
        </Button>
      </AlertDescription>
    </Alert>
  )
}
