import { useQuery } from '@tanstack/react-query';
import { api } from '../core/api';
import type { MarketPricesResponse } from '../types';

export function useMarketPrices() {
  return useQuery<MarketPricesResponse>({
    queryKey: ['market', 'prices'],
    queryFn: () => api.get<MarketPricesResponse>('/api/v1/market/prices'),
    refetchInterval: 5 * 60 * 1000,
  });
}
