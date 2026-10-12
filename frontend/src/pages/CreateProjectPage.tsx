import {
  CalendarDays,
  CheckCircle2,
  Clock3,
  Flag,
  Loader2,
  RotateCcw,
  Sparkles,
  Target,
} from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { NativeSelect } from '@/components/ui/native-select'
import { Textarea } from '@/components/ui/textarea'
import { toast } from '@/components/ui/toast'
import { confirmAiPlan, createProject, generateAiPlan } from '@/services/api'
import type { AiPlanResult, AiPlanTask } from '@/types'

const today = new Date().toISOString().slice(0, 10)

const STAGE_ITEMS = [
  { value: '选题阶段', label: '选题阶段' },
  { value: '文献调研', label: '文献调研' },
  { value: '方法设计', label: '方法设计' },
  { value: '实验进行', label: '实验进行' },
  { value: '论文撰写', label: '论文撰写' },
  { value: '修改投稿', label: '修改投稿' },
]

const PRIORITY_BADGE_CLASSES: Record<string, string> = {
  高: 'border-red-300 bg-red-50 text-red-600 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-400',
  中: 'border-amber-300 bg-amber-50 text-amber-700 dark:border-amber-500/40 dark:bg-amber-500/10 dark:text-amber-400',
  低: 'border-sky-300 bg-sky-50 text-sky-700 dark:border-sky-500/40 dark:bg-sky-500/10 dark:text-sky-400',
}

interface FormState {
  name: string
  goal: string
  deadline: string
  weeklyHours: string
  currentStage: string
  completedWork: string
}

type FormErrors = Partial<Record<keyof FormState, string>>

/** 新建项目：填写科研信息 → AI 生成科研计划 → 预览 → 确认写入 */
export default function CreateProjectPage() {
  const navigate = useNavigate()
  const [submitting, setSubmitting] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [plan, setPlan] = useState<AiPlanResult | null>(null)
  const [form, setForm] = useState<FormState>({
    name: '',
    goal: '',
    deadline: '',
    weeklyHours: '10',
    currentStage: '',
    completedWork: '',
  })
  const [errors, setErrors] = useState<FormErrors>({})

  const setField = (field: keyof FormState, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }))
    setErrors((prev) => ({ ...prev, [field]: undefined }))
  }

  const validate = (): boolean => {
    const next: FormErrors = {}
    if (!form.name.trim()) next.name = '请输入项目名称'
    else if (form.name.trim().length > 100) next.name = '项目名称不能超过 100 个字符'
    if (!form.goal.trim()) next.goal = '请输入科研目标描述'
    if (!form.deadline) next.deadline = '请选择截止日期'
    else if (form.deadline < today) next.deadline = '截止日期不能早于今天'
    const hours = Number(form.weeklyHours)
    if (!form.weeklyHours.trim() || Number.isNaN(hours)) {
      next.weeklyHours = '请输入每周可用小时数'
    } else if (hours <= 0) {
      next.weeklyHours = '每周可用小时数必须大于 0'
    } else if (hours > 168) {
      next.weeklyHours = '每周可用小时数不能超过 168'
    }
    if (!form.currentStage.trim()) next.currentStage = '请选择当前研究阶段'
    setErrors(next)
    return Object.keys(next).length === 0
  }

  /** 生成科研计划（只生成预览，不写数据库） */
  const handleGeneratePlan = async () => {
    if (!validate()) return
    setGenerating(true)
    setPlan(null)
    try {
      const result = await generateAiPlan({
        topic: form.goal.trim(),
        deadline: form.deadline,
        weeklyHours: Number(form.weeklyHours),
        currentStage: form.currentStage,
        completedWork: form.completedWork.trim() || null,
      })
      setPlan(result)
      if (result.source === 'demo') {
        toast.add({
          title: '演示模式',
          description: '未配置 DeepSeek API Key，返回预设示例计划',
          type: 'info',
        })
      } else {
        toast.add({ title: '科研计划生成成功', description: '请预览确认后写入看板', type: 'success' })
      }
    } catch {
      // 错误提示已由 api 层统一 toast 展示
    } finally {
      setGenerating(false)
    }
  }

  /** 确认计划：创建项目 + 批量写入任务（此时才落库） */
  const handleConfirmPlan = async () => {
    if (!validate() || !plan) return
    setSubmitting(true)
    try {
      const result = await confirmAiPlan({
        project: {
          name: form.name.trim(),
          goal: form.goal.trim(),
          deadline: form.deadline,
          weeklyHours: Number(form.weeklyHours),
        },
        tasks: plan.tasks,
      })
      toast.add({
        title: '项目创建成功',
        description: `已写入 ${result.tasks.length} 个任务到看板`,
        type: 'success',
      })
      navigate(`/projects/${result.project.id}`)
    } catch {
      // 错误提示已由 api 层统一 toast 展示
    } finally {
      setSubmitting(false)
    }
  }

  /** 不经过 AI，直接创建空项目 */
  const handleCreateEmpty = async () => {
    if (!validate()) return
    setSubmitting(true)
    try {
      const project = await createProject({
        name: form.name.trim(),
        goal: form.goal.trim(),
        deadline: form.deadline,
        weeklyHours: Number(form.weeklyHours),
      })
      toast.add({ title: '项目创建成功', description: '进入看板手动添加任务吧', type: 'success' })
      navigate(`/projects/${project.id}`)
    } catch {
      // 错误提示已由 api 层统一 toast 展示
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle>新建科研项目</CardTitle>
          <CardDescription>
            填写科研信息后，可让 AI 把目标拆解成可执行的科研任务计划。
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-5">
          <div className="flex flex-col gap-2">
            <Label htmlFor="name">项目名称</Label>
            <Input
              id="name"
              placeholder="如：毕业论文"
              value={form.name}
              onChange={(e) => setField('name', e.target.value)}
            />
            {errors.name && <p className="text-sm text-red-500">{errors.name}</p>}
          </div>

          <div className="flex flex-col gap-2">
            <Label htmlFor="goal">
              <span className="inline-flex items-center gap-1.5">
                <Target className="size-3.5 text-muted-foreground" />
                研究主题
              </span>
            </Label>
            <Textarea
              id="goal"
              rows={3}
              placeholder="如：虚拟世界智能体行为规划，12周完成论文初稿"
              value={form.goal}
              onChange={(e) => setField('goal', e.target.value)}
            />
            {errors.goal && <p className="text-sm text-red-500">{errors.goal}</p>}
          </div>

          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
            <div className="flex flex-col gap-2">
              <Label htmlFor="deadline">
                <span className="inline-flex items-center gap-1.5">
                  <CalendarDays className="size-3.5 text-muted-foreground" />
                  项目截止日期
                </span>
              </Label>
              <Input
                id="deadline"
                type="date"
                min={today}
                value={form.deadline}
                onChange={(e) => setField('deadline', e.target.value)}
              />
              {errors.deadline && (
                <p className="text-sm text-red-500">{errors.deadline}</p>
              )}
            </div>

            <div className="flex flex-col gap-2">
              <Label htmlFor="weeklyHours">
                <span className="inline-flex items-center gap-1.5">
                  <Clock3 className="size-3.5 text-muted-foreground" />
                  每周可用小时数
                </span>
              </Label>
              <Input
                id="weeklyHours"
                type="number"
                min={0.5}
                max={168}
                step={0.5}
                value={form.weeklyHours}
                onChange={(e) => setField('weeklyHours', e.target.value)}
              />
              {errors.weeklyHours && (
                <p className="text-sm text-red-500">{errors.weeklyHours}</p>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
            <div className="flex flex-col gap-2">
              <Label htmlFor="currentStage">当前研究阶段</Label>
              <NativeSelect
                id="currentStage"
                value={form.currentStage}
                onChange={(value) => setField('currentStage', value)}
                items={STAGE_ITEMS}
                placeholder="选择当前阶段"
              />
              {errors.currentStage && (
                <p className="text-sm text-red-500">{errors.currentStage}</p>
              )}
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="completedWork">已完成工作（可选）</Label>
              <Textarea
                id="completedWork"
                rows={1}
                placeholder="如：已读完 20 篇相关文献"
                value={form.completedWork}
                onChange={(e) => setField('completedWork', e.target.value)}
              />
            </div>
          </div>

          <div className="flex flex-wrap justify-end gap-2 border-t border-border pt-4">
            <Button
              variant="outline"
              disabled={generating || submitting}
              onClick={() => void handleCreateEmpty()}
            >
              {submitting ? '创建中…' : '跳过 AI，直接创建'}
            </Button>
            <Button disabled={generating || submitting} onClick={() => void handleGeneratePlan()}>
              {generating ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  正在生成科研计划…
                </>
              ) : (
                <>
                  <Sparkles className="size-4" />
                  生成科研计划
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {generating && (
        <Card>
          <CardContent className="flex items-center gap-3 py-6">
            <Loader2 className="size-5 animate-spin text-primary" />
            <div>
              <p className="text-sm font-medium">DeepSeek 正在拆解科研任务</p>
              <p className="mt-0.5 text-xs text-muted-foreground">
                通常需要 10~60 秒，请稍候…
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {plan && !generating && (
        <Card>
          <CardHeader>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <CardTitle>科研计划预览</CardTitle>
                <CardDescription>
                  共 {plan.tasks.length} 个任务，确认后写入看板
                </CardDescription>
              </div>
              <Badge variant={plan.source === 'demo' ? 'secondary' : 'default'}>
                {plan.source === 'demo' ? '演示模式' : 'DeepSeek 生成'}
              </Badge>
            </div>
            {plan.warning && (
              <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-700 dark:bg-amber-500/10 dark:text-amber-400">
                {plan.warning}
              </p>
            )}
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            {plan.tasks.map((task) => (
              <PlanTaskItem key={task.taskId} task={task} />
            ))}

            <div className="flex justify-end gap-2 border-t border-border pt-4">
              <Button
                variant="outline"
                disabled={submitting}
                onClick={() => {
                  setPlan(null)
                  void handleGeneratePlan()
                }}
              >
                <RotateCcw className="size-4" />
                重新生成
              </Button>
              <Button disabled={submitting} onClick={() => void handleConfirmPlan()}>
                {submitting ? '写入中…' : (
                  <>
                    <CheckCircle2 className="size-4" />
                    确认创建
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

/** 计划中的单个任务条目：标题、优先级、日期、耗时、产出与理由 */
function PlanTaskItem({ task }: { task: AiPlanTask }) {
  return (
    <div className="flex flex-col gap-1.5 rounded-xl border border-border bg-background p-3">
      <div className="flex items-start justify-between gap-2">
        <p className="min-w-0 text-sm font-medium leading-snug break-words">
          <span className="mr-1.5 text-xs text-muted-foreground tabular-nums">
            [{task.taskId}]
          </span>
          {task.title}
        </p>
        <Badge variant="outline" className={PRIORITY_BADGE_CLASSES[task.priority] ?? ''}>
          {task.priority}
        </Badge>
      </div>
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1">
          <CalendarDays className="size-3.5" />
          {task.startDate} ~ {task.dueDate}
        </span>
        <span className="inline-flex items-center gap-1">
          <Clock3 className="size-3.5" />
          {task.estimatedHours}h
        </span>
        {task.dependencies.length > 0 && (
          <span className="inline-flex items-center gap-1">
            <Flag className="size-3.5" />
            前置 {task.dependencies.join('、')}
          </span>
        )}
      </div>
      {task.expectedDeliverable && (
        <p className="text-xs text-muted-foreground">产出：{task.expectedDeliverable}</p>
      )}
      {task.rationale && (
        <p className="text-xs text-muted-foreground/80">安排理由：{task.rationale}</p>
      )}
    </div>
  )
}
