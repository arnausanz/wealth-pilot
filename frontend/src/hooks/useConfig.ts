import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../core/api';
import type {
  AssetConfigOut,
  AssetConfigPatch,
  AssetConfigCreate,
  ContributionOut,
  ContributionPatch,
  ContributionCreate,
  ScenarioRow,
  ObjectiveOut,
  ObjectivePatch,
  ParameterOut,
  WeightCheckResponse,
} from '../types';

// ─── Assets ──────────────────────────────────────────────────────────────────

export function useConfigAssets() {
  return useQuery<AssetConfigOut[]>({
    queryKey: ['config', 'assets'],
    queryFn: () => api.get<AssetConfigOut[]>('/api/v1/config/assets'),
    staleTime: 2 * 60 * 1000,
  });
}

export function useWeightCheck() {
  return useQuery<WeightCheckResponse>({
    queryKey: ['config', 'weight-check'],
    queryFn: () => api.get<WeightCheckResponse>('/api/v1/config/assets/weight-check'),
    staleTime: 0,
  });
}

export function usePatchAsset() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: AssetConfigPatch }) =>
      api.patch<AssetConfigOut>(`/api/v1/config/assets/${id}`, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['config', 'assets'] });
      qc.invalidateQueries({ queryKey: ['config', 'weight-check'] });
    },
  });
}

export function useCreateAsset() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: AssetConfigCreate) =>
      api.post<AssetConfigOut>('/api/v1/config/assets', data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['config', 'assets'] });
      qc.invalidateQueries({ queryKey: ['config', 'weight-check'] });
    },
  });
}

// ─── Contributions ────────────────────────────────────────────────────────────

export function useConfigContributions() {
  return useQuery<ContributionOut[]>({
    queryKey: ['config', 'contributions'],
    queryFn: () => api.get<ContributionOut[]>('/api/v1/config/contributions'),
    staleTime: 2 * 60 * 1000,
  });
}

export function usePatchContribution() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: ContributionPatch }) =>
      api.patch<ContributionOut>(`/api/v1/config/contributions/${id}`, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['config', 'contributions'] });
    },
  });
}

export function useCreateContribution() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ContributionCreate) =>
      api.post<ContributionOut>('/api/v1/config/contributions', data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['config', 'contributions'] });
    },
  });
}

export function useDeleteContribution() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.del(`/api/v1/config/contributions/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['config', 'contributions'] });
    },
  });
}

// ─── Scenarios ────────────────────────────────────────────────────────────────

export function useConfigScenarios() {
  return useQuery<ScenarioRow[]>({
    queryKey: ['config', 'scenarios'],
    queryFn: () => api.get<ScenarioRow[]>('/api/v1/config/scenarios'),
    staleTime: 2 * 60 * 1000,
  });
}

export function usePatchScenario() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      assetId,
      scenarioType,
      annualReturn,
    }: {
      assetId: number;
      scenarioType: 'adverse' | 'base' | 'optimistic';
      annualReturn: number;
    }) =>
      api.patch<ScenarioRow>(
        `/api/v1/config/scenarios/${assetId}/${scenarioType}`,
        { annual_return: annualReturn },
      ),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['config', 'scenarios'] });
      // Invalida les simulacions perquè els retorns han canviat
      qc.invalidateQueries({ queryKey: ['simulation'] });
    },
  });
}

// ─── Objectives ──────────────────────────────────────────────────────────────

export function useConfigObjectives() {
  return useQuery<ObjectiveOut[]>({
    queryKey: ['config', 'objectives'],
    queryFn: () => api.get<ObjectiveOut[]>('/api/v1/config/objectives'),
    staleTime: 2 * 60 * 1000,
  });
}

export function usePatchObjective() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: ObjectivePatch }) =>
      api.patch<ObjectiveOut>(`/api/v1/config/objectives/${id}`, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['config', 'objectives'] });
      qc.invalidateQueries({ queryKey: ['simulation'] });
    },
  });
}

// ─── Parameters ──────────────────────────────────────────────────────────────

export function useConfigParameters(category?: string) {
  return useQuery<ParameterOut[]>({
    queryKey: ['config', 'parameters', category ?? 'all'],
    queryFn: () => {
      const qs = category ? `?category=${encodeURIComponent(category)}` : '';
      return api.get<ParameterOut[]>(`/api/v1/config/parameters${qs}`);
    },
    staleTime: 2 * 60 * 1000,
  });
}

export function usePatchParameter() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ key, value }: { key: string; value: string }) =>
      api.patch<ParameterOut>(`/api/v1/config/parameters/${key}`, { value }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['config', 'parameters'] });
    },
  });
}

// ─── Reset ────────────────────────────────────────────────────────────────────

export function useResetDefaults() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.post<{ ok: boolean; changes: Record<string, number> }>('/api/v1/config/reset'),
    onSuccess: () => {
      // Invalida totes les queries de config i simulació
      qc.invalidateQueries({ queryKey: ['config'] });
      qc.invalidateQueries({ queryKey: ['simulation'] });
      qc.invalidateQueries({ queryKey: ['portfolio'] });
    },
  });
}
