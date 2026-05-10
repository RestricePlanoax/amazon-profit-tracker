"use client";

import { useMemo, useState } from "react";
import { ArrowDown, ArrowUp, Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import type { ProductProfitability } from "@/lib/types";
import { formatCurrency, formatMetricValue } from "@/lib/utils";

type ProductsTableProps = {
  products: ProductProfitability[];
  onRefresh: () => Promise<void>;
};

type SortDirection = "asc" | "desc";

export function ProductsTable({ products, onRefresh }: ProductsTableProps) {
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [savingSku, setSavingSku] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const sortedProducts = useMemo(() => {
    const items = [...products];
    items.sort((left, right) => {
      const delta = left.net_profit - right.net_profit;
      return sortDirection === "asc" ? delta : -delta;
    });
    return items;
  }, [products, sortDirection]);

  const handleSave = async (sku: string) => {
    const rawValue = drafts[sku];
    const numericValue = Number(rawValue);

    if (Number.isNaN(numericValue) || numericValue < 0) {
      setError("COGS must be a non-negative number.");
      return;
    }

    setSavingSku(sku);
    setError(null);

    try {
      await api.updateProductCogs(sku, numericValue);
      await onRefresh();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Failed to save COGS.");
    } finally {
      setSavingSku(null);
    }
  };

  return (
    <section className="glass-panel rounded-[2rem] border border-border/70 bg-card/85 p-6">
      <div className="mb-5 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h2 className="font-display text-2xl font-semibold">Profitability by SKU</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Rows with negative profit margin are highlighted so loss-making products stand out.
          </p>
        </div>

        <Button
          variant="outline"
          onClick={() =>
            setSortDirection((current) => (current === "desc" ? "asc" : "desc"))
          }
        >
          {sortDirection === "desc" ? (
            <>
              <ArrowDown className="h-4 w-4" />
              Sort by profit descending
            </>
          ) : (
            <>
              <ArrowUp className="h-4 w-4" />
              Sort by profit ascending
            </>
          )}
        </Button>
      </div>

      {error ? (
        <div className="mb-4 rounded-2xl border border-danger/20 bg-danger/8 px-4 py-3 text-sm text-danger">
          {error}
        </div>
      ) : null}

      <div className="overflow-x-auto rounded-[1.75rem] border border-border/80 bg-white/75">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-accent/70 text-muted-foreground">
            <tr>
              {[
                "SKU",
                "Units",
                "Revenue",
                "Ad Spend",
                "ACOS",
                "Fees",
                "Refund",
                "COGS",
                "Net Profit",
                "Profit / Unit",
                "Margin",
                "COGS / Unit",
              ].map((header) => (
                <th key={header} className="px-4 py-3 font-semibold">
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sortedProducts.map((product) => {
              const negativeMargin = product.profit_margin < 0;

              return (
                <tr
                  key={product.sku}
                  className={`border-t border-border/70 ${negativeMargin ? "bg-rose-50/85" : ""}`}
                >
                  <td className="px-4 py-4">
                    <div>
                      <p className="font-semibold">{product.sku}</p>
                      <p className="text-xs text-muted-foreground">{product.name ?? "Unnamed product"}</p>
                    </div>
                  </td>
                  <td className="px-4 py-4">{product.units_sold}</td>
                  <td className="px-4 py-4">{formatCurrency(product.revenue)}</td>
                  <td className="px-4 py-4">{formatCurrency(product.ad_spend)}</td>
                  <td className="px-4 py-4">{formatMetricValue(product.acos, "percent")}</td>
                  <td className="px-4 py-4">{formatCurrency(product.fees)}</td>
                  <td className="px-4 py-4">{formatCurrency(product.refund)}</td>
                  <td className="px-4 py-4">{formatCurrency(product.cogs)}</td>
                  <td className="px-4 py-4 font-semibold">{formatCurrency(product.net_profit)}</td>
                  <td className="px-4 py-4">{formatCurrency(product.profit_per_unit)}</td>
                  <td className={`px-4 py-4 font-semibold ${negativeMargin ? "text-danger" : "text-primary"}`}>
                    {formatMetricValue(product.profit_margin, "percent")}
                  </td>
                  <td className="px-4 py-4">
                    <div className="flex min-w-[180px] items-center gap-2">
                      <Input
                        type="number"
                        min="0"
                        step="0.01"
                        value={drafts[product.sku] ?? product.cogs_per_unit.toString()}
                        onChange={(event) =>
                          setDrafts((current) => ({
                            ...current,
                            [product.sku]: event.target.value,
                          }))
                        }
                      />
                      <Button
                        size="icon"
                        onClick={() => void handleSave(product.sku)}
                        disabled={savingSku === product.sku}
                      >
                        <Save className="h-4 w-4" />
                      </Button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
