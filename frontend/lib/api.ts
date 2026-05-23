import { getToken } from "@/lib/auth";
import type {
  AuthPayload,
  AuthResponse,
  DashboardInsightsResponse,
  DashboardSummary,
  DateBounds,
  DemoLoadResponse,
  Integration,
  IntegrationStatus,
  BulkCogsResult,
  MetricCatalogItem,
  Product,
  ProductProfitability,
  TrendPoint,
  UploadItem,
  UserProfile,
} from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(
  path: string,
  options: RequestInit & { auth?: boolean } = {},
): Promise<T> {
  const { auth = true, headers, body, ...rest } = options;
  const token = auth ? getToken() : null;

  const resolvedHeaders = new Headers(headers);
  if (!(body instanceof FormData)) {
    resolvedHeaders.set("Content-Type", "application/json");
  }
  if (token) {
    resolvedHeaders.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...rest,
    body,
    headers: resolvedHeaders,
    cache: "no-store",
  });

  const isJson = response.headers.get("content-type")?.includes("application/json");
  const payload = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    const detail =
      typeof payload === "string"
        ? payload
        : (payload.detail as string | undefined) ?? "Request failed.";
    throw new Error(detail);
  }

  return payload as T;
}

export const api = {
  signup(payload: AuthPayload) {
    return request<AuthResponse>("/auth/signup", {
      method: "POST",
      auth: false,
      body: JSON.stringify(payload),
    });
  },

  login(payload: AuthPayload) {
    return request<AuthResponse>("/auth/login", {
      method: "POST",
      auth: false,
      body: JSON.stringify(payload),
    });
  },

  getMe() {
    return request<UserProfile>("/auth/me");
  },

  getIntegrationStatus() {
    return request<IntegrationStatus>("/integrations/status");
  },

  connectIntegration(marketplace: string) {
    return request<Integration>("/integrations/connect", {
      method: "POST",
      body: JSON.stringify({ marketplace }),
    });
  },

  syncIntegration() {
    return request<IntegrationStatus>("/integrations/sync", {
      method: "POST",
    });
  },

  reconnectIntegration(marketplace: string) {
    return request<IntegrationStatus>("/integrations/reconnect", {
      method: "POST",
      body: JSON.stringify({ marketplace }),
    });
  },

  disconnectIntegration() {
    return request<IntegrationStatus>("/integrations/disconnect", {
      method: "POST",
    });
  },

  getDateBounds() {
    return request<DateBounds>("/dashboard/date-bounds");
  },

  getSummary(startDate: string, endDate: string) {
    return request<DashboardSummary>(
      `/dashboard/summary?start_date=${startDate}&end_date=${endDate}`,
    );
  },

  getTrends(startDate: string, endDate: string) {
    return request<TrendPoint[]>(
      `/dashboard/trends?start_date=${startDate}&end_date=${endDate}`,
    );
  },

  getInsights(startDate: string, endDate: string) {
    return request<DashboardInsightsResponse>(
      `/dashboard/insights?start_date=${startDate}&end_date=${endDate}`,
    );
  },

  getUploads() {
    return request<UploadItem[]>("/uploads");
  },

  deleteUpload(uploadId: string) {
    return request<UploadItem>(`/uploads/${uploadId}`, {
      method: "DELETE",
    });
  },

  reprocessUpload(uploadId: string) {
    return request<UploadItem>(`/uploads/${uploadId}/reprocess`, {
      method: "POST",
    });
  },

  uploadReport(uploadType: "orders" | "ads" | "settlement", file: File) {
    const formData = new FormData();
    formData.append("file", file);
    return request<UploadItem>(`/uploads/${uploadType}`, {
      method: "POST",
      body: formData,
    });
  },

  getProducts(startDate: string, endDate: string) {
    return request<ProductProfitability[]>(
      `/products/profitability?start_date=${startDate}&end_date=${endDate}`,
    );
  },

  updateProductCogs(sku: string, cogs: number) {
    return request<Product>(`/products/${encodeURIComponent(sku)}/cogs`, {
      method: "PUT",
      body: JSON.stringify({ cogs }),
    });
  },

  bulkUploadCogs(file: File) {
    const formData = new FormData();
    formData.append("file", file);
    return request<BulkCogsResult>("/products/cogs/bulk", {
      method: "POST",
      body: formData,
    });
  },

  loadDemoStore() {
    return request<DemoLoadResponse>("/demo/load", {
      method: "POST",
    });
  },

  getMetricCatalog() {
    return request<MetricCatalogItem[]>("/metrics/catalog");
  },
};
