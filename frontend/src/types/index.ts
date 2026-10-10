/** 风险等级：none 无风险 / medium 中风险（进度落后）/ high 高风险（已逾期） */
export type RiskLevel = 'none' | 'medium' | 'high'

/** 科研项目 */
export interface Project {
  id: number
  name: string
  category: string
  /** 截止日期（ISO 格式 yyyy-MM-dd） */
  deadline: string
  /** 每周可用小时数 */
  weeklyHours: number
  /** 整体进度 0-100 */
  progress: number
  tasksTotal: number
  tasksDone: number
  risk: RiskLevel
  /** 剩余天数 */
  daysLeft: number
}

/** 风险任务提醒 */
export interface RiskTask {
  id: number
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
