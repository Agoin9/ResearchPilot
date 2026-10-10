import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'

/** 首页加载骨架屏：与真实布局结构一致，避免加载时页面跳动 */
export function HomeSkeleton() {
  return (
    <div className="flex flex-col gap-6" aria-busy="true" aria-label="页面加载中">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <Card key={index}>
            <CardContent className="flex items-center gap-4">
              <Skeleton className="size-11 shrink-0 rounded-lg" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-7 w-24" />
                <Skeleton className="h-3 w-28" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="flex flex-col gap-6 lg:col-span-2">
          <Card>
            <CardContent>
              <Skeleton className="h-5 w-28" />
              <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
                {Array.from({ length: 4 }).map((_, index) => (
                  <Skeleton key={index} className="h-44 rounded-lg" />
                ))}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent>
              <Skeleton className="h-5 w-40" />
              <Skeleton className="mt-4 h-56 w-full" />
            </CardContent>
          </Card>
        </div>

        <div className="flex flex-col gap-6">
          <Card>
            <CardContent>
              <Skeleton className="h-5 w-24" />
              <div className="mt-4 space-y-3">
                {Array.from({ length: 2 }).map((_, index) => (
                  <Skeleton key={index} className="h-16 w-full rounded-lg" />
                ))}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent>
              <Skeleton className="h-5 w-28" />
              <Skeleton className="mx-auto mt-4 size-44 rounded-full" />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
