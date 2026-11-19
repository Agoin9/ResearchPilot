import {
  ArrowRight,
  BookOpenCheck,
  CalendarDays,
  FlaskConical,
  HelpCircle,
  Lightbulb,
  ListTodo,
} from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { EmptyState } from '@/components/common/EmptyState'
import { ErrorState } from '@/components/common/ErrorState'
import { NativeSelect } from '@/components/ui/native-select'
import { useAsyncData } from '@/hooks/useAsyncData'
import {
  fetchCards,
  fetchDocuments,
  fetchExperiments,
  fetchProjectDecisions,
  fetchProjectDetail,
  fetchProjects,
  fetchQuestions,
} from '@/services/api'
import type { ExperimentStatus } from '@/types'

const EXPERIMENT_STATUS_LABELS: Record<ExperimentStatus, string> = {
  draft: '设计中',
  running: '进行中',
  done: '已完成',
  failed: '失败',
  paused: '已暂停',
}

const EXPERIMENT_STATUS_BADGE_CLASSES: Record<ExperimentStatus, string> = {
  draft: 'border-border bg-muted text-muted-foreground',
  running: 'border-sky-300 bg-sky-50 text-sky-700 dark:border-sky-500/40 dark:bg-sky-500/10 dark:text-sky-400',
  done: 'border-emerald-300 bg-emerald-50 text-emerald-700 dark:border-emerald-500/40 dark:bg-emerald-500/10 dark:text-emerald-400',
  failed: 'border-red-300 bg-red-50 text-red-600 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-400',
  paused: 'border-amber-300 bg-amber-50 text-amber-700 dark:border-amber-500/40 dark:bg-amber-500/10 dark:text-amber-400',
}

const fmtDate = (iso: string | null) => {
  if (!iso) return ''
  const [, month, day] = iso.split('-')
  return `${month}-${day}`
}

/**
 * 科研驾驶舱：把一个项目当前"研究到哪了"聚合成一屏。
 * 全部数据来自真实后端接口（问题/文献/实验/决策/任务），前端仅做聚合展示。
 */
export default function CockpitPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { data: projects, loading: loadingProjects, error: projectError } = useAsyncData(fetchProjects)
  const [selectedId, setSelectedId] = useState<number | null>(null)

  const paramId = searchParams.get('project') ? Number(searchParams.get('project')) : null
  useEffect(() => {
    if (!projects || projects.length === 0) {
      setSelectedId(null)
      return
    }
    const found =
      projects.find((p) => p.id === paramId) ??
      projects.find((p) => p.status === 'active') ??
      projects[0]
    setSelectedId(found.id)
  }, [projects, paramId])

  const loadQuestions = useCallback(
    () => (selectedId !== null ? fetchQuestions(selectedId) : Promise.resolve([])),
    [selectedId]
  )
  const loadDocuments = useCallback(
    () => (selectedId !== null ? fetchDocuments(selectedId) : Promise.resolve([])),
    [selectedId]
  )
  const loadCards = useCallback(
    () => (selectedId !== null ? fetchCards(selectedId) : Promise.resolve([])),
    [selectedId]
  )
  const loadExperiments = useCallback(
    () => (selectedId !== null ? fetchExperiments(selectedId) : Promise.resolve([])),
    [selectedId]
  )
  const loadDecisions = useCallback(
    () => (selectedId !== null ? fetchProjectDecisions(selectedId) : Promise.resolve([])),
    [selectedId]
  )
  const loadDetail = useCallback(
    () => (selectedId !== null ? fetchProjectDetail(selectedId) : Promise.resolve(null)),
    [selectedId]
  )
  const { data: questions } = useAsyncData(loadQuestions)
  const { data: documents } = useAsyncData(loadDocuments)
  const { data: cards } = useAsyncData(loadCards)
  const { data: experiments } = useAsyncData(loadExperiments)
  const { data: decisions } = useAsyncData(loadDecisions)
  const { data: detail, loading: loadingDetail, error: detailError, reload: reloadDetail } =
    useAsyncData(loadDetail)

  if (loadingProjects) {
    return <p className="py-10 text-center text-sm text-muted-foreground">加载项目中…</p>
  }
  if (projectError || !projects || projects.length === 0) {
    return (
      <EmptyState
        icon={FlaskConical}
        title="还没有科研项目"
        description="先创建一个科研项目，驾驶舱会聚合该项目的科研进展。"
        actionLabel="新建项目"
        onAction={() => navigate('/projects/new')}
      />
    )
  }

  const selected = projects.find((p) => p.id === selectedId) ?? null
  const openQuestions = (questions ?? []).filter((q) => q.status === 'open')
  const hypotheses = [
    ...(questions ?? [])
      .filter((q) => q.hypothesis && q.status === 'open')
      .map((q) => ({ kind: '问题假设' as const, title: q.hypothesis as string, source: q.content })),
    ...(experiments ?? [])
      .filter((e) => e.hypothesis && (e.status === 'running' || e.status === 'draft'))
      .map((e) => ({ kind: '实验假设' as const, title: e.hypothesis as string, source: e.title })),
  ]
  const recentExperiments = [...(experiments ?? [])]
    .sort((a, b) => {
      const ta = a.lastRunAt ?? a.updatedAt
      const tb = b.lastRunAt ?? b.updatedAt
      return tb.localeCompare(ta)
    })
    .slice(0, 5)
  const recentDecisions = (decisions ?? []).slice(0, 3)
  const nextSuggestions = (decisions ?? []).flatMap((d) => d.nextSuggestions).slice(0, 5)
  const upcomingTasks = (detail?.tasks ?? [])
    .filter((t) => t.status !== 'done' && t.plannedStartDate)
    .sort((a, b) => (a.plannedStartDate ?? '').localeCompare(b.plannedStartDate ?? ''))
    .slice(0, 5)
  const docCount = documents?.length ?? 0
  const cardCount = cards?.length ?? 0
  const readingPercent = docCount > 0 ? Math.round((cardCount / docCount) * 100) : 0

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-5">
      {/* 顶部：项目选择 + 引导 */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <NativeSelect
            value={selectedId !== null ? String(selectedId) : ''}
            onChange={(value) => value && setSelectedId(Number(value))}
            items={projects.map((p) => ({ value: String(p.id), label: p.name }))}
            placeholder="选择项目"
            className="w-64"
          />
          {selected && (
            <Badge variant="secondary">
              截止 {selected.deadline} · 剩 {selected.daysLeft} 天
            </Badge>
          )}
        </div>
        <p className="text-xs text-muted-foreground">
          一屏看清：当前问题 → 文献证据 → 实验进展 → 重要发现 → 下一步
        </p>
      </div>

      {loadingDetail ? (
        <p className="py-10 text-center text-sm text-muted-foreground">聚合科研数据中…</p>
      ) : detailError ? (
        <ErrorState message={detailError} onRetry={() => void reloadDetail()} />
      ) : (
        <>
          {/* 第一行：研究问题 + 待验证假设 */}
          <div className="grid grid-cols-1 items-start gap-5 lg:grid-cols-2">
            <Card>
              <CardHeader className="flex-row items-center justify-between space-y-0">
                <div>
                  <CardTitle className="text-base">当前研究问题</CardTitle>
                  <CardDescription>每个问题聚合了它的证据与实验</CardDescription>
                </div>
                <Button size="sm" variant="outline" onClick={() => navigate(`/projects/${selectedId}`)}>
                  去管理
                </Button>
              </CardHeader>
              <CardContent className="flex flex-col gap-3">
                {!openQuestions.length ? (
                  <p className="rounded-xl border border-dashed border-border py-6 text-center text-xs text-muted-foreground">
                    暂无待解决的研究问题。到「研究问题」里写下你当前要回答的问题。
                  </p>
                ) : (
                  openQuestions.slice(0, 4).map((q) => (
                    <div key={q.id} className="rounded-lg border border-border p-3">
                      <p className="flex items-start gap-2 text-sm">
                        <HelpCircle className="mt-0.5 size-4 shrink-0 text-primary" />
                        {q.content}
                      </p>
                      <div className="mt-2 flex flex-wrap gap-2">
                        <Badge variant="outline" className="border-emerald-300 bg-emerald-50 text-emerald-700 dark:border-emerald-500/40 dark:bg-emerald-500/10 dark:text-emerald-400">
                          支持 {q.evidenceSupport}
                        </Badge>
                        <Badge variant="outline" className="border-red-300 bg-red-50 text-red-600 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-400">
                          反对 {q.evidenceAgainst}
                        </Badge>
                        <Badge variant="outline" className="border-border bg-muted text-muted-foreground">
                          参考 {q.evidenceNeutral}
                        </Badge>
                        <Badge variant="outline" className="border-sky-300 bg-sky-50 text-sky-700 dark:border-sky-500/40 dark:bg-sky-500/10 dark:text-sky-400">
                          实验 {q.experimentsCount}
                        </Badge>
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">待验证假设</CardTitle>
                <CardDescription>来自研究问题与进行中的实验</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col gap-3">
                {hypotheses.length === 0 ? (
                  <p className="rounded-xl border border-dashed border-border py-6 text-center text-xs text-muted-foreground">
                    还没有待验证假设。在问题或实验中写下假设，这里会自动出现。
                  </p>
                ) : (
                  hypotheses.slice(0, 5).map((h, index) => (
                    <div key={index} className="rounded-lg border border-border p-3">
                      <p className="text-sm">{h.title}</p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {h.kind} · 来源：{h.source.slice(0, 40)}
                      </p>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>

          {/* 第二行：文献进度 + 近期实验 */}
          <div className="grid grid-cols-1 items-start gap-5 lg:grid-cols-2">
            <Card>
              <CardHeader className="flex-row items-center justify-between space-y-0">
                <div>
                  <CardTitle className="text-base">文献阅读进度</CardTitle>
                  <CardDescription>已上传文献 → 结构化研究卡片</CardDescription>
                </div>
                <Button size="sm" variant="outline" onClick={() => navigate('/library', { state: { projectId: selectedId } })}>
                  去文献库
                </Button>
              </CardHeader>
              <CardContent className="flex flex-col gap-3">
                <div className="flex items-center gap-4">
                  <BookOpenCheck className="size-9 shrink-0 text-primary" />
                  <div className="flex-1">
                    <div className="flex items-baseline justify-between text-sm">
                      <span className="font-medium">
                        {cardCount} / {docCount} 篇已生成研究卡片
                      </span>
                      <span className="tabular-nums text-muted-foreground">{readingPercent}%</span>
                    </div>
                    <div className="mt-2 h-2 overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full rounded-full bg-primary transition-all"
                        style={{ width: `${readingPercent}%` }}
                      />
                    </div>
                  </div>
                </div>
                {docCount === 0 && (
                  <p className="text-xs text-muted-foreground">
                    还没有上传文献。上传 PDF 后可一键生成结构化卡片（研究问题、方法、数据集、指标、创新点、局限）。
                  </p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex-row items-center justify-between space-y-0">
                <div>
                  <CardTitle className="text-base">近期实验</CardTitle>
                  <CardDescription>按最近运行时间排序</CardDescription>
                </div>
                <Button size="sm" variant="outline" onClick={() => navigate('/lab', { state: { projectId: selectedId } })}>
                  去实验台
                </Button>
              </CardHeader>
              <CardContent className="flex flex-col gap-2">
                {recentExperiments.length === 0 ? (
                  <p className="rounded-xl border border-dashed border-border py-6 text-center text-xs text-muted-foreground">
                    还没有实验。围绕待验证假设设计第一个实验吧。
                  </p>
                ) : (
                  recentExperiments.map((e) => (
                    <div key={e.id} className="flex items-center justify-between gap-2 rounded-lg border border-border p-3">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium">{e.title}</p>
                        <p className="mt-0.5 text-xs text-muted-foreground">
                          {e.runCount} 次运行
                          {e.lastRunAt && <> · 最近 {e.lastRunAt.slice(0, 16).replace('T', ' ')}</>}
                        </p>
                      </div>
                      <Badge variant="outline" className={EXPERIMENT_STATUS_BADGE_CLASSES[e.status]}>
                        {EXPERIMENT_STATUS_LABELS[e.status]}
                      </Badge>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>

          {/* 第三行：重要发现 + 下一步计划 */}
          <div className="grid grid-cols-1 items-start gap-5 lg:grid-cols-2">
            <Card>
              <CardHeader className="flex-row items-center justify-between space-y-0">
                <div>
                  <CardTitle className="text-base">重要发现</CardTitle>
                  <CardDescription>来自科研决策日志（研究者本人判断）</CardDescription>
                </div>
                <Button size="sm" variant="outline" onClick={() => navigate('/decisions', { state: { projectId: selectedId } })}>
                  去决策日志
                </Button>
              </CardHeader>
              <CardContent className="flex flex-col gap-3">
                {recentDecisions.length === 0 ? (
                  <p className="rounded-xl border border-dashed border-border py-6 text-center text-xs text-muted-foreground">
                    还没有决策记录。实验有结果后，在「决策日志」里记下你的观察与判断。
                  </p>
                ) : (
                  recentDecisions.map((d) => (
                    <div key={d.id} className="rounded-lg border border-border p-3">
                      <div className="flex items-center gap-2">
                        <Lightbulb className="size-4 shrink-0 text-amber-500" />
                        <p className="min-w-0 flex-1 truncate text-sm font-medium">
                          {d.observations.slice(0, 60)}
                        </p>
                        <Badge
                          variant="outline"
                          className={
                            d.supportsHypothesis === true
                              ? 'border-emerald-300 bg-emerald-50 text-emerald-700 dark:border-emerald-500/40 dark:bg-emerald-500/10 dark:text-emerald-400'
                              : d.supportsHypothesis === false
                                ? 'border-red-300 bg-red-50 text-red-600 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-400'
                                : 'border-border bg-muted text-muted-foreground'
                          }
                        >
                          {d.supportsHypothesis === true ? '支持假设' : d.supportsHypothesis === false ? '否定假设' : '待定'}
                        </Badge>
                      </div>
                      {d.interpretation && (
                        <p className="mt-1.5 line-clamp-2 text-xs text-muted-foreground">{d.interpretation}</p>
                      )}
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">下一步计划</CardTitle>
                <CardDescription>决策建议 + 即将开始的科研任务</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col gap-2">
                {nextSuggestions.length === 0 && upcomingTasks.length === 0 ? (
                  <p className="rounded-xl border border-dashed border-border py-6 text-center text-xs text-muted-foreground">
                    暂无计划。在决策日志中写下下一步建议，或在看板安排任务。
                  </p>
                ) : (
                  <>
                    {nextSuggestions.map((s, index) => (
                      <div key={`s-${index}`} className="flex items-start gap-2 rounded-lg border border-border p-3">
                        <ArrowRight className="mt-0.5 size-4 shrink-0 text-primary" />
                        <p className="text-sm">{s}</p>
                      </div>
                    ))}
                    {upcomingTasks.map((t) => (
                      <div key={`t-${t.id}`} className="flex items-center justify-between gap-2 rounded-lg border border-border p-3">
                        <div className="flex min-w-0 items-center gap-2">
                          <ListTodo className="size-4 shrink-0 text-muted-foreground" />
                          <p className="truncate text-sm">{t.title}</p>
                        </div>
                        {t.plannedStartDate && (
                          <span className="flex shrink-0 items-center gap-1 text-xs text-muted-foreground">
                            <CalendarDays className="size-3.5" />
                            {fmtDate(t.plannedStartDate)} 起
                          </span>
                        )}
                      </div>
                    ))}
                  </>
                )}
              </CardContent>
            </Card>
          </div>

          {/* 空数据总引导 */}
          {!openQuestions.length && !hypotheses.length && !docCount && !recentExperiments.length && !recentDecisions.length && (
            <div className="rounded-xl border border-dashed border-border p-6 text-center">
              <p className="text-sm font-medium">这个项目还没有科研数据</p>
              <p className="mt-1 text-xs text-muted-foreground">
                建议从一条研究问题开始：问题 → 文献证据 → 实验 → 结果 → 决策，驾驶舱会逐步充实起来。
              </p>
              <Button size="sm" className="mt-3" onClick={() => navigate(`/projects/${selectedId}`)}>
                去项目仪表盘开始
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
