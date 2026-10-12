import axios from 'axios'
import { toast } from '@/components/ui/toast'
import type {
  AiPlanInput,
  AiPlanResult,
  AiPlanTask,
  AiWeeklyReport,
  DocumentDetail,
  DocumentInfo,
  HomeData,
  ProgressRecord,
  Project,
  ProjectDetail,
  ProjectInput,
  QaEntry,
  ReportInfo,
  ReportType,
  Task,
  TaskInput,
  TaskUpdateInput,
  WeeklyReport,
} from '@/types'

/**
 * 统一 axios 实例：默认走同源相对路径 /api，由 Vite 开发服务器代理转发到后端
 * http://127.0.0.1:8000（代理配置见 vite.config.ts）。
 *
 * 为什么不用浏览器直连 http://127.0.0.1:8000/api：
 * 浏览器从 http://localhost:5174 页面直连 127.0.0.1:8000 属于跨域 + 跨地址空间
 * 请求，会被 Chrome 的 Private Network Access / 本地网络访问权限、以及代理类
 * 浏览器插件拦截（表现为 net::ERR_CONNECTION_REFUSED）。同源代理模式下，请求
 * 先发到 localhost:5174（与页面同源，不受任何跨域限制），再由 Node 进程转发到
 * 后端，彻底绕开浏览器侧的所有限制。
 *
 * 如需浏览器直连后端（例如前后端不在同一台机器），在 frontend/.env 中设置：
 *   VITE_API_BASE_URL=http://127.0.0.1:8000/api
 */
const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 15000,
})

/** 把后端错误格式化成一行可读的中文提示 */
function formatErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    if (err.response) {
      const detail = (err.response.data as { detail?: unknown } | undefined)?.detail
      if (Array.isArray(detail)) {
        // FastAPI 参数校验错误：取每条错误的 msg 拼接
        return detail
          .map((item) =>
            typeof item === 'object' && item !== null && 'msg' in item
              ? String((item as { msg: unknown }).msg).replace(/^Value error, /, '')
              : '输入不合法'
          )
          .join('；')
      }
      if (typeof detail === 'string' && detail) {
        return detail
      }
      return `请求失败（HTTP ${err.response.status}）`
    }
    return '无法连接后端服务，请确认后端已启动（http://127.0.0.1:8000，启动命令：uvicorn app.main:app --reload）'
  }
  return err instanceof Error ? err.message : '请求失败，请稍后重试'
}

client.interceptors.response.use(
  (response) => response.data,
  (error: unknown) => {
    const message = formatErrorMessage(error)
    // 页面初始加载的错误由各页面的 ErrorState 展示，这里只对操作类请求弹 toast
    const isGet =
      axios.isAxiosError(error) && (error.config?.method ?? 'get').toLowerCase() === 'get'
    if (!isGet) {
      toast.add({ title: '操作失败', description: message, type: 'error' })
    }
    return Promise.reject(new Error(message))
  }
)

/** 首页聚合数据 */
export function fetchHomeData(): Promise<HomeData> {
  return client.get('/home')
}

/** 项目列表 */
export function fetchProjects(): Promise<Project[]> {
  return client.get('/projects')
}

/** 创建项目 */
export function createProject(data: ProjectInput): Promise<Project> {
  return client.post('/projects', data)
}

/** 更新项目（只提交要修改的字段） */
export function updateProject(
  id: number,
  data: Partial<ProjectInput> & { status?: Project['status'] }
): Promise<Project> {
  return client.put(`/projects/${id}`, data)
}

/** 删除项目（级联删除任务、进度记录） */
export function deleteProject(id: number): Promise<void> {
  return client.delete(`/projects/${id}`)
}

/** 项目详情（项目信息 + 任务列表） */
export function fetchProjectDetail(id: number): Promise<ProjectDetail> {
  return client.get(`/projects/${id}`)
}

/** 创建任务 */
export function createTask(data: TaskInput): Promise<Task> {
  return client.post('/tasks', data)
}

/** 更新任务（改状态 / 日期 / 优先级 / 进度等） */
export function updateTask(id: number, data: TaskUpdateInput): Promise<Task> {
  return client.put(`/tasks/${id}`, data)
}

/** 删除任务 */
export function deleteTask(id: number): Promise<void> {
  return client.delete(`/tasks/${id}`)
}

/** 新增进度记录（同步更新任务进度） */
export function addTaskProgress(
  id: number,
  data: { progress: number; hoursSpent?: number | null; note?: string | null }
): Promise<{ record: ProgressRecord; task: Task }> {
  return client.post(`/tasks/${id}/progress`, data)
}

/** 进度记录列表（时间升序） */
export function fetchTaskProgress(id: number): Promise<ProgressRecord[]> {
  return client.get(`/tasks/${id}/progress`)
}

/** 生成 AI 科研计划（只返回预览草稿，不写数据库） */
export function generateAiPlan(data: AiPlanInput): Promise<AiPlanResult> {
  return client.post('/ai/plan', data)
}

/** 确认 AI 计划：创建项目 + 批量写入任务 */
export function confirmAiPlan(data: {
  project: ProjectInput
  tasks: AiPlanTask[]
}): Promise<{ project: Project; tasks: Task[] }> {
  return client.post('/ai/plan/confirm', data)
}

/** 近 7 天科研活动聚合（周报数据源） */
export function fetchWeeklyReport(): Promise<WeeklyReport> {
  return client.get('/report/weekly')
}

/** 生成 AI 周报正文（无 Key 时返回模板周报） */
export function generateWeeklyReport(): Promise<AiWeeklyReport> {
  return client.post('/report/weekly/generate')
}

/** 上传 PDF 文献（FormData，axios 自动设置 multipart 边界） */
export function uploadDocument(
  projectId: number,
  file: File,
  title?: string
): Promise<DocumentInfo> {
  const form = new FormData()
  form.append('file', file)
  if (title) form.append('title', title)
  return client.post(`/projects/${projectId}/documents`, form)
}

/** 项目下的文献列表 */
export function fetchDocuments(projectId: number): Promise<DocumentInfo[]> {
  return client.get(`/projects/${projectId}/documents`)
}

/** 文献详情（含全文切片，用于"点击来源看原文"） */
export function fetchDocumentDetail(id: number): Promise<DocumentDetail> {
  return client.get(`/documents/${id}`)
}

/** 删除文献（级联删除切片与问答） */
export function deleteDocument(id: number): Promise<void> {
  return client.delete(`/documents/${id}`)
}

/** 对文献提问：后端关键词检索 + DeepSeek 只依据片段回答 */
export function askDocument(id: number, question: string): Promise<QaEntry> {
  return client.post(`/documents/${id}/qa`, { question })
}

/** 文献的问答历史 */
export function fetchDocumentQa(id: number): Promise<QaEntry[]> {
  return client.get(`/documents/${id}/qa`)
}

/** 把问答结果保存为笔记 */
export function saveQaNote(id: number): Promise<QaEntry> {
  return client.post(`/qa/${id}/save-note`)
}

/** 项目下已保存的笔记 */
export function fetchProjectNotes(projectId: number): Promise<QaEntry[]> {
  return client.get(`/projects/${projectId}/notes`)
}

/** 生成组会周报/导师汇报（后端聚合数据 + DeepSeek，落库并返回） */
export function generateMeetingReport(
  projectId: number,
  data: { reportType: ReportType; weekStart: string; weekEnd: string }
): Promise<ReportInfo> {
  return client.post(`/projects/${projectId}/reports`, data)
}

/** 项目汇报历史（最新在前） */
export function fetchMeetingReports(projectId: number): Promise<ReportInfo[]> {
  return client.get(`/projects/${projectId}/reports`)
}

/** 汇报详情 */
export function fetchReportDetail(id: number): Promise<ReportInfo> {
  return client.get(`/reports/${id}`)
}

/** 编辑后保存汇报正文 */
export function updateReportContent(id: number, content: string): Promise<ReportInfo> {
  return client.put(`/reports/${id}`, { content })
}

/** 导出 Markdown 的下载地址（同源，交给 <a download> 触发下载） */
export function reportExportUrl(id: number): string {
  return `${client.defaults.baseURL}/reports/${id}/export`
}
