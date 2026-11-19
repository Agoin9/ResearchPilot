import axios from 'axios'
import { toast } from '@/components/ui/toast'
import type {
  AiPlanInput,
  AiPlanResult,
  AiPlanTask,
  AiWeeklyReport,
  CardCompareResult,
  CardExtractResult,
  DocumentDetail,
  DocumentInfo,
  EvidenceType,
  Experiment,
  ExperimentAnalysis,
  ExperimentCompare,
  ExperimentDetail,
  ExperimentRun,
  ExperimentStatus,
  HomeData,
  LiteratureCard,
  MetricDef,
  MetricsOverview,
  NextExperiment,
  ProgressRecord,
  Project,
  ProjectDetail,
  ProjectInput,
  QaEntry,
  Question,
  QuestionStatus,
  ReplanInfo,
  ReportInfo,
  ReportType,
  ResearchActionLog,
  ResearchAnalysis,
  ResearchDecision,
  SuggestionAdoptInput,
  SuggestionAdoptResult,
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

/** 生成重规划方案（风险本地计算 + DeepSeek 调整建议，不修改任务） */
export function generateReplan(projectId: number): Promise<ReplanInfo> {
  return client.post(`/projects/${projectId}/replan`)
}

/** 接受重规划：应用调整到任务表 */
export function adoptReplan(
  id: number
): Promise<{ replan: ReplanInfo; appliedCount: number }> {
  return client.post(`/replans/${id}/adopt`)
}

/** 放弃重规划方案 */
export function rejectReplan(id: number): Promise<ReplanInfo> {
  return client.post(`/replans/${id}/reject`)
}

/** 重规划历史记录 */
export function fetchReplans(projectId: number): Promise<ReplanInfo[]> {
  return client.get(`/projects/${projectId}/replans`)
}

// ═══════════════════════════ v2：科研工作台 ═══════════════════════════

/** 项目下的研究问题列表（含证据计数） */
export function fetchQuestions(projectId: number): Promise<Question[]> {
  return client.get(`/projects/${projectId}/questions`)
}

/** 创建研究问题 */
export function createQuestion(
  projectId: number,
  data: { content: string; status?: QuestionStatus }
): Promise<Question> {
  return client.post(`/projects/${projectId}/questions`, data)
}

/** 更新研究问题（内容/状态/解答摘要） */
export function updateQuestion(
  id: number,
  data: Partial<{ content: string; status: QuestionStatus; answerSummary: string | null }>
): Promise<Question> {
  return client.put(`/questions/${id}`, data)
}

/** 删除研究问题 */
export function deleteQuestion(id: number): Promise<void> {
  return client.delete(`/questions/${id}`)
}

/** 项目下的文献卡片列表（可按问题/立场筛选） */
export function fetchCards(
  projectId: number,
  params?: { questionId?: number; evidenceType?: EvidenceType }
): Promise<LiteratureCard[]> {
  return client.get(`/projects/${projectId}/cards`, { params })
}

/** 手工创建研究卡片 */
export function createCard(
  projectId: number,
  data: Partial<LiteratureCard> & { documentId?: number | null; questionId?: number | null }
): Promise<LiteratureCard> {
  return client.post(`/projects/${projectId}/cards`, data)
}

/** 对文献 AI 抽取研究卡片（无 Key 时返回空模板） */
export function extractDocumentCard(documentId: number): Promise<CardExtractResult> {
  return client.post(`/documents/${documentId}/card`)
}

/** 该文献的卡片 */
export function fetchDocumentCard(documentId: number): Promise<LiteratureCard> {
  return client.get(`/documents/${documentId}/card`)
}

/** 修改卡片字段（source 自动置 manual） */
export function updateCard(
  id: number,
  data: Partial<LiteratureCard>
): Promise<LiteratureCard> {
  return client.put(`/cards/${id}`, data)
}

/** 删除卡片 */
export function deleteCard(id: number): Promise<void> {
  return client.delete(`/cards/${id}`)
}

/** 多卡片字段级对比 */
export function compareCards(projectId: number, cardIds: number[]): Promise<CardCompareResult> {
  return client.get(`/projects/${projectId}/cards/compare`, {
    params: { card_ids: cardIds.join(',') },
  })
}

/** 项目下的实验列表 */
export function fetchExperiments(projectId: number): Promise<Experiment[]> {
  return client.get(`/projects/${projectId}/experiments`)
}

/** 创建实验 */
export function createExperiment(
  projectId: number,
  data: {
    questionId?: number | null
    title: string
    objective: string
    hypothesis?: string | null
    design?: string | null
    metrics?: MetricDef[]
    status?: ExperimentStatus
  }
): Promise<Experiment> {
  return client.post(`/projects/${projectId}/experiments`, data)
}

/** 更新实验 */
export function updateExperiment(
  id: number,
  data: Partial<Experiment> & { metrics?: MetricDef[] }
): Promise<Experiment> {
  return client.put(`/experiments/${id}`, data)
}

/** 删除实验 */
export function deleteExperiment(id: number): Promise<void> {
  return client.delete(`/experiments/${id}`)
}

/** 实验详情（含全部运行记录） */
export function fetchExperimentDetail(id: number): Promise<ExperimentDetail> {
  return client.get(`/experiments/${id}`)
}

/** 新增运行记录 */
export function createRun(
  experimentId: number,
  data: {
    config?: Record<string, unknown>
    results?: Record<string, unknown>
    notes?: string | null
    startedAt?: string | null
    finishedAt?: string | null
  }
): Promise<ExperimentRun> {
  return client.post(`/experiments/${experimentId}/runs`, data)
}

/** 修改运行记录 */
export function updateRun(
  id: number,
  data: Partial<{
    config: Record<string, unknown>
    results: Record<string, unknown>
    notes: string | null
    startedAt: string | null
    finishedAt: string | null
  }>
): Promise<ExperimentRun> {
  return client.put(`/runs/${id}`, data)
}

/** 删除运行记录 */
export function deleteRun(id: number): Promise<void> {
  return client.delete(`/runs/${id}`)
}

/** 上传运行记录附件图片 */
export function uploadRunAttachment(id: number, file: File): Promise<ExperimentRun> {
  const form = new FormData()
  form.append('file', file)
  return client.post(`/runs/${id}/attachments`, form)
}

/** 同实验 run 对比（指标对齐） */
export function fetchExperimentCompare(id: number): Promise<ExperimentCompare> {
  return client.get(`/experiments/${id}/compare`)
}

/** 跨实验指标总览 */
export function fetchMetricsOverview(projectId: number): Promise<MetricsOverview> {
  return client.get(`/projects/${projectId}/metrics`)
}

/** 基于真实运行记录生成 AI 分析（无记录/无 Key 时后端返回 400） */
export function generateAnalysis(experimentId: number): Promise<ExperimentAnalysis> {
  return client.post(`/experiments/${experimentId}/analysis`)
}

/** 手工分析笔记（无 Key 时的人工替代） */
export function createAnalysisNote(
  experimentId: number,
  content: string
): Promise<ExperimentAnalysis> {
  return client.post(`/experiments/${experimentId}/analysis/notes`, { content })
}

/** 实验的分析历史 */
export function fetchAnalyses(experimentId: number): Promise<ExperimentAnalysis[]> {
  return client.get(`/experiments/${experimentId}/analyses`)
}

/** 编辑分析正文 */
export function updateAnalysisContent(id: number, content: string): Promise<ExperimentAnalysis> {
  return client.put(`/analyses/${id}`, { content })
}

/** 分析建议 → 转为科研任务（带来源标记） */
export function suggestionToTask(analysisId: number, suggestionIndex: number): Promise<Task> {
  return client.post(`/analyses/${analysisId}/suggestions/${suggestionIndex}/to-task`)
}

/** 分析建议 → 转为实验草稿 */
export function suggestionToExperiment(
  analysisId: number,
  suggestionIndex: number
): Promise<Experiment> {
  return client.post(`/analyses/${analysisId}/suggestions/${suggestionIndex}/to-experiment`)
}

/** 实验附件图片的访问地址 */
export function attachmentUrl(fileName: string): string {
  return `${client.defaults.baseURL}/uploads/${fileName}`
}

// ═══════════════════════════ v2.1：科研决策记录 ═══════════════════════════

/** 实验的决策记录列表 */
export function fetchExperimentDecisions(experimentId: number): Promise<ResearchDecision[]> {
  return client.get(`/experiments/${experimentId}/decisions`)
}

/** 项目下全部决策记录 */
export function fetchProjectDecisions(projectId: number): Promise<ResearchDecision[]> {
  return client.get(`/projects/${projectId}/decisions`)
}

/** 创建科研决策（内容全部来自研究者本人） */
export function createDecision(
  experimentId: number,
  data: {
    runIds: number[]
    observations: string
    interpretation?: string | null
    supportsHypothesis?: boolean | null
    unknowns?: string | null
    nextSuggestions?: string[]
  }
): Promise<ResearchDecision> {
  return client.post(`/experiments/${experimentId}/decisions`, data)
}

/** 更新科研决策 */
export function updateDecision(
  id: number,
  data: Partial<{
    runIds: number[]
    observations: string
    interpretation: string | null
    supportsHypothesis: boolean | null
    unknowns: string | null
    nextSuggestions: string[]
  }>
): Promise<ResearchDecision> {
  return client.put(`/decisions/${id}`, data)
}

/** 删除科研决策 */
export function deleteDecision(id: number): Promise<void> {
  return client.delete(`/decisions/${id}`)
}

// ═══════════════════════════ v2.2/2.3：AI 研究分析 ═══════════════════════════

/** 按研究问题生成七段式 AI 研究分析（无 Key 时演示模式） */
export function generateQuestionAnalysis(questionId: number): Promise<ResearchAnalysis> {
  return client.post(`/questions/${questionId}/analysis`)
}

/** 研究问题的分析历史 */
export function fetchQuestionAnalyses(questionId: number): Promise<ResearchAnalysis[]> {
  return client.get(`/questions/${questionId}/analyses`)
}

/** 分析详情 */
export function fetchResearchAnalysis(id: number): Promise<ResearchAnalysis> {
  return client.get(`/research-analyses/${id}`)
}

/** 采纳建议（可修改后提交）→ 创建实验 + 关联任务 */
export function adoptSuggestion(
  analysisId: number,
  index: number,
  data: SuggestionAdoptInput
): Promise<SuggestionAdoptResult> {
  return client.post(`/research-analyses/${analysisId}/suggestions/${index}/adopt`, data)
}

/** 拒绝建议（可选原因） */
export function rejectSuggestion(
  analysisId: number,
  index: number,
  reason?: string
): Promise<ResearchActionLog> {
  return client.post(`/research-analyses/${analysisId}/suggestions/${index}/reject`, {
    reason: reason || null,
  })
}

/** 修改建议（不采纳） */
export function modifySuggestion(
  analysisId: number,
  index: number,
  data: Partial<NextExperiment>
): Promise<NextExperiment> {
  return client.put(`/research-analyses/${analysisId}/suggestions/${index}`, data)
}

/** 分析的采纳/拒绝/修改历史 */
export function fetchAnalysisActions(analysisId: number): Promise<ResearchActionLog[]> {
  return client.get(`/research-analyses/${analysisId}/actions`)
}
