import { Text } from '@fluentui/react-components';
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

export type TrackingRow = {
  period: string;
  kpi_name: string;
  predicted?: { base: number } | null;
  actual?: { base: number } | null;
  variance?: { base: number } | null;
};

type Props = { rows: TrackingRow[] };

export function TrackingChart({ rows }: Props) {
  if (!rows.length) {
    return <Text>No realization records yet.</Text>;
  }
  const data = rows.map((r) => ({
    period: r.period,
    predicted: r.predicted?.base ?? null,
    actual: r.actual?.base ?? null,
  }));
  return (
    <div style={{ width: '100%', height: 260 }}>
      <ResponsiveContainer>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="period" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="predicted" stroke="#54749a" strokeDasharray="4 4" />
          <Line type="monotone" dataKey="actual" stroke="#2e7d32" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
