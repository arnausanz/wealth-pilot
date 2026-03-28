import { useQuery, keepPreviousData } from '@tanstack/react-query';
import { api } from '../core/api';
import type { ProjectionResponse, ScenariosInfoResponse } from '../types';

export function useScenariosInfo() {
  return useQuery<ScenariosInfoResponse>({
    queryKey: ['simulation', 'scenarios'],
    queryFn: () => api.get<ScenariosInfoResponse>('/api/v1/simulation/scenarios'),
    staleTime: 10 * 60 * 1000,
  });
}

export function useProjection(horizonYears: number, monthlyContribution?: number) {
  const params = new URLSearchParams({ horizon_years: String(horizonYears) });
  if (monthlyContribution !== undefined) {
    params.set('monthly_contribution', String(monthlyContribution));
  }

  return useQuery<ProjectionResponse>({
    queryKey: ['simulation', 'project', horizonYears, monthlyContribution],
    queryFn: () => api.get<ProjectionResponse>(`/api/v1/simulation/project?${params}`),
    staleTime: 5 * 60 * 1000,
    // Mostra les dades anteriors mentre es carreguen les noves (evita buit visual)
    placeholderData: keepPreviousData,
  });
}
