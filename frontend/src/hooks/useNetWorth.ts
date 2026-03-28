import { useQuery } from '@tanstack/react-query';
import { api } from '../core/api';
import type { NetWorthHistoryResponse } from '../types';

export function useNetWorthHistory(period: string) {
  return useQuery<NetWorthHistoryResponse>({
    queryKey: ['networth', 'history', period],
    queryFn: () => api.get<NetWorthHistoryResponse>(`/api/v1/networth/history?period=${period}`),
  });
}
