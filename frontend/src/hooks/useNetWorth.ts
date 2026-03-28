import { useQuery } from '@tanstack/react-query';
import { api } from '../core/api';
import type { NetWorthHistoryResponse } from '../types';

// Mapeja els labels del TimeSelector als períodes que espera l'API
const PERIOD_API_MAP: Record<string, string> = {
  '1M': '1m',
  '3M': '3m',
  '6M': '6m',
  '1A': '1y',
  'Tot': 'all',
};

export function useNetWorthHistory(period: string) {
  const apiPeriod = PERIOD_API_MAP[period] ?? period;

  return useQuery<NetWorthHistoryResponse>({
    queryKey: ['networth', 'history', apiPeriod],
    queryFn: () => api.get<NetWorthHistoryResponse>(`/api/v1/networth/history?period=${apiPeriod}`),
    staleTime: 5 * 60 * 1000,
  });
}
