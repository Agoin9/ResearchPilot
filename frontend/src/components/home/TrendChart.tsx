import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from 'recharts'
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from '@/components/ui/chart'
import type { TrendPoint } from '@/types'

/** 单序列 → 不使用图例，标题即系列名；颜色用顺序色阶蓝 */
const chartConfig = {
  completed: {
    label: '完成任务数',
    theme: { light: '#2a78d6', dark: '#3987e5' },
  },
} satisfies ChartConfig

/** 近 7 天任务完成趋势柱状图 */
export function TrendChart({ data }: { data: TrendPoint[] }) {
  return (
    <ChartContainer
      config={chartConfig}
      className="h-56 w-full"
      initialDimension={{ width: 640, height: 224 }}
    >
      <BarChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
        <CartesianGrid vertical={false} strokeDasharray="4 4" />
        <XAxis
          dataKey="date"
          tickLine={false}
          axisLine={false}
          tickMargin={8}
          fontSize={12}
        />
        <YAxis
          allowDecimals={false}
          tickLine={false}
          axisLine={false}
          tickMargin={4}
          fontSize={12}
        />
        <ChartTooltip
          cursor={{ fill: 'var(--muted)', opacity: 0.35 }}
          content={<ChartTooltipContent />}
        />
        <Bar
          dataKey="completed"
          fill="var(--color-completed)"
          radius={[4, 4, 0, 0]}
          maxBarSize={44}
        />
      </BarChart>
    </ChartContainer>
  )
}
