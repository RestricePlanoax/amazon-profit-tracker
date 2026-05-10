"use client";

import { useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TrendPoint } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { formatCurrency, formatDateLabel, formatMetricValue } from "@/lib/utils";

type ProfitChartProps = {
  data: TrendPoint[];
};

const chartModes = {
  financials: {
    label: "Financials",
    formatter: (value: number) => formatCurrency(value),
    lines: [
      { key: "revenue", label: "Revenue", color: "#f97316", type: "currency" as const },
      { key: "net_profit", label: "Net Profit", color: "#0f766e", type: "currency" as const },
      { key: "ad_spend", label: "Ad Spend", color: "#16211d", type: "currency" as const },
    ],
  },
  efficiency: {
    label: "Efficiency",
    formatter: (value: number) => `${value.toFixed(2)}%`,
    lines: [
      { key: "tacos", label: "TACOS", color: "#0f766e", type: "percent" as const },
      { key: "acos", label: "ACOS", color: "#f97316", type: "percent" as const },
      { key: "refund_rate", label: "Refund Rate", color: "#b91c1c", type: "percent" as const },
    ],
  },
};

type ChartModeKey = keyof typeof chartModes;

export function ProfitChart({ data }: ProfitChartProps) {
  const [mode, setMode] = useState<ChartModeKey>("financials");
  const activeMode = chartModes[mode];

  return (
    <section className="glass-panel rounded-[2rem] border border-border/70 bg-card/85 p-6">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="flex flex-col gap-2">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-muted-foreground">
            Trend chart
          </p>
          <h2 className="font-display text-2xl font-semibold">
            Daily performance across revenue, profit, and efficiency
          </h2>
        </div>

        <div className="flex flex-wrap gap-2">
          {(Object.keys(chartModes) as ChartModeKey[]).map((option) => (
            <Button
              key={option}
              variant={mode === option ? "default" : "outline"}
              onClick={() => setMode(option)}
            >
              {chartModes[option].label}
            </Button>
          ))}
        </div>
      </div>

      <div className="h-[380px] rounded-[1.5rem] border border-border/70 bg-white/70 p-4">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid stroke="rgba(22,33,29,0.08)" vertical={false} />
            <XAxis
              dataKey="date"
              tick={{ fill: "#5d675d", fontSize: 12 }}
              tickFormatter={(value) => formatDateLabel(value)}
              tickLine={false}
              axisLine={false}
              minTickGap={28}
            />
            <YAxis
              tick={{ fill: "#5d675d", fontSize: 12 }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => activeMode.formatter(Number(value))}
              width={72}
            />
            <Tooltip
              labelFormatter={(label) => formatDateLabel(String(label))}
              formatter={(value, name) => {
                const line = activeMode.lines.find((item) => item.label === String(name));
                return [
                  formatMetricValue(Number(value ?? 0), line?.type ?? "number"),
                  String(name),
                ];
              }}
              contentStyle={{
                borderRadius: "18px",
                border: "1px solid rgba(22,33,29,0.08)",
                backgroundColor: "rgba(255,255,255,0.94)",
              }}
            />
            {activeMode.lines.map((line) => (
              <Line
                key={line.key}
                type="monotone"
                dataKey={line.key}
                name={line.label}
                stroke={line.color}
                strokeWidth={3}
                dot={false}
                activeDot={{ r: 5 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
