import { useQuery } from '@tanstack/react-query';
import { api } from '../core/api';
import type { RebalanceResponse, PortfolioSummaryResponse } from '../types';

export function usePortfolioSummary() {
  return useQuery<PortfolioSummaryResponse>({
    queryKey: ['portfolio', 'summary'],
    queryFn: () => api.get<PortfolioSummaryResponse>('/api/v1/portfolio/summary'),
    staleTime: 5 * 60 * 1000,
  });
}

export function useRebalance() {
  return useQuery<RebalanceResponse>({
    queryKey: ['portfolio', 'rebalance'],
    queryFn: () => api.get<RebalanceResponse>('/api/v1/portfolio/rebalance'),
    staleTime: 5 * 60 * 1000,
  });
}
