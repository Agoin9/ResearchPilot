import {
  AlertOctagon,
  AlertTriangle,
  Check,
  History,
  Loader2,
  RefreshCw,
  X,
} from 'lucide-react'
import { useCallback, useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { toast } from '@/components/ui/toast'
import { useAsyncData } from '@/hooks/useAsyncData'
import {
  adoptReplan,
  fetchProjectDetail,
  fetchReplans,
  generateReplan,
  rejectReplan,
} from '@/services/api'
import type { ReplanInfo, ReplanTaskSnapshot } from '@/types'

const STATUS_LABELS: Record<ReplanInfo['status'], string> = {
  pending: '待处理',
  adopted: '已采纳',
  rejected: '已放弃',
}

const STATUS_BADGE_CLASSES: Record<ReplanInfo['status'], string> = {
  pending: 'border-sky-300 bg-sky-50 text-sky-700 dark:border-sky-500/40 dark:bg-sky-500/10 dark:text-sky-400',
  adopted: 'border-emerald-300 bg-emerald-50 text-emerald-700 dark:border-emerald-500/40 dark:bg-emerald-500/10 dark:text-emerald-400',
  rejected: 'border-border bg-muted text-muted-foreground',
}

const PRIORITY_LABELS: Record<string, string> = { high: '高', medium: '中', low: '低' }

/** 重规划 Tab：风险预警列表 + 生成调整方案 + 原计划 vs 新计划对比 + 历史记录 */
export function ReplanTab({ projectId }: { projectId: number }) {
  const loadDetail = useCallback(() => fetchProjectDetail(projectId), [projectId])
  const { data, reload } = useAsyncData(loadDetail)
  const loadReplans = useCallback(() => fetchReplans(projectId), [projectId])
  const { data: history, reload: reloadHistory } = useAsyncData(loadReplans)
  const [generating, setGenerating] = useState(false)
  const [current, setCurrent] = useState<ReplanInfo | null>(null)
  const [processing, setProcessing] = useState(false)

  const riskyTasks = (data?.tasks ?? []).filter((task) => task.risk !== 'none')

  const handleGenerate = async () => {
    setGenerating(true)
    setCurrent(null)
    try {
      const replan = await generateReplan(projectId)
      setCurrent(replan)
      void reloadHistory()
      if (replan.source === 'demo') {
        toast.add({ title: '演示模式', description: '未配置 DeepSeek Key，使用本地规则模拟调整', type: 'info' })
      } else {
        toast.add({ title: '重规划方案已生成', description: '请对比新旧计划后决定是否采纳', type: 'success' })
      }
    } catch {
      // 错误提示已由 api 层统一 toast 展示
    } finally {
      setGenerating(false)
    }
  }

  const handleAdopt = async () => {
    if (!current) return
    setProcessing(true)
    try {
      const result = await adoptReplan(current.id)
      setCurrent(result.replan)
      toast.add({ title: '已采纳调整', description: `共调整 ${result.appliedCount} 个任务，看板已更新`, type: 'success' })
      void reload()
      void reloadHistory()
    } catch {
      // 错误提示已由 api 层统一 toast 展示
    } finally {
      setProcessing(false)
    }
  }

  const handleReject = async () => {
    if (!current) return
    setProcessing(true)
    try {
      const updated = await rejectReplan(current.id)
      setCurrent(updated)
      toast.add({ title: '已放弃该方案', description: '任务计划保持不变', type: 'info' })
      void reloadHistory()
    } catch {
      // 错误提示已由 api 层统一 toast 展示
    } finally {
      setProcessing(false)
    }
  }

  return (
    <div className="flex flex-col gap-4">
      {/* 风险预警 */}
      <Card>
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <div>
            <CardTitle className="text-base">风险预警</CardTitle>
            <CardDescription>本地规则引擎实时计算：逾期 / 前置阻塞 / 进度落后 / 剩余工时不足</CardDescription>
          </div>
          <Badge variant={riskyTasks.length > 0 ? 'destructive' : 'secondary'}>
            {riskyTasks.length} 个风险任务
          </Badge>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          {riskyTasks.length === 0 ? (
            <p className="py-3 text-center text-sm text-muted-foreground">
              当前所有任务都在计划内正常推进
            </p>
          ) : (
            riskyTasks.map((task) => (
              <div
                key={task.id}
                className={`flex items-start gap-2 rounded-lg border px-3 py-2 text-sm ${
                  task.risk === 'high'
                    ? 'border-red-200 bg-red-50 text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-400'
                    : 'border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-400'
                }`}
              >
                {task.risk === 'high' ? (
                  <AlertOctagon className="mt-0.5 size-4 shrink-0" />
                ) : (
                  <AlertTriangle className="mt-0.5 size-4 shrink-0" />
                )}
                <div className="min-w-0">
                  <p className="font-medium">{task.title}</p>
                  <p className="mt-0.5 text-xs opacity-90">{task.riskReason}</p>
                </div>
              </div>
            ))
          )}
          <div className="flex justify-end pt-2">
            <Button disabled={generating} onClick={() => void handleGenerate()}>
              {generating ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  正在生成重规划方案…
                </>
              ) : (
                <>
                  <RefreshCw className="size-4" />
                  重新规划
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 当前方案：对比 + 采纳/放弃 */}
      {current && current.status === 'pending' && (
        <ReplanView
          replan={current}
          processing={processing}
          onAdopt={() => void handleAdopt()}
          onReject={() => void handleReject()}
        />
      )}

      {/* 历史记录 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <History className="size-4" />
            重规划历史
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {!history || history.length === 0 ? (
            <p className="py-3 text-center text-sm text-muted-foreground">还没有重规划记录</p>
          ) : (
            history.map((replan) => (
              <div key={replan.id} className="rounded-xl border border-border p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-medium">
                    {replan.createdAt.slice(0, 16).replace('T', ' ')} · {replan.changes.length} 条调整
                  </p>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className={STATUS_BADGE_CLASSES[replan.status]}>
                      {STATUS_LABELS[replan.status]}
                    </Badge>
                    <Badge variant={replan.source === 'demo' ? 'secondary' : 'default'}>
                      {replan.source === 'demo' ? '演示模式' : 'DeepSeek'}
                    </Badge>
                  </div>
                </div>
                <p className="mt-1.5 text-xs text-muted-foreground line-clamp-2">
                  {replan.planContent}
                </p>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  )
}

/** 单个方案视图：文字说明 + 影响评估 + 原计划 vs 新计划对比表 + 操作按钮 */
function ReplanView({
  replan,
  processing,
  onAdopt,
  onReject,
}: {
  replan: ReplanInfo
  processing: boolean
  onAdopt: () => void
  onReject: () => void
}) {
  const changeByTask = new Map(replan.changes.map((c) => [c.taskId, c]))
  const hasChanges = replan.changes.length > 0

  return (
    <Card className="border-primary/40">
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <CardTitle className="text-base">重规划方案</CardTitle>
          <Badge variant={replan.source === 'demo' ? 'secondary' : 'default'}>
            {replan.source === 'demo' ? '演示模式' : 'DeepSeek 生成'}
          </Badge>
        </div>
        <CardDescription>{replan.planContent}</CardDescription>
        {replan.impactSummary && (
          <p className="rounded-lg bg-muted px-3 py-2 text-xs text-muted-foreground">
            影响评估：{replan.impactSummary}
          </p>
        )}
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <CompareTable tasks={replan.originalTasks} changeByTask={changeByTask} />

        {replan.changes.length > 0 && (
          <div>
            <p className="mb-1.5 text-xs font-medium text-muted-foreground">调整理由</p>
            <ul className="flex flex-col gap-1.5">
              {replan.changes.map((change) => (
                <li key={change.taskId} className="text-xs text-muted-foreground">
                  <span className="font-medium text-foreground">「{change.title}」：</span>
                  {change.reason || (change.action === 'reprioritize' ? '调整优先级' : '调整计划日期')}
                </li>
              ))}
            </ul>
          </div>
        )}

        {hasChanges && (
          <div className="flex justify-end gap-2 border-t border-border pt-3">
            <Button variant="outline" disabled={processing} onClick={onReject}>
              <X className="size-4" />
              放弃
            </Button>
            <Button disabled={processing} onClick={onAdopt}>
              {processing ? <Loader2 className="size-4 animate-spin" /> : <Check className="size-4" />}
              接受调整
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

const fmtDate = (iso: string | null) => (iso ? iso.slice(5).replace('-', '-') : '—')

/** 原计划 vs 新计划对比表：高亮改动内容 */
function CompareTable({
  tasks,
  changeByTask,
}: {
  tasks: ReplanTaskSnapshot[]
  changeByTask: Map<number, ReplanInfo['changes'][number]>
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border text-left text-xs text-muted-foreground">
            <th className="py-2 pr-3 font-medium">任务</th>
            <th className="py-2 pr-3 font-medium">计划日期</th>
            <th className="py-2 pr-3 font-medium">优先级</th>
            <th className="py-2 pr-3 font-medium">预计工时</th>
            <th className="py-2 font-medium">状态</th>
          </tr>
        </thead>
        <tbody>
          {tasks.map((task) => {
            const change = changeByTask.get(task.taskId)
            const newStart = change?.plannedStartDate ?? task.plannedStartDate
            const newEnd = change?.plannedEndDate ?? task.plannedEndDate
            const newPriority = change?.priority ?? task.priority
            const newHours = change?.estimatedHours ?? task.estimatedHours
            const dateChanged =
              newStart !== task.plannedStartDate || newEnd !== task.plannedEndDate
            const priorityChanged = newPriority !== task.priority
            const hoursChanged = newHours !== task.estimatedHours
            const isChanged = Boolean(change)

            return (
              <tr
                key={task.taskId}
                className={`border-b border-border/60 ${isChanged ? 'bg-primary/5' : ''}`}
              >
                <td className="py-2 pr-3">
                  <span className="min-w-0 break-words">
                    {task.title}
                    {isChanged && (
                      <Badge variant="outline" className="ml-1.5 border-primary/40 text-primary">
                        调整
                      </Badge>
                    )}
                  </span>
                </td>
                <td className="py-2 pr-3 tabular-nums">
                  {dateChanged ? (
                    <span>
                      <span className="text-muted-foreground line-through">
                        {fmtDate(task.plannedStartDate)}~{fmtDate(task.plannedEndDate)}
                      </span>
                      <span className="ml-1.5 font-medium text-primary">
                        → {fmtDate(newStart)}~{fmtDate(newEnd)}
                      </span>
                    </span>
                  ) : (
                    <span className="text-muted-foreground">
                      {fmtDate(task.plannedStartDate)}~{fmtDate(task.plannedEndDate)}
                    </span>
                  )}
                </td>
                <td className="py-2 pr-3">
                  {priorityChanged ? (
                    <span>
                      <span className="text-muted-foreground line-through">
                        {PRIORITY_LABELS[task.priority]}
                      </span>
                      <span className="ml-1.5 font-medium text-primary">
                        → {PRIORITY_LABELS[newPriority]}
                      </span>
                    </span>
                  ) : (
                    <span className="text-muted-foreground">{PRIORITY_LABELS[task.priority]}</span>
                  )}
                </td>
                <td className="py-2 pr-3 tabular-nums">
                  {hoursChanged ? (
                    <span>
                      <span className="text-muted-foreground line-through">
                        {task.estimatedHours ?? '—'}
                      </span>
                      <span className="ml-1.5 font-medium text-primary">→ {newHours}</span>
                    </span>
                  ) : (
                    <span className="text-muted-foreground">{task.estimatedHours ?? '—'}</span>
                  )}
                </td>
                <td className="py-2">
                  <span className="text-muted-foreground">
                    {task.status === 'done' ? '已完成' : task.status === 'doing' ? `进行中 ${task.progress}%` : '待开始'}
                  </span>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
