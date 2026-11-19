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
  /** v2 任务来源（null = 手工创建） */
  sourceType?: TaskSourceType | null
  sourceId?: number | null
}

/** 项目详情：项目信息 + 任务列表 + 实验科研风险（v2） */
export interface ProjectDetail {
  project: Project
  tasks: Task[]
  experimentRisks?: ExperimentRisk[]
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
    experimentRuns?: number
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

// ═══════════════════════════ v2：科研工作台 ═══════════════════════════

/** 研究问题状态 */
export type QuestionStatus = 'open' | 'answered' | 'suspended'

/** 研究问题（列表项，含证据计数） */
export interface Question {
  id: number
  projectId: number
  content: string
  /** v2.1 研究目标 */
  objective: string | null
  /** v2.1 研究假设 */
  hypothesis: string | null
  answerSummary: string | null
  status: QuestionStatus
  evidenceSupport: number
  evidenceAgainst: number
  evidenceNeutral: number
  experimentsCount: number
  createdAt: string
  updatedAt: string
}

/** 证据立场 */
export type EvidenceType = 'support' | 'against' | 'neutral'

/** 原文证据片段（quote 为用户从原文摘录，page 为页码） */
export interface EvidenceSnippet {
  quote: string
  page: string | null
}

/** 文献研究卡片（PaperNote） */
export interface LiteratureCard {
  id: number
  projectId: number
  documentId: number | null
  questionId: number | null
  title: string | null
  authors: string | null
  year: string | null
  researchQuestion: string | null
  method: string | null
  materialsDatasets: string | null
  metrics: string | null
  keyResults: string | null
  /** v2.1 创新点 */
  innovations: string | null
  limitations: string | null
  relevance: string | null
  evidenceType: EvidenceType
  /** v2.1 原文证据片段及页码 */
  evidenceSnippets: EvidenceSnippet[]
  source: 'deepseek' | 'demo' | 'manual'
  createdAt: string
  updatedAt: string
}

/** 卡片抽取结果 */
export interface CardExtractResult {
  card: LiteratureCard
  warning: string
}

/** 卡片对比结果 */
export interface CardCompareResult {
  cards: LiteratureCard[]
}

/** 指标定义 */
export interface MetricDef {
  name: string
  unit: string
  higherIsBetter: boolean
}

/** 实验状态 */
export type ExperimentStatus = 'draft' | 'running' | 'done' | 'failed' | 'paused'

/** 实验 */
export interface Experiment {
  id: number
  projectId: number
  questionId: number | null
  title: string
  objective: string
  hypothesis: string | null
  /** v2.1 实验变量 */
  variables: string | null
  /** v2.1 对照条件 */
  controlConditions: string | null
  /** v2.1 数据集 */
  dataset: string | null
  /** v2.1 模型 */
  model: string | null
  design: string | null
  /** v2.1 实验配置 */
  config: Record<string, unknown>
  metrics: MetricDef[]
  status: ExperimentStatus
  runCount: number
  lastRunAt: string | null
  stalled: boolean
  createdAt: string
  updatedAt: string
}

/** 实验运行记录 */
export interface ExperimentRun {
  id: number
  experimentId: number
  runNo: number
  config: Record<string, unknown>
  results: Record<string, unknown>
  /** v2.1 随机种子 */
  randomSeed: number | null
  /** v2.1 代码 Git Commit */
  gitCommit: string | null
  /** v2.1 环境信息 */
  environment: Record<string, unknown>
  /** v2.1 日志路径 */
  logPath: string | null
  /** v2.1 结果文件路径 */
  resultFiles: string[]
  notes: string | null
  attachments: string[]
  startedAt: string | null
  finishedAt: string | null
  createdAt: string
}

/** 实验详情（实验 + 全部运行记录） */
export interface ExperimentDetail {
  experiment: Experiment
  runs: ExperimentRun[]
}

/** 同实验 run 对比（指标对齐） */
export interface ExperimentCompare {
  experimentId: number
  metricNames: string[]
  rows: Array<{
    runId: number
    runNo: number
    startedAt: string | null
    values: Record<string, unknown>
  }>
}

/** 跨实验指标总览 */
export interface MetricsOverview {
  metrics: Array<{
    name: string
    unit: string
    higherIsBetter: boolean
    points: Array<{
      experimentId: number
      experimentTitle: string
      experimentStatus: ExperimentStatus
      runId: number
      runNo: number
      value: number
    }>
  }>
}

/** 实验维度的科研风险提醒 */
export interface ExperimentRisk {
  experimentId: number
  title: string
  level: 'medium'
  reason: string
}

/** 分析建议类型 */
export type SuggestionType = 'new_task' | 'new_experiment' | 'read_literature' | 'modify_design'

/** 分析建议 */
export interface Suggestion {
  type: SuggestionType
  content: string
  reason: string
  converted: boolean
}

/** AI 实验分析 */
export interface ExperimentAnalysis {
  id: number
  projectId: number
  experimentId: number
  questionId: number | null
  runIds: number[]
  content: string
  suggestions: Suggestion[]
  source: 'deepseek' | 'manual'
  createdAt: string
}

/** 任务来源类型 */
export type TaskSourceType = 'question' | 'literature_card' | 'experiment_analysis' | 'manual'

/** 科研决策记录（v2.1：研究者本人基于真实实验记录做出的判断） */
export interface ResearchDecision {
  id: number
  projectId: number
  experimentId: number
  runIds: number[]
  observations: string
  interpretation: string | null
  supportsHypothesis: boolean | null
  unknowns: string | null
  nextSuggestions: string[]
  createdAt: string
  updatedAt: string
}

// ═══════════════════════════ v2.2/2.3：AI 研究分析 ═══════════════════════════

/** 实验事实（引用真实运行记录） */
export interface ObservedFact {
  experimentRunId: number
  content: string
}

/** 文献证据（引用真实卡片与片段，页码以库为准） */
export interface PaperEvidence {
  paperNoteId: number
  snippetId: string
  page: string | null
  quote: string
  statement: string
}

/** 下一步实验建议 */
export interface NextExperiment {
  objective: string
  hypothesis: string
  changedVariables: string
  fixedConditions: string
  metrics: string
  expectedObservation: string
  risks: string
  estimatedEffort: string
  converted: boolean
  rejected: boolean
}

/** 假设判定三态 */
export type HypothesisStatus = 'support' | 'not_support' | 'insufficient_evidence'

/** AI 研究分析（七段式） */
export interface ResearchAnalysis {
  id: number
  projectId: number
  questionId: number | null
  experimentIds: number[]
  runIds: number[]
  cardIds: number[]
  observedFacts: ObservedFact[]
  paperEvidence: PaperEvidence[]
  stats: {
    metrics: Array<{
      name: string
      unit: string
      higherIsBetter: boolean
      experiments: Array<{
        experimentId: number
        title: string
        runCount: number
        min: number
        max: number
        mean: number
        best: number
        bestRunNo: number
        latest: number
        latestRunNo: number
      }>
    }>
    comparisons: Array<{
      metric: string
      unit: string
      higherIsBetter: boolean
      rows: Array<{
        experimentId: number
        title: string
        best: number
        bestRunNo: number
        deltaVsFirst: number
      }>
    }>
  }
  interpretation: string
  hypothesisStatus: HypothesisStatus
  uncertainty: string
  nextExperiments: NextExperiment[]
  source: 'deepseek' | 'demo'
  warning: string
  createdAt: string
}

/** 建议采纳入参 */
export interface SuggestionAdoptInput {
  objective: string
  hypothesis: string
  variables?: string | null
  requiredData?: string | null
  preconditions?: string | null
  estimatedHours: number
  plannedStartDate: string
  plannedEndDate: string
  dependencies?: number[]
}

/** 采纳结果 */
export interface SuggestionAdoptResult {
  experiment: Experiment
  task: Task
  log: ResearchActionLog
}

/** 建议操作历史 */
export interface ResearchActionLog {
  id: number
  projectId: number
  analysisId: number | null
  suggestionIndex: number
  action: 'adopted' | 'rejected' | 'modified'
  payload: Record<string, unknown>
  taskId: number | null
  experimentId: number | null
  createdAt: string
}
