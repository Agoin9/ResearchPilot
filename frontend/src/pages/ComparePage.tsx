import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from 'recharts'
import { BarChart3, FlaskConical, Table2 } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { EmptyState } from '@/components/common/EmptyState'
import { ErrorState } from '@/components/common/ErrorState'
import { NativeSelect } from '@/components/ui/native-select'
import {
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from '@/components/ui/chart'
import { useAsyncData } from '@/hooks/useAsyncData'
import { fetchExperiments, fetchMetricsOverview, fetchProjects } from '@/services/api'
import type { Experiment, ExperimentStatus } from '@/types'

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

/**
 * 分类色板（已通过 validate_palette.js 明/暗双模式验证）：
 * 固定顺序分配，颜色跟随实验实体而非选择顺序——筛选变化不会重涂幸存系列。
 */
const SERIES_COLORS = {
  light: ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#6250d6', '#e34948'],
  dark: ['#3987e5', '#d95926', '#199e70', '#c98500', '#d55181', '#008300', '#9085e9', '#e66767'],
}
const MAX_SERIES = 8

function buildChartConfig(experiments: Experiment[]): ChartConfig {
  const config: ChartConfig = {}
  // 按实验 id 稳定排序后分配色槽：颜色跟随实体，不随勾选顺序变化
  const ordered = [...experiments].sort((a, b) => a.id - b.id)
  ordered.forEach((e, index) => {
    if (index >= MAX_SERIES) return
    const key = `exp${e.id}`
    config[key] = {
      label: e.title.length > 24 ? `${e.title.slice(0, 24)}…` : e.title,
      theme: {
        light: SERIES_COLORS.light[index],
        dark: SERIES_COLORS.dark[index],
      },
    }
  })
  return config
}

/**
 * 实验结果比较：勾选多个实验，对同一指标做可视化对比。
 * 数据全部来自数据库真实运行记录（/projects/{id}/metrics 本地聚合），
 * 系统不生成任何假数据。每个指标一张图（小倍数），另有数据表视图。
 */
export default function ComparePage() {
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
  const loadOverview = useCallback(
    () => (selectedId !== null ? fetchMetricsOverview(selectedId) : Promise.resolve({ metrics: [] })),
    [selectedId]
  )
  const { data: experiments, loading: loadingExperiments, error: experimentsError, reload: reloadExperiments } =
    useAsyncData(loadExperiments)
  const { data: overview, loading: loadingOverview, error: overviewError, reload: reloadOverview } =
    useAsyncData(loadOverview)

  const [selectedExpIds, setSelectedExpIds] = useState<number[]>([])
  const [showTable, setShowTable] = useState(false)

  // 项目切换时重置勾选
  useEffect(() => {
    setSelectedExpIds([])
    setShowTable(false)
  }, [selectedId])

  if (loadingProjects) {
    return <p className="py-10 text-center text-sm text-muted-foreground">加载项目中…</p>
  }
  if (projectError) {
    return <ErrorState message={projectError} onRetry={() => window.location.reload()} />
  }
  if (!projects || projects.length === 0) {
    return (
      <EmptyState
        icon={BarChart3}
        title="还没有科研项目"
        description="先创建项目并录入实验运行记录，再来对比结果。"
        actionLabel="新建项目"
        onAction={() => navigate('/projects/new')}
      />
    )
  }

  const expList = experiments ?? []
  const hasRuns = expList.some((e) => e.runCount > 0)
  const selectedExperiments = expList.filter((e) => selectedExpIds.includes(e.id))
  const chartConfig = buildChartConfig(expList)
  // 色槽按实验 id 稳定分配：id 排序超出 8 个的实验无法入图
  const slottedIds = new Set(
    [...expList]
      .sort((a, b) => a.id - b.id)
      .slice(0, MAX_SERIES)
      .map((e) => e.id)
  )

  const toggleExperiment = (id: number) => {
    setSelectedExpIds((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id)
      if (prev.length >= MAX_SERIES) return prev
      return [...prev, id]
    })
  }

  // 每个指标：按实验 × 运行号聚合为图表行
  const metrics = (overview?.metrics ?? []).map((metric) => {
    const byExp = new Map<number, Map<number, number>>()
    for (const point of metric.points) {
      if (!selectedExpIds.includes(point.experimentId)) continue
      if (!byExp.has(point.experimentId)) byExp.set(point.experimentId, new Map())
      byExp.get(point.experimentId)!.set(point.runNo, point.value)
    }
    const maxRun = Math.max(1, ...[...byExp.values()].flatMap((m) => [...m.keys()]))
    const rows: Record<string, number | string>[] = []
    for (let runNo = 1; runNo <= maxRun; runNo++) {
      const row: Record<string, number | string> = { runNo: `运行 ${runNo}` }
      for (const expId of selectedExpIds) {
        const value = byExp.get(expId)?.get(runNo)
        if (value !== undefined) row[`exp${expId}`] = value
      }
      rows.push(row)
    }
    return { ...metric, rows, maxRun }
  })

  // 数据表视图：实验 × 运行 × 指标值
  const tableMetrics = (overview?.metrics ?? []).filter((m) =>
    m.points.some((p) => selectedExpIds.includes(p.experimentId))
  )

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <BarChart3 className="size-5 text-muted-foreground" />
          <NativeSelect
            value={selectedId !== null ? String(selectedId) : ''}
            onChange={(value) => value && setSelectedId(Number(value))}
            items={projects.map((p) => ({ value: String(p.id), label: p.name }))}
            placeholder="选择项目"
            className="w-64"
          />
        </div>
        <Button
          variant="outline"
          size="sm"
          disabled={selectedExperiments.length === 0}
          onClick={() => setShowTable((v) => !v)}
        >
          <Table2 className="size-3.5" />
          {showTable ? '图表视图' : '数据表视图'}
        </Button>
      </div>

      {loadingExperiments || loadingOverview ? (
        <p className="py-10 text-center text-sm text-muted-foreground">加载实验与结果数据中…</p>
      ) : experimentsError || overviewError ? (
        <ErrorState
          message={experimentsError ?? overviewError ?? '加载失败'}
          onRetry={() => {
            void reloadExperiments()
            void reloadOverview()
          }}
        />
      ) : expList.length === 0 ? (
        <EmptyState
          icon={FlaskConical}
          title="还没有实验"
          description="到实验工作台创建实验并录入运行记录后，这里才能对比结果。"
          actionLabel="去实验工作台"
          onAction={() => navigate('/lab', { state: { projectId: selectedId } })}
        />
      ) : (
        <>
          {/* 实验选择 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">选择要对比的实验（{selectedExpIds.length}/{MAX_SERIES}）</CardTitle>
              <CardDescription>
                只有录入过运行记录的实验才有数据点；同一指标按「第 N 次运行」对齐比较
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-2">
              {expList.map((e) => (
                <button
                  key={e.id}
                  type="button"
                  disabled={e.runCount === 0 || !slottedIds.has(e.id)}
                  onClick={() => toggleExperiment(e.id)}
                  title={!slottedIds.has(e.id) ? '单次最多对比 8 个实验（超出色板槽位）' : undefined}
                  className={`flex items-center gap-2 rounded-lg border px-3 py-1.5 text-sm transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${
                    selectedExpIds.includes(e.id)
                      ? 'border-primary bg-primary/10 text-primary'
                      : 'border-border bg-background hover:border-primary/40'
                  }`}
                >
                  <input
                    type="checkbox"
                    className="size-3.5"
                    checked={selectedExpIds.includes(e.id)}
                    readOnly
                  />
                  {e.title.slice(0, 18)}
                  <Badge variant="outline" className={STATUS_BADGE_CLASSES[e.status]}>
                    {STATUS_LABELS[e.status]}
                  </Badge>
                  <span className="text-xs text-muted-foreground">{e.runCount} 次</span>
                </button>
              ))}
              {!hasRuns && (
                <p className="w-full text-xs text-muted-foreground">
                  所有实验都还没有运行记录——对比图表需要真实数据，先去录入。
                </p>
              )}
            </CardContent>
          </Card>

          {/* 数据表视图 */}
          {showTable && selectedExperiments.length > 0 ? (
            <Card>
              <CardHeader className="border-b border-border">
                <CardTitle className="text-base">结果数据表（真实记录）</CardTitle>
                <CardDescription>行 = 实验 × 运行，列 = 指标</CardDescription>
              </CardHeader>
              <CardContent className="overflow-x-auto pt-4">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-left text-xs text-muted-foreground">
                      <th className="py-2 pr-3 font-medium">实验</th>
                      <th className="py-2 pr-3 font-medium">运行</th>
                      {tableMetrics.map((m) => (
                        <th key={m.name} className="py-2 pr-3 font-medium">
                          {m.name}{m.unit ? `（${m.unit}）` : ''}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {selectedExperiments.flatMap((exp) => {
                      const runNos = new Set(
                        tableMetrics.flatMap((m) =>
                          m.points
                            .filter((p) => p.experimentId === exp.id)
                            .map((p) => p.runNo)
                        )
                      )
                      return [...runNos].sort((a, b) => a - b).map((runNo) => (
                        <tr key={`${exp.id}-${runNo}`} className="border-b border-border/50">
                          <td className="py-1.5 pr-3">{exp.title}</td>
                          <td className="py-1.5 pr-3 tabular-nums">#{runNo}</td>
                          {tableMetrics.map((m) => {
                            const point = m.points.find(
                              (p) => p.experimentId === exp.id && p.runNo === runNo
                            )
                            return (
                              <td key={m.name} className="py-1.5 pr-3 tabular-nums">
                                {point ? point.value : '—'}
                              </td>
                            )
                          })}
                        </tr>
                      ))
                    })}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          ) : (
            <>
              {/* 提示 */}
              {selectedExperiments.length === 0 && (
                <p className="rounded-xl border border-dashed border-border py-6 text-center text-sm text-muted-foreground">
                  勾选至少 2 个实验开始对比（勾 1 个也可以单独查看它的运行趋势）。
                </p>
              )}

              {/* 每个指标一张图（小倍数；绝不使用双轴） */}
              {selectedExperiments.length > 0 &&
                metrics.map((metric) => (
                  <Card key={metric.name}>
                    <CardHeader className="border-b border-border">
                      <div className="flex flex-wrap items-baseline justify-between gap-2">
                        <CardTitle className="text-base">
                          {metric.name}
                          {metric.unit && (
                            <span className="ml-1.5 text-xs font-normal text-muted-foreground">
                              （{metric.unit}）
                            </span>
                          )}
                        </CardTitle>
                        <span className="text-xs text-muted-foreground">
                          {metric.higherIsBetter ? '越高越好' : '越低越好'}
                        </span>
                      </div>
                    </CardHeader>
                    <CardContent className="pt-4">
                      <ChartContainer
                        config={chartConfig}
                        className="h-64 w-full"
                        initialDimension={{ width: 640, height: 256 }}
                      >
                        <BarChart data={metric.rows} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                          <CartesianGrid vertical={false} strokeDasharray="4 4" />
                          <XAxis
                            dataKey="runNo"
                            tickLine={false}
                            axisLine={false}
                            tickMargin={8}
                            fontSize={12}
                          />
                          <YAxis tickLine={false} axisLine={false} tickMargin={4} fontSize={12} />
                          <ChartTooltip
                            cursor={{ fill: 'var(--muted)', opacity: 0.35 }}
                            content={<ChartTooltipContent />}
                          />
                          <ChartLegend content={<ChartLegendContent />} />
                          {selectedExpIds.map((expId) => (
                            <Bar
                              key={expId}
                              dataKey={`exp${expId}`}
                              fill={`var(--color-exp${expId})`}
                              radius={[4, 4, 0, 0]}
                              maxBarSize={36}
                            />
                          ))}
                        </BarChart>
                      </ChartContainer>
                      <p className="mt-2 text-xs text-muted-foreground">
                        数据点来自 {metric.rows.length} 组运行记录；悬浮柱子可查看精确数值。
                      </p>
                    </CardContent>
                  </Card>
                ))}
            </>
          )}
        </>
      )}
    </div>
  )
}
