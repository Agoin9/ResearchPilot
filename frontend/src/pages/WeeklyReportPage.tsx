import {
  CheckCircle2,
  ClipboardCheck,
  Clock3,
  Copy,
  FileText,
  ListChecks,
  Loader2,
  Sparkles,
} from 'lucide-react'
import { useState } from 'react'
import { ErrorState } from '@/components/common/ErrorState'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { toast } from '@/components/ui/toast'
import { useAsyncData } from '@/hooks/useAsyncData'
import { fetchWeeklyReport, generateWeeklyReport } from '@/services/api'
import type { AiWeeklyReport } from '@/types'

const formatDate = (iso: string) => {
  const [, month, day] = iso.split('-')
  return `${month}-${day}`
}

/** 周报生成：近 7 天科研活动聚合 + AI 生成周报正文 */
export default function WeeklyReportPage() {
  const { data, loading, error, reload } = useAsyncData(fetchWeeklyReport)
  const [generating, setGenerating] = useState(false)
  const [report, setReport] = useState<AiWeeklyReport | null>(null)

  const handleGenerate = async () => {
    setGenerating(true)
    try {
      const result = await generateWeeklyReport()
      setReport(result)
      if (result.source === 'demo') {
        toast.add({
          title: '演示模式',
          description: '未配置 DeepSeek API Key，返回模板周报',
          type: 'info',
        })
      } else {
        toast.add({ title: '周报生成成功', type: 'success' })
      }
    } catch {
      // 错误提示已由 api 层统一 toast 展示
    } finally {
      setGenerating(false)
    }
  }

  const handleCopy = async () => {
    if (!report) return
    try {
      await navigator.clipboard.writeText(report.content)
      toast.add({ title: '已复制到剪贴板', type: 'success' })
    } catch {
      toast.add({ title: '复制失败，请手动选择文本复制', type: 'warning' })
    }
  }

  if (loading) {
    return <p className="py-10 text-center text-sm text-muted-foreground">加载本周数据中…</p>
  }
  if (error) {
    return <ErrorState message={error} onRetry={() => void reload()} />
  }

  const stats = data?.stats
  const hasActivity = (stats?.tasksCompleted ?? 0) + (stats?.progressUpdates ?? 0) > 0

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-heading text-xl font-semibold">周报生成</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            统计周期：{data ? `${data.weekStart} ~ ${data.weekEnd}` : '—'}（近 7 天）
          </p>
        </div>
        <Button disabled={generating} onClick={() => void handleGenerate()}>
          {generating ? (
            <>
              <Loader2 className="size-4 animate-spin" />
              正在生成周报…
            </>
          ) : (
            <>
              <Sparkles className="size-4" />
              生成 AI 周报
            </>
          )}
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="flex items-center gap-4">
            <div className="flex size-11 shrink-0 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
              <CheckCircle2 className="size-5" />
            </div>
            <div className="min-w-0">
              <div className="text-sm text-muted-foreground">本周完成任务</div>
              <div className="mt-0.5 text-2xl font-semibold tabular-nums">
                {stats?.tasksCompleted ?? 0}
                <span className="ml-1 text-sm font-normal text-muted-foreground">个</span>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4">
            <div className="flex size-11 shrink-0 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-600 dark:text-indigo-400">
              <Clock3 className="size-5" />
            </div>
            <div className="min-w-0">
              <div className="text-sm text-muted-foreground">本周投入时间</div>
              <div className="mt-0.5 text-2xl font-semibold tabular-nums">
                {(stats?.hoursSpent ?? 0).toFixed(1)}
                <span className="ml-1 text-sm font-normal text-muted-foreground">小时</span>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4">
            <div className="flex size-11 shrink-0 items-center justify-center rounded-lg bg-sky-500/10 text-sky-600 dark:text-sky-400">
              <ListChecks className="size-5" />
            </div>
            <div className="min-w-0">
              <div className="text-sm text-muted-foreground">进度更新</div>
              <div className="mt-0.5 text-2xl font-semibold tabular-nums">
                {stats?.progressUpdates ?? 0}
                <span className="ml-1 text-sm font-normal text-muted-foreground">条</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {!hasActivity && !report && (
        <Card>
          <CardContent className="flex flex-col items-center gap-2 py-10 text-center">
            <FileText className="size-8 text-muted-foreground" />
            <p className="text-sm font-medium">本周还没有科研记录</p>
            <p className="text-xs text-muted-foreground">
              去任务看板完成任务或更新进度后，这里会自动汇总
            </p>
          </CardContent>
        </Card>
      )}

      {(data?.projects ?? []).map((project) => (
        <Card key={project.projectId}>
          <CardHeader>
            <CardTitle className="text-base">{project.projectName}</CardTitle>
            <CardDescription>
              完成 {project.completedTasks.length} 个任务 · 更新 {project.progressRecords.length} 次进度
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            {project.completedTasks.length > 0 && (
              <div>
                <p className="mb-1.5 text-xs font-medium text-muted-foreground">完成任务</p>
                <ul className="flex flex-col gap-1">
                  {project.completedTasks.map((task) => (
                    <li key={task.id} className="flex items-center gap-2 text-sm">
                      <CheckCircle2 className="size-4 shrink-0 text-emerald-500" />
                      <span className="min-w-0 truncate">{task.title}</span>
                      <span className="ml-auto shrink-0 text-xs text-muted-foreground">
                        {formatDate(task.completedAt)}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {project.progressRecords.length > 0 && (
              <div>
                <p className="mb-1.5 text-xs font-medium text-muted-foreground">进度更新</p>
                <ul className="flex flex-col gap-1.5">
                  {project.progressRecords.map((record, index) => (
                    <li key={index} className="flex items-start gap-2 text-sm">
                      <ClipboardCheck className="mt-0.5 size-4 shrink-0 text-sky-500" />
                      <div className="min-w-0">
                        <p className="truncate">
                          {record.taskTitle}
                          <span className="ml-1.5 text-xs text-muted-foreground">
                            推进至 {record.progress}%
                            {record.hoursSpent != null && ` · ${record.hoursSpent}h`}
                          </span>
                        </p>
                        {record.note && (
                          <p className="text-xs text-muted-foreground">{record.note}</p>
                        )}
                      </div>
                      <span className="ml-auto shrink-0 text-xs text-muted-foreground">
                        {formatDate(record.createdAt)}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      ))}

      {report && (
        <Card>
          <CardHeader className="flex-row items-start justify-between space-y-0">
            <div>
              <CardTitle>AI 周报</CardTitle>
              <CardDescription>
                {report.source === 'demo' ? '模板生成（未配置 DeepSeek Key）' : 'DeepSeek 生成'}
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Badge variant={report.source === 'demo' ? 'secondary' : 'default'}>
                {report.source === 'demo' ? '演示模式' : 'AI 生成'}
              </Badge>
              <Button variant="outline" size="sm" onClick={() => void handleCopy()}>
                <Copy className="size-3.5" />
                复制
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-sm leading-relaxed whitespace-pre-wrap">{report.content}</div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
