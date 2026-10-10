import { Database, RefreshCw, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'

interface DemoControlPanelProps {
  failMode: boolean
  onToggleFail: (checked: boolean) => void
  onClearData: () => void
  onRestoreData: () => void
  onRefresh: () => void
}

/**
 * 演示控制面板（仅预览阶段使用，接入真实后端后移除）：
 * 用于验收「加载状态 / 空数据提示 / 错误提示」三种界面状态。
 */
export function DemoControlPanel({
  failMode,
  onToggleFail,
  onClearData,
  onRestoreData,
  onRefresh,
}: DemoControlPanelProps) {
  return (
    <div className="flex flex-wrap items-center gap-x-6 gap-y-3 rounded-xl border border-dashed border-border bg-card px-4 py-3">
      <div className="flex items-center gap-2 text-sm">
        <Database className="size-4 text-muted-foreground" />
        <span className="font-medium">演示控制</span>
        <span className="text-xs text-muted-foreground">
          （预览验收用，接入后端后移除）
        </span>
      </div>

      <div className="flex items-center gap-2">
        <Switch id="fail-mode" checked={failMode} onCheckedChange={onToggleFail} />
        <Label htmlFor="fail-mode" className="text-sm text-muted-foreground">
          模拟请求失败
        </Label>
      </div>

      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm" onClick={onClearData}>
          <Trash2 className="size-3.5" />
          清空数据
        </Button>
        <Button variant="outline" size="sm" onClick={onRestoreData}>
          恢复示例数据
        </Button>
        <Button variant="outline" size="sm" onClick={onRefresh}>
          <RefreshCw className="size-3.5" />
          刷新
        </Button>
      </div>
    </div>
  )
}
