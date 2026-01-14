import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { PIITypeCounts } from '@/contexts/AnalysisContext';

interface PIITypesChartProps {
  data: PIITypeCounts;
}

/**
 * Mapeamento de tipos de PII para nomes amigáveis ao usuário
 */
const piiTypeLabels: Record<string, string> = {
  'CPF': 'CPF',
  'EMAIL': 'Email',
  'TELEFONE': 'Telefone',
  'TELEFONE_DDI': 'Telefone (DDI)',
  'RG_CNH': 'RG/CNH',
  'PASSAPORTE': 'Passaporte',
  'CONTA_BANCARIA': 'Conta Bancária',
  'PIX': 'Chave PIX',
  'ENDERECO_RESIDENCIAL': 'Endereço',
  'NOME_PESSOAL': 'Nome Pessoal',
  'NOME_POR_IA': 'Nome (IA)',
  'NOME_CONTEXTO': 'Nome em Contexto',
  'CHAVE_PIX': 'Chave PIX'
};

export function PIITypesChart({ data }: PIITypesChartProps) {
  const colors = [
    'hsl(0, 80%, 40%)',
    'hsl(30, 100%, 50%)',
    'hsl(45, 100%, 45%)',
    'hsl(218, 87%, 39%)',
    'hsl(218, 70%, 55%)',
    'hsl(280, 70%, 50%)',
    'hsl(320, 70%, 50%)',
  ];

  const chartData = Object.entries(data)
    .map(([name, count]) => ({ 
      name: piiTypeLabels[name] || name, 
      count,
      originalType: name 
    }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 7);

  if (chartData.length === 0) {
    return (
      <div className="gov-card animate-slide-up h-full">
        <h3 className="text-lg font-semibold text-foreground mb-4">Tipos de PII Encontrados</h3>
        <div className="h-64 flex items-center justify-center text-muted-foreground">
          <p>Nenhum dado pessoal identificado ainda</p>
        </div>
      </div>
    );
  }

  return (
    <div className="gov-card animate-slide-up h-full flex flex-col">
      <h3 className="text-lg font-semibold text-foreground mb-4">Tipos de PII Encontrados</h3>
      <div className="flex-1 min-h-[200px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 5, right: 30, left: 5, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" horizontal={false} />
            <XAxis
              type="number"
              tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
              axisLine={{ stroke: 'hsl(var(--border))' }}
            />
            <YAxis
              type="category"
              dataKey="name"
              tick={{ fill: 'hsl(var(--foreground))', fontSize: 11 }}
              axisLine={{ stroke: 'hsl(var(--border))' }}
              width={70}
            />
            <Tooltip
              formatter={(value: number) => [`${value} ocorrências`, '']}
              contentStyle={{
                backgroundColor: 'hsl(var(--card))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '8px',
                padding: '8px 12px',
              }}
              labelStyle={{ color: 'hsl(var(--foreground))' }}
            />
            <Bar dataKey="count" radius={[0, 4, 4, 0]} maxBarSize={24}>
              {chartData.map((_, index) => (
                <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
