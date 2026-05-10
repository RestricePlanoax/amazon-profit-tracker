import type { DashboardInsightsResponse } from "@/lib/types";

type InsightsPanelProps = {
  data: DashboardInsightsResponse;
};

const severityStyles = {
  positive: "bg-emerald-100 text-emerald-800",
  warning: "bg-amber-100 text-amber-800",
  neutral: "bg-slate-100 text-slate-800",
};

export function InsightsPanel({ data }: InsightsPanelProps) {
  return (
    <section className="glass-panel rounded-[2rem] border border-border/70 bg-card/85 p-6">
      <div className="mb-6 flex flex-col gap-2">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-muted-foreground">
          Seller insights
        </p>
        <h2 className="font-display text-2xl font-semibold">
          Metric-led actions to improve profit quality
        </h2>
        <p className="text-sm leading-7 text-muted-foreground">{data.summary}</p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {data.insights.map((insight) => (
          <article
            key={insight.title}
            className="rounded-[1.5rem] border border-border/70 bg-white/75 p-5"
          >
            <div className="mb-3">
              <span
                className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${severityStyles[insight.severity]}`}
              >
                {insight.severity}
              </span>
            </div>
            <h3 className="font-display text-xl font-semibold">{insight.title}</h3>
            <p className="mt-3 text-sm leading-7 text-muted-foreground">{insight.body}</p>
          </article>
        ))}
      </div>

      <div className="mt-6 rounded-[1.5rem] border border-dashed border-border bg-accent/45 p-4 text-sm text-muted-foreground">
        Recommendation scaffolding is ready for a future LLM call: the backend now prepares a prompt
        template plus metric knowledge chunks so we can later plug in retrieval and tailored seller recommendations.
      </div>
    </section>
  );
}
