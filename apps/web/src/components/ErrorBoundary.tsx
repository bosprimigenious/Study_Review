import { AlertCircle } from 'lucide-react'
import { Component, type ErrorInfo, type ReactNode } from 'react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'

interface Props {
  children: ReactNode
}

interface State {
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('UI error:', error, info.componentStack)
  }

  render() {
    if (this.state.error) {
      return (
        <div className="p-8 max-w-xl mx-auto">
          <Alert variant="destructive">
            <AlertCircle className="h-5 w-5" />
            <AlertTitle>页面出错了</AlertTitle>
            <AlertDescription className="space-y-4">
              <p>{this.state.error.message || '未知错误'}</p>
              <Button
                variant="outline"
                onClick={() => {
                  this.setState({ error: null })
                  window.location.reload()
                }}
              >
                刷新页面
              </Button>
            </AlertDescription>
          </Alert>
        </div>
      )
    }
    return this.props.children
  }
}
