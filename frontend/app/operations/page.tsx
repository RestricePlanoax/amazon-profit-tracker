"use client";

import { useEffect, useEffectEvent, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { EmptyState } from "@/components/EmptyState";
import { api } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type {
  AdAnalysisResponse,
  DashboardSummary,
  DateBounds,
  ReimbursementsResponse,
  ReturnAnalysisResponse,
  StorageAnalysisResponse,
} from "@/lib/types";

const currencyFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 2,
});

export default function OperationsPage() {
  const [returnsData, setReturnsData] = useState<ReturnAnalysisResponse | null>(null);
  const [reimbursementsData, setReimbursementsData] = useState<ReimbursementsResponse | null>(null);
  const [storageData, setStorageData] = useState<StorageAnalysisResponse | null>(null);
  const [adData, setAdData] = useState<AdAnalysisResponse | null>(null);
  const [bounds, setBounds] = useState<DateBounds | null>(null);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadOperations = async () => {
    if (!getToken()) {
      return;
    }
    try {
      setError(null);
      const boundsResponse = await api.getDateBounds();
      const [returnResponse, reimbursementResponse, storageResponse, adResponse, summaryResponse] = await Promise.all([
        api.getReturnAnalysis(),
        api.getReimbursements(),
        api.getStorageAnalysis(),
        api.getAdAnalysis(),
        api.getSummary(boundsResponse.default_start_date, boundsResponse.default_end_date),
      ]);
      setBounds(boundsResponse);
      setReturnsData(returnResponse);
      setReimbursementsData(reimbursementResponse);
      setStorageData(storageResponse);
      setAdData(adResponse);
      setSummary(summaryResponse);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load operations analytics.");
    } finally {
      setLoading(false);
    }
  };

  const runInitialLoad = useEffectEvent(async () => {
    await loadOperations();
  });

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void runInitialLoad();
  }, []);

  const sourceMap = new Map(summary?.data_sources.map((source) => [source.key, source]) ?? []);
  const coverageMap = new Map(summary?.range_coverage.map((coverage) => [coverage.key, coverage]) ?? []);
  const operationWarnings = [
    {
      key: "returns",
      label: "Variant return intelligence",
      severity: sourceMap.get("returns")?.active ? "info" : "warning",
      body: sourceMap.get("returns")?.active
        ? "Returns CSVs are active, so variant-level return insights are powered by uploaded return events."
        : "Returns CSVs have not been uploaded yet, so return intelligence will stay thin even if refund rate exists on the dashboard.",
    },
    {
      key: "reimbursements",
      label: "Reimbursement recovery",
      severity: sourceMap.get("reimbursements")?.active ? "info" : "warning",
      body: sourceMap.get("reimbursements")?.active
        ? "Reimbursement cases are being tracked from uploaded recovery data."
        : "No reimbursements CSV has been uploaded yet, so Amazon-owed money may be undercounted.",
    },
    {
      key: "inventory",
      label: "Storage cost intelligence",
      severity: sourceMap.get("inventory")?.active ? "info" : "warning",
      body: sourceMap.get("inventory")?.active
        ? "Inventory snapshots are active, so storage warnings use uploaded stock and fee context."
        : "Inventory CSVs are missing, so storage risk is based on limited or demo-friendly data only.",
    },
    {
      key: "campaigns",
      label: "PPC waste detector",
      severity:
        sourceMap.get("campaigns")?.active || sourceMap.get("ads")?.active ? "info" : "warning",
      body: sourceMap.get("campaigns")?.active
        ? "Campaign metrics CSVs are active, so PPC waste detection is running at campaign level."
        : sourceMap.get("ads")?.active
          ? "Only SKU-level ads data is active, so PPC waste is inferred from aggregates instead of campaign rows."
          : "No ads or campaigns data is active, so PPC waste detection is not trustworthy yet.",
    },
    {
      key: "coverage",
      label: "Orders / ads / settlement coverage",
      severity:
        (coverageMap.get("orders")?.status === "complete" &&
          coverageMap.get("ads")?.status === "complete" &&
          coverageMap.get("settlement")?.status === "complete")
          ? "info"
          : "warning",
      body: bounds
        ? `Current operational window runs from ${bounds.default_start_date} to ${bounds.default_end_date}. Orders ${coverageMap.get("orders")?.coverage_pct.toFixed(0) ?? 0}%, ads ${coverageMap.get("ads")?.coverage_pct.toFixed(0) ?? 0}%, settlements ${coverageMap.get("settlement")?.coverage_pct.toFixed(0) ?? 0}% coverage.`
        : "Coverage information is still loading.",
    },
  ].filter((warning) => warning.severity !== "info" || warning.key === "coverage");

  const returnsSource = sourceMap.get("returns");
  const reimbursementsSource = sourceMap.get("reimbursements");
  const inventorySource = sourceMap.get("inventory");
  const campaignSource = sourceMap.get("campaigns");
  const adsCoverage = coverageMap.get("ads");
  const ordersCoverage = coverageMap.get("orders");
  const settlementCoverage = coverageMap.get("settlement");

  return (
    <AppShell title="Operations Intelligence">
      <div className="space-y-6">
        <section className="polaris-card p-6">
          <p className="text-xs font-semibold uppercase text-muted-foreground">
            Advanced analytics layer
          </p>
          <h1 className="mt-2 font-display text-3xl font-semibold">
            Returns, reimbursements, storage risk, and PPC waste
          </h1>
          {bounds ? (
            <p className="mt-3 text-sm text-muted-foreground">
              Trust checks currently reflect the window from {bounds.default_start_date} to {bounds.default_end_date}.
            </p>
          ) : null}
        </section>

        {loading ? (
          <div className="h-72 animate-pulse rounded-lg border border-border bg-card" />
        ) : error ? (
          <EmptyState title="Operations analytics unavailable" description={error} />
        ) : (
          <div className="grid gap-6">
            {operationWarnings.length > 0 ? (
              <section className="polaris-card p-5">
                <div className="mb-4">
                  <p className="text-xs font-semibold uppercase text-muted-foreground">
                    Operations trust flags
                  </p>
                  <h2 className="font-display text-2xl font-semibold">
                    Sections that need more source data
                  </h2>
                </div>
                <div className="grid gap-3 md:grid-cols-2">
                  {operationWarnings.map((warning) => (
                    <article
                      key={warning.key}
                      className="rounded-lg border border-border bg-[var(--surface-subdued)] p-4"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-sm font-semibold">{warning.label}</p>
                        <span
                          className={`polaris-badge ${
                            warning.severity === "warning"
                              ? "bg-amber-100 text-amber-800"
                              : "bg-sky-100 text-sky-800"
                          }`}
                        >
                          {warning.severity === "warning" ? "Needs data" : "Window check"}
                        </span>
                      </div>
                      <p className="mt-3 text-sm leading-6 text-muted-foreground">{warning.body}</p>
                    </article>
                  ))}
                </div>
              </section>
            ) : null}

            <section className="grid gap-4 xl:grid-cols-2">
              <div className="polaris-card p-6">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <p className="text-xs font-semibold uppercase text-muted-foreground">Variant return intelligence</p>
                  <span
                    className={`polaris-badge ${
                      returnsSource?.active ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"
                    }`}
                  >
                    {returnsSource?.active ? "Returns source live" : "Needs returns CSV"}
                  </span>
                </div>
                <p className="mt-2 text-sm text-muted-foreground">{returnsData?.summary_text}</p>
                <div className="mt-4 space-y-3">
                  {returnsData?.worst_variants.slice(0, 5).map((row) => (
                    <div key={`${row.sku}-${row.variant}`} className="rounded-lg bg-[var(--surface-subdued)] px-4 py-3">
                      <div className="flex items-center justify-between gap-3">
                        <p className="font-semibold">{row.sku} · {row.variant}</p>
                        <p className="text-sm text-rose-700">{row.return_rate.toFixed(1)}% returns</p>
                      </div>
                      <p className="mt-1 text-sm text-muted-foreground">
                        {currencyFormatter.format(row.refund_cost)} refund cost · top reason: {row.top_reason ?? "Unknown"}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="polaris-card p-6">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <p className="text-xs font-semibold uppercase text-muted-foreground">Reimbursement recovery</p>
                  <span
                    className={`polaris-badge ${
                      reimbursementsSource?.active ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"
                    }`}
                  >
                    {reimbursementsSource?.active ? "Recovery source live" : "Needs reimbursements CSV"}
                  </span>
                </div>
                <p className="mt-2 text-sm text-muted-foreground">
                  Amazon owes you {currencyFormatter.format(reimbursementsData?.summary.total_pending_amount ?? 0)} across {reimbursementsData?.summary.open_cases ?? 0} open cases.
                </p>
                <div className="mt-4 space-y-3">
                  {reimbursementsData?.cases.slice(0, 5).map((item) => (
                    <div key={item.id} className="rounded-lg bg-[var(--surface-subdued)] px-4 py-3">
                      <div className="flex items-center justify-between gap-3">
                        <p className="font-semibold">{item.sku}</p>
                        <p>{currencyFormatter.format(item.amount)}</p>
                      </div>
                      <p className="mt-1 text-sm text-muted-foreground">
                        {item.issue_type.replaceAll("_", " ")} · deadline {item.claim_deadline ?? "n/a"} · {item.status}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <section className="grid gap-4 xl:grid-cols-2">
              <div className="polaris-card p-6">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <p className="text-xs font-semibold uppercase text-muted-foreground">Storage cost intelligence</p>
                  <span
                    className={`polaris-badge ${
                      inventorySource?.active ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"
                    }`}
                  >
                    {inventorySource?.active ? "Inventory source live" : "Needs inventory CSV"}
                  </span>
                </div>
                <p className="mt-2 text-sm text-muted-foreground">{storageData?.summary_text}</p>
                <div className="mt-4 space-y-3">
                  {storageData?.slow_moving_inventory.slice(0, 5).map((row) => (
                    <div key={`${row.sku}-${row.days_in_storage}`} className="rounded-lg bg-[var(--surface-subdued)] px-4 py-3">
                      <div className="flex items-center justify-between gap-3">
                        <p className="font-semibold">{row.sku}</p>
                        <p className="text-sm">{row.days_in_storage} days</p>
                      </div>
                      <p className="mt-1 text-sm text-muted-foreground">
                        {row.quantity} units · {row.recommended_action}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="polaris-card p-6">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <p className="text-xs font-semibold uppercase text-muted-foreground">PPC waste detector</p>
                  <div className="flex flex-wrap gap-2">
                    <span
                      className={`polaris-badge ${
                        campaignSource?.active ? "bg-emerald-100 text-emerald-800" : "bg-sky-100 text-sky-800"
                      }`}
                    >
                      {campaignSource?.active ? "Campaign level" : "SKU aggregate"}
                    </span>
                    {adsCoverage ? (
                      <span className="polaris-badge bg-slate-100 text-slate-700">
                        Ads {adsCoverage.coverage_pct.toFixed(0)}%
                      </span>
                    ) : null}
                    {ordersCoverage ? (
                      <span className="polaris-badge bg-slate-100 text-slate-700">
                        Orders {ordersCoverage.coverage_pct.toFixed(0)}%
                      </span>
                    ) : null}
                    {settlementCoverage ? (
                      <span className="polaris-badge bg-slate-100 text-slate-700">
                        Settlements {settlementCoverage.coverage_pct.toFixed(0)}%
                      </span>
                    ) : null}
                  </div>
                </div>
                <p className="mt-2 text-sm text-muted-foreground">{adData?.summary_text}</p>
                <div className="mt-4 space-y-3">
                  {adData?.worst_campaigns.slice(0, 5).map((row) => (
                    <div key={`${row.campaign_id}-${row.sku}`} className="rounded-lg bg-[var(--surface-subdued)] px-4 py-3">
                      <div className="flex items-center justify-between gap-3">
                        <p className="font-semibold">{row.campaign_name}</p>
                        <p className={row.waste_flag ? "text-rose-700" : "text-emerald-700"}>
                          {row.waste_flag ? "Waste risk" : "Healthy"}
                        </p>
                      </div>
                      <p className="mt-1 text-sm text-muted-foreground">
                        {row.sku} · {currencyFormatter.format(row.daily_spend)} daily spend · ROAS {row.roas.toFixed(2)}x
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </section>
          </div>
        )}
      </div>
    </AppShell>
  );
}
