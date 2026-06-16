"use client";
import { useMemo, useState } from "react";
import { UploadCloud } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

type UploadBoxProps = {
  title: string;
  description: string;
  uploadType?:
    | "orders"
    | "ads"
    | "settlement"
    | "returns"
    | "reimbursements"
    | "campaigns"
    | "inventory";
  onUploaded: () => Promise<void>;
  helpText?: string;
  sampleHref?: string;
  disabled?: boolean;
  badge?: string;
};

export function UploadBox({
  title,
  description,
  uploadType,
  onUploaded,
  helpText,
  sampleHref,
  disabled = false,
  badge,
}: UploadBoxProps) {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const statusTone = useMemo(() => {
    if (!status) {
      return "border-border bg-accent/55 text-foreground";
    }
    if (status.toLowerCase().includes("failed") || status.toLowerCase().includes("choose")) {
      return "border-danger/20 bg-danger/8 text-danger";
    }
    return "border-emerald-200 bg-emerald-50 text-emerald-800";
  }, [status]);

  const handleUpload = async () => {
    if (disabled || !uploadType) {
      setStatus("This import type is queued for the next delivery step.");
      return;
    }
    if (!file) {
      setStatus("Choose a CSV file first.");
      return;
    }

    setSubmitting(true);
    setStatus(null);

    try {
      const response = await api.uploadReport(uploadType, file);
      setStatus(`Upload queued successfully. Current status: ${response.status}.`);
      setFile(null);
      await onUploaded();
    } catch (uploadError) {
      setStatus(uploadError instanceof Error ? uploadError.message : "Upload failed.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="polaris-card p-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-semibold">{title}</h2>
            {badge ? (
              <span className="polaris-badge bg-accent text-primary">
                {badge}
              </span>
            ) : null}
          </div>
          <p className="mt-1 text-sm leading-6 text-muted-foreground">{description}</p>
        </div>
        <div className="rounded-lg bg-accent p-2.5 text-primary">
          <UploadCloud className="h-5 w-5" />
        </div>
      </div>

      <div
        className={`mt-4 rounded-lg border border-dashed p-4 transition ${
          isDragging
            ? "border-primary bg-primary/6"
            : "border-border bg-[var(--surface-subdued)]"
        } ${disabled ? "opacity-70" : ""}`}
        onDragOver={(event) => {
          event.preventDefault();
          if (!disabled) {
            setIsDragging(true);
          }
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setIsDragging(false);
          if (disabled) {
            return;
          }
          const droppedFile = event.dataTransfer.files?.[0];
          if (droppedFile) {
            setFile(droppedFile);
          }
        }}
      >
        <input
          type="file"
          accept=".csv,text/csv"
          disabled={disabled}
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          className="w-full text-sm text-muted-foreground file:mr-4 file:rounded-lg file:border file:border-primary file:bg-primary file:px-3 file:py-2 file:text-sm file:font-semibold file:text-primary-foreground hover:file:bg-[#006e52]"
        />

        <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-muted-foreground">
            {file
              ? `Ready to upload: ${file.name}`
              : disabled
                ? "This import type will unlock in the next ingestion step."
                : "Drag a CSV here or choose one from your machine."}
          </p>
          <Button onClick={handleUpload} disabled={submitting}>
            {submitting ? "Uploading..." : disabled ? "Coming next" : "Upload CSV"}
          </Button>
        </div>

        {helpText || sampleHref ? (
          <div className="mt-4 flex flex-col gap-2 text-sm text-muted-foreground">
            {helpText ? <p>{helpText}</p> : null}
            {sampleHref ? (
              <a
                href={sampleHref}
                download
                className="font-semibold text-primary hover:text-primary/80"
              >
                Download sample CSV
              </a>
            ) : null}
          </div>
        ) : null}

        {status ? (
          <p className={`mt-4 rounded-lg border px-3 py-2 text-sm ${statusTone}`}>
            {status}
          </p>
        ) : null}
      </div>
    </section>
  );
}
