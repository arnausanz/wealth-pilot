import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';
import { api } from '../core/api';
import type {
  CompareResponse,
  SimulationDetailOut,
  SimulationEventOut,
  SimulationOut,
} from '../types';

const STALE = 5 * 60 * 1000;

// ─── Read hooks ───────────────────────────────────────────────────────────────

export function useSavedSimulations() {
  return useQuery<SimulationOut[]>({
    queryKey: ['simulation', 'saved'],
    queryFn: () => api.get<SimulationOut[]>('/api/v1/simulation/saved'),
    staleTime: STALE,
  });
}

export function useSimulationDetail(id: number | null) {
  return useQuery<SimulationDetailOut>({
    queryKey: ['simulation', 'detail', id],
    queryFn: () => api.get<SimulationDetailOut>(`/api/v1/simulation/saved/${id}`),
    enabled: id !== null,
    staleTime: STALE,
  });
}

// ─── Mutation hooks ──────────────────────────────────────────────────────────

interface SimulationCreatePayload {
  name: string;
  description?: string;
  base_scenario_type?: string;
  horizon_months?: number;
}

export function useCreateSimulation() {
  const qc = useQueryClient();
  return useMutation<SimulationOut, Error, SimulationCreatePayload>({
    mutationFn: (data) => api.post<SimulationOut>('/api/v1/simulation/saved', data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['simulation', 'saved'] });
    },
  });
}

export function useDeleteSimulation() {
  const qc = useQueryClient();
  return useMutation<void, Error, number>({
    mutationFn: (id) => api.del(`/api/v1/simulation/saved/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['simulation', 'saved'] });
    },
  });
}

interface EventCreatePayload {
  simId: number;
  event_date: string;
  name: string;
  event_type: string;
  amount: number;
  is_permanent?: boolean;
  notes?: string;
}

export function useAddEvent() {
  const qc = useQueryClient();
  return useMutation<SimulationEventOut, Error, EventCreatePayload>({
    mutationFn: ({ simId, ...data }) =>
      api.post<SimulationEventOut>(`/api/v1/simulation/saved/${simId}/events`, data),
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: ['simulation', 'detail', variables.simId] });
    },
  });
}

export function useDeleteEvent() {
  const qc = useQueryClient();
  return useMutation<void, Error, { eventId: number; simId: number }>({
    mutationFn: ({ eventId }) => api.del(`/api/v1/simulation/events/${eventId}`),
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: ['simulation', 'detail', variables.simId] });
    },
  });
}

interface ComparePayload {
  sim_ids: number[];
  horizon_years: number;
}

export function useCompareSimulations() {
  return useMutation<CompareResponse, Error, ComparePayload>({
    mutationFn: (data) =>
      api.post<CompareResponse>('/api/v1/simulation/compare', data),
  });
}
