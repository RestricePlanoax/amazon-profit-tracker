"use client";

import { useEffect, useEffectEvent, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { DateRangePicker } from "@/components/DateRangePicker";
import { EmptyState } from "@/components/EmptyState";
import { ProductsTable } from "@/components/ProductsTable";
import { api } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { DateBounds, ProductProfitability } from "@/lib/types";

export default function ProductsPage() {
  const [products, setProducts] = useState<ProductProfitability[]>([]);
  const [bounds, setBounds] = useState<DateBounds | null>(null);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [loading, setLoading] = useState(true);
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
      const response = await api.getProducts(startDate, endDate);
      setProducts(response);
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

  return (
    <AppShell title="Products">
      <div className="space-y-6">
        <div className="grid gap-4 rounded-[2rem] border border-border/70 bg-card/85 p-6 glass-panel xl:grid-cols-[1.1fr_0.9fr]">
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
            <div className="h-40 animate-pulse rounded-[1.5rem] border border-border bg-white/70" />
          )}
        </div>

        {loading ? (
          <div className="h-96 animate-pulse rounded-[2rem] border border-border bg-card/75" />
        ) : error ? (
          <EmptyState title="Products unavailable" description={error} />
        ) : products.length === 0 ? (
          <EmptyState
            title="No SKU data yet"
            description="Once you upload order or ad reports, SKU profitability will appear here."
          />
        ) : (
          <ProductsTable products={products} onRefresh={loadProducts} />
        )}
      </div>
    </AppShell>
  );
}
