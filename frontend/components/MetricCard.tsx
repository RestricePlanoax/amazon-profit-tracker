import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";
import type { MetricValue } from "@/lib/types";
import { formatCompactPercent, formatMetricValue } from "@/lib/utils";

type MetricCardProps = {
  label: string;
  metric: MetricValue;
  type: "currency" | "percent" | "number" | "ratio";
  description: string;
  lowerIsBetter?: boolean;
};

export function MetricCard({
  label,
  metric,
  type,
  description,
  lowerIsBetter = false,
}: MetricCardProps) {
  const change = metric.change_pct;
  const positiveDirection = change !== null ? change >= 0 : false;
  const isPositive = lowerIsBetter ? !positiveDirection : positiveDirection;

  return (
    <article className="glass-panel rounded-[1.75rem] border border-border/70 bg-card/85 p-5">
      <p className="text-sm font-semibold uppercase tracking-[0.15em] text-muted-foreground">
        {label}
      </p>
      <p className="mt-5 font-display text-4xl font-semibold text-foreground">
        {formatMetricValue(metric.current, type)}
      </p>
      <div className="mt-4 flex items-center justify-between gap-3">
        <div
          className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-semibold ${
            change === null
              ? "bg-slate-100 text-slate-700"
              : isPositive
                ? "bg-emerald-100 text-emerald-800"
                : "bg-rose-100 text-rose-800"
          }`}
        >
          {change === null ? (
            <Minus className="h-3.5 w-3.5" />
          ) : isPositive ? (
            <ArrowUpRight className="h-3.5 w-3.5" />
          ) : (
            <ArrowDownRight className="h-3.5 w-3.5" />
          )}
          {formatCompactPercent(change)}
        </div>
        <p className="text-xs text-muted-foreground">
          Prev {formatMetricValue(metric.previous, type)}
        </p>
      </div>
      <p className="mt-3 text-sm leading-6 text-muted-foreground">{description}</p>
    </article>
  );
}
