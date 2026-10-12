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
