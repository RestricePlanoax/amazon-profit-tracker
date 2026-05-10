import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const currencyFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 2,
});

const numberFormatter = new Intl.NumberFormat("en-IN");

export function formatCurrency(value: number) {
  return currencyFormatter.format(value);
}

export function formatMetricValue(
  value: number,
  type: "currency" | "percent" | "number" | "ratio",
) {
  if (type === "currency") {
    return formatCurrency(value);
  }
  if (type === "percent") {
    return `${value.toFixed(2)}%`;
  }
  if (type === "ratio") {
    return `${value.toFixed(2)}x`;
  }
  return numberFormatter.format(value);
}

export function formatDateLabel(value: string) {
  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(new Date(value));
}

export function formatCompactPercent(value: number | null) {
  if (value === null) {
    return "New";
  }
  const prefix = value > 0 ? "+" : "";
  return `${prefix}${value.toFixed(1)}%`;
}
