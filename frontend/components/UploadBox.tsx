"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { UploadCloud } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

type UploadBoxProps = {
  title: string;
  description: string;
  uploadType?: "orders" | "ads" | "settlement";
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
    <section className="glass-panel rounded-[2rem] border border-border/70 bg-card/85 p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="font-display text-2xl font-semibold">{title}</h2>
            {badge ? (
              <span className="rounded-full bg-accent px-3 py-1 text-xs font-semibold text-primary">
                {badge}
              </span>
            ) : null}
          </div>
          <p className="mt-2 text-sm leading-7 text-muted-foreground">{description}</p>
        </div>
        <div className="rounded-2xl bg-accent p-3 text-primary">
          <UploadCloud className="h-5 w-5" />
        </div>
      </div>

      <div
        className={`mt-5 rounded-[1.5rem] border border-dashed p-5 transition ${
          isDragging
            ? "border-primary bg-primary/6"
            : "border-border bg-white/75"
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
          className="w-full text-sm text-muted-foreground file:mr-4 file:rounded-full file:border-0 file:bg-primary file:px-4 file:py-2 file:font-semibold file:text-primary-foreground hover:file:bg-primary/90"
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
              <Link href={sampleHref} className="font-semibold text-primary hover:text-primary/80">
                Open sample CSV
              </Link>
            ) : null}
          </div>
        ) : null}

        {status ? (
          <p className={`mt-4 rounded-2xl border px-4 py-3 text-sm ${statusTone}`}>
            {status}
          </p>
        ) : null}
      </div>
    </section>
  );
}
