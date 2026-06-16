"use client";

import { useEffect, useEffectEvent, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { EmptyState } from "@/components/EmptyState";
import { api } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { DailyInsightsResponse } from "@/lib/types";

export default function BriefingPage() {
  const [data, setData] = useState<DailyInsightsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadBriefing = async () => {
    if (!getToken()) {
      return;
    }

    try {
      setError(null);
      const response = await api.getDailyInsights();
      setData(response);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load briefing.");
    } finally {
      setLoading(false);
    }
  };

  const runInitialLoad = useEffectEvent(async () => {
    await loadBriefing();
  });

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void runInitialLoad();
  }, []);

  return (
    <AppShell title="Daily Briefing">
      <div className="space-y-6">
        <section className="polaris-card p-6">
          <p className="text-xs font-semibold uppercase text-muted-foreground">
            Daily AI seller advisor
          </p>
          <h1 className="mt-2 font-display text-3xl font-semibold">
            Decisions first, dashboard second
          </h1>
          <p className="mt-2 max-w-3xl text-sm leading-7 text-muted-foreground">
            This briefing compresses the day into the most important leak, the best and worst
            performers, and the actions worth taking immediately.
          </p>
        </section>

        {loading ? (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {Array.from({ length: 4 }).map((_, index) => (
              <div key={index} className="h-36 animate-pulse rounded-lg border border-border bg-card" />
            ))}
          </div>
        ) : error ? (
          <EmptyState title="Briefing unavailable" description={error} />
        ) : !data ? (
          <EmptyState title="No briefing yet" description="Run the analysis engine by uploading data or loading the demo store." />
        ) : (
          <>
            <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              {[
                { label: "Biggest leak", value: data.biggest_profit_leak ?? "No open leak" },
                { label: "Worst SKU today", value: data.worst_sku_today ?? "No SKU yet" },
                { label: "Best SKU today", value: data.best_sku_today ?? "No SKU yet" },
                {
                  label: "Recommended actions",
                  value: data.recommended_actions.length > 0 ? `${data.recommended_actions.length} actions` : "No actions yet",
                },
              ].map((card) => (
                <div key={card.label} className="polaris-card p-5">
                  <p className="text-xs font-semibold uppercase text-muted-foreground">{card.label}</p>
                  <p className="mt-3 text-lg font-semibold leading-7">{card.value}</p>
                </div>
              ))}
            </section>

            <section className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
              <div className="polaris-card p-6">
                <p className="text-xs font-semibold uppercase text-muted-foreground">
                  Recommended actions
                </p>
                <div className="mt-4 space-y-3">
                  {data.recommended_actions.length > 0 ? (
                    data.recommended_actions.map((action) => (
                      <div key={action} className="rounded-lg bg-[var(--surface-subdued)] px-4 py-3 text-sm font-medium">
                        {action}
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-muted-foreground">No actions generated yet.</p>
                  )}
                </div>
              </div>

              <div className="polaris-card p-6">
                <p className="text-xs font-semibold uppercase text-muted-foreground">
                  Insight feed
                </p>
                <div className="mt-4 space-y-4">
                  {data.insights.map((insight) => (
                    <article key={insight.id} className="rounded-lg border border-border bg-card p-4">
                      <div className="flex items-center justify-between gap-3">
                        <h2 className="font-display text-xl font-semibold">{insight.headline}</h2>
                        <span className="polaris-badge bg-accent text-primary">{insight.priority}</span>
                      </div>
                      <p className="mt-3 text-sm leading-7 text-muted-foreground">{insight.insight_text}</p>
                    </article>
                  ))}
                </div>
              </div>
            </section>
          </>
        )}
      </div>
    </AppShell>
  );
}
