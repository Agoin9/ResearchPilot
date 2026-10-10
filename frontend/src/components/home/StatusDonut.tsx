import { Cell, Pie, PieChart } from 'recharts'
import {
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from '@/components/ui/chart'
import type { StatusSlice } from '@/types'

/** 3 个类别 → 分类色阶前 3 槽（蓝/橙/青），已验证浅深双模式通过 */
const chartConfig = {
  done: {
    label: '已完成',
    theme: { light: '#2a78d6', dark: '#3987e5' },
  },
  doing: {
    label: '进行中',
    theme: { light: '#eb6834', dark: '#d95926' },
  },
  todo: {
    label: '待开始',
    theme: { light: '#1baf7a', dark: '#199e70' },
  },
} satisfies ChartConfig

const DATA_KEY: Record<string, keyof typeof chartConfig> = {
  已完成: 'done',
  进行中: 'doing',
  待开始: 'todo',
}

/** 任务状态分布圆环：中央总数 + 底部图例 + 悬停提示 */
export function StatusDonut({ data }: { data: StatusSlice[] }) {
  const total = data.reduce((sum, item) => sum + item.value, 0)

  return (
    <ChartContainer
      config={chartConfig}
      className="h-56 w-full"
      initialDimension={{ width: 320, height: 224 }}
    >
      <PieChart margin={{ top: 4, right: 8, bottom: 0, left: 8 }}>
        <Pie
          data={data}
          dataKey="value"
          nameKey="name"
          innerRadius="62%"
          outerRadius="88%"
          paddingAngle={2}
          strokeWidth={0}
        >
          {data.map((item) => (
            <Cell
              key={item.name}
              fill={`var(--color-${DATA_KEY[item.name] ?? 'done'})`}
            />
          ))}
        </Pie>
        <ChartTooltip content={<ChartTooltipContent nameKey="name" />} />
        <ChartLegend content={<ChartLegendContent nameKey="name" />} />
      </PieChart>
      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-semibold tabular-nums">{total}</span>
        <span className="text-xs text-muted-foreground">任务总数</span>
      </div>
    </ChartContainer>
  )
}
