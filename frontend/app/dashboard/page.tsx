"use client";

import { useEffect, useEffectEvent, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { DateRangePicker } from "@/components/DateRangePicker";
import { EmptyState } from "@/components/EmptyState";
import { InsightsPanel } from "@/components/InsightsPanel";
import { MetricCard } from "@/components/MetricCard";
import { ProfitChart } from "@/components/ProfitChart";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type {
  DashboardMetricSet,
  DashboardInsightsResponse,
  DashboardSummary,
  DateBounds,
  MetricCatalogItem,
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

const trustPriorityMetricKeys: Array<keyof DashboardMetricSet> = [
  "net_profit",
  "profit_margin",
  "revenue",
  "ad_spend",
  "acos",
  "refund_rate",
];

const metricLabels: Record<keyof DashboardMetricSet, string> = {
  revenue: "Revenue",
  net_profit: "Net Profit",
  profit_margin: "Profit Margin",
  tacos: "TACOS",
  acos: "ACOS",
  refund_rate: "Refund Rate",
  ad_spend: "Ad Spend",
  roas: "ROAS",
  avg_order_value: "AOV",
  orders_count: "Orders",
  units_sold: "Units Sold",
  ctr: "CTR",
  cpc: "CPC",
  ad_sales: "Ad Sales",
  fees: "Fees",
  taxes: "Taxes",
  reimbursements: "Reimbursements",
  refunds: "Refunds",
  cogs: "COGS",
  profit_per_order: "Profit / Order",
};

function buildTrustWarnings(summary: DashboardSummary) {
  return trustPriorityMetricKeys
    .map((metricKey) => summary.metric_trust.find((item) => item.metric_key === metricKey))
    .filter(
      (
        item,
      ): item is NonNullable<typeof item> => item !== undefined && item.status !== "complete",
    )
    .slice(0, 4)
    .map((item) => {
      const severity =
        item.status === "missing" ? "critical" : item.status === "limited" ? "warning" : "info";
      return {
        metricKey: item.metric_key,
        label: metricLabels[item.metric_key],
        severity,
        headline:
          item.status === "missing"
            ? `${metricLabels[item.metric_key]} is not fully trustworthy yet`
            : item.status === "limited"
              ? `${metricLabels[item.metric_key]} is based on thin coverage`
              : `${metricLabels[item.metric_key]} is only partially covered`,
        body: item.note,
      };
    });
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [insights, setInsights] = useState<DashboardInsightsResponse | null>(null);
  const [bounds, setBounds] = useState<DateBounds | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [metricCatalog, setMetricCatalog] = useState<MetricCatalogItem[]>([]);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [loading, setLoading] = useState(true);
  const [loadingDemo, setLoadingDemo] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadBounds = useEffectEvent(async () => {
    if (!getToken()) {
      return;
    }

    try {
      const [profileData, boundsData, metricCatalogData] = await Promise.all([
        api.getMe(),
        api.getDateBounds(),
        api.getMetricCatalog(),
      ]);
      setProfile(profileData);
      setMetricCatalog(metricCatalogData);
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
  const configuredHeadlineMetrics = metricCatalog
    .filter((item) => item.dashboard_slot === "headline" && item.visible_by_default)
    .slice(0, 6);
  const configuredSupportingMetrics = metricCatalog
    .filter((item) => item.dashboard_slot === "supporting" && item.visible_by_default)
    .slice(0, 6);
  const renderedHeadlineMetrics =
    configuredHeadlineMetrics.length > 0 ? configuredHeadlineMetrics : headlineMetrics;
  const renderedSupportingMetrics =
    configuredSupportingMetrics.length > 0 ? configuredSupportingMetrics : supportingMetrics;
  const metricTrustMap = new Map(summary?.metric_trust.map((item) => [item.metric_key, item]) ?? []);
  const trustWarnings = summary ? buildTrustWarnings(summary) : [];

  const handleLoadDemoStore = async () => {
    setLoadingDemo(true);
    setError(null);
    try {
      await api.loadDemoStore();
      const boundsData = await api.getDateBounds();
      setBounds(boundsData);
      setStartDate(boundsData.default_start_date);
      setEndDate(boundsData.default_end_date);
      setLoading(true);
    } catch (demoError) {
      setError(demoError instanceof Error ? demoError.message : "Failed to load demo store.");
    } finally {
      setLoadingDemo(false);
    }
  };
  const getMetricType = (
    item:
      | MetricCatalogItem
      | {
          type: "currency" | "percent" | "number" | "ratio";
        },
  ) => ("format" in item ? item.format : item.type);

  return (
    <AppShell title="Dashboard">
      <div className="space-y-6">
        <div className="polaris-card grid gap-4 p-6 xl:grid-cols-[1.1fr_0.9fr]">
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
            <div className="mt-5">
              <Button variant="outline" onClick={() => void handleLoadDemoStore()} disabled={loadingDemo}>
                {loadingDemo ? "Loading demo..." : "Load demo store"}
              </Button>
            </div>
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
            <div className="h-40 animate-pulse rounded-lg border border-border bg-card" />
          )}
        </div>

        {loading ? (
          <>
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {Array.from({ length: 6 }).map((_, index) => (
                <div
                  key={index}
                  className="h-48 animate-pulse rounded-lg border border-border bg-card"
                />
              ))}
            </div>
            <div className="h-96 animate-pulse rounded-lg border border-border bg-card" />
          </>
        ) : error ? (
          <EmptyState title="Dashboard unavailable" description={error} />
        ) : !summary || !hasData ? (
          <div className="space-y-4">
            <EmptyState
              title="Upload your first reports"
              description="Once you upload order and ads CSV files, this dashboard will unlock date-based analysis, growth comparisons, and seller insights."
            />
            <div className="flex justify-center">
              <Button onClick={() => void handleLoadDemoStore()} disabled={loadingDemo}>
                {loadingDemo ? "Loading demo..." : "Load demo store instead"}
              </Button>
            </div>
          </div>
        ) : (
          <>
            {trustWarnings.length > 0 ? (
              <section className="polaris-card p-5">
                <div className="mb-4">
                  <p className="text-xs font-semibold uppercase text-muted-foreground">
                    Trust flags
                  </p>
                  <h2 className="font-display text-2xl font-semibold">
                    Important metrics with incomplete backing data
                  </h2>
                  <p className="mt-2 text-sm text-muted-foreground">
                    These metrics still render, but they should be read with caution until the
                    missing source data is uploaded for this date range.
                  </p>
                </div>
                <div className="grid gap-3 md:grid-cols-2">
                  {trustWarnings.map((warning) => (
                    <article
                      key={warning.metricKey}
                      className="rounded-lg border border-border bg-[var(--surface-subdued)] p-4"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-sm font-semibold">{warning.label}</p>
                        <span
                          className={`polaris-badge ${
                            warning.severity === "critical"
                              ? "bg-rose-100 text-rose-800"
                              : warning.severity === "warning"
                                ? "bg-amber-100 text-amber-800"
                                : "bg-sky-100 text-sky-800"
                          }`}
                        >
                          {warning.severity === "critical"
                            ? "Missing"
                            : warning.severity === "warning"
                              ? "Limited"
                              : "Partial"}
                        </span>
                      </div>
                      <p className="mt-3 font-display text-xl font-semibold">{warning.headline}</p>
                      <p className="mt-2 text-sm leading-6 text-muted-foreground">
                        {warning.body}
                      </p>
                    </article>
                  ))}
                </div>
              </section>
            ) : null}

            <section className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
              <div className="polaris-card p-5">
                <div className="mb-4">
                  <p className="text-xs font-semibold uppercase text-muted-foreground">
                    Range coverage
                  </p>
                  <h2 className="font-display text-2xl font-semibold">
                    How complete this window is
                  </h2>
                </div>
                <div className="grid gap-3 md:grid-cols-3">
                  {summary.range_coverage.map((coverage) => (
                    <div
                      key={coverage.key}
                      className="rounded-lg border border-border bg-[var(--surface-subdued)] p-4"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-sm font-semibold">{coverage.label}</p>
                        <span
                          className={`polaris-badge ${
                            coverage.status === "complete"
                              ? "bg-emerald-100 text-emerald-800"
                              : coverage.status === "partial"
                                ? "bg-amber-100 text-amber-800"
                                : coverage.status === "limited"
                                  ? "bg-orange-100 text-orange-800"
                                  : "bg-slate-100 text-slate-700"
                          }`}
                        >
                          {coverage.coverage_pct.toFixed(0)}%
                        </span>
                      </div>
                      <p className="mt-3 font-display text-2xl font-semibold">
                        {coverage.covered_days}/{coverage.expected_days} days
                      </p>
                      <p className="mt-2 text-xs leading-5 text-muted-foreground">
                        {coverage.latest_data_date
                          ? `Latest raw data date ${coverage.latest_data_date}`
                          : "No source rows in this selected window yet"}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="polaris-card p-5">
                <div className="mb-4">
                  <p className="text-xs font-semibold uppercase text-muted-foreground">
                    Data freshness
                  </p>
                  <h2 className="font-display text-2xl font-semibold">
                    Source health at a glance
                  </h2>
                </div>
                <div className="space-y-3">
                  {summary.data_sources.map((source) => (
                    <div
                      key={source.key}
                      className="rounded-lg border border-border bg-[var(--surface-subdued)] p-4"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-sm font-semibold">{source.name}</p>
                        <span
                          className={`polaris-badge ${
                            source.active
                              ? "bg-emerald-100 text-emerald-800"
                              : "bg-slate-100 text-slate-700"
                          }`}
                        >
                          {source.active ? "Fresh" : "Waiting"}
                        </span>
                      </div>
                      <p className="mt-2 text-xs text-muted-foreground">
                        {source.last_refresh_at
                          ? `Last refresh ${new Date(source.last_refresh_at).toLocaleString()}`
                          : "No completed import or sync yet"}
                      </p>
                      <p className="mt-1 text-[11px] text-muted-foreground">
                        {source.active
                          ? "Included in trust checks where relevant."
                          : "This source is not contributing data yet."}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {renderedHeadlineMetrics.map((item) => (
                <MetricCard
                  key={item.key}
                  label={item.label}
                  metric={summary.metrics[item.key]}
                  type={getMetricType(item)}
                  description={item.description}
                  lowerIsBetter={
                    "polarity" in item ? item.polarity === "lower_is_better" : item.lowerIsBetter
                  }
                  trust={metricTrustMap.get(item.key)}
                />
              ))}
            </div>

            <section className="polaris-card p-6">
              <div className="mb-5">
                <p className="text-xs font-semibold uppercase text-muted-foreground">
                  Supporting metrics
                </p>
                <h2 className="font-display text-2xl font-semibold">
                  Additional performance markers that matter
                </h2>
              </div>
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {renderedSupportingMetrics.map((metric) => (
                  <div
                    key={metric.key}
                    className="rounded-lg border border-border bg-[var(--surface-subdued)] p-5"
                  >
                    <p className="text-xs font-semibold uppercase text-muted-foreground">
                      {metric.label}
                    </p>
                    <p className="mt-3 font-display text-3xl font-semibold">
                      {getMetricType(metric) === "ratio"
                        ? `${summary.metrics[metric.key].current.toFixed(2)}x`
                        : getMetricType(metric) === "percent"
                          ? `${summary.metrics[metric.key].current.toFixed(2)}%`
                          : getMetricType(metric) === "currency"
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
                    {metricTrustMap.get(metric.key) ? (
                      <div className="mt-3 rounded-lg border border-border/70 bg-card px-3 py-2">
                        <p className="text-[11px] font-medium text-muted-foreground">
                          Powered by {metricTrustMap.get(metric.key)?.powered_by.join(" + ")}
                        </p>
                        <p className="mt-1 text-[11px] text-muted-foreground">
                          Coverage {metricTrustMap.get(metric.key)?.coverage_pct.toFixed(0)}%
                        </p>
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            </section>

            <ProfitChart data={trends} metricTrust={summary.metric_trust} />
            {insights ? <InsightsPanel data={insights} /> : null}
          </>
        )}
      </div>
    </AppShell>
  );
}
