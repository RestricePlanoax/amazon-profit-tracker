import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";
import type { MetricTrust, MetricValue } from "@/lib/types";
import { formatCompactPercent, formatMetricValue } from "@/lib/utils";

type MetricCardProps = {
  label: string;
  metric: MetricValue;
  type: "currency" | "percent" | "number" | "ratio";
  description: string;
  lowerIsBetter?: boolean;
  trust?: MetricTrust;
};

export function MetricCard({
  label,
  metric,
  type,
  description,
  lowerIsBetter = false,
  trust,
}: MetricCardProps) {
  const change = metric.change_pct;
  const positiveDirection = change !== null ? change >= 0 : false;
  const isPositive = lowerIsBetter ? !positiveDirection : positiveDirection;

  return (
    <article className="polaris-card p-5">
      <p className="text-xs font-black uppercase tracking-[0.14em] text-muted-foreground">
        {label}
      </p>
      <p className="mt-3 font-display text-3xl font-black text-foreground">
        {formatMetricValue(metric.current, type)}
      </p>
      <div className="mt-4 flex items-center justify-between gap-3">
        <div
          className={`polaris-badge gap-1 ${
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
        <p className="text-xs font-semibold text-muted-foreground">
          Prev {formatMetricValue(metric.previous, type)}
        </p>
      </div>
      <p className="mt-3 text-xs leading-5 text-muted-foreground">{description}</p>
      {trust ? (
        <div className="mt-3 space-y-2 rounded-lg border border-border bg-[var(--surface-subdued)] p-3">
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={`polaris-badge ${
                trust.status === "complete"
                  ? "bg-emerald-100 text-emerald-800"
                  : trust.status === "partial"
                    ? "bg-amber-100 text-amber-800"
                    : trust.status === "limited"
                      ? "bg-orange-100 text-orange-800"
                      : "bg-slate-100 text-slate-700"
              }`}
            >
              {trust.coverage_pct.toFixed(0)}% coverage
            </span>
            <p className="text-[11px] font-medium text-muted-foreground">
              Powered by {trust.powered_by.join(" + ")}
            </p>
          </div>
          <p className="text-[11px] leading-5 text-muted-foreground">{trust.note}</p>
          <p className="text-[11px] text-muted-foreground">
            Freshness {trust.freshness_at ? new Date(trust.freshness_at).toLocaleString() : "not available yet"}
          </p>
        </div>
      ) : null}
    </article>
  );
}
