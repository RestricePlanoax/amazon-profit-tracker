export type AuthPayload = {
  email: string;
  password: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
};

export type Store = {
  id: string;
  name: string;
  marketplace: string;
  created_at: string;
};

export type UserProfile = {
  id: string;
  email: string;
  created_at: string;
  store: Store;
  needs_onboarding: boolean;
};

export type DashboardSummary = {
  start_date: string;
  end_date: string;
  previous_start_date: string;
  previous_end_date: string;
  metrics: DashboardMetricSet;
  last_data_refresh: string | null;
  data_sources: DataSourceStatus[];
};

export type DataSourceStatus = {
  name: string;
  active: boolean;
  last_refresh_at: string | null;
};

export type TrendPoint = {
  date: string;
  revenue: number;
  ad_sales: number;
  ad_spend: number;
  fees: number;
  taxes: number;
  reimbursements: number;
  refund: number;
  cogs: number;
  net_profit: number;
  profit_margin: number;
  tacos: number;
  acos: number;
  roas: number;
  refund_rate: number;
  orders_count: number;
  units_sold: number;
  clicks: number;
  impressions: number;
  ctr: number;
  cpc: number;
  avg_order_value: number;
};

export type MetricValue = {
  current: number;
  previous: number;
  change_pct: number | null;
};

export type DashboardMetricSet = {
  revenue: MetricValue;
  net_profit: MetricValue;
  profit_margin: MetricValue;
  tacos: MetricValue;
  acos: MetricValue;
  refund_rate: MetricValue;
  ad_spend: MetricValue;
  roas: MetricValue;
  avg_order_value: MetricValue;
  orders_count: MetricValue;
  units_sold: MetricValue;
  ctr: MetricValue;
  cpc: MetricValue;
  ad_sales: MetricValue;
  fees: MetricValue;
  taxes: MetricValue;
  reimbursements: MetricValue;
  refunds: MetricValue;
  cogs: MetricValue;
  profit_per_order: MetricValue;
};

export type DateBounds = {
  min_date: string;
  max_date: string;
  default_start_date: string;
  default_end_date: string;
};

export type DashboardInsight = {
  title: string;
  body: string;
  severity: "positive" | "warning" | "neutral";
  metric_keys: string[];
};

export type DashboardInsightsResponse = {
  summary: string;
  insights: DashboardInsight[];
  llm_prompt_template: string;
  knowledge_chunks: Array<{
    id: string;
    title: string;
    content: string;
  }>;
};

export type UploadItem = {
  id: string;
  upload_type: string;
  import_type: string;
  status: string;
  error_message: string | null;
  rows_inserted: number;
  rows_skipped: number;
  can_reprocess: boolean;
  uploaded_at: string;
};

export type Integration = {
  id: string;
  provider: string;
  status: string;
  region: string | null;
  external_seller_id: string | null;
  connected_at: string | null;
  last_synced_at: string | null;
  created_at: string;
  updated_at: string;
};

export type SyncJob = {
  id: string;
  job_type: string;
  status: string;
  progress_percent: number;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  rows_processed: number;
  created_at: string;
};

export type IntegrationStatus = {
  integration: Integration | null;
  has_connection: boolean;
  latest_job: SyncJob | null;
};

export type Product = {
  id: string;
  sku: string;
  name: string | null;
  cogs: number;
  created_at: string;
};

export type ProductProfitability = {
  sku: string;
  name: string | null;
  cogs_per_unit: number;
  units_sold: number;
  revenue: number;
  ad_spend: number;
  ad_sales: number;
  fees: number;
  refund: number;
  cogs: number;
  net_profit: number;
  profit_margin: number;
  refund_rate: number;
  acos: number;
  roas: number;
  profit_per_unit: number;
};
