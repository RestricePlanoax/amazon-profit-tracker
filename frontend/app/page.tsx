import Link from "next/link";
import {
  ArrowRight,
  BadgeIndianRupee,
  ChartColumnBig,
  CheckCircle2,
  LineChart,
  ShoppingCart,
  Sparkles,
  Wallet,
} from "lucide-react";

const features = [
  {
    title: "SKU-level profit",
    description: "See which products actually make money after ads, fees, refunds, and COGS.",
    icon: ShoppingCart,
  },
  {
    title: "Ad spend leakage",
    description: "Spot SKUs where ad spend quietly eats margin before the month is over.",
    icon: ChartColumnBig,
  },
  {
    title: "Fees and refunds",
    description: "Bring Amazon fees and refund drag into the same view as sales performance.",
    icon: Wallet,
  },
  {
    title: "Daily profit dashboard",
    description: "Track revenue and true profit day by day instead of relying on topline sales.",
    icon: BadgeIndianRupee,
  },
];

export default function Home() {
  return (
    <main className="min-h-screen overflow-hidden bg-background">
      <section className="mx-auto flex w-full max-w-7xl flex-col px-4 py-4 sm:px-6 lg:px-8">
        <header className="ds-card z-10 flex items-center justify-between gap-3 px-4 py-3 sm:px-5">
          <Link href="/" className="relative flex items-center gap-3">
            <span className="grid h-10 w-10 place-items-center rounded-2xl bg-foreground text-sm font-black text-white shadow-sm">
              AP
            </span>
            <span>
              <span className="block text-sm font-black leading-5 text-foreground">
                Amazon Seller
              </span>
              <span className="block text-xs font-semibold text-muted-foreground">
                Profit Tracker
              </span>
            </span>
          </Link>
          <div className="relative flex items-center gap-2">
            <Link
              href="/login"
              className="rounded-2xl px-4 py-2 text-sm font-bold text-foreground transition hover:bg-muted"
            >
              Login
            </Link>
            <Link
              href="/signup"
              className="whitespace-nowrap rounded-2xl bg-foreground px-4 py-2 text-sm font-bold text-white shadow-sm transition hover:-translate-y-0.5 hover:bg-primary"
            >
              Sign up
            </Link>
          </div>
        </header>

        <section className="hero-shell mt-5 px-5 py-8 sm:px-8 lg:px-10 lg:py-12">
          <div className="relative z-10 grid items-center gap-10 lg:grid-cols-[0.96fr_1.04fr]">
            <div className="space-y-7">
              <div className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-2 text-[11px] font-black uppercase tracking-[0.12em] text-emerald-100 backdrop-blur sm:text-xs">
                <Sparkles className="h-4 w-4 text-[var(--gold)]" />
                Seller-grade profit intelligence
              </div>

              <div className="space-y-5">
                <h1 className="font-display max-w-3xl text-4xl font-black leading-[0.95] text-white sm:text-6xl lg:text-7xl">
                  Know your real Amazon profit, not just revenue
                </h1>
                <p className="max-w-2xl text-base leading-8 text-white/72 sm:text-lg">
                  Upload order and ad CSV reports, connect Amazon when ready, and
                  turn messy seller data into margin, TACOS, refunds, and SKU-level decisions.
                </p>
              </div>

              <div className="flex flex-col gap-3 sm:flex-row">
                <Link
                  href="/signup"
                  className="inline-flex items-center justify-center gap-2 rounded-2xl bg-[var(--gold)] px-5 py-3 text-base font-black text-foreground shadow-lg shadow-black/20 transition hover:-translate-y-0.5"
                >
                  Start free MVP
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  href="/login"
                  className="inline-flex items-center justify-center rounded-2xl border border-white/18 bg-white/10 px-5 py-3 text-base font-bold text-white backdrop-blur transition hover:bg-white/16"
                >
                  Login
                </Link>
              </div>

              <div className="grid gap-3 text-sm text-white/78 sm:grid-cols-3">
                {["No SP-API needed to start", "CSV reports in minutes", "SKU profit clarity"].map(
                  (item) => (
                    <div key={item} className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-emerald-300" />
                      <span>{item}</span>
                    </div>
                  ),
                )}
              </div>
            </div>

            <div className="dashboard-frame p-3 sm:p-4">
              <div className="rounded-[22px] border border-border bg-[#fbf8f1] p-4">
                <div className="mb-4 flex items-center justify-between gap-3">
                  <div>
                    <p className="text-xs font-black uppercase tracking-[0.16em] text-muted-foreground">
                      Profit command center
                    </p>
                    <p className="mt-1 text-xl font-black text-foreground">April snapshot</p>
                  </div>
                  <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-black text-emerald-800">
                    Synced
                  </span>
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="rounded-3xl bg-foreground p-5 text-white">
                    <p className="text-xs font-bold uppercase tracking-[0.14em] text-white/55">
                      Revenue
                    </p>
                    <p className="mt-4 text-4xl font-black">₹4,500</p>
                    <p className="mt-2 text-sm text-white/62">From uploaded orders</p>
                  </div>
                  <div className="rounded-3xl border border-emerald-200 bg-emerald-50 p-5">
                    <p className="text-xs font-bold uppercase tracking-[0.14em] text-emerald-800/70">
                      Net profit
                    </p>
                    <p className="mt-4 text-4xl font-black text-primary">₹1,075</p>
                    <p className="mt-2 text-sm text-emerald-950/60">After ads, fees, COGS</p>
                  </div>
                </div>

                <div className="mt-3 grid gap-3 md:grid-cols-[0.95fr_1.05fr]">
                  <div className="rounded-3xl border border-border bg-card p-4">
                    <p className="text-sm font-black">SKU profitability</p>
                    <div className="mt-4 space-y-3">
                      {[
                        ["SKU-001", "₹550", "72%"],
                        ["SKU-002", "₹525", "48%"],
                        ["SKU-009", "-₹140", "-8%"],
                      ].map(([sku, profit, margin]) => (
                        <div key={sku} className="flex items-center justify-between gap-3">
                          <div>
                            <p className="text-sm font-bold">{sku}</p>
                            <p className="text-xs text-muted-foreground">{margin} margin</p>
                          </div>
                          <p
                            className={`text-sm font-black ${
                              profit.startsWith("-") ? "text-rose-600" : "text-primary"
                            }`}
                          >
                            {profit}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="rounded-3xl border border-border bg-card p-4">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-black">Revenue vs profit</p>
                      <LineChart className="h-4 w-4 text-primary" />
                    </div>
                    <div className="mt-5 flex h-32 items-end gap-2">
                      {[38, 58, 46, 72, 54, 84, 68].map((height, index) => (
                        <div key={height + index} className="flex flex-1 flex-col items-center gap-2">
                          <div className="flex h-24 w-full items-end rounded-full bg-muted">
                            <div
                              className="w-full rounded-full bg-primary"
                              style={{ height: `${height}%` }}
                            />
                          </div>
                          <span className="text-[10px] font-bold text-muted-foreground">
                            D{index + 1}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="relative z-10 grid gap-4 py-5 sm:grid-cols-2 lg:grid-cols-4">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <article key={feature.title} className="ds-card p-5">
                <div className="relative">
                  <div className="mb-5 inline-flex rounded-2xl bg-[var(--surface-selected)] p-3 text-primary">
                    <Icon className="h-5 w-5" />
                  </div>
                  <h2 className="font-display text-xl font-black">{feature.title}</h2>
                  <p className="mt-2 text-sm leading-7 text-muted-foreground">
                    {feature.description}
                  </p>
                </div>
              </article>
            );
          })}
        </section>

        <section className="ds-card mb-8 p-5 sm:p-6">
          <div className="relative grid gap-5 lg:grid-cols-3">
            {[
              ["TACOS and ACOS", "See if ad growth is profitable, not just loud."],
              ["Refund pressure", "Catch SKUs where returns quietly destroy contribution."],
              ["COGS control", "Update costs and instantly recompute true margin."],
            ].map(([title, body]) => (
              <div key={title} className="rounded-3xl border border-border bg-[var(--surface-subdued)] p-5">
                <p className="text-sm font-black text-foreground">{title}</p>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">{body}</p>
              </div>
            ))}
          </div>
        </section>
      </section>
    </main>
  );
}
