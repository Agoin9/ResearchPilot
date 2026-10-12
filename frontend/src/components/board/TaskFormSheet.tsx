import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { NativeSelect } from '@/components/ui/native-select'
import { Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { Slider } from '@/components/ui/slider'
import { Textarea } from '@/components/ui/textarea'
import { toast } from '@/components/ui/toast'
import { createTask, updateTask } from '@/services/api'
import type { Task, TaskPriority, TaskStatus } from '@/types'

const PRIORITY_ITEMS: Array<{ value: TaskPriority; label: string }> = [
  { value: 'high', label: '高' },
  { value: 'medium', label: '中' },
  { value: 'low', label: '低' },
]

interface TaskFormSheetProps {
  /** 是否打开 */
  open: boolean
  onOpenChange: (open: boolean) => void
  /** 所属项目 */
  projectId: number
  /** 编辑中的任务；null 表示新增 */
  task: Task | null
  /** 新增时的初始状态（在哪个列点的新增） */
  initialStatus: TaskStatus
  /** 保存成功后的回调 */
  onSaved: () => void
}

/** 新增 / 编辑任务表单（右侧抽屉），保存后刷新看板 */
export function TaskFormSheet({
  open,
  onOpenChange,
  projectId,
  task,
  initialStatus,
  onSaved,
}: TaskFormSheetProps) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [priority, setPriority] = useState<TaskPriority>('medium')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [estimatedHours, setEstimatedHours] = useState('')
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  // 每次打开时用任务数据（或空表单）重置
  useEffect(() => {
    if (!open) return
    setTitle(task?.title ?? '')
    setDescription(task?.description ?? '')
    setPriority(task?.priority ?? 'medium')
    setStartDate(task?.plannedStartDate ?? '')
    setEndDate(task?.plannedEndDate ?? '')
    setEstimatedHours(task?.estimatedHours != null ? String(task.estimatedHours) : '')
    setProgress(task?.progress ?? 0)
    setError('')
  }, [open, task])

  const handleSubmit = async () => {
    if (!title.trim()) {
      setError('请输入任务标题')
      return
    }
    if (startDate && endDate && endDate < startDate) {
      setError('计划截止日期不能早于计划开始日期')
      return
    }
    const hours = estimatedHours.trim() ? Number(estimatedHours) : null
    if (hours !== null && (Number.isNaN(hours) || hours <= 0)) {
      setError('预计耗时必须大于 0')
      return
    }

    setSubmitting(true)
    try {
      if (task) {
        await updateTask(task.id, {
          title: title.trim(),
          description: description.trim() || null,
          priority,
          plannedStartDate: startDate || null,
          plannedEndDate: endDate || null,
          estimatedHours: hours,
          progress,
        })
        toast.add({ title: '任务已更新', type: 'success' })
      } else {
        await createTask({
          projectId,
          title: title.trim(),
          description: description.trim() || null,
          status: initialStatus,
          priority,
          plannedStartDate: startDate || null,
          plannedEndDate: endDate || null,
          estimatedHours: hours,
        })
        toast.add({ title: '任务已添加', type: 'success' })
      }
      onOpenChange(false)
      onSaved()
    } catch {
      // 错误提示已由 api 层统一 toast 展示
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>{task ? '编辑任务' : '新增任务'}</SheetTitle>
          <SheetDescription>
            {task ? '修改任务信息与进度，保存后立即生效。' : '填写任务信息，添加后可在看板中流转状态。'}
          </SheetDescription>
        </SheetHeader>

        <div className="flex flex-1 flex-col gap-4 overflow-y-auto px-4">
          <div className="flex flex-col gap-2">
            <Label htmlFor="task-title">任务标题</Label>
            <Input
              id="task-title"
              placeholder="如：完成文献综述初稿"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>

          <div className="flex flex-col gap-2">
            <Label htmlFor="task-description">任务描述（可选）</Label>
            <Textarea
              id="task-description"
              rows={3}
              placeholder="具体要做什么、产出是什么"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-2">
              <Label>优先级</Label>
              <NativeSelect
                value={priority}
                onChange={(value) => setPriority((value || 'medium') as TaskPriority)}
                items={PRIORITY_ITEMS}
                placeholder="选择优先级"
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="task-hours">预计耗时（小时，可选）</Label>
              <Input
                id="task-hours"
                type="number"
                min={0.5}
                step={0.5}
                placeholder="如：20"
                value={estimatedHours}
                onChange={(e) => setEstimatedHours(e.target.value)}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-2">
              <Label htmlFor="task-start">计划开始日期</Label>
              <Input
                id="task-start"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="task-end">计划截止日期</Label>
              <Input
                id="task-end"
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
          </div>

          {task && (
            <div className="flex flex-col gap-2">
              <Label>
                完成进度：<span className="font-medium text-foreground">{progress}%</span>
              </Label>
              <Slider
                value={[progress]}
                onValueChange={(value) => {
                  const first = Array.isArray(value) ? value[0] : value
                  setProgress(Math.round(first ?? 0))
                }}
                min={0}
                max={100}
              />
              <p className="text-xs text-muted-foreground">
                进度到 100% 会自动标记为完成；已完成任务回退进度会回到「进行中」。
              </p>
            </div>
          )}

          {error && <p className="text-sm text-red-500">{error}</p>}
        </div>

        <SheetFooter>
          <Button variant="outline" disabled={submitting} onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button disabled={submitting} onClick={() => void handleSubmit()}>
            {submitting ? '保存中…' : '保存'}
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}
