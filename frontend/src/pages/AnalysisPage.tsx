import {
  ArrowLeft,
  BarChart3,
  CheckCircle2,
  FlaskConical,
  History,
  Pencil,
  Quote,
  XCircle,
} from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ErrorState } from '@/components/common/ErrorState'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { Textarea } from '@/components/ui/textarea'
import { toast } from '@/components/ui/toast'
import { useAsyncData } from '@/hooks/useAsyncData'
import {
  adoptSuggestion,
  fetchAnalysisActions,
  fetchProjectDetail,
  fetchResearchAnalysis,
  modifySuggestion,
  rejectSuggestion,
} from '@/services/api'
import type {
  HypothesisStatus,
  NextExperiment,
  ResearchActionLog,
  ResearchAnalysis,
} from '@/types'

const STATUS_LABELS: Record<HypothesisStatus, string> = {
  support: '支持假设',
  not_support: '不支持假设',
  insufficient_evidence: '证据不足',
}

const STATUS_BADGE_CLASSES: Record<HypothesisStatus, string> = {
  support: 'border-emerald-300 bg-emerald-50 text-emerald-700 dark:border-emerald-500/40 dark:bg-emerald-500/10 dark:text-emerald-400',
  not_support: 'border-red-300 bg-red-50 text-red-600 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-400',
  insufficient_evidence: 'border-amber-300 bg-amber-50 text-amber-700 dark:border-amber-500/40 dark:bg-amber-500/10 dark:text-amber-400',
}

const ACTION_LABELS: Record<ResearchActionLog['action'], string> = {
  adopted: '采纳',
  rejected: '拒绝',
  modified: '修改',
}

const fmtTime = (iso: string) => iso.slice(0, 16).replace('T', ' ')

/** 确定性统计块（Python 后端计算，AI 只引用） */
function StatsBlock({ analysis }: { analysis: ResearchAnalysis }) {
  const { stats } = analysis
  if (!stats.metrics.length) {
    return (
      <p className="text-xs text-muted-foreground">
        无可用统计（运行记录中没有数值型指标）。
      </p>
    )
  }
  return (
    <div className="flex flex-col gap-4">
      {stats.metrics.map((metric) => (
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
              <thead>
                <tr className="border-b border-border text-left text-xs text-muted-foreground">
                  <th className="py-1.5 pr-3 font-medium">实验</th>
                  <th className="py-1.5 pr-3 font-medium">运行</th>
                  <th className="py-1.5 pr-3 font-medium">最小</th>
                  <th className="py-1.5 pr-3 font-medium">最大</th>
                  <th className="py-1.5 pr-3 font-medium">均值</th>
                  <th className="py-1.5 font-medium">最优（第几次）</th>
                </tr>
              </thead>
              <tbody>
                {metric.experiments.map((row) => (
                  <tr key={row.experimentId} className="border-b border-border/50">
                    <td className="py-1.5 pr-3">{row.title}</td>
                    <td className="py-1.5 pr-3 tabular-nums">{row.runCount}</td>
                    <td className="py-1.5 pr-3 tabular-nums">{row.min}</td>
                    <td className="py-1.5 pr-3 tabular-nums">{row.max}</td>
                    <td className="py-1.5 pr-3 tabular-nums">{row.mean}</td>
                    <td className="py-1.5 tabular-nums">
                      {row.best}（#{row.bestRunNo}）
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}
      {stats.comparisons.length > 0 && (
        <div>
          <p className="mb-1.5 text-sm font-medium">跨实验比较（最优值差）</p>
          {stats.comparisons.map((comparison) => (
            <p key={comparison.metric} className="text-xs text-muted-foreground">
              {comparison.metric}：{comparison.rows.map((r) => `${r.title} ${r.best}（Δ${r.deltaVsFirst > 0 ? '+' : ''}${r.deltaVsFirst}）`).join('；')}
            </p>
          ))}
        </div>
      )}
    </div>
  )
}

/** 修改建议抽屉 */
function ModifySuggestionSheet({
  open,
  onOpenChange,
  analysisId,
  index,
  suggestion,
  onSaved,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  analysisId: number
  index: number
  suggestion: NextExperiment
  onSaved: () => void
}) {
  const [fields, setFields] = useState<Record<string, string>>({})
  const [submitting, setSubmitting] = useState(false)
  const keys: Array<[keyof NextExperiment, string, number]> = [
    ['objective', '实验目的', 3],
    ['hypothesis', '待验证假设', 3],
    ['changedVariables', '改变变量', 2],
    ['fixedConditions', '保持不变的条件', 2],
    ['metrics', '评价指标', 2],
    ['expectedObservation', '预期观察', 2],
    ['risks', '风险', 2],
    ['estimatedEffort', '估计工作量', 1],
  ]

  useEffect(() => {
    if (!open) return
    const next: Record<string, string> = {}
    for (const [key] of keys) next[key] = String(suggestion[key] ?? '')
    setFields(next)
  }, [open, suggestion])

  const handleSave = async () => {
    setSubmitting(true)
    try {
      await modifySuggestion(analysisId, index, {
        objective: fields.objective,
        hypothesis: fields.hypothesis,
        changedVariables: fields.changedVariables,
        fixedConditions: fields.fixedConditions,
        metrics: fields.metrics,
        expectedObservation: fields.expectedObservation,
        risks: fields.risks,
        estimatedEffort: fields.estimatedEffort,
      })
      toast.add({ title: '建议已修改并留档', type: 'success' })
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
          <SheetTitle>修改建议 #{index + 1}</SheetTitle>
          <SheetDescription>修改只保存并留档，不会创建任何实验或任务。</SheetDescription>
        </SheetHeader>
        <div className="flex flex-1 flex-col gap-3 overflow-y-auto px-4">
          {keys.map(([key, label, rows]) => (
            <div key={key} className="flex flex-col gap-2">
              <Label>{label}</Label>
              <Textarea
                rows={rows}
                value={fields[key] ?? ''}
                onChange={(e) => setFields((prev) => ({ ...prev, [key]: e.target.value }))}
              />
            </div>
          ))}
        </div>
        <SheetFooter>
          <Button variant="outline" disabled={submitting} onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button disabled={submitting} onClick={() => void handleSave()}>
            {submitting ? '保存中…' : '保存修改'}
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}

/** 采纳建议抽屉：确认执行计划（创建实验 + 关联任务） */
function AdoptSuggestionSheet({
  open,
  onOpenChange,
  analysis,
  index,
  suggestion,
  onAdopted,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  analysis: ResearchAnalysis
  index: number
  suggestion: NextExperiment
  onAdopted: () => void
}) {
  const [objective, setObjective] = useState('')
  const [hypothesis, setHypothesis] = useState('')
  const [variables, setVariables] = useState('')
  const [requiredData, setRequiredData] = useState('')
  const [preconditions, setPreconditions] = useState('')
  const [estimatedHours, setEstimatedHours] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [selectedDeps, setSelectedDeps] = useState<number[]>([])
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const loadTasks = useCallback(
    () => fetchProjectDetail(analysis.projectId).then((d) => d.tasks),
    [analysis.projectId]
  )
  const { data: tasks } = useAsyncData(loadTasks)
  const candidateTasks = (tasks ?? []).filter((t) => t.status !== 'done')

  useEffect(() => {
    if (!open) return
    setObjective(suggestion.objective)
    setHypothesis(suggestion.hypothesis)
    setVariables(suggestion.changedVariables)
    setRequiredData(suggestion.fixedConditions)
    setPreconditions('')
    setEstimatedHours('8')
    const start = new Date()
    const end = new Date()
    end.setDate(end.getDate() + 14)
    setStartDate(start.toISOString().slice(0, 10))
    setEndDate(end.toISOString().slice(0, 10))
    setSelectedDeps([])
    setError('')
  }, [open, suggestion])

  const handleSubmit = async () => {
    if (!objective.trim() || !hypothesis.trim()) {
      setError('实验目的与研究假设不能为空')
      return
    }
    const hours = Number(estimatedHours)
    if (Number.isNaN(hours) || hours <= 0) {
      setError('预计工时必须是大于 0 的数字')
      return
    }
    if (!startDate || !endDate || endDate < startDate) {
      setError('计划日期不合法（截止不能早于开始）')
      return
    }
    setSubmitting(true)
    try {
      const result = await adoptSuggestion(analysis.id, index, {
        objective: objective.trim(),
        hypothesis: hypothesis.trim(),
        variables: variables.trim() || null,
        requiredData: requiredData.trim() || null,
        preconditions: preconditions.trim() || null,
        estimatedHours: hours,
        plannedStartDate: startDate,
        plannedEndDate: endDate,
        dependencies: selectedDeps,
      })
      toast.add({
        title: '已采纳：实验与任务已创建',
        description: `实验「${result.experiment.title.slice(0, 30)}…」+ 任务已写入看板（带来源标记）`,
        type: 'success',
      })
      onOpenChange(false)
      onAdopted()
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
          <SheetTitle>确认采纳建议 #{index + 1}</SheetTitle>
          <SheetDescription>
            这是执行计划确认：确认后将创建实验与关联任务；修改建议内容不会改变原始建议（留档为"修改"）。
          </SheetDescription>
        </SheetHeader>
        <div className="flex flex-1 flex-col gap-3 overflow-y-auto px-4">
          <div className="flex flex-col gap-2">
            <Label htmlFor="adopt-objective">实验目的 *</Label>
            <Textarea id="adopt-objective" rows={2} value={objective} onChange={(e) => setObjective(e.target.value)} />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="adopt-hypothesis">研究假设 *</Label>
            <Textarea id="adopt-hypothesis" rows={2} value={hypothesis} onChange={(e) => setHypothesis(e.target.value)} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-2">
              <Label htmlFor="adopt-vars">实验变量</Label>
              <Textarea id="adopt-vars" rows={2} value={variables} onChange={(e) => setVariables(e.target.value)} />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="adopt-data">所需数据</Label>
              <Textarea id="adopt-data" rows={2} value={requiredData} onChange={(e) => setRequiredData(e.target.value)} />
            </div>
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="adopt-pre">前置条件</Label>
            <Input id="adopt-pre" value={preconditions} onChange={(e) => setPreconditions(e.target.value)} />
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div className="flex flex-col gap-2">
              <Label>预计工时（小时）*</Label>
              <Input type="number" min={0.5} step={0.5} value={estimatedHours} onChange={(e) => setEstimatedHours(e.target.value)} />
            </div>
            <div className="flex flex-col gap-2">
              <Label>计划开始</Label>
              <Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
            </div>
            <div className="flex flex-col gap-2">
              <Label>计划截止</Label>
              <Input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
            </div>
          </div>
          <div className="flex flex-col gap-2">
            <Label>依赖任务（可选，勾选未完成的前置任务）</Label>
            {candidateTasks.length === 0 ? (
              <p className="text-xs text-muted-foreground">项目暂无未完成任务，可不选依赖。</p>
            ) : (
              <div className="flex max-h-40 flex-col gap-1 overflow-y-auto rounded-lg border border-border p-2">
                {candidateTasks.map((t) => (
                  <label key={t.id} className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      className="size-3.5"
                      checked={selectedDeps.includes(t.id)}
                      onChange={() =>
                        setSelectedDeps((prev) =>
                          prev.includes(t.id) ? prev.filter((x) => x !== t.id) : [...prev, t.id]
                        )
                      }
                    />
                    {t.title.slice(0, 40)}
                  </label>
                ))}
              </div>
            )}
          </div>
          {error && <p className="text-sm text-red-500">{error}</p>}
        </div>
        <SheetFooter>
          <Button variant="outline" disabled={submitting} onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button disabled={submitting} onClick={() => void handleSubmit()}>
            {submitting ? '创建中…' : '确认采纳（创建实验+任务）'}
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}

/** AI 研究分析报告页（七段式） */
export default function AnalysisPage() {
  const navigate = useNavigate()
  const { id } = useParams()
  const analysisId = Number(id)
  const loadAnalysis = useCallback(() => fetchResearchAnalysis(analysisId), [analysisId])
  const { data: analysis, loading, error, reload } = useAsyncData(loadAnalysis)
  const loadActions = useCallback(() => fetchAnalysisActions(analysisId), [analysisId])
  const { data: actions } = useAsyncData(loadActions)

  const [modifyIndex, setModifyIndex] = useState<number | null>(null)
  const [adoptIndex, setAdoptIndex] = useState<number | null>(null)
  const [rejecting, setRejecting] = useState<number | null>(null)

  const handleReject = async (index: number) => {
    if (rejecting !== index) {
      setRejecting(index)
      return
    }
    try {
      await rejectSuggestion(analysisId, index)
      setRejecting(null)
      toast.add({ title: '已拒绝该建议并留档', type: 'info' })
      void reload()
    } catch {
      // 错误提示已由 api 层统一 toast 展示
    }
  }

  if (loading) {
    return <p className="py-10 text-center text-sm text-muted-foreground">加载分析报告中…</p>
  }
  if (error || !analysis) {
    return (
      <div className="flex flex-col items-center gap-4 py-10">
        <ErrorState message={error ?? '分析报告不存在'} onRetry={() => void reload()} />
        <Button variant="outline" onClick={() => navigate(-1)}>
          返回
        </Button>
      </div>
    )
  }

  const suggestion = (i: number) => analysis.nextExperiments[i]

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <Button variant="outline" size="sm" onClick={() => navigate(-1)}>
          <ArrowLeft className="size-3.5" />
          返回
        </Button>
        <div className="flex items-center gap-2">
          <Badge variant={analysis.source === 'demo' ? 'secondary' : 'default'}>
            {analysis.source === 'demo' ? '演示模式' : 'DeepSeek 生成'}
          </Badge>
          <span className="text-xs text-muted-foreground">{fmtTime(analysis.createdAt)}</span>
        </div>
      </div>

      {analysis.warning && (
        <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-700 dark:bg-amber-500/10 dark:text-amber-400">
          {analysis.warning}
        </p>
      )}

      {/* 实验事实 */}
      <Card>
        <CardHeader className="border-b border-border">
          <CardTitle className="text-base">实验事实（observed_facts）</CardTitle>
          <CardDescription>全部来自数据库真实运行记录，附带运行记录 ID 可溯源</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-2 pt-4">
          {analysis.observedFacts.length === 0 ? (
            <p className="text-xs text-muted-foreground">无实验事实。</p>
          ) : (
            analysis.observedFacts.map((fact, i) => (
              <div key={i} className="flex items-start gap-2 rounded-lg border border-border p-3">
                <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-emerald-500" />
                <div className="min-w-0">
                  <p className="text-sm">{fact.content}</p>
                  <p className="mt-0.5 text-xs text-muted-foreground">运行记录 #{fact.experimentRunId}</p>
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>

      {/* 文献证据 */}
      <Card>
        <CardHeader className="border-b border-border">
          <CardTitle className="text-base">文献证据（paper_evidence）</CardTitle>
          <CardDescription>引用真实卡片与片段，页码与原文以数据库为准</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-2 pt-4">
          {analysis.paperEvidence.length === 0 ? (
            <p className="text-xs text-muted-foreground">未找到文献依据（引用留空，不编造）。</p>
          ) : (
            analysis.paperEvidence.map((ev, i) => (
              <div key={i} className="rounded-lg border border-border p-3">
                <p className="text-sm">{ev.statement}</p>
                <p className="mt-1.5 flex items-start gap-1.5 text-xs text-muted-foreground">
                  <Quote className="mt-0.5 size-3.5 shrink-0" />
                  "{ev.quote}"
                </p>
                <p className="mt-1 text-[11px] text-muted-foreground">
                  卡片 #{ev.paperNoteId} · 片段 {ev.snippetId}
                  {ev.page ? ` · p.${ev.page}` : ''}
                </p>
              </div>
            ))
          )}
        </CardContent>
      </Card>

      {/* 确定性统计 */}
      <Card>
        <CardHeader className="border-b border-border">
          <CardTitle className="flex items-center gap-2 text-base">
            <BarChart3 className="size-4" />
            确定性统计（Python 后端计算）
          </CardTitle>
          <CardDescription>AI 解释所引用的数值全部来自本块，系统不生成假数据</CardDescription>
        </CardHeader>
        <CardContent className="pt-4">
          <StatsBlock analysis={analysis} />
        </CardContent>
      </Card>

      {/* 解释与假设判定 */}
      <Card>
        <CardHeader className="border-b border-border">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <CardTitle className="text-base">解释与假设判定</CardTitle>
            <Badge variant="outline" className={STATUS_BADGE_CLASSES[analysis.hypothesisStatus]}>
              {STATUS_LABELS[analysis.hypothesisStatus]}
            </Badge>
          </div>
          <CardDescription>interpretation 为推测而非结论；判定分支持/不支持/证据不足三态</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3 pt-4">
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{analysis.interpretation}</p>
          <div className="rounded-lg bg-muted px-3 py-2">
            <p className="mb-1 text-xs font-medium text-muted-foreground">不确定性（uncertainty）</p>
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{analysis.uncertainty || '无'}</p>
          </div>
        </CardContent>
      </Card>

      {/* 下一步实验建议 */}
      <Card>
        <CardHeader className="border-b border-border">
          <CardTitle className="flex items-center gap-2 text-base">
            <FlaskConical className="size-4" />
            下一步实验建议（{analysis.nextExperiments.length}）
          </CardTitle>
          <CardDescription>建议不是结论：需您确认（可修改）后才创建实验与任务</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3 pt-4">
          {analysis.nextExperiments.length === 0 && (
            <p className="text-xs text-muted-foreground">暂无建议。</p>
          )}
          {analysis.nextExperiments.map((item, index) => (
            <div key={index} className="rounded-lg border border-border p-3">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium">{item.objective}</p>
                  <p className="mt-1 text-xs text-muted-foreground">假设：{item.hypothesis}</p>
                  <div className="mt-2 grid grid-cols-1 gap-x-4 gap-y-1 text-xs text-muted-foreground sm:grid-cols-2">
                    <p>改变变量：{item.changedVariables || '—'}</p>
                    <p>保持不变：{item.fixedConditions || '—'}</p>
                    <p>指标：{item.metrics || '—'}</p>
                    <p>预期观察：{item.expectedObservation || '—'}</p>
                    <p>风险：{item.risks || '—'}</p>
                    <p>工作量：{item.estimatedEffort || '—'}</p>
                  </div>
                </div>
                <div className="flex shrink-0 flex-col gap-1">
                  {item.converted ? (
                    <Badge variant="secondary">已采纳</Badge>
                  ) : item.rejected ? (
                    <Badge variant="outline" className="border-border bg-muted text-muted-foreground">已拒绝</Badge>
                  ) : (
                    <>
                      <Button
                        size="sm"
                        disabled={rejecting === index}
                        onClick={() => { setModifyIndex(index) }}
                      >
                        <Pencil className="size-3.5" />
                        修改
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={rejecting === index}
                        onClick={() => { setAdoptIndex(index) }}
                      >
                        <CheckCircle2 className="size-3.5" />
                        采纳
                      </Button>
                      <Button
                        size="sm"
                        variant={rejecting === index ? 'destructive' : 'ghost'}
                        onClick={() => void handleReject(index)}
                      >
                        <XCircle className="size-3.5" />
                        {rejecting === index ? '确认拒绝' : '拒绝'}
                      </Button>
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* 操作历史 */}
      <Card>
        <CardHeader className="border-b border-border">
          <CardTitle className="flex items-center gap-2 text-base">
            <History className="size-4" />
            操作历史
          </CardTitle>
          <CardDescription>采纳/拒绝/修改全部留档，可回溯当时的决定</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-2 pt-4">
          {!actions || actions.length === 0 ? (
            <p className="text-xs text-muted-foreground">暂无操作记录。</p>
          ) : (
            actions.map((log) => (
              <div key={log.id} className="flex items-center justify-between gap-2 rounded-lg border border-border p-3">
                <div className="min-w-0">
                  <p className="text-sm">
                    <Badge variant="outline" className="mr-2 border-primary/40 text-primary">
                      {ACTION_LABELS[log.action]}
                    </Badge>
                    建议 #{log.suggestionIndex + 1}
                    {log.taskId != null && <span className="ml-2 text-xs text-muted-foreground">任务 #{log.taskId}</span>}
                    {log.experimentId != null && <span className="ml-2 text-xs text-muted-foreground">实验 #{log.experimentId}</span>}
                  </p>
                </div>
                <span className="shrink-0 text-xs text-muted-foreground">{fmtTime(log.createdAt)}</span>
              </div>
            ))
          )}
        </CardContent>
      </Card>

      {modifyIndex !== null && (
        <ModifySuggestionSheet
          open={modifyIndex !== null}
          onOpenChange={(v) => !v && setModifyIndex(null)}
          analysisId={analysis.id}
          index={modifyIndex}
          suggestion={suggestion(modifyIndex)}
          onSaved={() => void reload()}
        />
      )}
      {adoptIndex !== null && (
        <AdoptSuggestionSheet
          open={adoptIndex !== null}
          onOpenChange={(v) => !v && setAdoptIndex(null)}
          analysis={analysis}
          index={adoptIndex}
          suggestion={suggestion(adoptIndex)}
          onAdopted={() => void reload()}
        />
      )}
    </div>
  )
}
