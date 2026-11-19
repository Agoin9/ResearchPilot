import {
  ArrowRight,
  ClipboardList,
  FlaskConical,
  Lightbulb,
  Pencil,
  Plus,
  Trash2,
} from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { EmptyState } from '@/components/common/EmptyState'
import { ErrorState } from '@/components/common/ErrorState'
import { Label } from '@/components/ui/label'
import { NativeSelect } from '@/components/ui/native-select'
import { Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { Textarea } from '@/components/ui/textarea'
import { toast } from '@/components/ui/toast'
import { useAsyncData } from '@/hooks/useAsyncData'
import {
  createDecision,
  deleteDecision,
  fetchExperimentDecisions,
  fetchExperimentDetail,
  fetchExperiments,
  fetchProjects,
  updateDecision,
} from '@/services/api'
import type { Experiment, ExperimentRun, ResearchDecision } from '@/types'

function supportsBadge(supports: boolean | null) {
  if (supports === true) {
    return (
      <Badge variant="outline" className="border-emerald-300 bg-emerald-50 text-emerald-700 dark:border-emerald-500/40 dark:bg-emerald-500/10 dark:text-emerald-400">
        支持假设
      </Badge>
    )
  }
  if (supports === false) {
    return (
      <Badge variant="outline" className="border-red-300 bg-red-50 text-red-600 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-400">
        否定假设
      </Badge>
    )
  }
  return <Badge variant="outline" className="border-border bg-muted text-muted-foreground">待定</Badge>
}

const fmtTime = (iso: string) => iso.slice(0, 16).replace('T', ' ')

interface DecisionFormSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  experiments: Experiment[]
  decision: ResearchDecision | null
  defaultExperimentId: number | null
  onSaved: () => void
}

/** 新建 / 编辑科研决策（内容全部来自研究者本人） */
function DecisionFormSheet({
  open,
  onOpenChange,
  experiments,
  decision,
  defaultExperimentId,
  onSaved,
}: DecisionFormSheetProps) {
  const [experimentId, setExperimentId] = useState('')
  const [runs, setRuns] = useState<ExperimentRun[]>([])
  const [selectedRunIds, setSelectedRunIds] = useState<number[]>([])
  const [observations, setObservations] = useState('')
  const [interpretation, setInterpretation] = useState('')
  const [supports, setSupports] = useState('')
  const [unknowns, setUnknowns] = useState('')
  const [suggestionsText, setSuggestionsText] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [loadingRuns, setLoadingRuns] = useState(false)

  useEffect(() => {
    if (!open) return
    setExperimentId(
      decision != null ? String(decision.experimentId) : defaultExperimentId != null ? String(defaultExperimentId) : ''
    )
    setSelectedRunIds(decision?.runIds ?? [])
    setObservations(decision?.observations ?? '')
    setInterpretation(decision?.interpretation ?? '')
    setSupports(decision?.supportsHypothesis === null ? 'pending' : decision != null ? String(decision.supportsHypothesis) : 'pending')
    setUnknowns(decision?.unknowns ?? '')
    setSuggestionsText((decision?.nextSuggestions ?? []).join('\n'))
    setRuns([])
    setError('')
  }, [open, decision, defaultExperimentId])

  // 实验变化时加载其运行记录
  useEffect(() => {
    if (!open || !experimentId) return
    setLoadingRuns(true)
    fetchExperimentDetail(Number(experimentId))
      .then((detail) => setRuns(detail.runs))
      .catch(() => setRuns([]))
      .finally(() => setLoadingRuns(false))
  }, [open, experimentId])

  const handleSubmit = async () => {
    if (!experimentId) {
      setError('请选择关联的实验')
      return
    }
    if (selectedRunIds.length === 0) {
      setError('请至少勾选一条作为判断依据的运行记录')
      return
    }
    if (!observations.trim()) {
      setError('请填写观察到的事实')
      return
    }
    const supportsValue =
      supports === 'true' ? true : supports === 'false' ? false : null
    const suggestions = suggestionsText
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean)
    setSubmitting(true)
    try {
      if (decision) {
        await updateDecision(decision.id, {
          runIds: selectedRunIds,
          observations: observations.trim(),
          interpretation: interpretation.trim() || null,
          supportsHypothesis: supportsValue,
          unknowns: unknowns.trim() || null,
          nextSuggestions: suggestions,
        })
        toast.add({ title: '决策已更新', type: 'success' })
      } else {
        await createDecision(Number(experimentId), {
          runIds: selectedRunIds,
          observations: observations.trim(),
          interpretation: interpretation.trim() || null,
          supportsHypothesis: supportsValue,
          unknowns: unknowns.trim() || null,
          nextSuggestions: suggestions,
        })
        toast.add({ title: '决策已记录', type: 'success' })
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
          <SheetTitle>{decision ? '编辑决策' : '记录研究决策'}</SheetTitle>
          <SheetDescription>
            基于真实运行记录写下你自己的判断——观察到什么、怎么解释、下一步做什么。
          </SheetDescription>
        </SheetHeader>
        <div className="flex flex-1 flex-col gap-3 overflow-y-auto px-4">
          <div className="flex flex-col gap-2">
            <Label>关联实验</Label>
            <NativeSelect
              value={experimentId}
              onChange={setExperimentId}
              items={experiments.map((e) => ({ value: String(e.id), label: e.title.slice(0, 24) }))}
              placeholder="选择实验"
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label>作为判断依据的运行记录</Label>
            {loadingRuns ? (
              <p className="text-xs text-muted-foreground">加载运行记录中…</p>
            ) : runs.length === 0 ? (
              <p className="rounded-lg border border-dashed border-border px-3 py-2 text-xs text-muted-foreground">
                该实验还没有运行记录——决策必须基于真实记录，请先录入。
              </p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {runs.map((run) => (
                  <button
                    key={run.id}
                    type="button"
                    onClick={() =>
                      setSelectedRunIds((prev) =>
                        prev.includes(run.id) ? prev.filter((x) => x !== run.id) : [...prev, run.id]
                      )
                    }
                    className={`flex items-center gap-2 rounded-lg border px-2.5 py-1 text-xs transition-colors ${
                      selectedRunIds.includes(run.id)
                        ? 'border-primary bg-primary/10 text-primary'
                        : 'border-border hover:border-primary/40'
                    }`}
                  >
                    <input type="checkbox" className="size-3" checked={selectedRunIds.includes(run.id)} readOnly />
                    运行 #{run.runNo}
                    {Object.keys(run.results ?? {}).length > 0 && (
                      <span className="text-muted-foreground">
                        ({Object.entries(run.results)
                          .slice(0, 2)
                          .map(([k, v]) => `${k}=${String(v)}`)
                          .join(', ')})
                      </span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="d-observations">观察到的事实 *</Label>
            <Textarea
              id="d-observations"
              rows={3}
              placeholder="如：第 1 次运行 Accuracy=87.3%，比基线高 2.1 个百分点"
              value={observations}
              onChange={(e) => setObservations(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="d-interpretation">分析解释</Label>
            <Textarea
              id="d-interpretation"
              rows={3}
              placeholder="这些结果说明了什么？"
              value={interpretation}
              onChange={(e) => setInterpretation(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label>是否支持假设</Label>
            <NativeSelect
              value={supports}
              onChange={setSupports}
              items={[
                { value: 'true', label: '支持假设' },
                { value: 'false', label: '否定假设' },
                { value: 'pending', label: '待定 / 无法判断' },
              ]}
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="d-unknowns">未知因素</Label>
            <Textarea
              id="d-unknowns"
              rows={2}
              placeholder="如：单次运行未重复验证；不同种子下的稳定性未知"
              value={unknowns}
              onChange={(e) => setUnknowns(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="d-suggestions">下一步研究建议（每行一条）</Label>
            <Textarea
              id="d-suggestions"
              rows={3}
              placeholder={'更换种子重复 3 次验证稳定性\n补充消融实验'}
              value={suggestionsText}
              onChange={(e) => setSuggestionsText(e.target.value)}
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

/** 研究决策日志：观察事实 / 分析解释 / 待验证问题 / 下一步建议 */
export default function DecisionsPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const [searchParams] = useSearchParams()
  const { data: projects, loading: loadingProjects, error: projectError } = useAsyncData(fetchProjects)
  const [selectedId, setSelectedId] = useState<number | null>(null)

  const stateProjectId = (location.state as { projectId?: number } | null)?.projectId
  const paramId = searchParams.get('project') ? Number(searchParams.get('project')) : null
  useEffect(() => {
    if (!projects || projects.length === 0) {
      setSelectedId(null)
      return
    }
    const found =
      projects.find((p) => p.id === paramId) ??
      projects.find((p) => p.id === stateProjectId) ??
      projects.find((p) => p.status === 'active') ??
      projects[0]
    setSelectedId(found.id)
  }, [projects, paramId, stateProjectId])

  const loadExperiments = useCallback(
    () => (selectedId !== null ? fetchExperiments(selectedId) : Promise.resolve([])),
    [selectedId]
  )
  const { data: experiments, loading: loadingExperiments, reload: reloadExperiments } = useAsyncData(loadExperiments)

  // 按实验查看决策：默认选择第一个有决策/有运行记录的实验
  const [experimentId, setExperimentId] = useState<number | null>(null)
  const loadDecisions = useCallback(
    () => (experimentId !== null ? fetchExperimentDecisions(experimentId) : Promise.resolve([])),
    [experimentId]
  )
  const { data: decisions, loading: loadingDecisions, error: decisionsError, reload: reloadDecisions } =
    useAsyncData(loadDecisions)

  useEffect(() => {
    if (!experiments || experiments.length === 0) {
      setExperimentId(null)
      return
    }
    if (experimentId !== null && experiments.some((e) => e.id === experimentId)) return
    const withRuns = experiments.filter((e) => e.runCount > 0)
    setExperimentId((withRuns[0] ?? experiments[0])?.id ?? null)
  }, [experiments, experimentId])

  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<ResearchDecision | null>(null)
  const [confirmingDelete, setConfirmingDelete] = useState<number | null>(null)

  const handleDelete = async (id: number) => {
    if (confirmingDelete !== id) {
      setConfirmingDelete(id)
      return
    }
    try {
      await deleteDecision(id)
      setConfirmingDelete(null)
      toast.add({ title: '决策已删除', description: '实验与运行记录不受影响', type: 'success' })
      void reloadDecisions()
    } catch {
      // 错误提示已由 api 层统一 toast 展示
    }
  }

  if (loadingProjects) {
    return <p className="py-10 text-center text-sm text-muted-foreground">加载项目中…</p>
  }
  if (projectError) {
    return <ErrorState message={projectError} onRetry={() => window.location.reload()} />
  }
  if (!projects || projects.length === 0) {
    return (
      <EmptyState
        icon={ClipboardList}
        title="还没有科研项目"
        description="先创建项目并完成实验，再来记录研究决策。"
        actionLabel="新建项目"
        onAction={() => navigate('/projects/new')}
      />
    )
  }

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <ClipboardList className="size-5 text-muted-foreground" />
          <NativeSelect
            value={selectedId !== null ? String(selectedId) : ''}
            onChange={(value) => value && setSelectedId(Number(value))}
            items={projects.map((p) => ({ value: String(p.id), label: p.name }))}
            placeholder="选择项目"
            className="w-56"
          />
          <NativeSelect
            value={experimentId !== null ? String(experimentId) : ''}
            onChange={(value) => value && setExperimentId(Number(value))}
            items={(experiments ?? []).map((e) => ({ value: String(e.id), label: e.title.slice(0, 24) }))}
            placeholder="选择实验"
            className="w-56"
          />
        </div>
        <Button
          size="sm"
          disabled={!experiments || experiments.length === 0}
          onClick={() => { setEditing(null); setFormOpen(true) }}
        >
          <Plus className="size-3.5" />
          记录新决策
        </Button>
      </div>

      <p className="text-xs text-muted-foreground">
        决策日志记录的是你自己的科研判断：基于真实运行记录观察到的事实、解释、假设判定与下一步建议。
      </p>

      {loadingExperiments || loadingDecisions ? (
        <p className="py-10 text-center text-sm text-muted-foreground">加载决策记录中…</p>
      ) : decisionsError ? (
        <ErrorState message={decisionsError} onRetry={() => void reloadDecisions()} />
      ) : (experiments ?? []).length === 0 ? (
        <EmptyState
          icon={FlaskConical}
          title="还没有实验"
          description="决策必须基于实验运行记录。先去实验工作台创建实验。"
          actionLabel="去实验工作台"
          onAction={() => navigate('/lab', { state: { projectId: selectedId } })}
        />
      ) : (decisions ?? []).length === 0 ? (
        <div className="rounded-xl border border-dashed border-border py-12 text-center">
          <Lightbulb className="mx-auto size-8 text-muted-foreground" />
          <p className="mt-3 text-sm font-medium">还没有决策记录</p>
          <p className="mt-1 text-xs text-muted-foreground">
            做完一组实验运行后，点右上角「记录新决策」写下你的观察与判断。
          </p>
        </div>
      ) : (
        (decisions ?? []).map((decision) => (
          <Card key={decision.id}>
            <CardHeader className="border-b border-border">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex flex-wrap items-center gap-2">
                  <CardTitle className="text-sm font-medium">{fmtTime(decision.createdAt)}</CardTitle>
                  {supportsBadge(decision.supportsHypothesis)}
                </div>
                <div className="flex shrink-0 gap-1">
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-7 gap-1 px-2 text-xs"
                    onClick={() => { setEditing(decision); setFormOpen(true) }}
                  >
                    <Pencil className="size-3.5" />
                    编辑
                  </Button>
                  <Button
                    size="sm"
                    variant={confirmingDelete === decision.id ? 'destructive' : 'ghost'}
                    className="h-7 gap-1 px-2 text-xs"
                    onClick={() => void handleDelete(decision.id)}
                  >
                    <Trash2 className="size-3.5" />
                    {confirmingDelete === decision.id ? '确认删除' : '删除'}
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              <p className="text-xs text-muted-foreground">
                依据运行记录：{decision.runIds.map((id) => `#${id}`).join('、')}
                <span className="ml-2">更新于 {fmtTime(decision.updatedAt)}</span>
              </p>
              <div>
                <p className="mb-1 text-xs font-medium text-muted-foreground">观察到的事实</p>
                <p className="text-sm leading-relaxed">{decision.observations}</p>
              </div>
              {decision.interpretation && (
                <div>
                  <p className="mb-1 text-xs font-medium text-muted-foreground">分析解释</p>
                  <p className="text-sm leading-relaxed text-muted-foreground">{decision.interpretation}</p>
                </div>
              )}
              {decision.unknowns && (
                <div>
                  <p className="mb-1 text-xs font-medium text-muted-foreground">未知因素 / 待验证问题</p>
                  <p className="text-sm leading-relaxed text-amber-700 dark:text-amber-400">{decision.unknowns}</p>
                </div>
              )}
              {decision.nextSuggestions.length > 0 && (
                <div>
                  <p className="mb-1.5 text-xs font-medium text-muted-foreground">下一步研究建议</p>
                  <ul className="flex flex-col gap-1.5">
                    {decision.nextSuggestions.map((s, index) => (
                      <li key={index} className="flex items-start gap-2 text-sm">
                        <ArrowRight className="mt-0.5 size-4 shrink-0 text-primary" />
                        {s}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>
        ))
      )}

      <DecisionFormSheet
        open={formOpen}
        onOpenChange={setFormOpen}
        experiments={experiments ?? []}
        decision={editing}
        defaultExperimentId={experimentId}
        onSaved={() => {
          void reloadDecisions()
          void reloadExperiments()
        }}
      />
    </div>
  )
}
