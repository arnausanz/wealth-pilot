// ─── Backend retorna Decimal com a string ──────────────────────────────────
// Tots els camps numèrics de l'API arriben com a string.
// Usa parseFloat() o el helper n() per convertir-los.
export const n = (v: string | number | null | undefined): number =>
  v == null ? 0 : typeof v === 'number' ? v : parseFloat(v) || 0;

// ─── Net Worth ──────────────────────────────────────────────────────────────

export interface AssetSnapshot {
  asset_id: number;
  display_name: string;
  ticker_yf: string;
  shares: string | number;
  price_eur: string | number;
  value_eur: string | number;
  cost_basis_eur: string | number;
  pnl_eur: string | number;
  pnl_pct: string | number;
  color_hex?: string;
  weight_actual_pct?: string | number;
}

export interface NetWorthSnapshot {
  id: number;
  snapshot_date: string;                        // "YYYY-MM-DD"
  total_net_worth: string | number;
  investment_portfolio_value: string | number;  // inv_value backend field
  cash_and_bank_value: string | number;         // cash_value backend field
  real_estate_value: string | number;
  pension_value: string | number;
  other_assets_value: string | number;
  total_liabilities: string | number;
  change_eur: string | number;
  change_pct: string | number;
  trigger_source: string;
  created_at: string;
  asset_snapshots: AssetSnapshot[];
}

export interface NetWorthHistoryResponse {
  snapshots: NetWorthSnapshot[];
  period: string;
  current_net_worth: string | number;
  change_eur_period: string | number;
  change_pct_period: string | number;
}

// ─── Market Prices ──────────────────────────────────────────────────────────

export interface AssetPrice {
  asset_id: number;
  display_name: string;
  ticker_yf: string;
  asset_type: string;
  price_close: string | number | null;
  price_date: string | null;
  currency: string;
  is_stale: boolean;
  stale_days: number;
  change_pct_1d: string | number | null;
  change_eur_1d: string | number | null;
}

export interface MarketPricesResponse {
  prices: AssetPrice[];
  total_assets: number;
  fresh_count: number;
  stale_count: number;
  no_data_count: number;
  cached: boolean;
  cache_age_seconds: number | null;
}

// ─── Asset colors (per ticker_yf) ──────────────────────────────────────────
export const ASSET_COLORS: Record<string, string> = {
  'IWDA.AS': '#3B82F6',
  'PPFB.DE': '#F59E0B',
  'IMAE.AS': '#8B5CF6',
  'EMIM.AS': '#06B6D4',
  'CSJP.AS': '#10B981',
  'WDEF.MI': '#F97316',
  'BTC-EUR': '#E11D48',
};

export const ASSET_COLOR_DEFAULT = '#64748B';

// ─── Portfolio / Rebalanceig ─────────────────────────────────────────────────

export interface RebalanceSuggestion {
  asset_id: number;
  display_name: string;
  ticker_yf: string | null;
  color_hex: string | null;
  value_eur: string | number;
  weight_actual_pct: string | number;
  target_weight_pct: string | number | null;
  weight_diff_pct: string | number | null;
  direction: 'overweight' | 'underweight' | 'missing' | 'on_track';
  action_eur: string | number | null;
}

export interface RebalanceResponse {
  snapshot_date: string;
  total_investment_eur: string | number;
  total_target_pct: string | number | null;
  suggestions: RebalanceSuggestion[];
}

export interface PortfolioSummaryResponse {
  snapshot_date: string;
  total_net_worth: string | number;
  investment_portfolio_value: string | number;
  cash_and_bank_value: string | number;
  change_eur: string | number | null;
  change_pct: string | number | null;
  on_track: boolean | null;
  on_track_detail: string | null;
}

// ─── Simulation ──────────────────────────────────────────────────────────────

export interface ScenarioInfo {
  scenario_type: 'adverse' | 'base' | 'optimistic';
  blended_return_pct: string | number;
  label: string;
  description: string;
}

export interface ScenariosInfoResponse {
  scenarios: ScenarioInfo[];
  monthly_contributions: string | number;
  current_investment_eur: string | number;
}

export interface ScenarioProjection {
  scenario_type: 'adverse' | 'base' | 'optimistic';
  label: string;
  annual_return_pct: string | number;
  end_value: string | number;
  total_return_eur: string | number;
  total_return_pct: string | number;
  total_contributions_eur: string | number;
  cagr_pct: string | number | null;
  data_points: (string | number)[];
}

export interface ProjectionResponse {
  horizon_years: number;
  horizon_months: number;
  start_value: string | number;
  monthly_contribution: string | number;
  home_purchase_target: string | number | null;
  home_purchase_date: string | null;
  scenarios: Record<'adverse' | 'base' | 'optimistic', ScenarioProjection>;
}

// ─── History ─────────────────────────────────────────────────────────────────

export interface TransactionOut {
  id: number;
  tx_date: string;
  tx_type: string;
  amount_eur: string | number;
  description: string | null;
  mw_symbol: string | null;
  display_name: string | null;
  ticker_yf: string | null;
  color_hex: string | null;
  shares: string | number | null;
  account_name: string | null;
}

export interface TransactionsResponse {
  transactions: TransactionOut[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface AssetInvestmentSummary {
  asset_id: number;
  display_name: string;
  ticker_yf: string | null;
  color_hex: string | null;
  shares: string | number;
  total_invested_eur: string | number;
  avg_cost_eur: string | number | null;
  current_price_eur: string | number | null;
  current_value_eur: string | number | null;
  pnl_eur: string | number | null;
  pnl_pct: string | number | null;
  buy_count: number;
  sell_count: number;
  first_buy_date: string | null;
  last_buy_date: string | null;
}

export interface InvestmentSummaryResponse {
  assets: AssetInvestmentSummary[];
  total_invested_eur: string | number;
  total_current_value_eur: string | number | null;
  total_pnl_eur: string | number | null;
  total_pnl_pct: string | number | null;
}

// ─── Config ───────────────────────────────────────────────────────────────────

export interface AssetConfigOut {
  id: number;
  name: string;
  display_name: string;
  ticker_yf: string | null;
  ticker_mw: string | null;
  isin: string | null;
  asset_type: string;
  currency: string;
  color_hex: string | null;
  target_weight: string | number | null;
  is_active: boolean;
  sort_order: number;
}

export interface AssetConfigPatch {
  display_name?: string;
  ticker_yf?: string;
  ticker_mw?: string;
  isin?: string;
  color_hex?: string;
  target_weight?: number | null;
  is_active?: boolean;
  sort_order?: number;
}

export interface AssetConfigCreate {
  name: string;
  display_name: string;
  ticker_yf?: string;
  ticker_mw?: string;
  isin?: string;
  asset_type?: string;
  currency?: string;
  color_hex?: string;
  target_weight?: number;
  sort_order?: number;
}

export interface ContributionOut {
  id: number;
  asset_id: number;
  asset_display_name: string;
  asset_ticker_yf: string | null;
  asset_color_hex: string | null;
  amount: string | number;
  day_of_month: number;
  is_active: boolean;
  notes: string | null;
}

export interface ContributionPatch {
  amount?: number;
  day_of_month?: number;
  is_active?: boolean;
  notes?: string;
}

export interface ContributionCreate {
  asset_id: number;
  amount: number;
  day_of_month?: number;
  notes?: string;
}

export interface ScenarioRow {
  asset_id: number;
  display_name: string;
  ticker_yf: string | null;
  adverse: string | number | null;
  base: string | number | null;
  optimistic: string | number | null;
}

export interface ObjectiveOut {
  id: number;
  key: string;
  name: string;
  description: string | null;
  objective_type: string;
  target_amount: string | number;
  target_date: string | null;
  current_amount: string | number;
  is_active: boolean;
}

export interface ObjectivePatch {
  name?: string;
  description?: string;
  target_amount?: number;
  target_date?: string;
  current_amount?: number;
  is_active?: boolean;
}

export interface ParameterOut {
  key: string;
  value: string;
  value_type: string;
  description: string | null;
  category: string | null;
  is_editable: boolean;
}

export interface WeightCheckResponse {
  total_weight: string | number;
  is_valid: boolean;
  message: string;
}

// ─── Analytics ────────────────────────────────────────────────────────────────

export interface ExpenseCategory {
  category: string;
  total_eur: string | number;
  pct_of_total: string | number;
  tx_count: number;
  color_hex: string | null;
}
export interface ExpenseBreakdownResponse {
  year: number;
  month: number | null;
  categories: ExpenseCategory[];
  total_eur: string | number;
}
export interface CashflowMonth {
  month: string;
  income_eur: string | number;
  expenses_eur: string | number;
  investments_eur: string | number;
  savings_eur: string | number;
  savings_rate_pct: string | number | null;
}
export interface CashflowResponse {
  months: CashflowMonth[];
  avg_income: string | number;
  avg_expenses: string | number;
  avg_savings_rate_pct: string | number | null;
}
export interface NetWorthMonth {
  month: string;
  total_net_worth: string | number;
  investment_value: string | number;
  cash_value: string | number;
}
export interface NetWorthEvolutionResponse {
  months: NetWorthMonth[];
}
export interface AnalyticsAlert {
  id: string;
  severity: 'info' | 'warning' | 'critical';
  title: string;
  detail: string;
  category: string | null;
}
export interface AlertsResponse {
  alerts: AnalyticsAlert[];
}

// ─── Open Simulator ───────────────────────────────────────────────────────────

export interface SimulationOut {
  id: number;
  name: string;
  description: string | null;
  base_scenario_type: string;
  horizon_months: number;
  is_pinned: boolean;
  created_at: string;
}
export interface SimulationEventOut {
  id: number;
  simulation_id: number;
  event_date: string;
  name: string;
  event_type: string;
  amount: string | number;
  is_permanent: boolean;
  notes: string | null;
}
export interface SimulationDetailOut {
  id: number;
  name: string;
  description: string | null;
  base_scenario_type: string;
  horizon_months: number;
  is_pinned: boolean;
  events: SimulationEventOut[];
}
export interface ProjectionSeries {
  sim_id: number | null;
  name: string;
  color: string;
  annual_return_pct: string | number;
  data_points: (string | number)[];
  end_value: string | number;
  total_contributions_eur: string | number;
  total_return_eur: string | number;
}
export interface CompareResponse {
  horizon_years: number;
  start_value: string | number;
  series: ProjectionSeries[];
}
