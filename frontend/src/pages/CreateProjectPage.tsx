import { CalendarDays, Clock3, Sparkles, Target } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
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
import { Textarea } from '@/components/ui/textarea'
import { toast } from '@/components/ui/toast'
import { createProject } from '@/services/api'

const today = new Date().toISOString().slice(0, 10)

interface FormState {
  name: string
  goal: string
  deadline: string
  weeklyHours: string
}

type FormErrors = Partial<Record<keyof FormState, string>>

/** 新建项目：填写科研目标、截止时间、每周可用小时，创建后跳转到项目看板 */
export default function CreateProjectPage() {
  const navigate = useNavigate()
  const [submitting, setSubmitting] = useState(false)
  const [form, setForm] = useState<FormState>({
    name: '',
    goal: '',
    deadline: '',
    weeklyHours: '15',
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
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const handleSubmit = async () => {
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

  const handleAiDecompose = () => {
    toast.add({
      title: 'AI 智能拆解暂未接入',
      description: '当前版本先手动管理任务，创建项目后可在看板中添加任务。',
      type: 'info',
    })
  }

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle>新建科研项目</CardTitle>
          <CardDescription>
            填写科研目标与时间安排，创建后在看板中手动添加任务。
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
                科研目标描述
              </span>
            </Label>
            <Textarea
              id="goal"
              rows={4}
              placeholder="如：2026 年 12 月底前完成毕业论文初稿，包含文献综述、实验设计和数据分析"
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
                  截止时间
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

          <div className="flex justify-end gap-2 border-t border-border pt-4">
            <Button variant="outline" disabled={submitting} onClick={handleAiDecompose}>
              <Sparkles className="size-4" />
              AI 智能拆解
            </Button>
            <Button disabled={submitting} onClick={() => void handleSubmit()}>
              {submitting ? '创建中…' : '创建项目'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
