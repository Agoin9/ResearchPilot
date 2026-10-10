import { mockHomeData } from '@/data/mockData'
import type { HomeData } from '@/types'

/**
 * 模拟 API 层：真实后端就绪后，将这里替换为 axios 请求即可。
 * 内置两个演示开关，用于验收「错误提示」和「空数据提示」两种状态。
 */
let failMode = false
let emptyMode = false

export function setFailMode(value: boolean) {
  failMode = value
}

export function setEmptyMode(value: boolean) {
  emptyMode = value
}

export function getFailMode() {
  return failMode
}

export function getEmptyMode() {
  return emptyMode
}

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

const EMPTY_DATA: HomeData = {
  stats: {
    activeProjects: 0,
    todoTasks: 0,
    weeklyHoursSpent: 0,
    weeklyHoursDelta: 0,
    riskTaskCount: 0,
  },
  projects: [],
  riskTasks: [],
  trend: [],
  distribution: [],
}

/** 获取首页聚合数据（模拟 700ms 网络延迟） */
export async function fetchHomeData(): Promise<HomeData> {
  await delay(700)
  if (failMode) {
    throw new Error('模拟网络错误：请求超时，请检查网络后重试')
  }
  if (emptyMode) {
    return EMPTY_DATA
  }
  return mockHomeData
}
