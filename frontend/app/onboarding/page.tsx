"use client";

import Link from "next/link";
import { useEffect, useEffectEvent, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  CheckCircle2,
  CloudUpload,
  LoaderCircle,
  PlugZap,
  RefreshCw,
  ShieldCheck,
  Store,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { UploadBox } from "@/components/UploadBox";
import { api } from "@/lib/api";
import { clearToken, getToken } from "@/lib/auth";
import type { IntegrationStatus, UploadItem, UserProfile } from "@/lib/types";

type Step = "choose" | "connect" | "upload";

const marketplaces = [
  { value: "IN", label: "India (IN)" },
  { value: "US", label: "United States (US)" },
  { value: "UK", label: "United Kingdom (UK)" },
  { value: "EU", label: "Europe (EU)" },
];

function formatTimestamp(value: string | null) {
  if (!value) {
    return "Not yet";
  }

  return new Date(value).toLocaleString();
}

function getConnectionBadge(status: string | undefined) {
  switch (status) {
    case "connected":
      return "Healthy";
    case "syncing":
      return "Syncing";
    case "error":
      return "Needs attention";
    case "disconnected":
      return "Disconnected";
    default:
      return "Pending";
  }
}

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>("choose");
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [integrationStatus, setIntegrationStatus] = useState<IntegrationStatus | null>(null);
  const [uploads, setUploads] = useState<UploadItem[]>([]);
  const [marketplace, setMarketplace] = useState("IN");
  const [action, setAction] = useState<"connect" | "sync" | "reconnect" | "disconnect" | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadIntegrationStatus = useEffectEvent(async () => {
    const integration = await api.getIntegrationStatus();
    setIntegrationStatus(integration);
    if (integration.integration?.region) {
      setMarketplace(integration.integration.region.toUpperCase());
    }
  });

  const loadOnboarding = useEffectEvent(async () => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }

    try {
      setError(null);
      const [me, integration, uploadHistory] = await Promise.all([
        api.getMe(),
        api.getIntegrationStatus(),
        api.getUploads(),
      ]);
      setProfile(me);
      setIntegrationStatus(integration);
      setUploads(uploadHistory);
      if (integration.integration?.region) {
        setMarketplace(integration.integration.region.toUpperCase());
      }

      if (!me.needs_onboarding) {
        setStep("choose");
      } else if (integration.has_connection) {
        setStep("connect");
      } else if (uploadHistory.length > 0) {
        setStep("upload");
      }
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load onboarding.");
    } finally {
      setLoading(false);
    }
  });

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadOnboarding();
  }, []);

  useEffect(() => {
    const isSyncing =
      integrationStatus?.integration?.status === "syncing" ||
      integrationStatus?.latest_job?.status === "queued" ||
      integrationStatus?.latest_job?.status === "running";

    if (!isSyncing) {
      return;
    }

    const interval = window.setInterval(() => {
      void loadIntegrationStatus();
    }, 1500);

    return () => window.clearInterval(interval);
  }, [
    integrationStatus?.integration?.status,
    integrationStatus?.latest_job?.status,
  ]);

  const handleConnect = async () => {
    setAction("connect");
    setError(null);

    try {
      const integration = await api.connectIntegration(marketplace);
      setIntegrationStatus({
        integration,
        has_connection: true,
        latest_job: null,
      });
      setStep("connect");
    } catch (connectError) {
      setError(connectError instanceof Error ? connectError.message : "Connection setup failed.");
    } finally {
      setAction(null);
    }
  };

  const refreshUploads = async () => {
    const uploadHistory = await api.getUploads();
    setUploads(uploadHistory);
  };

  const handleSync = async () => {
    setAction("sync");
    setError(null);

    try {
      const status = await api.syncIntegration();
      setIntegrationStatus(status);
    } catch (syncError) {
      setError(syncError instanceof Error ? syncError.message : "Sync could not be started.");
    } finally {
      setAction(null);
    }
  };

  const handleReconnect = async () => {
    setAction("reconnect");
    setError(null);

    try {
      const status = await api.reconnectIntegration(marketplace);
      setIntegrationStatus(status);
    } catch (reconnectError) {
      setError(
        reconnectError instanceof Error ? reconnectError.message : "Reconnect could not be saved.",
      );
    } finally {
      setAction(null);
    }
  };

  const handleDisconnect = async () => {
    setAction("disconnect");
    setError(null);

    try {
      const status = await api.disconnectIntegration();
      setIntegrationStatus(status);
    } catch (disconnectError) {
      setError(
        disconnectError instanceof Error ? disconnectError.message : "Disconnect failed.",
      );
    } finally {
      setAction(null);
    }
  };

  const integration = integrationStatus?.integration ?? null;
  const latestJob = integrationStatus?.latest_job ?? null;
  const isSyncing =
    integration?.status === "syncing" ||
    latestJob?.status === "queued" ||
    latestJob?.status === "running";
  const progress = latestJob?.progress_percent ?? 0;
  const canSync = Boolean(integration && integration.status !== "disconnected");

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center px-6">
        <div className="glass-panel rounded-[2rem] border border-border/70 bg-card/85 px-8 py-6 text-center">
          <p className="font-display text-2xl font-semibold">Preparing onboarding</p>
          <p className="mt-2 text-sm text-muted-foreground">
            Loading your store setup options.
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen px-6 py-8 lg:px-10">
      <div className="mx-auto max-w-7xl space-y-6">
        <header className="glass-panel flex flex-col gap-5 rounded-[2.5rem] border border-border/70 bg-card/85 p-8 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl">
            <p className="font-display text-sm uppercase tracking-[0.3em] text-primary">
              Seller onboarding
            </p>
            <h1 className="mt-4 font-display text-5xl font-semibold leading-tight">
              Choose how you want to start feeding your profit engine
            </h1>
            <p className="mt-4 text-lg leading-8 text-muted-foreground">
              Connect Amazon for future auto-sync or upload CSV reports manually today.
              Both flows are designed to feed the same analytics layer.
            </p>
            {profile ? (
              <p className="mt-4 text-sm font-medium text-foreground">
                Store: {profile.store.name} · Account: {profile.email}
              </p>
            ) : null}
          </div>

          <div className="flex flex-wrap gap-3">
            <Button variant="outline" onClick={() => router.push("/dashboard")}>
              Skip to dashboard
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                clearToken();
                router.push("/");
              }}
            >
              Exit setup
            </Button>
          </div>
        </header>

        {error ? (
          <div className="rounded-[1.75rem] border border-danger/20 bg-danger/8 px-5 py-4 text-sm text-danger">
            {error}
          </div>
        ) : null}

        <section className="grid gap-4 lg:grid-cols-3">
          {[
            {
              stepId: 1,
              title: "Choose flow",
              body: "Pick Amazon connection or manual report upload.",
              active: step === "choose",
            },
            {
              stepId: 2,
              title: "Configure source",
              body:
                step === "connect"
                  ? "Marketplace saved for Amazon connection beta."
                  : "Upload your first report set or configure auto-sync.",
              active: step !== "choose",
            },
            {
              stepId: 3,
              title: "Open dashboard",
              body: "Your shared profit model powers the same analytics either way.",
              active: false,
            },
          ].map((item) => (
            <div
              key={item.stepId}
              className={`rounded-[1.75rem] border p-5 ${
                item.active
                  ? "border-primary bg-primary/8"
                  : "border-border bg-white/75"
              }`}
            >
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-foreground text-sm font-semibold text-white">
                  {item.stepId}
                </div>
                <div>
                  <p className="font-display text-xl font-semibold">{item.title}</p>
                  <p className="mt-1 text-sm text-muted-foreground">{item.body}</p>
                </div>
              </div>
            </div>
          ))}
        </section>

        {step === "choose" ? (
          <section className="grid gap-6 xl:grid-cols-2">
            <article className="glass-panel rounded-[2.25rem] border border-border/70 bg-card/85 p-7">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm uppercase tracking-[0.2em] text-muted-foreground">
                    Option A
                  </p>
                  <h2 className="mt-3 font-display text-3xl font-semibold">
                    Connect Amazon Account
                  </h2>
                  <p className="mt-3 text-sm leading-7 text-muted-foreground">
                    Auto-sync orders, ads, fees, and payouts. This beta setup stores your
                    marketplace intent now so we can complete the sync flow next.
                  </p>
                </div>
                <div className="rounded-2xl bg-accent p-3 text-primary">
                  <Store className="h-6 w-6" />
                </div>
              </div>

              <div className="mt-6 space-y-3">
                {[
                  "Future-ready integration record in the backend",
                  "Shared analytics tables with the CSV flow",
                  "Clean path to sync jobs and connection health",
                ].map((item) => (
                  <div key={item} className="flex items-center gap-3 text-sm text-foreground">
                    <CheckCircle2 className="h-4 w-4 text-primary" />
                    {item}
                  </div>
                ))}
              </div>

              <Button className="mt-8" onClick={() => setStep("connect")}>
                Connect Amazon
                <ArrowRight className="h-4 w-4" />
              </Button>
            </article>

            <article className="glass-panel rounded-[2.25rem] border border-border/70 bg-card/85 p-7">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm uppercase tracking-[0.2em] text-muted-foreground">
                    Option B
                  </p>
                  <h2 className="mt-3 font-display text-3xl font-semibold">
                    Upload Reports
                  </h2>
                  <p className="mt-3 text-sm leading-7 text-muted-foreground">
                    Upload CSV exports manually today. Orders and ads are live now, with
                    settlement and inventory onboarding slots already prepared.
                  </p>
                </div>
                <div className="rounded-2xl bg-accent p-3 text-primary">
                  <CloudUpload className="h-6 w-6" />
                </div>
              </div>

              <div className="mt-6 space-y-3">
                {[
                  "Fastest route to visible profit insights",
                  "Reusable upload center with status feedback",
                  "Same destination tables as future Amazon sync",
                ].map((item) => (
                  <div key={item} className="flex items-center gap-3 text-sm text-foreground">
                    <CheckCircle2 className="h-4 w-4 text-primary" />
                    {item}
                  </div>
                ))}
              </div>

              <Button className="mt-8" variant="outline" onClick={() => setStep("upload")}>
                Upload reports
                <ArrowRight className="h-4 w-4" />
              </Button>
            </article>
          </section>
        ) : null}

        {step === "connect" ? (
          <section className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
            <article className="glass-panel rounded-[2.25rem] border border-border/70 bg-card/85 p-7">
              <p className="text-sm uppercase tracking-[0.2em] text-muted-foreground">
                Amazon connection beta
              </p>
              <h2 className="mt-3 font-display text-3xl font-semibold">
                Capture marketplace now, finish auto-sync next
              </h2>
              <p className="mt-3 text-sm leading-7 text-muted-foreground">
                This beta flow keeps the UX honest: save your marketplace, create the
                integration record, and trigger a realistic sync that feeds the same shared
                analytics tables as CSV uploads.
              </p>

              <label className="mt-6 block text-sm font-semibold text-foreground">
                Marketplace
              </label>
              <select
                value={marketplace}
                onChange={(event) => setMarketplace(event.target.value)}
                className="mt-2 w-full rounded-2xl border border-border bg-white/80 px-4 py-3 text-sm font-medium text-foreground outline-none focus:border-primary"
              >
                {marketplaces.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>

              <div className="mt-6 flex flex-wrap gap-3">
                <Button onClick={() => void handleConnect()} disabled={Boolean(action)}>
                  {action === "connect" ? "Connecting..." : "Connect Amazon"}
                </Button>
                <Button variant="outline" onClick={() => setStep("choose")}>
                  Back
                </Button>
              </div>
            </article>

            <aside className="glass-panel rounded-[2.25rem] border border-border/70 bg-card/85 p-7">
              <div className="flex items-center gap-3">
                <ShieldCheck className="h-5 w-5 text-primary" />
                <p className="font-display text-2xl font-semibold">Connection status</p>
              </div>

              {integration ? (
                <div className="mt-6 space-y-4">
                  <div className="rounded-[1.75rem] bg-foreground p-5 text-white">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="text-sm uppercase tracking-[0.2em] text-white/60">
                          Provider
                        </p>
                        <p className="mt-2 font-display text-2xl font-semibold">
                          Amazon · {(integration.region ?? "pending").toUpperCase()}
                        </p>
                      </div>
                      <div className="rounded-full bg-white/12 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-white/80">
                        {getConnectionBadge(integration.status)}
                      </div>
                    </div>
                    <p className="mt-2 text-sm text-white/75">Status: {integration.status}</p>
                    <p className="mt-1 text-sm text-white/75">
                      Last synced: {formatTimestamp(integration.last_synced_at)}
                    </p>
                    <p className="mt-1 text-sm text-white/75">
                      Connected at: {formatTimestamp(integration.connected_at)}
                    </p>
                  </div>

                  <div className="rounded-[1.75rem] border border-border bg-white/75 p-5">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="text-sm uppercase tracking-[0.18em] text-muted-foreground">
                          Latest sync job
                        </p>
                        <p className="mt-2 font-display text-xl font-semibold text-foreground">
                          {latestJob ? latestJob.job_type.replaceAll("_", " ") : "No sync yet"}
                        </p>
                      </div>
                      {isSyncing ? (
                        <LoaderCircle className="h-5 w-5 animate-spin text-primary" />
                      ) : (
                        <PlugZap className="h-5 w-5 text-primary" />
                      )}
                    </div>

                    {latestJob ? (
                      <>
                        <p className="mt-3 text-sm text-muted-foreground">
                          {latestJob.status} · {latestJob.rows_processed} rows processed
                        </p>
                        <div className="mt-4 h-2 overflow-hidden rounded-full bg-accent">
                          <div
                            className="h-full rounded-full bg-primary transition-all duration-500"
                            style={{ width: `${progress}%` }}
                          />
                        </div>
                        <p className="mt-2 text-xs text-muted-foreground">
                          Progress: {progress}% · Started {formatTimestamp(latestJob.started_at)}
                        </p>
                        {latestJob.error_message ? (
                          <p className="mt-2 text-xs text-danger">{latestJob.error_message}</p>
                        ) : null}
                      </>
                    ) : (
                      <p className="mt-3 text-sm text-muted-foreground">
                        Run your first sync to pull placeholder Amazon account data into the
                        shared dashboard engine.
                      </p>
                    )}
                  </div>

                  <div className="flex flex-wrap gap-3">
                    <Button
                      onClick={() => void handleSync()}
                      disabled={!canSync || isSyncing || Boolean(action)}
                    >
                      {action === "sync" ? "Starting sync..." : "Sync now"}
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => void handleReconnect()}
                      disabled={Boolean(action)}
                    >
                      {action === "reconnect" ? "Saving..." : "Reconnect"}
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => void handleDisconnect()}
                      disabled={Boolean(action)}
                    >
                      {action === "disconnect" ? "Disconnecting..." : "Disconnect"}
                    </Button>
                    <Button onClick={() => router.push("/dashboard")}>
                      Go to dashboard
                      <ArrowRight className="h-4 w-4" />
                    </Button>
                    <Button variant="outline" onClick={() => setStep("upload")}>
                      Also upload reports
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="mt-6 rounded-[1.75rem] border border-dashed border-border bg-white/75 p-6 text-sm text-muted-foreground">
                  No Amazon connection record yet. Save your marketplace to create the first
                  integration row.
                </div>
              )}
            </aside>
          </section>
        ) : null}

        {step === "upload" ? (
          <section className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm uppercase tracking-[0.2em] text-muted-foreground">
                  Manual import center
                </p>
                <h2 className="mt-2 font-display text-3xl font-semibold">
                  Upload reports into the shared analytics engine
                </h2>
              </div>
              <div className="flex gap-3">
                <Button variant="outline" onClick={() => setStep("choose")}>
                  Back
                </Button>
                <Button onClick={() => router.push("/dashboard")}>
                  Open dashboard
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </div>
            </div>

            <div className="grid gap-4 xl:grid-cols-2">
              <UploadBox
                title="Orders CSV"
                description="Import order-level sales, fees, and refunds."
                uploadType="orders"
                onUploaded={refreshUploads}
                helpText="Supports the current CSV parser and powers revenue, profit, and SKU metrics."
                sampleHref="/sample_orders.csv"
                badge="Live now"
              />
              <UploadBox
                title="Ads CSV"
                description="Import ad spend, attributed sales, clicks, and impressions."
                uploadType="ads"
                onUploaded={refreshUploads}
                helpText="Feeds TACOS, ACOS, ROAS, CPC, and trend analysis."
                sampleHref="/sample_ads.csv"
                badge="Live now"
              />
              <UploadBox
                title="Settlement CSV"
                description="Prepare payout, fees, taxes, and reimbursements data."
                uploadType="settlement"
                onUploaded={refreshUploads}
                helpText="Imports taxes and reimbursements so net profit gets closer to real payout math."
                sampleHref="/sample_settlements.csv"
                badge="Live now"
              />
              <UploadBox
                title="Inventory CSV"
                description="Prepare stock snapshots for future sell-through and stockout analysis."
                onUploaded={refreshUploads}
                helpText="Inventory schema is ready now so the next import step can plug straight into it."
                sampleHref="/sample_inventory.csv"
                disabled
                badge="Optional"
              />
            </div>

            <section className="glass-panel rounded-[2rem] border border-border/70 bg-card/85 p-6">
              <div className="mb-5 flex items-center justify-between">
                <div>
                  <h3 className="font-display text-2xl font-semibold">Current upload activity</h3>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Manual imports and Amazon sync will both eventually surface here as trusted data events.
                  </p>
                </div>
                <Button variant="outline" onClick={() => void refreshUploads()}>
                  <RefreshCw className="h-4 w-4" />
                  Refresh
                </Button>
              </div>

              {uploads.length === 0 ? (
                <div className="rounded-[1.75rem] border border-dashed border-border bg-white/75 p-6 text-sm text-muted-foreground">
                  No uploads yet. Start with orders and ads to unlock the dashboard immediately.
                </div>
              ) : (
                <div className="overflow-hidden rounded-[1.75rem] border border-border/80 bg-white/75">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-accent/70 text-muted-foreground">
                      <tr>
                        <th className="px-4 py-3 font-semibold">Report</th>
                        <th className="px-4 py-3 font-semibold">Status</th>
                        <th className="px-4 py-3 font-semibold">Rows</th>
                        <th className="px-4 py-3 font-semibold">Uploaded</th>
                      </tr>
                    </thead>
                    <tbody>
                      {uploads.slice(0, 6).map((upload) => (
                        <tr key={upload.id} className="border-t border-border/70">
                          <td className="px-4 py-4 font-semibold capitalize">
                            {upload.upload_type}
                          </td>
                          <td className="px-4 py-4 text-muted-foreground">{upload.status}</td>
                          <td className="px-4 py-4 text-muted-foreground">
                            {upload.rows_inserted} inserted
                          </td>
                          <td className="px-4 py-4 text-muted-foreground">
                            {new Date(upload.uploaded_at).toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>

            <div className="rounded-[1.75rem] border border-border bg-white/75 p-5 text-sm text-muted-foreground">
              Need the full uploads workspace later? You can also use the dedicated{" "}
              <Link href="/uploads" className="font-semibold text-primary hover:text-primary/80">
                uploads page
              </Link>
              .
            </div>
          </section>
        ) : null}
      </div>
    </main>
  );
}
