import { useQuery } from '@tanstack/react-query';
import { api } from '../core/api';
import type { InvestmentSummaryResponse, TransactionsResponse } from '../types';

interface TransactionFilters {
  page?: number;
  per_page?: number;
  tx_type?: string;
  ticker_yf?: string;
  date_from?: string;
  date_to?: string;
}

export function useTransactions(filters: TransactionFilters = {}) {
  const params = new URLSearchParams();
  if (filters.page)         params.set('page', String(filters.page));
  if (filters.per_page)     params.set('per_page', String(filters.per_page));
  if (filters.tx_type)      params.set('tx_type', filters.tx_type);
  if (filters.ticker_yf)    params.set('ticker_yf', filters.ticker_yf);
  if (filters.date_from)    params.set('date_from', filters.date_from);
  if (filters.date_to)      params.set('date_to', filters.date_to);

  return useQuery<TransactionsResponse>({
    queryKey: ['history', 'transactions', filters],
    queryFn: () => api.get<TransactionsResponse>(`/api/v1/history/transactions?${params}`),
    staleTime: 5 * 60 * 1000,
  });
}

export function useInvestmentSummary() {
  return useQuery<InvestmentSummaryResponse>({
    queryKey: ['history', 'investments'],
    queryFn: () => api.get<InvestmentSummaryResponse>('/api/v1/history/investments'),
    staleTime: 5 * 60 * 1000,
  });
}
