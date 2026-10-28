import { Text } from '@fluentui/react-components';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

export type TornadoBar = {
  name: string;
  low_impact: number;
  base_impact: number;
  high_impact: number;
  swing: number;
};

type Props = {
  bars: TornadoBar[];
  scenarios?: { low: number; base: number; high: number };
};

export function SensitivityTornado({ bars, scenarios }: Props) {
  if (!bars.length) {
    return <Text>No sensitivity data yet.</Text>;
  }
  const data = bars.map((b) => ({
    name: b.name,
    lowDelta: b.low_impact - b.base_impact,
    highDelta: b.high_impact - b.base_impact,
  }));
  return (
    <div>
      {scenarios ? (
        <Text block size={200} style={{ marginBottom: 8 }}>
          Scenarios — low: {scenarios.low.toFixed(1)}, base: {scenarios.base.toFixed(1)}, high:{' '}
          {scenarios.high.toFixed(1)}
        </Text>
      ) : null}
      <div style={{ width: '100%', height: 280 }}>
        <ResponsiveContainer>
          <BarChart layout="vertical" data={data} margin={{ left: 24, right: 16 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" />
            <YAxis type="category" dataKey="name" width={100} />
            <Tooltip />
            <Legend />
            <Bar dataKey="lowDelta" name="Low vs base" fill="#54749a" />
            <Bar dataKey="highDelta" name="High vs base" fill="#4c6a80" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
