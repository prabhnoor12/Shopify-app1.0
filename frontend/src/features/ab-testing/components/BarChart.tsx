import React from 'react';
import {
  BarChart as ReBarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  ErrorBar,
} from 'recharts';

interface BarChartProps {
  data: Array<any>;
  dataKey: string;
  xAxisKey: string;
}

const BarChart: React.FC<BarChartProps> = ({ data, dataKey, xAxisKey }) => {
  return (
    <div className="ab-bar-chart">
      <ResponsiveContainer width="100%" height={300}>
        <ReBarChart data={data} margin={{ top: 16, right: 24, left: 0, bottom: 16 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={xAxisKey} fontSize={13} />
          <YAxis fontSize={13} />
          <Tooltip formatter={(value: any) => (typeof value === 'number' ? value.toFixed(2) : value)} />
          <Bar dataKey={dataKey} fill="#3182ce">
            {data[0] && data[0].ci && (
              <ErrorBar
                dataKey="ci"
                width={6}
                stroke="#2b6cb0"
                direction="y"
                strokeWidth={2}
              />
            )}
          </Bar>
        </ReBarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default BarChart;
