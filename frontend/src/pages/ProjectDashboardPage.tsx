import {
  AlertOctagon,
  AlertTriangle,
  CalendarDays,
  Clock3,
  ListChecks,
  Pencil,
  Trash2,
} from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ProjectBoard } from '@/components/board/ProjectBoard'
import { ErrorState } from '@/components/common/ErrorState'
import { DocumentLibraryTab } from '@/components/documents/DocumentLibraryTab'
import { ReportCenterTab } from '@/components/reports/ReportCenterTab'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Progress } from '@/components/ui/progress'
import { NativeSelect } from '@/components/ui/native-select'
import { Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'
import { toast } from '@/components/ui/toast'
import { useAsyncData } from '@/hooks/useAsyncData'
import { deleteProject, fetchProjectDetail, fetchProjects, updateProject } from '@/services/api'
import type { ProjectStatus } from '@/types'

const STATUS_LABELS: Record<ProjectStatus, string> = {
  active: '进行中',
  completed: '已完成',
  paused: '已暂停',
}

const STATUS_ITEMS: Array<{ value: ProjectStatus; label: string }> = [
  { value: 'active', label: '进行中' },
  { value: 'paused', label: '已暂停' },
  { value: 'completed', label: '已完成' },
]

interface EditProjectSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  project: { id: number; name: string; goal: string; deadline: string; weeklyHours: number; status: ProjectStatus }
  onSaved: () => void
}

/** 编辑项目抽屉：名称 / 目标 / 截止时间 / 每周小时 / 状态 */
function EditProjectSheet({ open, onOpenChange, project, onSaved }: EditProjectSheetProps) {
  const [name, setName] = useState('')
  const [goal, setGoal] = useState('')
  const [deadline, setDeadline] = useState('')
  const [weeklyHours, setWeeklyHours] = useState('')
  const [status, setStatus] = useState<ProjectStatus>('active')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (!open) return
    setName(project.name)
    setGoal(project.goal)
    setDeadline(project.deadline)
    setWeeklyHours(String(project.weeklyHours))
    setStatus(project.status)
    setError('')
  }, [open, project])

  const handleSubmit = async () => {
    if (!name.trim()) {
      setError('请输入项目名称')
      return
    }
    if (!goal.trim()) {
      setError('请输入科研目标描述')
      return
    }
    if (!deadline) {
      setError('请选择截止日期')
      return
    }
    const hours = Number(weeklyHours)
    if (Number.isNaN(hours) || hours <= 0) {
      setError('每周可用小时数必须大于 0')
      return
    }

    setSubmitting(true)
    try {
      await updateProject(project.id, {
        name: name.trim(),
        goal: goal.trim(),
        deadline,
        weeklyHours: hours,
        status,
      })
      toast.add({ title: '项目已更新', type: 'success' })
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
          <SheetTitle>编辑项目</SheetTitle>
          <SheetDescription>修改项目信息，保存后立即生效。</SheetDescription>
        </SheetHeader>

        <div className="flex flex-1 flex-col gap-4 overflow-y-auto px-4">
          <div className="flex flex-col gap-2">
            <Label htmlFor="project-name">项目名称</Label>
            <Input id="project-name" value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="project-goal">科研目标描述</Label>
            <Textarea id="project-goal" rows={4} value={goal} onChange={(e) => setGoal(e.target.value)} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-2">
              <Label htmlFor="project-deadline">截止时间</Label>
              <Input
                id="project-deadline"
                type="date"
                value={deadline}
                onChange={(e) => setDeadline(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="project-hours">每周可用小时数</Label>
              <Input
                id="project-hours"
                type="number"
                min={0.5}
                max={168}
                step={0.5}
                value={weeklyHours}
                onChange={(e) => setWeeklyHours(e.target.value)}
              />
            </div>
          </div>
          <div className="flex flex-col gap-2">
            <Label>项目状态</Label>
            <NativeSelect
              value={status}
              onChange={(value) => setStatus((value || 'active') as ProjectStatus)}
              items={STATUS_ITEMS}
            />
          </div>
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

/** 项目详情看板：项目信息卡 + 风险横幅 + 三列任务看板 */
export default function ProjectDashboardPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const projectId = Number(id)
  // 用 useCallback 固定 fetcher 引用，避免每次渲染生成新函数导致无限请求循环
  const loadDetail = useCallback(() => fetchProjectDetail(projectId), [projectId])
  const { data, loading, error, reload } = useAsyncData(loadDetail)
  // 项目列表（顶部切换器用）
  const { data: projectList } = useAsyncData(fetchProjects)
  const [editOpen, setEditOpen] = useState(false)
  const [confirmingDelete, setConfirmingDelete] = useState(false)

  const handleDeleteProject = async () => {
    if (!confirmingDelete) {
      setConfirmingDelete(true)
      return
    }
    try {
      await deleteProject(projectId)
      toast.add({ title: '项目已删除', description: '任务与进度记录已一并清除', type: 'success' })
      navigate('/')
    } catch {
      // 错误提示已由 api 层统一 toast 展示
    }
  }

  if (loading) {
    return <p className="py-10 text-center text-sm text-muted-foreground">加载项目中…</p>
  }
  if (error || !data) {
    return (
      <div className="flex flex-col items-center gap-4 py-10">
        <ErrorState message={error ?? '项目加载失败'} onRetry={() => void reload()} />
        <Button variant="outline" onClick={() => navigate('/')}>
          返回首页
        </Button>
      </div>
    )
  }

  const { project } = data
  const daysLeft = project.daysLeft
  const urgent = daysLeft <= 30

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6">
      {projectList && projectList.length > 1 && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm text-muted-foreground">切换项目</span>
          <NativeSelect
            value={String(projectId)}
            onChange={(value) => {
              if (value && value !== String(projectId)) {
                navigate(`/projects/${value}`)
              }
            }}
            items={projectList.map((p) => ({ value: String(p.id), label: p.name }))}
            className="w-64"
          />
        </div>
      )}

      <Card>
        <CardHeader className="flex-row items-start justify-between space-y-0 gap-2">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <CardTitle className="truncate">{project.name}</CardTitle>
              <Badge variant="secondary">{STATUS_LABELS[project.status]}</Badge>
              {project.risk === 'high' && (
                <Badge
                  variant="outline"
                  className="border-red-300 bg-red-50 text-red-600 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-400"
                >
                  <AlertOctagon className="size-3" />
                  高风险
                </Badge>
              )}
              {project.risk === 'medium' && (
                <Badge
                  variant="outline"
                  className="border-amber-300 bg-amber-50 text-amber-700 dark:border-amber-500/40 dark:bg-amber-500/10 dark:text-amber-400"
                >
                  <AlertTriangle className="size-3" />
                  进度落后
                </Badge>
              )}
            </div>
            <p className="mt-2 text-sm text-muted-foreground">{project.goal}</p>
          </div>
          <div className="flex shrink-0 gap-2">
            <Button variant="outline" size="sm" onClick={() => setEditOpen(true)}>
              <Pencil className="size-3.5" />
              编辑项目
            </Button>
            <Button
              size="sm"
              variant={confirmingDelete ? 'destructive' : 'outline'}
              onClick={() => void handleDeleteProject()}
            >
              <Trash2 className="size-3.5" />
              {confirmingDelete ? '确认删除' : '删除项目'}
            </Button>
          </div>
        </CardHeader>

        <CardContent className="flex flex-col gap-4">
          <div className="flex flex-wrap items-center gap-x-5 gap-y-1.5 text-sm text-muted-foreground">
            <span className="inline-flex items-center gap-1.5">
              <CalendarDays className="size-4" />
              截止 {project.deadline}
              {daysLeft < 0 ? (
                <span className="font-medium text-red-500">已逾期 {Math.abs(daysLeft)} 天</span>
              ) : (
                <span className={urgent ? 'font-medium text-red-500' : 'font-medium text-foreground'}>
                  剩 {daysLeft} 天
                </span>
              )}
            </span>
            <span className="inline-flex items-center gap-1.5">
              <Clock3 className="size-4" />
              每周 {project.weeklyHours} 小时
            </span>
            <span className="inline-flex items-center gap-1.5">
              <ListChecks className="size-4" />
              任务 {project.tasksDone}/{project.tasksTotal}
            </span>
          </div>
          <div>
            <div className="mb-1.5 flex items-center justify-between text-sm">
              <span className="text-muted-foreground">整体进度</span>
              <span className="font-medium tabular-nums">{project.progress}%</span>
            </div>
            <Progress value={project.progress} className="h-2" />
          </div>
        </CardContent>
      </Card>

      {project.risk === 'high' && (
        <div className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-400">
          <AlertOctagon className="mt-0.5 size-5 shrink-0" />
          <div>
            <p className="font-medium">项目存在延期风险</p>
            <p className="mt-0.5 text-xs opacity-90">
              有任务已逾期或项目已过截止日期，建议优先处理逾期任务、调整后续计划。
            </p>
          </div>
        </div>
      )}
      {project.risk === 'medium' && (
        <div className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-400">
          <AlertTriangle className="mt-0.5 size-5 shrink-0" />
          <div>
            <p className="font-medium">项目进度落后</p>
            <p className="mt-0.5 text-xs opacity-90">
              部分任务进度落后于计划，建议加快推进或调整任务安排。
            </p>
          </div>
        </div>
      )}

      <Tabs defaultValue="board">
        <TabsList>
          <TabsTrigger value="board">任务看板</TabsTrigger>
          <TabsTrigger value="library">文献库</TabsTrigger>
          <TabsTrigger value="reports">汇报中心</TabsTrigger>
        </TabsList>
        <TabsContent value="board" className="pt-4">
          <ProjectBoard projectId={projectId} />
        </TabsContent>
        <TabsContent value="library" className="pt-4">
          <DocumentLibraryTab projectId={projectId} />
        </TabsContent>
        <TabsContent value="reports" className="pt-4">
          <ReportCenterTab projectId={projectId} />
        </TabsContent>
      </Tabs>

      <EditProjectSheet
        open={editOpen}
        onOpenChange={setEditOpen}
        project={project}
        onSaved={() => void reload()}
      />
    </div>
  )
}
