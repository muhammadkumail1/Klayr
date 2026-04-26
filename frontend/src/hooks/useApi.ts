/**
 * TanStack Query hooks for The AI Scientist API.
 *
 * All hooks follow the pattern:
 *   - Queries: useXxx(params?) → { data, isLoading, isError, error }
 *   - Mutations: useXxx() → { mutate, isPending, isSuccess, isError, data, error }
 */

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseQueryOptions,
} from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  ExperimentPlan,
  OptimizeResponse,
  CollaboratorsResponse,
  ReviewsResponse,
  ReviewEntry,
  ReportResponse,
  LitSearchResponse,
  RunResponse,
  PlansListResponse,
} from "@/lib/api";

// ---------------------------------------------------------------------------
// Query keys (centralised to avoid typos)
// ---------------------------------------------------------------------------

export const queryKeys = {
  plans: (limit?: number, offset?: number) => ["plans", limit, offset] as const,
  plan: (id: string) => ["plan", id] as const,
  optimize: (planId: string, mode: string) => ["optimize", planId, mode] as const,
  collaborators: (planId?: string, query?: string, domain?: string) =>
    ["collaborators", planId, query, domain] as const,
  reviews: (planId: string) => ["reviews", planId] as const,
  report: (planId: string) => ["report", planId] as const,
  litSearch: (query: string) => ["lit-search", query] as const,
  health: () => ["health"] as const,
};

// ---------------------------------------------------------------------------
// Plans
// ---------------------------------------------------------------------------

export function usePlans(limit = 20, offset = 0) {
  return useQuery<PlansListResponse, Error>({
    queryKey: queryKeys.plans(limit, offset),
    queryFn: () => api.listPlans(limit, offset),
    staleTime: 30_000,
  });
}

export function usePlan(planId: string | undefined) {
  return useQuery<ExperimentPlan, Error>({
    queryKey: queryKeys.plan(planId ?? ""),
    queryFn: () => api.getPlan(planId!),
    enabled: !!planId,
    staleTime: 60_000,
  });
}

// ---------------------------------------------------------------------------
// Pipeline mutations
// ---------------------------------------------------------------------------

export function useRunPipeline() {
  const queryClient = useQueryClient();

  return useMutation<RunResponse, Error, { hypothesis: string; domain?: string }>({
    mutationFn: ({ hypothesis, domain }) => api.runPipeline(hypothesis, domain),
    onSuccess: (data) => {
      // Pre-populate the plan in cache so ExperimentDetail loads immediately
      queryClient.setQueryData(queryKeys.plan(data.plan_id), data.plan);
      // Invalidate list so DashboardHome refreshes
      queryClient.invalidateQueries({ queryKey: ["plans"] });
    },
  });
}

// ---------------------------------------------------------------------------
// Feedback mutation
// ---------------------------------------------------------------------------

export function useSubmitFeedback() {
  return useMutation<
    { feedback_id: string },
    Error,
    {
      plan_id: string;
      section: string;
      original_content: string;
      correction: string;
      experiment_domain: string;
    }
  >({
    mutationFn: (data) => api.submitFeedback(data),
  });
}

// ---------------------------------------------------------------------------
// Cost Optimizer
// ---------------------------------------------------------------------------

export function useOptimize(
  planId: string | undefined,
  mode: "lean" | "standard" | "premium" = "standard",
  options?: { enabled?: boolean }
) {
  return useQuery<OptimizeResponse, Error>({
    queryKey: queryKeys.optimize(planId ?? "", mode),
    queryFn: () => api.optimizePlan(planId!, mode),
    enabled: !!planId && (options?.enabled ?? false),
    staleTime: 120_000,
  });
}

export function useOptimizeMutation() {
  const queryClient = useQueryClient();
  return useMutation<
    OptimizeResponse,
    Error,
    { planId: string; mode: "lean" | "standard" | "premium" }
  >({
    mutationFn: ({ planId, mode }) => api.optimizePlan(planId, mode),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.optimize(data.plan_id, data.mode), data);
    },
  });
}

// ---------------------------------------------------------------------------
// Collaborators
// ---------------------------------------------------------------------------

export function useCollaborators(params: {
  plan_id?: string;
  query?: string;
  domain?: string;
  enabled?: boolean;
}) {
  return useQuery<CollaboratorsResponse, Error>({
    queryKey: queryKeys.collaborators(params.plan_id, params.query, params.domain),
    queryFn: () =>
      api.findCollaborators({
        plan_id: params.plan_id,
        query: params.query,
        domain: params.domain,
      }),
    enabled: params.enabled ?? !!(params.plan_id || params.query),
    staleTime: 60_000,
  });
}

export function useCollaboratorsMutation() {
  return useMutation<
    CollaboratorsResponse,
    Error,
    { plan_id?: string; query?: string; domain?: string }
  >({
    mutationFn: (params) => api.findCollaborators(params),
  });
}

// ---------------------------------------------------------------------------
// Reviews
// ---------------------------------------------------------------------------

export function useReviews(planId: string | undefined) {
  return useQuery<ReviewsResponse, Error>({
    queryKey: queryKeys.reviews(planId ?? ""),
    queryFn: () => api.getReviews(planId!),
    enabled: !!planId,
    staleTime: 30_000,
  });
}

export function useSubmitReview() {
  const queryClient = useQueryClient();
  return useMutation<
    ReviewEntry,
    Error,
    {
      plan_id: string;
      section: string;
      rating: number;
      comment: string;
      correction?: string;
      reviewer_name?: string;
    }
  >({
    mutationFn: (data) => api.submitReview(data),
    onSuccess: (_data, variables) => {
      // Refetch reviews for the plan
      queryClient.invalidateQueries({ queryKey: queryKeys.reviews(variables.plan_id) });
    },
  });
}

// ---------------------------------------------------------------------------
// Report
// ---------------------------------------------------------------------------

export function useReport(planId: string | undefined, enabled = false) {
  return useQuery<ReportResponse, Error>({
    queryKey: queryKeys.report(planId ?? ""),
    queryFn: () => api.getReport(planId!),
    enabled: !!planId && enabled,
    staleTime: 120_000,
  });
}

// ---------------------------------------------------------------------------
// Literature search
// ---------------------------------------------------------------------------

export function useLitSearchMutation() {
  return useMutation<LitSearchResponse, Error, { query: string; limit?: number }>({
    mutationFn: ({ query, limit }) => api.searchLiterature(query, limit),
  });
}

// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------

export function useHealth() {
  return useQuery({
    queryKey: queryKeys.health(),
    queryFn: () => api.health(),
    staleTime: 60_000,
    retry: 1,
  });
}
