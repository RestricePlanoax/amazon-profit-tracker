"use client";

import { useEffect, useEffectEvent, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { EmptyState } from "@/components/EmptyState";
import { UploadBox } from "@/components/UploadBox";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { UploadItem } from "@/lib/types";

const statusStyles: Record<string, string> = {
  pending: "bg-amber-100 text-amber-800",
  processing: "bg-sky-100 text-sky-800",
  completed: "bg-emerald-100 text-emerald-800",
  failed: "bg-rose-100 text-rose-800",
  deleted: "bg-slate-100 text-slate-700",
};

export default function UploadsPage() {
  const [uploads, setUploads] = useState<UploadItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeUploadAction, setActiveUploadAction] = useState<string | null>(null);

  const loadUploads = async () => {
    if (!getToken()) {
      return;
    }

    try {
      setError(null);
      const response = await api.getUploads();
      setUploads(response);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load uploads.");
    } finally {
      setLoading(false);
    }
  };

  const runInitialLoad = useEffectEvent(async () => {
    await loadUploads();
  });

  // Initial data loading happens client-side because auth lives in localStorage.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void runInitialLoad();
  }, []);

  const handleDeleteUpload = async (uploadId: string) => {
    setActiveUploadAction(`delete-${uploadId}`);
    try {
      await api.deleteUpload(uploadId);
      await loadUploads();
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Failed to delete import.");
    } finally {
      setActiveUploadAction(null);
    }
  };

  const handleReprocessUpload = async (uploadId: string) => {
    setActiveUploadAction(`reprocess-${uploadId}`);
    try {
      await api.reprocessUpload(uploadId);
      await loadUploads();
    } catch (reprocessError) {
      setError(
        reprocessError instanceof Error ? reprocessError.message : "Failed to reprocess import.",
      );
    } finally {
      setActiveUploadAction(null);
    }
  };

  return (
    <AppShell title="Uploads">
      <div className="space-y-6">
        <div className="grid gap-4 xl:grid-cols-2">
          <UploadBox
            title="Upload orders CSV"
            description="Accepted columns: order_date, order_id, sku, units, revenue, fees, refund"
            uploadType="orders"
            onUploaded={loadUploads}
          />
          <UploadBox
            title="Upload ads CSV"
            description="Accepted columns: date, sku, spend, sales, clicks, impressions"
            uploadType="ads"
            onUploaded={loadUploads}
          />
          <UploadBox
            title="Upload settlement CSV"
            description="Accepted columns: settlement_date, settlement_id, total_amount, fees, taxes, reimbursements"
            uploadType="settlement"
            onUploaded={loadUploads}
          />
        </div>

        <div className="grid gap-4 lg:grid-cols-[1.3fr_0.7fr]">
          <section className="polaris-card p-6">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <h2 className="font-display text-2xl font-semibold">Upload history</h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  Every CSV stays local to the backend storage folder for this MVP.
                </p>
              </div>
            </div>

            {loading ? (
              <div className="space-y-3">
                {Array.from({ length: 4 }).map((_, index) => (
                  <div
                    key={index}
                    className="h-16 animate-pulse rounded-lg border border-border bg-card"
                  />
                ))}
              </div>
            ) : error ? (
              <EmptyState title="Could not load uploads" description={error} />
            ) : uploads.length === 0 ? (
              <EmptyState
                title="No reports uploaded yet"
                description="Upload an orders CSV or ads CSV to start generating profit metrics."
              />
            ) : (
              <div className="overflow-hidden rounded-lg border border-border bg-card">
                <table className="w-full text-left text-sm">
                  <thead className="bg-muted text-muted-foreground">
                    <tr>
                      <th className="px-5 py-3 font-semibold">Type</th>
                      <th className="px-5 py-3 font-semibold">Status</th>
                      <th className="px-5 py-3 font-semibold">Uploaded</th>
                      <th className="px-5 py-3 font-semibold">Rows</th>
                      <th className="px-5 py-3 font-semibold">Error</th>
                      <th className="px-5 py-3 font-semibold">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {uploads.map((upload) => (
                      <tr key={upload.id} className="border-t border-border/70">
                        <td className="px-5 py-4 font-semibold capitalize">{upload.upload_type}</td>
                        <td className="px-5 py-4">
                          <span
                            className={`polaris-badge ${statusStyles[upload.status] ?? "bg-slate-100 text-slate-700"}`}
                          >
                            {upload.status}
                          </span>
                        </td>
                        <td className="px-5 py-4 text-muted-foreground">
                          {new Date(upload.uploaded_at).toLocaleString()}
                        </td>
                        <td className="px-5 py-4 text-muted-foreground">
                          {upload.rows_inserted} inserted · {upload.rows_skipped} skipped
                        </td>
                        <td className="px-5 py-4 text-muted-foreground">
                          {upload.error_message ?? "—"}
                        </td>
                        <td className="px-5 py-4">
                          <div className="flex flex-wrap gap-2">
                            <Button
                              variant="outline"
                              onClick={() => void handleReprocessUpload(upload.id)}
                              disabled={
                                !upload.can_reprocess ||
                                upload.status === "processing" ||
                                activeUploadAction !== null
                              }
                            >
                              {activeUploadAction === `reprocess-${upload.id}`
                                ? "Reprocessing..."
                                : "Reprocess"}
                            </Button>
                            <Button
                              variant="outline"
                              onClick={() => void handleDeleteUpload(upload.id)}
                              disabled={
                                upload.status === "processing" ||
                                upload.status === "deleted" ||
                                activeUploadAction !== null
                              }
                            >
                              {activeUploadAction === `delete-${upload.id}` ? "Deleting..." : "Delete"}
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <aside className="polaris-card p-6">
            <h2 className="font-display text-2xl font-semibold">CSV sample format</h2>
            <p className="mt-2 text-sm leading-7 text-muted-foreground">
              Column names are normalized automatically: spaces are converted to underscores,
              and headers are matched case-insensitively.
            </p>

            <div className="mt-5 space-y-4">
              <div className="rounded-lg bg-foreground p-4 text-sm text-white/85">
                <p className="mb-2 text-white">Orders CSV</p>
                <pre className="overflow-x-auto whitespace-pre-wrap">
                  order_date,order_id,sku,units,revenue,fees,refund
                </pre>
              </div>
              <div className="rounded-lg border border-border bg-card p-4 text-sm text-foreground">
                <p className="mb-2 font-semibold">Ads CSV</p>
                <pre className="overflow-x-auto whitespace-pre-wrap">
                  date,sku,spend,sales,clicks,impressions
                </pre>
              </div>
              <div className="rounded-lg border border-border bg-card p-4 text-sm text-foreground">
                <p className="mb-2 font-semibold">Settlement CSV</p>
                <pre className="overflow-x-auto whitespace-pre-wrap">
                  settlement_date,settlement_id,total_amount,fees,taxes,reimbursements
                </pre>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </AppShell>
  );
}
