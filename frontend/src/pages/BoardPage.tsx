import { FlaskConical, KanbanSquare } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { ProjectBoard } from '@/components/board/ProjectBoard'
import { EmptyState } from '@/components/common/EmptyState'
import { ErrorState } from '@/components/common/ErrorState'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { NativeSelect } from '@/components/ui/native-select'
import { useAsyncData } from '@/hooks/useAsyncData'
import { fetchProjects } from '@/services/api'
import type { ProjectStatus } from '@/types'

const STATUS_LABELS: Record<ProjectStatus, string> = {
  active: '进行中',
  completed: '已完成',
  paused: '已暂停',
}

/** 任务看板：选择项目后展示三列看板（支持 ?project=id 直达） */
export default function BoardPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { data: projects, loading, error, reload } = useAsyncData(fetchProjects)
  const [selectedId, setSelectedId] = useState<number | null>(null)

  // 初始/参数变化时选择项目：?project= 参数 → 第一个进行中的项目 → 第一个项目
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

  if (loading) {
    return <p className="py-10 text-center text-sm text-muted-foreground">加载项目中…</p>
  }
  if (error) {
    return <ErrorState message={error} onRetry={() => void reload()} />
  }
  if (!projects || projects.length === 0) {
    return (
      <EmptyState
        icon={FlaskConical}
        title="还没有科研项目"
        description="先创建一个科研项目，再在看板中管理任务。"
        actionLabel="新建项目"
        onAction={() => navigate('/projects/new')}
      />
    )
  }
  if (selectedId === null) {
    return null
  }

  const selected = projects.find((p) => p.id === selectedId)

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <KanbanSquare className="size-5 text-muted-foreground" />
          <NativeSelect
            value={String(selectedId)}
            onChange={(value) => value && setSelectedId(Number(value))}
            items={projects.map((p) => ({ value: String(p.id), label: p.name }))}
            placeholder="选择项目"
            className="w-56"
          />
          {selected && (
            <Badge variant="secondary">{STATUS_LABELS[selected.status]}</Badge>
          )}
        </div>
        <Button variant="outline" size="sm" onClick={() => navigate(`/projects/${selectedId}`)}>
          项目详情
        </Button>
      </div>

      <ProjectBoard projectId={selectedId} />
    </div>
  )
}
