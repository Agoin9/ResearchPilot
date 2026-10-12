/** 风险等级：none 无风险 / medium 中风险（进度落后）/ high 高风险（已逾期） */
export type RiskLevel = 'none' | 'medium' | 'high'

/** 项目状态 */
export type ProjectStatus = 'active' | 'completed' | 'paused'

/** 任务状态 */
export type TaskStatus = 'todo' | 'doing' | 'done'

/** 任务优先级 */
export type TaskPriority = 'high' | 'medium' | 'low'

/** 科研项目（列表/详情项，含后端实时计算的聚合字段） */
export interface Project {
  id: number
  name: string
  /** 科研目标描述 */
  goal: string
  /** 截止日期（ISO 格式 yyyy-MM-dd） */
  deadline: string
  /** 每周可用小时数 */
  weeklyHours: number
  status: ProjectStatus
  /** 整体进度 0-100 */
  progress: number
  tasksTotal: number
  tasksDone: number
  risk: RiskLevel
  /** 剩余天数（可为负，表示已逾期） */
  daysLeft: number
}

/** 风险任务提醒 */
export interface RiskTask {
  id: number
  projectId: number
  taskTitle: string
  projectName: string
  level: 'medium' | 'high'
  reason: string
}

/** 近 7 天任务完成趋势点 */
export interface TrendPoint {
  date: string
  completed: number
}

/** 任务状态分布切片 */
export interface StatusSlice {
  name: string
  value: number
}

/** 首页顶部统计卡片数据 */
export interface HomeStats {
  activeProjects: number
  todoTasks: number
  weeklyHoursSpent: number
  weeklyHoursDelta: number
  riskTaskCount: number
}

/** 首页聚合数据 */
export interface HomeData {
  stats: HomeStats
  projects: Project[]
  riskTasks: RiskTask[]
  trend: TrendPoint[]
  distribution: StatusSlice[]
}

/** 任务（含后端实时计算的风险字段） */
export interface Task {
  id: number
  projectId: number
  parentId: number | null
  title: string
  description: string | null
  status: TaskStatus
  priority: TaskPriority
  plannedStartDate: string | null
  plannedEndDate: string | null
  estimatedHours: number | null
  progress: number
  isMilestone: boolean
  sortOrder: number
  risk: RiskLevel
  riskReason: string
}

/** 项目详情：项目信息 + 任务列表 */
export interface ProjectDetail {
  project: Project
  tasks: Task[]
}

/** 进度记录 */
export interface ProgressRecord {
  id: number
  taskId: number
  progress: number
  hoursSpent: number | null
  note: string | null
  createdAt: string
}

/** 创建/更新项目的入参 */
export interface ProjectInput {
  name: string
  goal: string
  deadline: string
  weeklyHours: number
}

/** AI 科研计划中的单个任务（预览用，priority 为 高/中/低） */
export interface AiPlanTask {
  taskId: string
  title: string
  description: string
  startDate: string
  dueDate: string
  priority: '高' | '中' | '低'
  expectedDeliverable: string
  dependencies: string[]
  estimatedHours: number
  rationale: string
}

/** 生成 AI 科研计划的输入 */
export interface AiPlanInput {
  topic: string
  deadline: string
  weeklyHours: number
  currentStage: string
  completedWork?: string | null
}

/** AI 科研计划生成结果 */
export interface AiPlanResult {
  /** deepseek = 真实生成；demo = 未配置 Key 的演示模式 */
  source: 'deepseek' | 'demo'
  tasks: AiPlanTask[]
  warning: string
}

/** 周报：本周完成的任务 */
export interface WeeklyCompletedTask {
  id: number
  title: string
  completedAt: string
}

/** 周报：单条进度更新 */
export interface WeeklyProgressItem {
  taskTitle: string
  progress: number
  hoursSpent: number | null
  note: string | null
  createdAt: string
}

/** 周报：单个项目的本周活动 */
export interface WeeklyProjectReport {
  projectId: number
  projectName: string
  completedTasks: WeeklyCompletedTask[]
  progressRecords: WeeklyProgressItem[]
}

/** 周报聚合数据 */
export interface WeeklyReport {
  weekStart: string
  weekEnd: string
  stats: {
    tasksCompleted: number
    hoursSpent: number
    progressUpdates: number
  }
  projects: WeeklyProjectReport[]
}

/** AI 生成的周报正文 */
export interface AiWeeklyReport {
  source: 'deepseek' | 'demo'
  content: string
}

/** 文献（上传的 PDF） */
export interface DocumentInfo {
  id: number
  projectId: number
  title: string
  fileName: string
  chunkCount: number
  createdAt: string
}

/** 文献切片 */
export interface DocChunk {
  id: number
  chunkIndex: number
  content: string
}

/** 文献详情（含全文与切片） */
export interface DocumentDetail extends DocumentInfo {
  fullText: string
  chunks: DocChunk[]
}

/** 回答中的引用片段 */
export interface Citation {
  chunkIndex: number
  quote: string
}

/** 文献问答记录 */
export interface QaEntry {
  id: number
  documentId: number
  projectId: number
  question: string
  answer: string
  citations: Citation[]
  confidence: number
  source: 'deepseek' | 'demo'
  isSaved: boolean
  createdAt: string
}

/** 汇报类型：meeting 组会周报 / supervisor 导师汇报 */
export type ReportType = 'meeting' | 'supervisor'

/** 组会周报与导师汇报 */
export interface ReportInfo {
  id: number
  projectId: number
  title: string
  reportType: ReportType
  weekStart: string | null
  weekEnd: string | null
  content: string
  source: 'deepseek' | 'demo'
  createdAt: string
  updatedAt: string
}

/** 重规划：单条调整建议 */
export interface ReplanChange {
  taskId: number
  action: 'reschedule' | 'reprioritize'
  title: string
  plannedStartDate: string | null
  plannedEndDate: string | null
  priority: TaskPriority | null
  estimatedHours: number | null
  reason: string
}

/** 重规划：任务快照（原计划） */
export interface ReplanTaskSnapshot {
  taskId: number
  title: string
  status: TaskStatus
  progress: number
  priority: TaskPriority
  plannedStartDate: string | null
  plannedEndDate: string | null
  estimatedHours: number | null
  riskLevel: RiskLevel
  riskReasons: string[]
}

/** 重规划方案记录 */
export interface ReplanInfo {
  id: number
  projectId: number
  triggerType: string
  planContent: string
  impactSummary: string
  changes: ReplanChange[]
  originalTasks: ReplanTaskSnapshot[]
  source: 'deepseek' | 'demo'
  status: 'pending' | 'adopted' | 'rejected'
  createdAt: string
  decidedAt: string | null
}

/** 创建任务的入参 */
export interface TaskInput {
  projectId: number
  title: string
  description?: string | null
  status?: TaskStatus
  priority?: TaskPriority
  plannedStartDate?: string | null
  plannedEndDate?: string | null
  estimatedHours?: number | null
}

/** 更新任务的入参（全部可选） */
export type TaskUpdateInput = Partial<
  Omit<TaskInput, 'projectId'> & { status: TaskStatus; progress: number }
>
