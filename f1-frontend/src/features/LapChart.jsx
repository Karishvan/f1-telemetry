import { TIRE_COLORS } from "../utils/constants";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { formatLapTime } from "../utils/formatters";

const transformDataForMultiLine = (laps) => {
  return laps.map((lap) => {
    const stintKey = `${lap.compound}_${lap.stint}`;
    return {
      lap: lap.lap,
      [stintKey]: lap.time,
      compound: lap.compound,
      stint: lap.stint,
      stintKey: stintKey,
    };
  });
};

const LapChart = ({ data, driver }) => {
  const chartData = transformDataForMultiLine(data);
  const uniqueStints = [...new Set(chartData.map((d) => d.stintKey))];
  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={chartData}>
        <CartesianGrid
          strokeDasharray="3 3"
          vertical={false}
          stroke="#374151"
        />
        <XAxis
          dataKey="lap"
          type="number"
          domain={["dataMin", "dataMax"]}
          stroke="#9ca3af"
        />
        <YAxis
          domain={["auto", "auto"]}
          stroke="#9ca3af"
          tickFormatter={(value) => {
            return formatLapTime(value);
          }}
        />
        <Tooltip
          labelFormatter={(label) => `LAP: ${label}`}
          formatter={(value, name) => [
            <span style={{ color: TIRE_COLORS[name] }}>
              {formatLapTime(value)}
            </span>,
            name,
          ]}
          contentStyle={{ backgroundColor: "#1f2937", border: "none" }}
          itemStyle={{ color: "#f3f4f6" }}
        />

        {uniqueStints.map((stintKey) => {
          const compound = stintKey.split("_")[0];

          return (
            <Line
              key={stintKey}
              type="monotone"
              dataKey={stintKey}
              stroke={TIRE_COLORS[compound]}
              strokeWidth={3}
              connectNulls={false}
              dot={true}
              animationDuration={500}
              name={compound}
            />
          );
        })}

        {chartData.map((lap, i) => {
          const prevLap = chartData[i - 1];
          if (prevLap && lap.stintKey !== prevLap.stintKey) {
            return (
              <ReferenceLine
                key={`pit-${lap.lap}`}
                x={(lap.lap + prevLap.lap) / 2}
                stroke="#ef4444"
                strokeDasharray="5 5"
                label={{
                  value: "BOX",
                  fill: "#ef4444",
                  fontSize: 12,
                  position: "top",
                  fontWeight: "bold",
                }}
              />
            );
          }
          return null;
        })}
      </LineChart>
    </ResponsiveContainer>
  );
};

export default LapChart;
