import { BookOpenCheck } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { EmptyState } from '@/components/common/EmptyState'
import { ErrorState } from '@/components/common/ErrorState'
import { NativeSelect } from '@/components/ui/native-select'
import { useAsyncData } from '@/hooks/useAsyncData'
import { DocumentLibraryTab } from '@/components/documents/DocumentLibraryTab'
import { fetchProjects } from '@/services/api'
import type { ProjectStatus } from '@/types'

const STATUS_LABELS: Record<ProjectStatus, string> = {
  active: '进行中',
  completed: '已完成',
  paused: '已暂停',
}

/**
 * 文献研究库页面：上传论文 → 生成结构化研究卡片（问题/方法/数据集/指标/创新点/局限），
 * 证据片段可点击定位原文。复用项目详情页文献库 Tab 组件，默认打开「研究卡片」视图。
 */
export default function LibraryPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const [searchParams] = useSearchParams()
  const { data: projects, loading, error } = useAsyncData(fetchProjects)
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

  if (loading) {
    return <p className="py-10 text-center text-sm text-muted-foreground">加载项目中…</p>
  }
  if (error) {
    return <ErrorState message={error} onRetry={() => window.location.reload()} />
  }
  if (!projects || projects.length === 0) {
    return (
      <EmptyState
        icon={BookOpenCheck}
        title="还没有科研项目"
        description="先创建一个科研项目，再上传论文建立文献研究库。"
        actionLabel="新建项目"
        onAction={() => navigate('/projects/new')}
      />
    )
  }

  const selected = projects.find((p) => p.id === selectedId) ?? null

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <BookOpenCheck className="size-5 text-muted-foreground" />
          <NativeSelect
            value={selectedId !== null ? String(selectedId) : ''}
            onChange={(value) => value && setSelectedId(Number(value))}
            items={projects.map((p) => ({ value: String(p.id), label: p.name }))}
            placeholder="选择项目"
            className="w-64"
          />
          {selected && <Badge variant="secondary">{STATUS_LABELS[selected.status]}</Badge>}
        </div>
        <Button variant="outline" size="sm" onClick={() => navigate(`/projects/${selectedId}`)}>
          项目仪表盘
        </Button>
      </div>

      {selectedId !== null && <DocumentLibraryTab projectId={selectedId} initialView="cards" />}
    </div>
  )
}
