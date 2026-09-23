"use client";

import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { TopArtist } from "@/lib/types";

export function TopArtistsChart({ data }: { data: TopArtist[] }) {
  const chartData = [...data].reverse(); // Recharts renders bottom-up; keep #1 at top
  return (
    <ResponsiveContainer width="100%" height={Math.max(220, chartData.length * 34)}>
      <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 24, top: 4, bottom: 4 }}>
        <CartesianGrid horizontal={false} stroke="var(--gridline)" />
        <XAxis type="number" tick={{ fill: "var(--text-muted)", fontSize: 12 }} axisLine={{ stroke: "var(--gridline)" }} tickLine={false} allowDecimals={false} />
        <YAxis
          type="category"
          dataKey="artist_name"
          width={140}
          tick={{ fill: "var(--text-secondary)", fontSize: 12 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          cursor={{ fill: "var(--gridline)", opacity: 0.4 }}
          contentStyle={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            fontSize: 13,
          }}
          formatter={(value) => [`${value} plays`, "Play count"]}
        />
        <Bar dataKey="play_count" radius={[0, 4, 4, 0]} maxBarSize={18}>
          {chartData.map((_, i) => (
            <Cell key={i} fill="var(--series-1)" />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
