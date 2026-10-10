import { RotateCcw, TriangleAlert } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface ErrorStateProps {
  message?: string
  onRetry?: () => void
}

/** 错误提示：警告图标 + 错误信息 + 重试按钮 */
export function ErrorState({
  message = '数据加载失败，请稍后重试',
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-destructive/30 bg-destructive/5 px-6 py-16 text-center">
      <div className="flex size-14 items-center justify-center rounded-full bg-destructive/10">
        <TriangleAlert className="size-7 text-destructive" />
      </div>
      <h3 className="mt-4 text-base font-medium">加载失败</h3>
      <p className="mt-1.5 max-w-sm text-sm text-muted-foreground">{message}</p>
      {onRetry && (
        <Button className="mt-5" variant="outline" onClick={onRetry}>
          <RotateCcw className="size-4" />
          重试
        </Button>
      )}
    </div>
  )
}
