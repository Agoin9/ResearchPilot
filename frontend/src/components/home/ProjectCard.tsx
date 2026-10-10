import {
  AlertOctagon,
  AlertTriangle,
  CalendarDays,
  ChevronRight,
  ListChecks,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import type { Project } from '@/types'

/** 风险徽章：状态色 + 图标 + 文字，绝不只用颜色传达含义 */
function RiskBadge({ risk }: { risk: Project['risk'] }) {
  if (risk === 'high') {
    return (
      <Badge variant="outline" className="border-red-300 bg-red-50 text-red-600 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-400">
        <AlertOctagon className="size-3" />
        高风险
      </Badge>
    )
  }
  if (risk === 'medium') {
    return (
      <Badge variant="outline" className="border-amber-300 bg-amber-50 text-amber-700 dark:border-amber-500/40 dark:bg-amber-500/10 dark:text-amber-400">
        <AlertTriangle className="size-3" />
        进度落后
      </Badge>
    )
  }
  return null
}

/** 项目卡片：进度、截止倒计时、风险标记、操作按钮 */
export function ProjectCard({ project }: { project: Project }) {
  const navigate = useNavigate()
  const deadlineUrgent = project.daysLeft <= 30

  return (
    <Card className="gap-4">
      <CardHeader className="border-b border-border">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <CardTitle className="truncate">{project.name}</CardTitle>
            <Badge variant="secondary" className="mt-1.5 w-fit">
              {project.category}
            </Badge>
          </div>
          <RiskBadge risk={project.risk} />
        </div>
      </CardHeader>

      <CardContent className="flex flex-col gap-4">
        <div>
          <div className="mb-1.5 flex items-center justify-between text-sm">
            <span className="text-muted-foreground">整体进度</span>
            <span className="font-medium tabular-nums">{project.progress}%</span>
          </div>
          <Progress value={project.progress} className="h-2" />
        </div>

        <div className="flex flex-wrap items-center gap-x-5 gap-y-1.5 text-sm text-muted-foreground">
          <span className="inline-flex items-center gap-1.5">
            <CalendarDays className="size-4" />
            截止 {project.deadline}
            <span
              className={
                deadlineUrgent
                  ? 'font-medium text-red-500'
                  : 'font-medium text-foreground'
              }
            >
              剩 {project.daysLeft} 天
            </span>
          </span>
          <span className="inline-flex items-center gap-1.5">
            <ListChecks className="size-4" />
            任务 {project.tasksDone}/{project.tasksTotal}
          </span>
          <span className="inline-flex items-center gap-1.5">
            <ClockIcon className="size-4" />
            每周 {project.weeklyHours} 小时
          </span>
        </div>
      </CardContent>

      <CardFooter className="justify-end gap-2">
        <Button variant="outline" size="sm" onClick={() => navigate(`/projects/${project.id}`)}>
          项目详情
        </Button>
        <Button size="sm" onClick={() => navigate('/board')}>
          进入看板
          <ChevronRight className="size-3.5" />
        </Button>
      </CardFooter>
    </Card>
  )
}

function ClockIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </svg>
  )
}
