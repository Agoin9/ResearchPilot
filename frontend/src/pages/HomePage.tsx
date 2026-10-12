import { FlaskConical, Plus, RefreshCw } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { EmptyState } from '@/components/common/EmptyState'
import { ErrorState } from '@/components/common/ErrorState'
import { HomeSkeleton } from '@/components/home/HomeSkeleton'
import { ProjectCard } from '@/components/home/ProjectCard'
import { RiskAlertList } from '@/components/home/RiskAlertList'
import { StatCards } from '@/components/home/StatCards'
import { StatusDonut } from '@/components/home/StatusDonut'
import { TrendChart } from '@/components/home/TrendChart'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useAsyncData } from '@/hooks/useAsyncData'
import { fetchHomeData } from '@/services/api'

const todayText = new Date().toLocaleDateString('zh-CN', {
  year: 'numeric',
  month: 'long',
  day: 'numeric',
  weekday: 'long',
})

/** 首页：统计概览 + 项目列表 + 风险提醒 + 图表（数据来自后端 /api/home） */
export default function HomePage() {
  const navigate = useNavigate()
  const { data, loading, error, reload } = useAsyncData(fetchHomeData)

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-heading text-xl font-semibold">
            今天也要稳步推进科研
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">{todayText}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => void reload()}>
            <RefreshCw className="size-4" />
            刷新
          </Button>
          <Button onClick={() => navigate('/projects/new')}>
            <Plus className="size-4" />
            新建项目
          </Button>
        </div>
      </div>

      {loading ? (
        <HomeSkeleton />
      ) : error ? (
        <ErrorState message={error} onRetry={() => void reload()} />
      ) : !data || data.projects.length === 0 ? (
        <EmptyState
          icon={FlaskConical}
          title="还没有科研项目"
          description="创建你的第一个科研项目，录入科研目标与截止时间，开始管理你的科研任务。"
          actionLabel="新建项目"
          onAction={() => navigate('/projects/new')}
        />
      ) : (
        <>
          <StatCards stats={data.stats} />

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <div className="flex flex-col gap-6 lg:col-span-2">
              <Card>
                <CardHeader className="flex-row items-center justify-between space-y-0">
                  <div>
                    <CardTitle>科研项目</CardTitle>
                    <CardDescription>共 {data.projects.length} 个进行中的项目</CardDescription>
                  </div>
                  <Badge variant="secondary">进行中</Badge>
                </CardHeader>
                <CardContent className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  {data.projects.map((project) => (
                    <ProjectCard key={project.id} project={project} />
                  ))}
                  <button
                    type="button"
                    onClick={() => navigate('/projects/new')}
                    className="flex min-h-44 flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-border text-muted-foreground transition-colors hover:border-primary/50 hover:bg-primary/5 hover:text-primary"
                  >
                    <Plus className="size-6" />
                    <span className="text-sm font-medium">新建项目</span>
                  </button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>近 7 天任务完成趋势</CardTitle>
                  <CardDescription>每日完成任务数量</CardDescription>
                </CardHeader>
                <CardContent>
                  <TrendChart data={data.trend} />
                </CardContent>
              </Card>
            </div>

            <div className="flex flex-col gap-6">
              <Card>
                <CardHeader className="flex-row items-center justify-between space-y-0">
                  <CardTitle>风险提醒</CardTitle>
                  <Badge
                    variant={
                      data.riskTasks.length > 0 ? 'destructive' : 'secondary'
                    }
                  >
                    {data.riskTasks.length} 项
                  </Badge>
                </CardHeader>
                <CardContent>
                  <RiskAlertList riskTasks={data.riskTasks} />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>任务状态分布</CardTitle>
                  <CardDescription>全部项目的任务统计</CardDescription>
                </CardHeader>
                <CardContent>
                  <StatusDonut data={data.distribution} />
                </CardContent>
              </Card>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
