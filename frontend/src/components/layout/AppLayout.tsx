import { Outlet, useLocation } from 'react-router-dom'
import { Sidebar } from '@/components/layout/Sidebar'
import { Topbar } from '@/components/layout/Topbar'

const PAGE_TITLES: Array<{ match: (pathname: string) => boolean; title: string }> = [
  { match: (p) => p === '/', title: '科研总览' },
  { match: (p) => p === '/projects/new', title: '新建项目' },
  { match: (p) => p === '/board', title: '任务看板' },
  { match: (p) => p.startsWith('/projects/'), title: '项目仪表盘' },
  { match: (p) => p === '/report', title: '周报生成' },
]

/** 应用整体布局：左侧导航 + 顶栏 + 内容区 */
export function AppLayout() {
  const { pathname } = useLocation()
  const title =
    PAGE_TITLES.find((item) => item.match(pathname))?.title ?? 'ResearchPilot'

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar title={title} />
        <main className="flex-1 overflow-y-auto bg-muted/30 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
