import { useCallback, useEffect, useState } from 'react'

interface AsyncState<T> {
  data: T | null
  loading: boolean
  error: string | null
}

/**
 * 通用异步数据加载 Hook：统一管理 loading / error / data 三态。
 * 页面初始自动加载一次，并暴露 reload 用于手动刷新或错误重试。
 */
export function useAsyncData<T>(fetcher: () => Promise<T>) {
  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    loading: true,
    error: null,
  })

  const load = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }))
    try {
      const data = await fetcher()
      setState({ data, loading: false, error: null })
    } catch (err) {
      setState({
        data: null,
        loading: false,
        error: err instanceof Error ? err.message : '请求失败，请稍后重试',
      })
    }
  }, [fetcher])

  useEffect(() => {
    void load()
  }, [load])

  return { ...state, reload: load }
}
