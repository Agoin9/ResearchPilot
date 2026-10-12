import { NavLink } from 'react-router-dom'
import {
  BarChart3,
  FilePlus2,
  FileText,
  FlaskConical,
  KanbanSquare,
  LayoutDashboard,
} from 'lucide-react'
import { cn } from 'cn'
import { useEffect, useState } from 'react'
import { fetchProjects } from '@/services/api'

/** 左侧导航栏：Logo + 五个页面入口 */
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

  const navItems = [
    { to: '/', label: '首页', icon: LayoutDashboard, end: true },
    { to: '/projects/new', label: '新建项目', icon: FilePlus2 },
    { to: '/board', label: '任务看板', icon: KanbanSquare },
    {
      to: firstProjectId !== null ? `/projects/${firstProjectId}` : '/projects/new',
      label: '项目仪表盘',
      icon: BarChart3,
    },
    { to: '/report', label: '周报生成', icon: FileText },
  ]

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

      <nav className="flex flex-1 flex-col gap-1 px-3 pt-2">
        {navItems.map((item) => (
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
        ))}
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
