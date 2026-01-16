import { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { RiskDistribution, getRiskLabel, getRiskColor } from '@/contexts/AnalysisContext';

interface RiskDistributionChartProps {
  distribution: RiskDistribution;
}

export function RiskDistributionChart({ distribution }: RiskDistributionChartProps) {
  // Defensive: fallback if distribution is missing or malformed
  const safeDist = distribution && typeof distribution === 'object' ? distribution : {
    critical: 0, high: 0, moderate: 0, low: 0, safe: 0
  };
  const safeNumber = (v: any) => (typeof v === 'number' && !isNaN(v) ? v : 0);
  const data = [
    { name: 'Crítico', value: safeNumber(safeDist.critical), color: getRiskColor('critical') },
    { name: 'Alto', value: safeNumber(safeDist.high), color: getRiskColor('high') },
    { name: 'Moderado', value: safeNumber(safeDist.moderate), color: getRiskColor('moderate') },
    { name: 'Baixo', value: safeNumber(safeDist.low), color: getRiskColor('low') },
    { name: 'Seguro', value: safeNumber(safeDist.safe), color: getRiskColor('safe') },
  ].filter(item => item.value > 0);

  const total = safeNumber(safeDist.critical) + safeNumber(safeDist.high) + safeNumber(safeDist.moderate) + safeNumber(safeDist.low) + safeNumber(safeDist.safe);

  if (!distribution || total === 0) {
    return (
      <div className="gov-card animate-slide-up h-full">
        <h3 className="text-lg font-semibold text-foreground mb-4">Distribuição de Nível de Risco</h3>
        <div className="h-64 flex items-center justify-center text-muted-foreground">
          <p>Nenhum dado disponível</p>
        </div>
      </div>
    );
  }

  // Animation state to trigger donut animation after mount
  const [animate, setAnimate] = useState(false);
  useEffect(() => {
    setAnimate(true);
  }, [distribution]);

  return (
    <div className="gov-card animate-slide-up h-full flex flex-col">
      <h3 className="text-lg font-semibold text-foreground mb-4">Distribuição de Nível de Risco</h3>
      <div className="flex-1 min-h-[200px]">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart margin={{ top: 20, right: 80, bottom: 20, left: 80 }}>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius="35%"
              outerRadius="55%"
              paddingAngle={3}
              dataKey="value"
              isAnimationActive={animate}
              animationDuration={900}
              animationBegin={0}
              label={({ name, percent, cx, cy, midAngle, outerRadius }) => {
                const RADIAN = Math.PI / 180;
                const radius = outerRadius * 1.4;
                const x = cx + radius * Math.cos(-midAngle * RADIAN);
                const y = cy + radius * Math.sin(-midAngle * RADIAN);
                return (
                  <text
                    x={x}
                    y={y}
                    fill="hsl(var(--foreground))"
                    textAnchor={x > cx ? 'start' : 'end'}
                    dominantBaseline="central"
                    fontSize={12}
                    fontWeight={500}
                  >
                    {`${name}: ${(percent * 100).toFixed(0)}%`}
                  </text>
                );
              }}
              labelLine={{
                stroke: 'hsl(var(--muted-foreground))',
                strokeWidth: 1,
              }}
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} strokeWidth={0} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value: number) => [`${value} pedidos`, '']}
              contentStyle={{
                backgroundColor: 'hsl(var(--card))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '8px',
                padding: '8px 12px',
              }}
            />
            <Legend
              verticalAlign="bottom"
              height={32}
              wrapperStyle={{ paddingTop: '10px' }}
              formatter={(value) => (
                <span className="text-xs text-foreground">{value}</span>
              )}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-2 pt-2 border-t border-border">
        <p className="text-sm text-muted-foreground text-center">
          Total: <span className="font-semibold text-foreground">{total}</span> pedidos analisados
        </p>
      </div>
    </div>
  );
}
