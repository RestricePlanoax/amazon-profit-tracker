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
  range_coverage: RangeCoverageStatus[];
  metric_trust: MetricTrust[];
};

export type DataSourceStatus = {
  key: string;
  name: string;
  active: boolean;
  status: string;
  last_refresh_at: string | null;
};

export type RangeCoverageStatus = {
  key: string;
  label: string;
  covered_days: number;
  expected_days: number;
  coverage_pct: number;
  status: "complete" | "partial" | "limited" | "missing";
  latest_data_date: string | null;
};

export type MetricTrust = {
  metric_key: keyof DashboardMetricSet;
  powered_by: string[];
  coverage_pct: number;
  freshness_at: string | null;
  status: "complete" | "partial" | "limited" | "missing";
  note: string;
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
  import_batch_id: string | null;
  upload_type: string;
  import_type: string;
  status: string;
  error_message: string | null;
  rows_inserted: number;
  rows_skipped: number;
  can_reprocess: boolean;
  uploaded_at: string;
};

export type DemoLoadResponse = {
  store_id: string;
  import_batch_id: string;
  rows_inserted: number;
  message: string;
};

export type BulkCogsResult = {
  rows_processed: number;
  products_created: number;
  products_updated: number;
  rows_skipped: number;
  errors: string[];
};

export type MetricCatalogItem = {
  key: keyof DashboardMetricSet;
  label: string;
  category: string;
  format: "currency" | "percent" | "number" | "ratio";
  polarity: "higher_is_better" | "lower_is_better";
  description: string;
  formula_label: string;
  business_question: string;
  warning_threshold: number | null;
  critical_threshold: number | null;
  visible_by_default: boolean;
  dashboard_slot: "headline" | "supporting";
  onboarding_required: boolean;
  sort_order: number;
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

export type ProfitAlert = {
  id: string;
  sku: string | null;
  alert_type: string;
  severity: "low" | "medium" | "high" | "critical";
  title: string;
  message: string;
  metric_value: number | null;
  created_at: string;
  resolved: boolean;
  resolved_at: string | null;
};

export type ProfitAlertsResponse = {
  summary: {
    total_open: number;
    high_priority: number;
    margin_drop: number;
    unexpected_fees: number;
    ad_waste: number;
    return_spike: number;
    storage_risk: number;
  };
  alerts: ProfitAlert[];
};

export type ReturnAnalysisResponse = {
  worst_variants: Array<{
    sku: string;
    variant: string;
    return_rate: number;
    refund_cost: number;
    return_units: number;
    top_reason: string | null;
  }>;
  top_return_reasons: Array<{
    reason: string;
    occurrences: number;
    refund_cost: number;
  }>;
  summary_text: string;
};

export type ReimbursementsResponse = {
  summary: {
    total_pending_amount: number;
    near_expiry_count: number;
    open_cases: number;
  };
  cases: Array<{
    id: string;
    sku: string;
    issue_type: string;
    amount: number;
    status: string;
    detected_at: string;
    claim_deadline: string | null;
    claimed: boolean;
    received: boolean;
  }>;
};

export type StorageAnalysisResponse = {
  summary_text: string;
  slow_moving_inventory: Array<{
    sku: string;
    quantity: number;
    days_in_storage: number;
    monthly_storage_fee: number;
    warning_level: string;
    recommended_action: string;
  }>;
};

export type AdAnalysisResponse = {
  summary_text: string;
  worst_campaigns: Array<{
    campaign_id: string;
    campaign_name: string;
    sku: string;
    daily_spend: number;
    clicks: number;
    orders: number;
    acos: number;
    roas: number;
    conversion_rate: number;
    waste_flag: boolean;
  }>;
};

export type SellerInsight = {
  id: string;
  priority: string;
  headline: string;
  insight_text: string;
  created_at: string;
};

export type DailyInsightsResponse = {
  biggest_profit_leak: string | null;
  worst_sku_today: string | null;
  best_sku_today: string | null;
  recommended_actions: string[];
  insights: SellerInsight[];
};
