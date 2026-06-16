"use client";

import { useEffect, useEffectEvent, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { DateRangePicker } from "@/components/DateRangePicker";
import { EmptyState } from "@/components/EmptyState";
import { ProductsTable } from "@/components/ProductsTable";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { DashboardSummary, DateBounds, ProductProfitability } from "@/lib/types";

const productTrustMetricKeys = ["net_profit", "profit_margin", "ad_spend", "acos", "refund_rate"] as const;

export default function ProductsPage() {
  const [products, setProducts] = useState<ProductProfitability[]>([]);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [bounds, setBounds] = useState<DateBounds | null>(null);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [loading, setLoading] = useState(true);
  const [cogsFile, setCogsFile] = useState<File | null>(null);
  const [bulkCogsStatus, setBulkCogsStatus] = useState<string | null>(null);
  const [uploadingCogs, setUploadingCogs] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadBounds = useEffectEvent(async () => {
    if (!getToken()) {
      return;
    }

    try {
      const response = await api.getDateBounds();
      setBounds(response);
      setStartDate(response.default_start_date);
      setEndDate(response.default_end_date);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load products.");
      setLoading(false);
    }
  });

  const loadProducts = async () => {
    if (!getToken() || !startDate || !endDate) {
      return;
    }

    try {
      setError(null);
      const [productsResponse, summaryResponse] = await Promise.all([
        api.getProducts(startDate, endDate),
        api.getSummary(startDate, endDate),
      ]);
      setProducts(productsResponse);
      setSummary(summaryResponse);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load products.");
    } finally {
      setLoading(false);
    }
  };

  const runInitialLoad = useEffectEvent(async () => {
    await loadProducts();
  });

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadBounds();
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void runInitialLoad();
  }, [startDate, endDate]);

  const handleBulkCogsUpload = async () => {
    if (!cogsFile) {
      setBulkCogsStatus("Choose a COGS CSV first.");
      return;
    }
    setUploadingCogs(true);
    setBulkCogsStatus(null);
    try {
      const result = await api.bulkUploadCogs(cogsFile);
      setBulkCogsStatus(
        `${result.products_created} created, ${result.products_updated} updated, ${result.rows_skipped} skipped.`,
      );
      setCogsFile(null);
      setLoading(true);
      await loadProducts();
    } catch (uploadError) {
      setBulkCogsStatus(uploadError instanceof Error ? uploadError.message : "COGS upload failed.");
    } finally {
      setUploadingCogs(false);
    }
  };

  const trustWarnings =
    summary?.metric_trust
      .filter(
        (item) =>
          productTrustMetricKeys.includes(item.metric_key as (typeof productTrustMetricKeys)[number]) &&
          item.status !== "complete",
      )
      .slice(0, 3) ?? [];
  const tableTrustMetrics =
    summary?.metric_trust.filter((item) =>
      ["net_profit", "profit_margin", "ad_spend", "acos"].includes(item.metric_key),
    ) ?? [];

  return (
    <AppShell title="Products">
      <div className="space-y-6">
        <div className="polaris-card grid gap-4 p-6 xl:grid-cols-[1.1fr_0.9fr]">
          <div>
            <h1 className="font-display text-3xl font-semibold">SKU profitability</h1>
            <p className="mt-2 text-sm leading-7 text-muted-foreground">
              Compare net profit, ad efficiency, refund pressure, and contribution per unit
              across your catalog for any calendar range from 2024 onward.
            </p>
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

        <section className="polaris-card p-5">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h2 className="font-display text-2xl font-semibold">Bulk update COGS</h2>
              <p className="mt-1 text-sm leading-6 text-muted-foreground">
                Upload a CSV with columns <span className="font-semibold">sku,name,cogs</span> to update
                product costs and recompute profit instantly.
              </p>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
              <input
                type="file"
                accept=".csv,text/csv"
                onChange={(event) => setCogsFile(event.target.files?.[0] ?? null)}
                className="text-sm text-muted-foreground file:mr-4 file:rounded-2xl file:border file:border-primary file:bg-primary file:px-4 file:py-2 file:text-sm file:font-black file:text-primary-foreground"
              />
              <Button onClick={() => void handleBulkCogsUpload()} disabled={uploadingCogs}>
                {uploadingCogs ? "Uploading..." : "Upload COGS"}
              </Button>
            </div>
          </div>
          {bulkCogsStatus ? (
            <p className="mt-4 rounded-2xl border border-border bg-[var(--surface-subdued)] px-4 py-3 text-sm text-muted-foreground">
              {bulkCogsStatus}
            </p>
          ) : null}
        </section>

        {trustWarnings.length > 0 ? (
          <section className="polaris-card p-5">
            <div className="mb-4">
              <p className="text-xs font-semibold uppercase text-muted-foreground">
                Product trust flags
              </p>
              <h2 className="font-display text-2xl font-semibold">
                SKU rankings are using incomplete source coverage
              </h2>
              <p className="mt-2 text-sm text-muted-foreground">
                Profitability is still useful here, but some metrics are partial for the selected date range.
              </p>
            </div>
            <div className="grid gap-3 md:grid-cols-3">
              {trustWarnings.map((warning) => (
                <article
                  key={warning.metric_key}
                  className="rounded-lg border border-border bg-[var(--surface-subdued)] p-4"
                >
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-semibold">{warning.metric_key.replaceAll("_", " ")}</p>
                    <span
                      className={`polaris-badge ${
                        warning.status === "missing"
                          ? "bg-rose-100 text-rose-800"
                          : warning.status === "limited"
                            ? "bg-amber-100 text-amber-800"
                            : "bg-sky-100 text-sky-800"
                      }`}
                    >
                      {warning.status}
                    </span>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-muted-foreground">{warning.note}</p>
                </article>
              ))}
            </div>
          </section>
        ) : null}

        {loading ? (
          <div className="h-96 animate-pulse rounded-lg border border-border bg-card" />
        ) : error ? (
          <EmptyState title="Products unavailable" description={error} />
        ) : products.length === 0 ? (
          <EmptyState
            title="No SKU data yet"
            description="Once you upload order or ad reports, SKU profitability will appear here."
          />
        ) : (
          <ProductsTable products={products} onRefresh={loadProducts} trustMetrics={tableTrustMetrics} />
        )}
      </div>
    </AppShell>
  );
}
