"use client";

import { useEffect, useEffectEvent, useState } from "react";
import { AlertTriangle, BadgeIndianRupee, ShieldAlert, Siren } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { EmptyState } from "@/components/EmptyState";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { ProfitAlertsResponse } from "@/lib/types";

const currencyFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 2,
});

export default function AlertsPage() {
  const [data, setData] = useState<ProfitAlertsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [resolvingId, setResolvingId] = useState<string | null>(null);

  const loadAlerts = async () => {
    if (!getToken()) {
      return;
    }

    try {
      setError(null);
      const response = await api.getProfitAlerts();
      setData(response);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load alerts.");
    } finally {
      setLoading(false);
    }
  };

  const runInitialLoad = useEffectEvent(async () => {
    await loadAlerts();
  });

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void runInitialLoad();
  }, []);

  const handleResolve = async (alertId: string) => {
    setResolvingId(alertId);
    try {
      await api.resolveProfitAlert(alertId);
      await loadAlerts();
    } catch (resolveError) {
      setError(resolveError instanceof Error ? resolveError.message : "Failed to resolve alert.");
    } finally {
      setResolvingId(null);
    }
  };

  const cards = data
    ? [
        {
          label: "Open alerts",
          value: data.summary.total_open,
          icon: AlertTriangle,
        },
        {
          label: "High priority",
          value: data.summary.high_priority,
          icon: Siren,
        },
        {
          label: "Margin drops",
          value: data.summary.margin_drop,
          icon: BadgeIndianRupee,
        },
        {
          label: "Unexpected fees",
          value: data.summary.unexpected_fees,
          icon: ShieldAlert,
        },
      ]
    : [];

  return (
    <AppShell title="Profit Leaks">
      <div className="space-y-6">
        <section className="polaris-card p-6">
          <p className="text-xs font-semibold uppercase text-muted-foreground">
            Leak detection engine
          </p>
          <h1 className="mt-2 font-display text-3xl font-semibold">
            Silent profit loss, surfaced automatically
          </h1>
          <p className="mt-2 max-w-3xl text-sm leading-7 text-muted-foreground">
            These alerts compare current SKU health against recent behavior so sellers can act
            before leakage compounds through ads, refunds, fee shifts, and slow inventory.
          </p>
        </section>

        {loading ? (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {Array.from({ length: 4 }).map((_, index) => (
              <div key={index} className="h-36 animate-pulse rounded-lg border border-border bg-card" />
            ))}
          </div>
        ) : error ? (
          <EmptyState title="Alerts unavailable" description={error} />
        ) : !data || data.alerts.length === 0 ? (
          <EmptyState
            title="No active profit leaks"
            description="Once the analysis engine detects margin drops, fee shocks, ad waste, or storage risk, alerts will appear here."
          />
        ) : (
          <>
            <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              {cards.map((card) => {
                const Icon = card.icon;
                return (
                  <div key={card.label} className="polaris-card p-5">
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <p className="text-xs font-semibold uppercase text-muted-foreground">
                          {card.label}
                        </p>
                        <p className="mt-3 font-display text-4xl font-semibold">{card.value}</p>
                      </div>
                      <div className="rounded-lg bg-[var(--surface-selected)] p-3 text-secondary">
                        <Icon className="h-5 w-5" />
                      </div>
                    </div>
                  </div>
                );
              })}
            </section>

            <section className="polaris-card overflow-hidden">
              <div className="border-b border-border px-6 py-5">
                <h2 className="font-display text-2xl font-semibold">Open alerts</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-muted text-muted-foreground">
                    <tr>
                      <th className="px-5 py-3 font-semibold">Severity</th>
                      <th className="px-5 py-3 font-semibold">Type</th>
                      <th className="px-5 py-3 font-semibold">SKU</th>
                      <th className="px-5 py-3 font-semibold">Message</th>
                      <th className="px-5 py-3 font-semibold">Metric</th>
                      <th className="px-5 py-3 font-semibold">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.alerts.map((alert) => (
                      <tr key={alert.id} className="border-t border-border/70 align-top">
                        <td className="px-5 py-4">
                          <span
                            className={`polaris-badge ${
                              alert.severity === "critical"
                                ? "bg-rose-100 text-rose-800"
                                : alert.severity === "high"
                                  ? "bg-amber-100 text-amber-800"
                                  : "bg-slate-100 text-slate-700"
                            }`}
                          >
                            {alert.severity}
                          </span>
                        </td>
                        <td className="px-5 py-4 capitalize">{alert.alert_type.replaceAll("_", " ")}</td>
                        <td className="px-5 py-4 font-semibold">{alert.sku ?? "Store-wide"}</td>
                        <td className="px-5 py-4 text-muted-foreground">{alert.message}</td>
                        <td className="px-5 py-4 text-muted-foreground">
                          {alert.metric_value !== null ? currencyFormatter.format(alert.metric_value) : "—"}
                        </td>
                        <td className="px-5 py-4">
                          <Button
                            variant="outline"
                            onClick={() => void handleResolve(alert.id)}
                            disabled={resolvingId !== null}
                          >
                            {resolvingId === alert.id ? "Resolving..." : "Resolve"}
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </>
        )}
      </div>
    </AppShell>
  );
}
