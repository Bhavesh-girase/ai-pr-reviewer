import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts'

interface SeverityData {
  name: string
  value: number
  fill: string
}

interface SeverityChartProps {
  data: SeverityData[]
}

export default function SeverityChart({ data }: SeverityChartProps) {
  // Filter out zero-values to avoid empty slice rendering issues
  const activeData = data.filter(d => d.value > 0)
  const total = data.reduce((acc, curr) => acc + curr.value, 0)

  // Fallback for rendering the empty/completed ring nicely
  const displayData = activeData.length > 0 
    ? activeData 
    : [{ name: 'All Clean', value: 1, fill: '#1f1f23' }]

  return (
    <div className="h-[220px] w-full flex items-center justify-center relative">
      {/* Absolute center indicator */}
      <div className="absolute flex flex-col items-center justify-center select-none pointer-events-none z-10">
        <span className="text-3xl font-extrabold text-white tracking-tight leading-none font-mono">
          {total}
        </span>
        <span className="text-[9px] text-zinc-500 font-bold uppercase tracking-wider mt-1.5">
          {total === 1 ? 'Issue' : 'Issues'}
        </span>
      </div>

      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={displayData}
            cx="50%"
            cy="50%"
            innerRadius={68}
            outerRadius={82}
            paddingAngle={activeData.length > 1 ? 4 : 0}
            dataKey="value"
            animationDuration={600}
          >
            {displayData.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={entry.fill} 
                stroke="#09090b" 
                strokeWidth={2}
                className="focus:outline-none"
              />
            ))}
          </Pie>
          {activeData.length > 0 && (
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const item = payload[0].payload as SeverityData
                  return (
                    <div className="rounded-lg border border-zinc-800 bg-zinc-950 px-2.5 py-1.5 shadow-xl text-xs font-mono">
                      <div className="flex items-center gap-2">
                        <span className="h-2 w-2 rounded-full" style={{ backgroundColor: item.fill }} />
                        <span className="text-zinc-400 font-semibold">{item.name}:</span>
                        <span className="text-white font-bold">{item.value}</span>
                      </div>
                    </div>
                  )
                }
                return null
              }}
            />
          )}
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
export type { SeverityData }
