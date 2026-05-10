import Link from "next/link";
import {
  ArrowRight,
  BadgeIndianRupee,
  ChartColumnBig,
  ShoppingCart,
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
    <main className="flex min-h-screen flex-col">
      <section className="mx-auto flex w-full max-w-7xl flex-1 flex-col px-6 py-8 lg:px-10">
        <header className="glass-panel flex items-center justify-between rounded-full border border-border/70 bg-card/75 px-5 py-3">
          <div>
            <p className="font-display text-sm uppercase tracking-[0.3em] text-muted-foreground">
              Amazon Seller Profit Tracker
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="rounded-full px-4 py-2 text-sm font-semibold text-foreground transition hover:bg-accent"
            >
              Login
            </Link>
            <Link
              href="/signup"
              className="rounded-full bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90"
            >
              Sign up
            </Link>
          </div>
        </header>

        <div className="grid flex-1 items-center gap-14 py-16 lg:grid-cols-[1.1fr_0.9fr] lg:py-24">
          <div className="space-y-8">
            <div className="inline-flex items-center rounded-full border border-primary/20 bg-primary/8 px-4 py-2 text-sm font-semibold text-primary">
              CSV-first MVP built for Amazon sellers
            </div>

            <div className="space-y-5">
              <h1 className="font-display max-w-3xl text-5xl leading-tight font-semibold text-foreground md:text-6xl">
                Know your real Amazon profit, not just revenue
              </h1>
              <p className="max-w-2xl text-lg leading-8 text-muted-foreground">
                Upload order and ad CSV reports, track profit by day and by SKU, and
                stop guessing which products are actually healthy.
              </p>
            </div>

            <div className="flex flex-col gap-4 sm:flex-row">
              <Link
                href="/signup"
                className="inline-flex items-center justify-center gap-2 rounded-full bg-primary px-6 py-3 text-base font-semibold text-primary-foreground transition hover:bg-primary/90"
              >
                Start free MVP
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                href="/login"
                className="inline-flex items-center justify-center rounded-full border border-border bg-card/80 px-6 py-3 text-base font-semibold text-foreground transition hover:bg-card"
              >
                Login
              </Link>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              {features.map((feature) => {
                const Icon = feature.icon;
                return (
                  <article
                    key={feature.title}
                    className="glass-panel rounded-3xl border border-border/70 bg-card/80 p-5"
                  >
                    <div className="mb-4 inline-flex rounded-2xl bg-accent p-3 text-primary">
                      <Icon className="h-5 w-5" />
                    </div>
                    <h2 className="font-display text-xl font-semibold">{feature.title}</h2>
                    <p className="mt-2 text-sm leading-7 text-muted-foreground">
                      {feature.description}
                    </p>
                  </article>
                );
              })}
            </div>
          </div>

          <div className="relative">
            <div className="glass-panel data-grid rounded-[2rem] border border-border/70 bg-card/80 p-6">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="rounded-3xl bg-foreground p-5 text-white">
                  <p className="text-sm uppercase tracking-[0.2em] text-white/65">Revenue</p>
                  <p className="mt-4 font-display text-4xl font-semibold">₹4,500</p>
                  <p className="mt-2 text-sm text-white/70">Last 2 days from uploaded reports</p>
                </div>
                <div className="rounded-3xl bg-white/85 p-5">
                  <p className="text-sm uppercase tracking-[0.2em] text-muted-foreground">
                    Net profit
                  </p>
                  <p className="mt-4 font-display text-4xl font-semibold text-primary">₹1,075</p>
                  <p className="mt-2 text-sm text-muted-foreground">True margin after ads and fees</p>
                </div>
                <div className="rounded-3xl border border-border/80 bg-white/65 p-5">
                  <p className="text-sm font-semibold text-muted-foreground">SKU-001</p>
                  <p className="mt-3 font-display text-2xl font-semibold">₹550 profit</p>
                  <p className="mt-1 text-sm text-muted-foreground">55% contribution over 2 days</p>
                </div>
                <div className="rounded-3xl border border-border/80 bg-white/65 p-5">
                  <p className="text-sm font-semibold text-muted-foreground">Ad spend leakage</p>
                  <p className="mt-3 font-display text-2xl font-semibold">₹650</p>
                  <p className="mt-1 text-sm text-muted-foreground">Surface loss-makers early</p>
                </div>
              </div>

              <div className="mt-6 rounded-3xl border border-border/70 bg-white/75 p-5">
                <div className="mb-4 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-muted-foreground">Daily trend</p>
                    <p className="font-display text-xl font-semibold">Revenue vs net profit</p>
                  </div>
                  <div className="rounded-full bg-accent px-3 py-1 text-xs font-semibold text-primary">
                    30D view
                  </div>
                </div>
                <div className="flex h-36 items-end gap-3">
                  {[52, 64, 48, 70, 57, 80, 61].map((height, index) => (
                    <div key={height + index} className="flex flex-1 flex-col items-center gap-3">
                      <div
                        className="w-full rounded-full bg-primary/18"
                        style={{ height: `${height}%` }}
                      >
                        <div
                          className="mt-auto h-2/3 rounded-full bg-primary"
                          style={{ height: `${Math.max(height - 18, 16)}%` }}
                        />
                      </div>
                      <span className="text-xs text-muted-foreground">D{index + 1}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
