import { useQuery } from '@tanstack/react-query';
import { api } from '../core/api';
import type {
  AlertsResponse,
  CashflowResponse,
  ExpenseBreakdownResponse,
  NetWorthEvolutionResponse,
} from '../types';

const STALE = 5 * 60 * 1000;

export function useExpenseBreakdown(year: number, month?: number) {
  const params = new URLSearchParams({ year: String(year) });
  if (month !== undefined) params.set('month', String(month));

  return useQuery<ExpenseBreakdownResponse>({
    queryKey: ['analytics', 'expenses', year, month ?? null],
    queryFn: () =>
      api.get<ExpenseBreakdownResponse>(`/api/v1/analytics/expenses?${params}`),
    staleTime: STALE,
  });
}

export function useCashflow(months = 12) {
  return useQuery<CashflowResponse>({
    queryKey: ['analytics', 'cashflow', months],
    queryFn: () =>
      api.get<CashflowResponse>(`/api/v1/analytics/cashflow?months=${months}`),
    staleTime: STALE,
  });
}

export function useNetworthEvolution(months = 24) {
  return useQuery<NetWorthEvolutionResponse>({
    queryKey: ['analytics', 'evolution', months],
    queryFn: () =>
      api.get<NetWorthEvolutionResponse>(`/api/v1/analytics/evolution?months=${months}`),
    staleTime: STALE,
  });
}

export function useAnalyticsAlerts() {
  return useQuery<AlertsResponse>({
    queryKey: ['analytics', 'alerts'],
    queryFn: () => api.get<AlertsResponse>('/api/v1/analytics/alerts'),
    staleTime: STALE,
  });
}
