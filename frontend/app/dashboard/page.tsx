"use client";

import { useEffect, useEffectEvent, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { DateRangePicker } from "@/components/DateRangePicker";
import { EmptyState } from "@/components/EmptyState";
import { InsightsPanel } from "@/components/InsightsPanel";
import { MetricCard } from "@/components/MetricCard";
import { ProfitChart } from "@/components/ProfitChart";
import { api } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type {
  DashboardMetricSet,
  DashboardInsightsResponse,
  DashboardSummary,
  DateBounds,
  TrendPoint,
  UserProfile,
} from "@/lib/types";

const headlineMetrics: Array<{
  key: keyof DashboardMetricSet;
  label: string;
  type: "currency" | "percent" | "number" | "ratio";
  description: string;
  lowerIsBetter?: boolean;
}> = [
  {
    key: "revenue",
    label: "Revenue",
    type: "currency" as const,
    description: "Total sales captured from uploaded order reports.",
  },
  {
    key: "net_profit",
    label: "Net Profit",
    type: "currency" as const,
    description: "Revenue left after fees, refunds, ads, and COGS.",
  },
  {
    key: "profit_margin",
    label: "Profit Margin",
    type: "percent" as const,
    description: "Net profit expressed as a share of revenue.",
  },
  {
    key: "tacos",
    label: "TACOS",
    type: "percent" as const,
    description: "Ad spend as a percentage of total revenue.",
    lowerIsBetter: true,
  },
  {
    key: "acos",
    label: "ACOS",
    type: "percent" as const,
    description: "Ad spend relative to ad-attributed sales.",
    lowerIsBetter: true,
  },
  {
    key: "refund_rate",
    label: "Refund Rate",
    type: "percent" as const,
    description: "Share of revenue lost to refunds in the selected period.",
    lowerIsBetter: true,
  },
];

const supportingMetrics: Array<{
  key: keyof DashboardMetricSet;
  label: string;
  type: "currency" | "percent" | "number" | "ratio";
}> = [
  { key: "ad_spend", label: "Ad Spend", type: "currency" as const },
  { key: "roas", label: "ROAS", type: "ratio" as const },
  { key: "avg_order_value", label: "AOV", type: "currency" as const },
  { key: "orders_count", label: "Orders", type: "number" as const },
  { key: "units_sold", label: "Units Sold", type: "number" as const },
  { key: "cpc", label: "CPC", type: "currency" as const },
];

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [insights, setInsights] = useState<DashboardInsightsResponse | null>(null);
  const [bounds, setBounds] = useState<DateBounds | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadBounds = useEffectEvent(async () => {
    if (!getToken()) {
      return;
    }

    try {
      const [profileData, boundsData] = await Promise.all([api.getMe(), api.getDateBounds()]);
      setProfile(profileData);
      setBounds(boundsData);
      setStartDate(boundsData.default_start_date);
      setEndDate(boundsData.default_end_date);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load dashboard.");
      setLoading(false);
    }
  });

  const loadDashboard = useEffectEvent(async () => {
    if (!getToken() || !startDate || !endDate) {
      return;
    }

    setError(null);

    try {
      const [summaryData, trendsData, insightsData] = await Promise.all([
        api.getSummary(startDate, endDate),
        api.getTrends(startDate, endDate),
        api.getInsights(startDate, endDate),
      ]);

      setSummary(summaryData);
      setTrends(trendsData);
      setInsights(insightsData);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load dashboard.");
    } finally {
      setLoading(false);
    }
  });

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadBounds();
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadDashboard();
  }, [startDate, endDate]);

  const hasData = Boolean(summary && summary.metrics.orders_count.current > 0);

  return (
    <AppShell title="Dashboard">
      <div className="space-y-6">
        <div className="grid gap-4 rounded-[2rem] border border-border/70 bg-card/85 p-6 glass-panel xl:grid-cols-[1.1fr_0.9fr]">
          <div>
            <p className="font-display text-3xl font-semibold">
              {profile?.store.name ?? "Your store"}
            </p>
            <p className="mt-2 max-w-2xl text-sm leading-7 text-muted-foreground">
              Review period-over-period seller performance, compare ad efficiency against
              true profit, and spot where refunds or cost pressure are eating margin.
            </p>
            {summary ? (
              <div className="mt-4 space-y-2">
                <p className="text-sm font-medium text-primary">
                  Comparing {summary.start_date} to {summary.end_date} against the previous
                  window {summary.previous_start_date} to {summary.previous_end_date}.
                </p>
                <p className="text-sm text-muted-foreground">
                  Last refresh:{" "}
                  {summary.last_data_refresh
                    ? new Date(summary.last_data_refresh).toLocaleString()
                    : "No completed imports yet"}
                </p>
              </div>
            ) : null}
          </div>

          {bounds ? (
            <DateRangePicker
              key={`${startDate}-${endDate}`}
              bounds={bounds}
              startDate={startDate}
              endDate={endDate}
              onApply={({ startDate: nextStartDate, endDate: nextEndDate }) => {
                setLoading(true);
                setStartDate(nextStartDate);
                setEndDate(nextEndDate);
              }}
            />
          ) : (
            <div className="h-40 animate-pulse rounded-[1.5rem] border border-border bg-white/70" />
          )}
        </div>

        {loading ? (
          <>
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {Array.from({ length: 6 }).map((_, index) => (
                <div
                  key={index}
                  className="h-48 animate-pulse rounded-3xl border border-border bg-card/70"
                />
              ))}
            </div>
            <div className="h-96 animate-pulse rounded-[2rem] border border-border bg-card/75" />
          </>
        ) : error ? (
          <EmptyState title="Dashboard unavailable" description={error} />
        ) : !summary || !hasData ? (
          <EmptyState
            title="Upload your first reports"
            description="Once you upload order and ads CSV files, this dashboard will unlock date-based analysis, growth comparisons, and seller insights."
          />
        ) : (
          <>
            <section className="grid gap-4 md:grid-cols-2">
              {summary.data_sources.map((source) => (
                <div
                  key={source.name}
                  className="glass-panel rounded-[1.5rem] border border-border/70 bg-card/85 p-5"
                >
                  <p className="text-sm font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                    {source.name}
                  </p>
                  <div className="mt-3 flex items-center justify-between gap-3">
                    <p className="font-display text-2xl font-semibold">
                      {source.active ? "Active" : "Inactive"}
                    </p>
                    <span
                      className={`rounded-full px-3 py-1 text-xs font-semibold ${
                        source.active
                          ? "bg-emerald-100 text-emerald-800"
                          : "bg-slate-100 text-slate-700"
                      }`}
                    >
                      {source.active ? "Healthy" : "Waiting"}
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-muted-foreground">
                    {source.last_refresh_at
                      ? `Last activity ${new Date(source.last_refresh_at).toLocaleString()}`
                      : "No refresh recorded yet"}
                  </p>
                </div>
              ))}
            </section>

            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {headlineMetrics.map((item) => (
                <MetricCard
                  key={item.key}
                  label={item.label}
                  metric={summary.metrics[item.key]}
                  type={item.type}
                  description={item.description}
                  lowerIsBetter={item.lowerIsBetter}
                />
              ))}
            </div>

            <section className="glass-panel rounded-[2rem] border border-border/70 bg-card/85 p-6">
              <div className="mb-5">
                <p className="text-sm font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                  Supporting metrics
                </p>
                <h2 className="font-display text-2xl font-semibold">
                  Additional performance markers that matter
                </h2>
              </div>
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {supportingMetrics.map((metric) => (
                  <div
                    key={metric.key}
                    className="rounded-[1.5rem] border border-border/70 bg-white/75 p-5"
                  >
                    <p className="text-sm font-semibold uppercase tracking-[0.15em] text-muted-foreground">
                      {metric.label}
                    </p>
                    <p className="mt-3 font-display text-3xl font-semibold">
                      {metric.type === "ratio"
                        ? `${summary.metrics[metric.key].current.toFixed(2)}x`
                        : metric.type === "percent"
                          ? `${summary.metrics[metric.key].current.toFixed(2)}%`
                          : metric.type === "currency"
                            ? new Intl.NumberFormat("en-IN", {
                                style: "currency",
                                currency: "INR",
                                maximumFractionDigits: 2,
                              }).format(summary.metrics[metric.key].current)
                            : new Intl.NumberFormat("en-IN").format(
                                summary.metrics[metric.key].current,
                              )}
                    </p>
                    <p className="mt-2 text-xs text-muted-foreground">
                      Previous {summary.metrics[metric.key].previous.toFixed(2)}
                    </p>
                  </div>
                ))}
              </div>
            </section>

            <ProfitChart data={trends} />
            {insights ? <InsightsPanel data={insights} /> : null}
          </>
        )}
      </div>
    </AppShell>
  );
}
