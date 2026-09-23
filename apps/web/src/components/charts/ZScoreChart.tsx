"use client";

import { Bar, BarChart, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatFeatureName } from "@/lib/format";

export function ZScoreChart({ data }: { data: { feature: string; z: number }[] }) {
  const sorted = [...data].sort((a, b) => b.z - a.z);
  const chartData = sorted.map((d) => ({ ...d, name: formatFeatureName(d.feature) }));

  return (
    <ResponsiveContainer width="100%" height={Math.max(240, chartData.length * 32)}>
      <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 24, top: 4, bottom: 4 }}>
        <XAxis type="number" tick={{ fill: "var(--text-muted)", fontSize: 12 }} axisLine={{ stroke: "var(--gridline)" }} tickLine={false} />
        <YAxis
          type="category"
          dataKey="name"
          width={150}
          tick={{ fill: "var(--text-secondary)", fontSize: 12 }}
          axisLine={false}
          tickLine={false}
        />
        <ReferenceLine x={0} stroke="var(--baseline, var(--text-muted))" />
        <Tooltip
          contentStyle={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            fontSize: 13,
          }}
          formatter={(value) => {
            const num = Number(value);
            return [`${num >= 0 ? "+" : ""}${num.toFixed(2)}σ vs. average listener`, ""];
          }}
        />
        <Bar dataKey="z" radius={4} maxBarSize={16}>
          {chartData.map((d, i) => (
            <Cell key={i} fill={d.z >= 0 ? "var(--series-1)" : "var(--series-8)"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
