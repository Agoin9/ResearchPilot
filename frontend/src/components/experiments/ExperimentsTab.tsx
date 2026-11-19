import {
  AlertTriangle,
  BarChart3,
  FlaskConical,
  Pencil,
  Plus,
  Trash2,
} from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { NativeSelect } from '@/components/ui/native-select'
import { Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { Textarea } from '@/components/ui/textarea'
import { toast } from '@/components/ui/toast'
import { useAsyncData } from '@/hooks/useAsyncData'
import {
  createExperiment,
  deleteExperiment,
  fetchExperiments,
  fetchMetricsOverview,
  fetchQuestions,
  updateExperiment,
} from '@/services/api'
import type { Experiment, ExperimentStatus, MetricDef, Question } from '@/types'
import { ExperimentDetail } from './ExperimentDetail'

const STATUS_LABELS: Record<ExperimentStatus, string> = {
  draft: '设计中',
  running: '进行中',
  done: '已完成',
  failed: '失败',
  paused: '已暂停',
}

const STATUS_BADGE_CLASSES: Record<ExperimentStatus, string> = {
  draft: 'border-border bg-muted text-muted-foreground',
  running: 'border-sky-300 bg-sky-50 text-sky-700 dark:border-sky-500/40 dark:bg-sky-500/10 dark:text-sky-400',
  done: 'border-emerald-300 bg-emerald-50 text-emerald-700 dark:border-emerald-500/40 dark:bg-emerald-500/10 dark:text-emerald-400',
  failed: 'border-red-300 bg-red-50 text-red-600 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-400',
  paused: 'border-amber-300 bg-amber-50 text-amber-700 dark:border-amber-500/40 dark:bg-amber-500/10 dark:text-amber-400',
}

const STATUS_ITEMS: Array<{ value: ExperimentStatus; label: string }> = [
  { value: 'draft', label: '设计中' },
  { value: 'running', label: '进行中' },
  { value: 'done', label: '已完成' },
  { value: 'failed', label: '失败' },
  { value: 'paused', label: '已暂停' },
]

interface ExperimentFormSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  projectId: number
  experiment: Experiment | null
  questions: Question[]
  onSaved: () => void
}

/** 新建 / 编辑实验抽屉（含指标定义与 v2.1 设计字段） */
function ExperimentFormSheet({
  open,
  onOpenChange,
  projectId,
  experiment,
  questions,
  onSaved,
}: ExperimentFormSheetProps) {
  const [title, setTitle] = useState('')
  const [objective, setObjective] = useState('')
  const [hypothesis, setHypothesis] = useState('')
  const [variables, setVariables] = useState('')
  const [controlConditions, setControlConditions] = useState('')
  const [dataset, setDataset] = useState('')
  const [model, setModel] = useState('')
  const [design, setDesign] = useState('')
  const [configJson, setConfigJson] = useState('')
  const [status, setStatus] = useState<ExperimentStatus>('draft')
  const [questionId, setQuestionId] = useState('')
  const [metricsText, setMetricsText] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (!open) return
    setTitle(experiment?.title ?? '')
    setObjective(experiment?.objective ?? '')
    setHypothesis(experiment?.hypothesis ?? '')
    setVariables(experiment?.variables ?? '')
    setControlConditions(experiment?.controlConditions ?? '')
    setDataset(experiment?.dataset ?? '')
    setModel(experiment?.model ?? '')
    setDesign(experiment?.design ?? '')
    setConfigJson(JSON.stringify(experiment?.config ?? {}, null, 2))
    setStatus(experiment?.status ?? 'draft')
    setQuestionId(experiment?.questionId != null ? String(experiment.questionId) : '')
    setMetricsText(
      (experiment?.metrics ?? [])
        .map((m) => `${m.name}${m.unit ? `(${m.unit})` : ''}${m.higherIsBetter ? '' : '[低好]'}`)
        .join(', ')
    )
    setError('')
  }, [open, experiment])

  const parseMetrics = (): MetricDef[] => {
    if (!metricsText.trim()) return []
    const result: MetricDef[] = []
    for (const part of metricsText.split(/[,，]/)) {
      const trimmed = part.trim()
      if (!trimmed) continue
      const lowBetter = trimmed.includes('[低好]')
      const name = trimmed.replace(/\(.+?\)/g, '').replace('[低好]', '').trim()
      const unitMatch = trimmed.match(/\((.+?)\)/)
      if (!name) continue
      result.push({
        name,
        unit: unitMatch ? unitMatch[1] : '',
        higherIsBetter: !lowBetter,
      })
    }
    return result
  }

  const handleSubmit = async () => {
    if (!title.trim()) {
      setError('请输入实验标题')
      return
    }
    if (!objective.trim()) {
      setError('请输入实验目的')
      return
    }
    let config: Record<string, unknown> = {}
    if (configJson.trim()) {
      try {
        const parsed = JSON.parse(configJson)
        if (parsed === null || typeof parsed !== 'object' || Array.isArray(parsed)) {
          setError('实验配置必须是 JSON 对象（如 {"epochs": 50}）')
          return
        }
        config = parsed
      } catch {
        setError('实验配置不是合法 JSON，请检查格式')
        return
      }
    }
    const payload = {
      questionId: questionId ? Number(questionId) : null,
      title: title.trim(),
      objective: objective.trim(),
      hypothesis: hypothesis.trim() || null,
      variables: variables.trim() || null,
      controlConditions: controlConditions.trim() || null,
      dataset: dataset.trim() || null,
      model: model.trim() || null,
      design: design.trim() || null,
      config,
      metrics: parseMetrics(),
      status,
    }
    setSubmitting(true)
    try {
      if (experiment) {
        await updateExperiment(experiment.id, payload)
        toast.add({ title: '实验已更新', type: 'success' })
      } else {
        await createExperiment(projectId, payload)
        toast.add({ title: '实验已创建', type: 'success' })
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
      <SheetContent className="sm:max-w-lg">
        <SheetHeader>
          <SheetTitle>{experiment ? '编辑实验' : '新建实验'}</SheetTitle>
          <SheetDescription>
            记录实验目的、假设与方案；结果通过「运行记录」录入。执行仍在你的实验室/服务器上进行。
          </SheetDescription>
        </SheetHeader>
        <div className="flex flex-1 flex-col gap-3 overflow-y-auto px-4">
          <div className="flex flex-col gap-2">
            <Label htmlFor="exp-title">实验标题</Label>
            <Input
              id="exp-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="如：方法A vs 方法B 在数据集X上的对比"
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="exp-objective">实验目的</Label>
            <Textarea
              id="exp-objective"
              rows={2}
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="exp-hypothesis">待验证假设（可选）</Label>
            <Textarea
              id="exp-hypothesis"
              rows={2}
              placeholder="如：方法A在X数据集上的精度高于方法B"
              value={hypothesis}
              onChange={(e) => setHypothesis(e.target.value)}
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-2">
              <Label htmlFor="exp-variables">实验变量</Label>
              <Textarea
                id="exp-variables"
                rows={2}
                placeholder="如：模型结构、学习率"
                value={variables}
                onChange={(e) => setVariables(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="exp-control">对照条件</Label>
              <Textarea
                id="exp-control"
                rows={2}
                placeholder="如：相同数据划分、相同训练轮数"
                value={controlConditions}
                onChange={(e) => setControlConditions(e.target.value)}
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-2">
              <Label htmlFor="exp-dataset">数据集</Label>
              <Input
                id="exp-dataset"
                placeholder="如：数据集X（训练8:验证2）"
                value={dataset}
                onChange={(e) => setDataset(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="exp-model">模型</Label>
              <Input
                id="exp-model"
                placeholder="如：方法A、方法B"
                value={model}
                onChange={(e) => setModel(e.target.value)}
              />
            </div>
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="exp-config">实验配置（JSON 对象，可选）</Label>
            <Textarea
              id="exp-config"
              rows={3}
              className="font-mono text-xs"
              placeholder='{"epochs": 50, "batchSize": 32}'
              value={configJson}
              onChange={(e) => setConfigJson(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="exp-design">实验方案（Markdown，可选）</Label>
            <Textarea
              id="exp-design"
              rows={4}
              placeholder="流程、分组、评价方式……"
              value={design}
              onChange={(e) => setDesign(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="exp-metrics">指标定义（逗号分隔）</Label>
            <Input
              id="exp-metrics"
              placeholder="Accuracy(%), F1, 训练时长(h)[低好]"
              value={metricsText}
              onChange={(e) => setMetricsText(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              格式：指标名(单位)，加 [低好] 表示数值越低越好；同名指标会参与结果对比。
            </p>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-2">
              <Label>关联研究问题</Label>
              <NativeSelect
                value={questionId}
                onChange={setQuestionId}
                items={questions.map((q) => ({ value: String(q.id), label: q.content.slice(0, 20) }))}
                placeholder="不关联"
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label>状态</Label>
              <NativeSelect
                value={status}
                onChange={(value) => setStatus((value || 'draft') as ExperimentStatus)}
                items={STATUS_ITEMS}
              />
            </div>
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

/** 实验 Tab：实验列表 + 跨实验指标总览 + 点击进入实验详情（运行记录/对比/AI 分析） */
export function ExperimentsTab({ projectId }: { projectId: number }) {
  const loadExperiments = useCallback(() => fetchExperiments(projectId), [projectId])
  const loadQuestions = useCallback(() => fetchQuestions(projectId), [projectId])
  const loadOverview = useCallback(() => fetchMetricsOverview(projectId), [projectId])
  const { data, loading, reload } = useAsyncData(loadExperiments)
  const { data: questions } = useAsyncData(loadQuestions)
  const { data: overview } = useAsyncData(loadOverview)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<Experiment | null>(null)
  const [confirmingDelete, setConfirmingDelete] = useState<number | null>(null)

  const handleDelete = async (id: number) => {
    if (confirmingDelete !== id) {
      setConfirmingDelete(id)
      return
    }
    try {
      await deleteExperiment(id)
      setConfirmingDelete(null)
      toast.add({ title: '实验已删除', description: '运行记录与附件已一并清除', type: 'success' })
      void reload()
    } catch {
      // 错误提示已由 api 层统一 toast 展示
    }
  }

  if (loading) {
    return <p className="py-10 text-center text-sm text-muted-foreground">加载实验中…</p>
  }

  const experiments = data ?? []

  if (selectedId !== null) {
    return (
      <ExperimentDetail
        experimentId={selectedId}
        onBack={() => setSelectedId(null)}
        onChanged={() => void reload()}
      />
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <FlaskConical className="size-5 text-muted-foreground" />
          <h3 className="text-base font-semibold">实验</h3>
          <Badge variant="secondary">{experiments.length} 个</Badge>
        </div>
        <Button onClick={() => { setEditing(null); setFormOpen(true) }}>
          <Plus className="size-4" />
          新建实验
        </Button>
      </div>

      <p className="text-xs text-muted-foreground">
        实验是科研的核心载体：记录设计、假设与每次真实运行结果，支持对比与 AI 分析。
      </p>

      {experiments.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border py-10 text-center text-sm text-muted-foreground">
          还没有实验。围绕研究问题设计第一个实验，或从文献卡片的启发开始。
        </div>
      ) : (
        experiments.map((experiment) => (
          <Card
            key={experiment.id}
            className="cursor-pointer transition-colors hover:border-primary/40"
            onClick={() => setSelectedId(experiment.id)}
          >
            <CardHeader className="border-b border-border">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex flex-wrap items-center gap-2">
                  <CardTitle className="text-base">{experiment.title}</CardTitle>
                  <Badge variant="outline" className={STATUS_BADGE_CLASSES[experiment.status]}>
                    {STATUS_LABELS[experiment.status]}
                  </Badge>
                  {experiment.stalled && (
                    <Badge variant="destructive">
                      <AlertTriangle className="mr-1 size-3" />
                      停滞 {(() => {
                        if (!experiment.lastRunAt) return ''
                        const days = Math.floor(
                          (Date.now() - new Date(experiment.lastRunAt).getTime()) / 86400000
                        )
                        return `${days} 天`
                      })()}
                    </Badge>
                  )}
                </div>
                <div className="flex shrink-0 gap-1" onClick={(e) => e.stopPropagation()}>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-7 gap-1 px-2 text-xs"
                    onClick={() => { setEditing(experiment); setFormOpen(true) }}
                  >
                    <Pencil className="size-3.5" />
                    编辑
                  </Button>
                  <Button
                    size="sm"
                    variant={confirmingDelete === experiment.id ? 'destructive' : 'ghost'}
                    className="h-7 gap-1 px-2 text-xs"
                    onClick={() => void handleDelete(experiment.id)}
                  >
                    <Trash2 className="size-3.5" />
                    {confirmingDelete === experiment.id ? '确认删除' : '删除'}
                  </Button>
                </div>
              </div>
              <CardDescription className="mt-1 line-clamp-2">{experiment.objective}</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-muted-foreground">
              <span>{experiment.runCount} 次运行记录</span>
              {experiment.lastRunAt && (
                <span>最近运行：{experiment.lastRunAt.slice(0, 16).replace('T', ' ')}</span>
              )}
              {experiment.metrics.length > 0 && (
                <span>指标：{experiment.metrics.map((m) => m.name).join('、')}</span>
              )}
            </CardContent>
          </Card>
        ))
      )}

      {/* 跨实验指标总览 */}
      {(overview?.metrics ?? []).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <BarChart3 className="size-4" />
              跨实验指标总览
            </CardTitle>
            <CardDescription>按同名指标聚合全部实验的运行结果（本地计算）</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {overview?.metrics.map((metric) => (
              <div key={metric.name}>
                <p className="mb-1.5 text-sm font-medium">
                  {metric.name}
                  {metric.unit && <span className="text-xs text-muted-foreground">（{metric.unit}）</span>}
                  <span className="ml-2 text-xs text-muted-foreground">
                    {metric.higherIsBetter ? '越高越好' : '越低越好'}
                  </span>
                </p>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <tbody>
                      {metric.points.map((point) => (
                        <tr key={`${point.experimentId}-${point.runId}`} className="border-b border-border/50">
                          <td className="py-1.5 pr-3 text-xs text-muted-foreground">
                            {point.experimentTitle} · 运行 #{point.runNo}
                          </td>
                          <td className="py-1.5 tabular-nums">{point.value}</td>
                          <td className="py-1.5 text-xs">
                            <Badge variant="outline" className={STATUS_BADGE_CLASSES[point.experimentStatus]}>
                              {STATUS_LABELS[point.experimentStatus]}
                            </Badge>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      <ExperimentFormSheet
        open={formOpen}
        onOpenChange={setFormOpen}
        projectId={projectId}
        experiment={editing}
        questions={questions ?? []}
        onSaved={() => void reload()}
      />
    </div>
  )
}
