import {
  AlertOctagon,
  AlertTriangle,
  CalendarDays,
  CirclePlay,
  CheckCircle2,
  Flag,
  Milestone,
  Pencil,
  Plus,
  RotateCcw,
  Trash2,
} from 'lucide-react'
import { useCallback, useState } from 'react'
import { ErrorState } from '@/components/common/ErrorState'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { toast } from '@/components/ui/toast'
import { useAsyncData } from '@/hooks/useAsyncData'
import { deleteTask, fetchProjectDetail, updateTask } from '@/services/api'
import type { Task, TaskPriority, TaskStatus } from '@/types'
import { TaskFormSheet } from './TaskFormSheet'

const COLUMNS: Array<{ status: TaskStatus; title: string }> = [
  { status: 'todo', title: '待开始' },
  { status: 'doing', title: '进行中' },
  { status: 'done', title: '已完成' },
]

const PRIORITY_LABELS: Record<TaskPriority, string> = {
  high: '高',
  medium: '中',
  low: '低',
}

const PRIORITY_BADGE_CLASSES: Record<TaskPriority, string> = {
  high: 'border-red-300 bg-red-50 text-red-600 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-400',
  medium:
    'border-amber-300 bg-amber-50 text-amber-700 dark:border-amber-500/40 dark:bg-amber-500/10 dark:text-amber-400',
  low: 'border-sky-300 bg-sky-50 text-sky-700 dark:border-sky-500/40 dark:bg-sky-500/10 dark:text-sky-400',
}

const STATUS_TRANSITIONS: Record<
  TaskStatus,
  Array<{ to: TaskStatus; label: string; icon: typeof CirclePlay }>
> = {
  todo: [{ to: 'doing', label: '开始', icon: CirclePlay }],
  doing: [{ to: 'done', label: '完成', icon: CheckCircle2 }],
  done: [{ to: 'todo', label: '重新打开', icon: RotateCcw }],
}

function formatDate(iso: string | null): string {
  if (!iso) return ''
  const [, month, day] = iso.split('-')
  return `${month}-${day}`
}

interface TaskCardProps {
  task: Task
  onEdit: (task: Task) => void
  onChanged: () => void
}

/** 任务卡片：标题、徽章、计划日期、进度条、风险标记 + 操作按钮 */
function TaskCard({ task, onEdit, onChanged }: TaskCardProps) {
  const [confirmingDelete, setConfirmingDelete] = useState(false)

  const handleStatusChange = async (to: TaskStatus) => {
    try {
      await updateTask(task.id, { status: to })
      toast.add({
        title: to === 'done' ? '任务已完成' : to === 'doing' ? '任务已开始' : '任务已重新打开',
        type: 'success',
      })
      onChanged()
    } catch {
      // 错误提示已由 api 层统一 toast 展示
    }
  }

  const handleDelete = async () => {
    if (!confirmingDelete) {
      setConfirmingDelete(true)
      return
    }
    try {
      await deleteTask(task.id)
      toast.add({ title: '任务已删除', type: 'success' })
      onChanged()
    } catch {
      // 错误提示已由 api 层统一 toast 展示
    }
  }

  return (
    <div className="flex flex-col gap-3 rounded-xl border border-border bg-background p-3 shadow-sm">
      <div className="flex items-start justify-between gap-2">
        <p className="min-w-0 text-sm font-medium leading-snug break-words">
          {task.title}
        </p>
        <Badge variant="outline" className={PRIORITY_BADGE_CLASSES[task.priority]}>
          {PRIORITY_LABELS[task.priority]}
        </Badge>
      </div>

      <div className="flex flex-wrap items-center gap-1.5">
        {task.isMilestone && (
          <Badge variant="secondary">
            <Milestone className="size-3" />
            里程碑
          </Badge>
        )}
        {task.estimatedHours != null && (
          <span className="text-xs text-muted-foreground">预计 {task.estimatedHours}h</span>
        )}
      </div>

      {(task.plannedStartDate || task.plannedEndDate) && (
        <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
          <CalendarDays className="size-3.5" />
          {task.plannedStartDate ? formatDate(task.plannedStartDate) : '—'} ~{' '}
          {task.plannedEndDate ? formatDate(task.plannedEndDate) : '—'}
        </span>
      )}

      {(task.status === 'doing' || task.progress > 0) && (
        <div className="flex flex-col gap-1">
          <Progress value={task.progress} className="h-1.5" />
          <span className="text-xs text-muted-foreground tabular-nums">
            {task.progress}%
          </span>
        </div>
      )}

      {task.risk !== 'none' && (
        <div
          className={
            task.risk === 'high'
              ? 'flex items-start gap-1.5 rounded-lg bg-red-50 px-2 py-1.5 text-xs text-red-600 dark:bg-red-500/10 dark:text-red-400'
              : 'flex items-start gap-1.5 rounded-lg bg-amber-50 px-2 py-1.5 text-xs text-amber-700 dark:bg-amber-500/10 dark:text-amber-400'
          }
        >
          {task.risk === 'high' ? (
            <AlertOctagon className="mt-px size-3.5 shrink-0" />
          ) : (
            <AlertTriangle className="mt-px size-3.5 shrink-0" />
          )}
          <span>{task.riskReason}</span>
        </div>
      )}

      <div className="flex items-center gap-1 border-t border-border pt-2">
        {STATUS_TRANSITIONS[task.status].map(({ to, label, icon: Icon }) => (
          <Button
            key={to}
            size="sm"
            variant="outline"
            className="h-7 gap-1 px-2 text-xs"
            onClick={() => void handleStatusChange(to)}
          >
            <Icon className="size-3.5" />
            {label}
          </Button>
        ))}
        <div className="flex-1" />
        <Button
          size="sm"
          variant="ghost"
          className="h-7 gap-1 px-2 text-xs"
          onClick={() => onEdit(task)}
        >
          <Pencil className="size-3.5" />
          编辑
        </Button>
        <Button
          size="sm"
          variant={confirmingDelete ? 'destructive' : 'ghost'}
          className="h-7 gap-1 px-2 text-xs"
          onClick={() => void handleDelete()}
        >
          <Trash2 className="size-3.5" />
          {confirmingDelete ? '确认删除' : '删除'}
        </Button>
      </div>
    </div>
  )
}

/** 三列看板：待开始 / 进行中 / 已完成，支持新增、编辑、状态流转、删除 */
export function ProjectBoard({ projectId }: { projectId: number }) {
  // 用 useCallback 固定 fetcher 引用：内联箭头函数每次渲染都是新引用，
  // 会导致 useAsyncData 的 effect 反复触发，陷入无限请求循环
  const loadDetail = useCallback(() => fetchProjectDetail(projectId), [projectId])
  const { data, loading, error, reload } = useAsyncData(loadDetail)
  const [addStatus, setAddStatus] = useState<TaskStatus | null>(null)
  const [editingTask, setEditingTask] = useState<Task | null>(null)

  if (loading) {
    return <p className="py-10 text-center text-sm text-muted-foreground">加载任务中…</p>
  }
  if (error) {
    return <ErrorState message={error} onRetry={() => void reload()} />
  }

  const tasks = data?.tasks ?? []

  return (
    <div className="grid grid-cols-1 items-start gap-4 md:grid-cols-3">
      {COLUMNS.map((column) => {
        const columnTasks = tasks.filter((task) => task.status === column.status)
        return (
          <div
            key={column.status}
            className="flex flex-col gap-3 rounded-xl border border-border bg-card p-3"
          >
            <div className="flex items-center justify-between px-1">
              <div className="flex items-center gap-2">
                <Flag className="size-4 text-muted-foreground" />
                <h3 className="text-sm font-medium">{column.title}</h3>
                <Badge variant="secondary" className="tabular-nums">
                  {columnTasks.length}
                </Badge>
              </div>
              <Button
                size="sm"
                variant="ghost"
                className="h-7 gap-1 px-2 text-xs"
                onClick={() => setAddStatus(column.status)}
              >
                <Plus className="size-3.5" />
                新增
              </Button>
            </div>

            {columnTasks.map((task) => (
              <TaskCard
                key={task.id}
                task={task}
                onEdit={setEditingTask}
                onChanged={() => void reload()}
              />
            ))}

            {columnTasks.length === 0 && (
              <div className="rounded-xl border border-dashed border-border py-8 text-center text-xs text-muted-foreground">
                暂无任务，点击右上角「新增」
              </div>
            )}
          </div>
        )
      })}

      <TaskFormSheet
        open={addStatus !== null}
        onOpenChange={(open) => !open && setAddStatus(null)}
        projectId={projectId}
        task={null}
        initialStatus={addStatus ?? 'todo'}
        onSaved={() => void reload()}
      />
      <TaskFormSheet
        open={editingTask !== null}
        onOpenChange={(open) => !open && setEditingTask(null)}
        projectId={projectId}
        task={editingTask}
        initialStatus={editingTask?.status ?? 'todo'}
        onSaved={() => void reload()}
      />
    </div>
  )
}
