"use client";

import { useEffect, useEffectEvent, useState } from "react";
import { LoaderCircle, PlugZap, RefreshCw, ShieldCheck, Unplug } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { EmptyState } from "@/components/EmptyState";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { IntegrationStatus, UserProfile } from "@/lib/types";

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

export default function SettingsPage() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [integrationStatus, setIntegrationStatus] = useState<IntegrationStatus | null>(null);
  const [marketplace, setMarketplace] = useState("IN");
  const [action, setAction] = useState<"connect" | "sync" | "reconnect" | "disconnect" | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshIntegrationStatus = async () => {
    const integration = await api.getIntegrationStatus();
    setIntegrationStatus(integration);
    if (integration.integration?.region) {
      setMarketplace(integration.integration.region.toUpperCase());
    }
  };

  const loadIntegrationStatus = useEffectEvent(async () => {
    await refreshIntegrationStatus();
  });

  const loadProfile = useEffectEvent(async () => {
    if (!getToken()) {
      return;
    }

    try {
      const [response, integration] = await Promise.all([api.getMe(), api.getIntegrationStatus()]);
      setProfile(response);
      setIntegrationStatus(integration);
      if (integration.integration?.region) {
        setMarketplace(integration.integration.region.toUpperCase());
      }
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load settings.");
    } finally {
      setLoading(false);
    }
  });

  // Settings load after mount because the JWT is stored client-side for the MVP.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadProfile();
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
      setIntegrationStatus({ integration, has_connection: true, latest_job: null });
    } catch (connectError) {
      setError(connectError instanceof Error ? connectError.message : "Connection setup failed.");
    } finally {
      setAction(null);
    }
  };

  const handleSync = async () => {
    setAction("sync");
    setError(null);

    try {
      const integration = await api.syncIntegration();
      setIntegrationStatus(integration);
    } catch (syncError) {
      setError(syncError instanceof Error ? syncError.message : "Failed to start sync.");
    } finally {
      setAction(null);
    }
  };

  const handleReconnect = async () => {
    setAction("reconnect");
    setError(null);

    try {
      const integration = await api.reconnectIntegration(marketplace);
      setIntegrationStatus(integration);
    } catch (reconnectError) {
      setError(reconnectError instanceof Error ? reconnectError.message : "Reconnect failed.");
    } finally {
      setAction(null);
    }
  };

  const handleDisconnect = async () => {
    setAction("disconnect");
    setError(null);

    try {
      const integration = await api.disconnectIntegration();
      setIntegrationStatus(integration);
    } catch (disconnectError) {
      setError(disconnectError instanceof Error ? disconnectError.message : "Disconnect failed.");
    } finally {
      setAction(null);
    }
  };

  const handleRefresh = async () => {
    try {
      await refreshIntegrationStatus();
    } catch (refreshError) {
      setError(refreshError instanceof Error ? refreshError.message : "Refresh failed.");
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

  return (
    <AppShell title="Settings">
      <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <section className="glass-panel rounded-[2rem] border border-border/70 bg-card/85 p-6">
          <h1 className="font-display text-3xl font-semibold">Store settings</h1>
          <p className="mt-2 text-sm leading-7 text-muted-foreground">
            The MVP creates one default store during signup and uses it for uploads,
            daily metrics, and SKU profitability.
          </p>

          {loading ? (
            <div className="mt-6 h-40 animate-pulse rounded-3xl border border-border bg-white/70" />
          ) : error ? (
            <div className="mt-6">
              <EmptyState title="Settings unavailable" description={error} />
            </div>
          ) : profile ? (
            <div className="mt-6 space-y-4">
              <div className="rounded-3xl border border-border bg-white/75 p-5">
                <p className="text-sm text-muted-foreground">Store name</p>
                <p className="mt-2 font-display text-2xl font-semibold">{profile.store.name}</p>
              </div>
              <div className="rounded-3xl border border-border bg-white/75 p-5">
                <p className="text-sm text-muted-foreground">Marketplace</p>
                <p className="mt-2 text-lg font-semibold">{profile.store.marketplace}</p>
              </div>
              <div className="rounded-3xl border border-border bg-white/75 p-5">
                <p className="text-sm text-muted-foreground">Account email</p>
                <p className="mt-2 text-lg font-semibold">{profile.email}</p>
              </div>
              <div className="rounded-3xl border border-border bg-white/75 p-5">
                <div className="flex items-center gap-3">
                  <ShieldCheck className="h-5 w-5 text-primary" />
                  <div>
                    <p className="text-sm text-muted-foreground">Amazon connection</p>
                    <p className="mt-1 text-lg font-semibold">
                      {integration
                        ? `${integration.status} · ${(integration.region ?? "pending").toUpperCase()}`
                        : "Not connected"}
                    </p>
                  </div>
                </div>
                <p className="mt-3 text-sm text-muted-foreground">
                  Last synced: {formatTimestamp(integration?.last_synced_at ?? null)}
                </p>
              </div>
            </div>
          ) : null}
        </section>

        <aside className="glass-panel rounded-[2rem] border border-border/70 bg-card/85 p-6">
          <h2 className="font-display text-2xl font-semibold">Amazon connection</h2>
          <p className="mt-2 text-sm leading-7 text-muted-foreground">
            Manage the beta Amazon account connection here. Sync writes into the same
            orders, ads, settlements, and inventory tables that manual uploads use.
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

          <div className="mt-6 rounded-[1.75rem] border border-border bg-white/75 p-5">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-sm uppercase tracking-[0.2em] text-muted-foreground">
                  Connection health
                </p>
                <p className="mt-2 font-display text-2xl font-semibold">
                  {integration ? `Amazon ${integration.status}` : "Waiting to connect"}
                </p>
                <p className="mt-2 text-sm text-muted-foreground">
                  Last synced: {formatTimestamp(integration?.last_synced_at ?? null)}
                </p>
              </div>
              {isSyncing ? (
                <LoaderCircle className="h-5 w-5 animate-spin text-primary" />
              ) : integration ? (
                <PlugZap className="h-5 w-5 text-primary" />
              ) : (
                <Unplug className="h-5 w-5 text-muted-foreground" />
              )}
            </div>

            {latestJob ? (
              <>
                <p className="mt-4 text-sm text-muted-foreground">
                  Latest job: {latestJob.status} · {latestJob.rows_processed} rows processed
                </p>
                <div className="mt-4 h-2 overflow-hidden rounded-full bg-accent">
                  <div
                    className="h-full rounded-full bg-primary transition-all duration-500"
                    style={{ width: `${progress}%` }}
                  />
                </div>
                <p className="mt-2 text-xs text-muted-foreground">
                  Progress {progress}% · Started {formatTimestamp(latestJob.started_at)}
                </p>
                {latestJob.error_message ? (
                  <p className="mt-2 text-xs text-danger">{latestJob.error_message}</p>
                ) : null}
              </>
            ) : (
              <p className="mt-4 text-sm text-muted-foreground">
                No sync has run yet. Start one to seed the shared analytics engine with
                Amazon connection data.
              </p>
            )}
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            {integration ? (
              <>
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
              </>
            ) : (
              <Button onClick={() => void handleConnect()} disabled={Boolean(action)}>
                {action === "connect" ? "Connecting..." : "Connect Amazon"}
              </Button>
            )}
            <Button variant="outline" onClick={() => void handleRefresh()}>
              <RefreshCw className="h-4 w-4" />
              Refresh
            </Button>
          </div>

          <div className="mt-6 rounded-[1.75rem] bg-foreground p-5 text-white">
            <p className="text-sm uppercase tracking-[0.2em] text-white/60">Roadmap TODO</p>
            <ul className="mt-4 space-y-3 text-sm text-white/85">
              <li>Replace beta connect with Amazon OAuth / SP-API authorization.</li>
              <li>Pull real report documents and incremental sync windows.</li>
              <li>Show sync history by job type and richer health monitoring.</li>
              <li>Support multiple marketplaces per seller account.</li>
            </ul>
          </div>
        </aside>
      </div>
    </AppShell>
  );
}
