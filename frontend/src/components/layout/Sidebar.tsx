import { NavLink } from 'react-router-dom'
import {
  BarChart3,
  BookOpenCheck,
  ClipboardList,
  FilePlus2,
  FileText,
  FlaskConical,
  Gauge,
  KanbanSquare,
  LayoutDashboard,
  Scale,
} from 'lucide-react'
import { cn } from 'cn'
import { useEffect, useState } from 'react'
import { fetchProjects } from '@/services/api'

interface NavItem {
  to: string
  label: string
  icon: typeof LayoutDashboard
  end?: boolean
}

/** 左侧导航栏：Logo + 总览 / 科研工作台 / 项目管理 三组入口 */
export function Sidebar() {
  // 「项目仪表盘」指向最新一个项目；没有项目时引导去新建
  const [firstProjectId, setFirstProjectId] = useState<number | null>(null)
  useEffect(() => {
    fetchProjects()
      .then((list) => {
        const first = list.find((p) => p.status === 'active') ?? list[0]
        setFirstProjectId(first?.id ?? null)
      })
      .catch(() => setFirstProjectId(null))
  }, [])

  const overviewItems: NavItem[] = [
    { to: '/', label: '首页', icon: LayoutDashboard, end: true },
    { to: '/cockpit', label: '科研驾驶舱', icon: Gauge },
    { to: '/report', label: '周报生成', icon: FileText },
    { to: '/projects/new', label: '新建项目', icon: FilePlus2 },
  ]

  const workbenchItems: NavItem[] = [
    { to: '/library', label: '文献研究库', icon: BookOpenCheck },
    { to: '/lab', label: '实验工作台', icon: FlaskConical },
    { to: '/compare', label: '结果比较', icon: Scale },
    { to: '/decisions', label: '决策日志', icon: ClipboardList },
  ]

  const manageItems: NavItem[] = [
    { to: '/board', label: '任务看板', icon: KanbanSquare },
    {
      to: firstProjectId !== null ? `/projects/${firstProjectId}` : '/projects/new',
      label: '项目仪表盘',
      icon: BarChart3,
    },
  ]

  const renderItems = (items: NavItem[]) =>
    items.map((item) => (
      <NavLink
        key={item.to}
        to={item.to}
        end={item.end}
        className={({ isActive }) =>
          cn(
            'flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground',
            isActive && 'bg-primary/10 text-primary hover:bg-primary/15'
          )
        }
      >
        <item.icon className="size-4" />
        {item.label}
      </NavLink>
    ))

  return (
    <aside className="flex w-60 shrink-0 flex-col border-r border-border bg-card">
      <div className="flex items-center gap-2.5 px-5 py-5">
        <div className="flex size-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <FlaskConical className="size-5" />
        </div>
        <div className="leading-tight">
          <div className="font-heading text-sm font-semibold tracking-wide">
            ResearchPilot
          </div>
          <div className="text-xs text-muted-foreground">研途智控</div>
        </div>
      </div>

      <nav className="flex flex-1 flex-col gap-1 overflow-y-auto px-3 pt-2">
        {renderItems(overviewItems)}
        <p className="mt-4 mb-1 px-3 text-[11px] font-medium tracking-wide text-muted-foreground/70">
          科研工作台
        </p>
        {renderItems(workbenchItems)}
        <p className="mt-4 mb-1 px-3 text-[11px] font-medium tracking-wide text-muted-foreground/70">
          项目管理
        </p>
        {renderItems(manageItems)}
      </nav>

      <div className="border-t border-border px-5 py-4">
        <p className="text-xs leading-relaxed text-muted-foreground">
          科研任务智能管理
          <br />
          数据存储在本机 SQLite
        </p>
      </div>
    </aside>
  )
}
