import {
  AlertOctagon,
  AlertTriangle,
  ArrowRight,
  CircleCheck,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import type { RiskTask } from '@/types'

/** 风险提醒列表：红色=已逾期，黄色=进度落后；空时显示"一切正常" */
export function RiskAlertList({ riskTasks }: { riskTasks: RiskTask[] }) {
  const navigate = useNavigate()

  if (riskTasks.length === 0) {
    return (
      <div className="flex flex-col items-center py-8 text-center">
        <CircleCheck className="size-8 text-emerald-500" />
        <p className="mt-2 text-sm font-medium">暂无风险任务</p>
        <p className="mt-0.5 text-xs text-muted-foreground">
          所有任务都在计划内正常推进
        </p>
      </div>
    )
  }

  return (
    <ul className="flex flex-col gap-3">
      {riskTasks.map((task) => (
        <li
          key={task.id}
          className="flex items-start gap-3 rounded-lg border border-border bg-background/60 p-3"
        >
          {task.level === 'high' ? (
            <AlertOctagon className="mt-0.5 size-4 shrink-0 text-red-500" />
          ) : (
            <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-500" />
          )}
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium">{task.taskTitle}</p>
            <p className="mt-0.5 text-xs text-muted-foreground">
              {task.projectName} · {task.reason}
            </p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="shrink-0 text-primary"
            onClick={() => navigate('/board')}
          >
            去处理
            <ArrowRight className="size-3.5" />
          </Button>
        </li>
      ))}
    </ul>
  )
}
