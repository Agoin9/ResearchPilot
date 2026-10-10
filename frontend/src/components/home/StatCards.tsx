import {
  ArrowDownRight,
  ArrowUpRight,
  Clock3,
  FolderKanban,
  ListTodo,
  TriangleAlert,
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import type { HomeStats } from '@/types'

interface StatItem {
  label: string
  value: string
  unit?: string
  sub?: React.ReactNode
  icon: React.ComponentType<{ className?: string }>
  iconClass: string
}

/** 首页统计卡片行：进行中项目 / 待完成任务 / 本周投入 / 风险任务 */
export function StatCards({ stats }: { stats: HomeStats }) {
  const items: StatItem[] = [
    {
      label: '进行中项目',
      value: String(stats.activeProjects),
      unit: '个',
      icon: FolderKanban,
      iconClass: 'bg-primary/10 text-primary',
    },
    {
      label: '待完成任务',
      value: String(stats.todoTasks),
      unit: '项',
      icon: ListTodo,
      iconClass: 'bg-sky-500/10 text-sky-600 dark:text-sky-400',
    },
    {
      label: '本周投入时间',
      value: stats.weeklyHoursSpent.toFixed(1),
      unit: '小时',
      sub: (
        <span
          className={
            stats.weeklyHoursDelta >= 0
              ? 'text-emerald-600 dark:text-emerald-400'
              : 'text-red-500'
          }
        >
          {stats.weeklyHoursDelta >= 0 ? (
            <ArrowUpRight className="inline size-3.5" />
          ) : (
            <ArrowDownRight className="inline size-3.5" />
          )}
          较上周 {stats.weeklyHoursDelta >= 0 ? '+' : ''}
          {stats.weeklyHoursDelta} 小时
        </span>
      ),
      icon: Clock3,
      iconClass: 'bg-indigo-500/10 text-indigo-600 dark:text-indigo-400',
    },
    {
      label: '风险任务',
      value: String(stats.riskTaskCount),
      unit: '项',
      sub: (
        <span className="text-muted-foreground">
          {stats.riskTaskCount > 0 ? '建议尽快处理' : '一切正常'}
        </span>
      ),
      icon: TriangleAlert,
      iconClass:
        stats.riskTaskCount > 0
          ? 'bg-red-500/10 text-red-500'
          : 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
    },
  ]

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {items.map((item) => (
        <Card key={item.label}>
          <CardContent className="flex items-center gap-4">
            <div
              className={`flex size-11 shrink-0 items-center justify-center rounded-lg ${item.iconClass}`}
            >
              <item.icon className="size-5" />
            </div>
            <div className="min-w-0">
              <div className="text-sm text-muted-foreground">{item.label}</div>
              <div className="mt-0.5 text-2xl font-semibold tabular-nums">
                {item.value}
                {item.unit && (
                  <span className="ml-1 text-sm font-normal text-muted-foreground">
                    {item.unit}
                  </span>
                )}
              </div>
              {item.sub && (
                <div className="mt-0.5 text-xs">{item.sub}</div>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
