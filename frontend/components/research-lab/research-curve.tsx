"use client";

import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export type ResearchCurvePoint = { date: string; wealth_index: number; return_decimal: number; drawdown: number };

export default function ResearchCurve({ points }: { points: ResearchCurvePoint[] }) {
  return <div className="research-curve" role="img" aria-label="Hypothetical wealth index, with the same values available in the table below">
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={points} margin={{ top: 12, right: 20, bottom: 8, left: 8 }}>
        <CartesianGrid stroke="var(--line)" strokeDasharray="3 3" />
        <XAxis dataKey="date" minTickGap={45} tick={{ fontSize: 11 }} />
        <YAxis domain={["auto", "auto"]} tick={{ fontSize: 11 }} width={64} />
        <Tooltip formatter={(value: number) => [Number.isFinite(value) ? value.toFixed(4) : "Unavailable", "Wealth index"]} />
        <Line dataKey="wealth_index" name="Wealth index" type="linear" dot={false} isAnimationActive={false} stroke="var(--accent, #3854d9)" strokeWidth={2} />
      </LineChart>
    </ResponsiveContainer>
  </div>;
}
