import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts'

interface CategoryData {
  name: string
  value: number
}

interface CategoryChartProps {
  data: CategoryData[]
}

export default function CategoryChart({ data }: CategoryChartProps) {
  return (
    <div className="h-[240px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          layout="vertical"
          data={data}
          margin={{ top: 10, right: 15, left: 15, bottom: 5 }}
        >
          {/* Numerical X Axis */}
          <XAxis
            type="number"
            stroke="#71717a"
            fontSize={11}
            tickLine={false}
            axisLine={false}
            allowDecimals={false}
          />
          {/* Categorical Y Axis with text spacing */}
          <YAxis
            type="category"
            dataKey="name"
            stroke="#a1a1aa"
            fontSize={11}
            tickLine={false}
            axisLine={false}
            width={95}
          />
          {/* Custom Tooltip */}
          <Tooltip
            cursor={{ fill: '#18181b', opacity: 0.25 }}
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const item = payload[0].payload as CategoryData
                return (
                  <div className="rounded-lg border border-border bg-zinc-950 px-2.5 py-1.5 shadow-xl text-xs font-mono">
                    <div className="flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full bg-indigo-500" />
                      <span className="text-zinc-400 font-semibold">{item.name}:</span>
                      <span className="text-white font-bold">{item.value} issues</span>
                    </div>
                  </div>
                )
              }
              return null
            }}
          />
          {/* Horizontal indigo styled bar */}
          <Bar dataKey="value" fill="#6366f1" radius={[0, 4, 4, 0]} maxBarSize={16} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
export type { CategoryData }
