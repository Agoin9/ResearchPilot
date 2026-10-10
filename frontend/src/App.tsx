import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { PagePlaceholder } from '@/components/common/PagePlaceholder'
import { AppLayout } from '@/components/layout/AppLayout'
import { Toaster } from '@/components/ui/toast'
import BoardPage from '@/pages/BoardPage'
import CreateProjectPage from '@/pages/CreateProjectPage'
import HomePage from '@/pages/HomePage'
import ProjectDashboardPage from '@/pages/ProjectDashboardPage'
import WeeklyReportPage from '@/pages/WeeklyReportPage'

function NotFoundPage() {
  return (
    <PagePlaceholder
      title="页面不存在"
      description="您访问的页面地址有误，请通过左侧导航前往其他页面。"
    />
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/projects/new" element={<CreateProjectPage />} />
          <Route path="/board" element={<BoardPage />} />
          <Route path="/projects/:id" element={<ProjectDashboardPage />} />
          <Route path="/report" element={<WeeklyReportPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
      <Toaster />
    </BrowserRouter>
  )
}
