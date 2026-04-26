/**
 * API client for The AI Scientist backend.
 *
 * All functions return typed data matching the FastAPI response models.
 * The Vite dev proxy forwards /api → http://localhost:8000
 * so no base URL config is needed.
 */

// ---------------------------------------------------------------------------
// Shared types
// ---------------------------------------------------------------------------

export type ExperimentStatus = "Pending" | "In Progress" | "Completed" | "Needs Review";

export interface Paper {
  title: string;
  authors: string[];
  year: number;
  url: string;
  abstract?: string;
  abstract_summary?: string;
  source: string;
  similarity?: number;
}

export interface LiteratureResult {
  novelty_signal: "not_found" | "similar_work_exists" | "exact_match_found";
  gap_analysis: string;
  references: Paper[];
}

export interface ProtocolStep {
  step_number: number;
  title: string;
  description: string;
  duration_minutes: number;
  equipment_needed: string[];
  notes?: string;
}

export interface Reagent {
  name: string;
  catalog_number: string;
  supplier: string;
  quantity: string;
  unit_cost_usd: number;
  total_cost_usd: number;
  hazard_class?: string;
}

export interface BudgetLine {
  category: string;
  description: string;
  cost_usd: number;
}

export interface Budget {
  line_items: BudgetLine[];
  grand_total_usd: number;
  currency_note: string;
}

export interface TimelinePhase {
  phase_name: string;
  duration_days: number;
  tasks: string[];
  depends_on: string[];
  milestone?: string;
}

export interface ValidationApproach {
  primary_metric: string;
  success_threshold: string;
  statistical_test: string;
  controls: string[];
  sample_size_per_group?: number;
  power?: number;
  alpha?: number;
  effect_size_estimate?: string;
}

export interface BiosafetyAssessment {
  level: string;
  hazardous_materials: string[];
  required_ppe: string[];
  waste_disposal_protocol: string;
  special_requirements: string[];
  regulatory_notes?: string;
}

export interface RiskFactor {
  description: string;
  severity: string;
  likelihood: string;
  mitigation: string;
}

export interface ExperimentPlan {
  plan_id: string;
  hypothesis: string;
  refined_hypothesis: string;
  experiment_domain: string;
  sub_hypotheses: string[];
  alternative_hypotheses: string[];
  expected_outcomes: string[];
  literature_result: LiteratureResult;
  protocol_steps: ProtocolStep[];
  materials: Reagent[];
  budget: Budget;
  timeline: TimelinePhase[];
  validation: ValidationApproach;
  biosafety?: BiosafetyAssessment;
  risks: RiskFactor[];
  quality_score?: number;
  created_at: string;
  feedback_incorporated: boolean;
}

export interface RunResponse {
  plan_id: string;
  quality_score: number;
  quality_errors: string[];
  plan: ExperimentPlan;
}

export interface PlanSummary {
  plan_id: string;
  hypothesis: string;
  experiment_domain: string;
  quality_score?: number;
  created_at: string;
}

export interface PlansListResponse {
  count: number;
  offset: number;
  plans: PlanSummary[];
}

export interface OptimizationItem {
  item: string;
  original_supplier: string;
  alt_supplier: string;
  original_cost: number;
  optimized_cost: number;
  savings_pct: number;
  risk: string;
  notes: string;
}

export interface OptimizeResponse {
  plan_id: string;
  mode: string;
  optimizations: OptimizationItem[];
  total_original_usd: number;
  total_optimized_usd: number;
  total_savings_pct: number;
}

export interface CollaboratorProfile {
  name: string;
  initials: string;
  institution: string;
  department: string;
  match_pct: number;
  topic: string;
  recent_publication: string;
  domains: string[];
}

export interface CollaboratorsResponse {
  plan_id?: string;
  query?: string;
  collaborators: CollaboratorProfile[];
}

export interface ReviewEntry {
  review_id: string;
  plan_id: string;
  section: string;
  rating: number;
  comment: string;
  correction: string;
  reviewer_name: string;
  initials: string;
  created_at: string;
}

export interface ReviewsResponse {
  plan_id: string;
  reviews: ReviewEntry[];
  avg_rating: number;
  count: number;
}

export interface ReportResponse {
  plan_id: string;
  title: string;
  markdown: string;
  word_count: number;
  created_at: string;
}

export interface LitSearchResponse {
  query: string;
  count: number;
  papers: Paper[];
}

export interface HealthResponse {
  status: string;
  version: string;
  uptime_seconds: number;
}

export interface SSEEvent {
  type: "node_start" | "node_complete" | "node_error" | "complete" | "error";
  node?: string;
  message?: string;
  plan?: ExperimentPlan;
  error?: string;
}

// ---------------------------------------------------------------------------
// Error class
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly detail: string
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

// ---------------------------------------------------------------------------
// Fetch helper
// ---------------------------------------------------------------------------

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail ?? body.message ?? detail;
    } catch {
      // ignore parse errors
    }
    throw new ApiError(res.status, detail);
  }

  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Pipeline endpoints
// ---------------------------------------------------------------------------

export const api = {
  /** Run the full pipeline synchronously (25–45 s). */
  runPipeline(hypothesis: string, domain = "other"): Promise<RunResponse> {
    return apiFetch<RunResponse>("/api/run", {
      method: "POST",
      body: JSON.stringify({ hypothesis, domain }),
    });
  },

  /**
   * Stream pipeline progress via SSE.
   * The returned EventSource emits events; caller receives each SSEEvent.
   * To trigger a full run with hypothesis we open the SSE connection with
   * a POST-encoded body via fetch and read the stream manually.
   */
  streamPipeline(
    hypothesis: string,
    domain = "other",
    onEvent: (event: SSEEvent) => void,
    onError?: (err: Error) => void
  ): () => void {
    let cancelled = false;
    let controller: AbortController | null = new AbortController();

    (async () => {
      try {
        const res = await fetch("/api/run/stream", {
          method: "POST",
          headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
          body: JSON.stringify({ hypothesis, domain }),
          signal: controller?.signal,
        });

        if (!res.ok || !res.body) {
          const detail = `SSE connection failed: HTTP ${res.status}`;
          onError?.(new ApiError(res.status, detail));
          return;
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (!cancelled) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const parts = buffer.split("\n\n");
          buffer = parts.pop() ?? "";

          for (const part of parts) {
            const dataLine = part
              .split("\n")
              .find((l) => l.startsWith("data:"));
            if (!dataLine) continue;
            const json = dataLine.slice(5).trim();
            try {
              const event: SSEEvent = JSON.parse(json);
              onEvent(event);
            } catch {
              // skip malformed event
            }
          }
        }
      } catch (err) {
        if (!cancelled) {
          onError?.(err instanceof Error ? err : new Error(String(err)));
        }
      }
    })();

    return () => {
      cancelled = true;
      controller?.abort();
      controller = null;
    };
  },

  // ---------------------------------------------------------------------------
  // Plan endpoints
  // ---------------------------------------------------------------------------

  getPlan(planId: string): Promise<ExperimentPlan> {
    return apiFetch<ExperimentPlan>(`/api/plan/${planId}`);
  },

  listPlans(limit = 20, offset = 0): Promise<PlansListResponse> {
    return apiFetch<PlansListResponse>(`/api/plans?limit=${limit}&offset=${offset}`);
  },

  // ---------------------------------------------------------------------------
  // Feedback
  // ---------------------------------------------------------------------------

  submitFeedback(data: {
    plan_id: string;
    section: string;
    original_content: string;
    correction: string;
    experiment_domain: string;
  }): Promise<{ feedback_id: string }> {
    return apiFetch("/api/feedback", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  // ---------------------------------------------------------------------------
  // Cost Optimizer
  // ---------------------------------------------------------------------------

  optimizePlan(planId: string, mode: "lean" | "standard" | "premium" = "standard"): Promise<OptimizeResponse> {
    return apiFetch<OptimizeResponse>("/api/optimize", {
      method: "POST",
      body: JSON.stringify({ plan_id: planId, mode }),
    });
  },

  // ---------------------------------------------------------------------------
  // Collaborators
  // ---------------------------------------------------------------------------

  findCollaborators(params: { plan_id?: string; query?: string; domain?: string }): Promise<CollaboratorsResponse> {
    const qs = new URLSearchParams();
    if (params.plan_id) qs.set("plan_id", params.plan_id);
    if (params.query) qs.set("query", params.query);
    if (params.domain) qs.set("domain", params.domain);
    return apiFetch<CollaboratorsResponse>(`/api/collaborators?${qs.toString()}`);
  },

  // ---------------------------------------------------------------------------
  // Reviews
  // ---------------------------------------------------------------------------

  submitReview(data: {
    plan_id: string;
    section: string;
    rating: number;
    comment: string;
    correction?: string;
    reviewer_name?: string;
  }): Promise<ReviewEntry> {
    return apiFetch<ReviewEntry>("/api/reviews", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  getReviews(planId: string): Promise<ReviewsResponse> {
    return apiFetch<ReviewsResponse>(`/api/reviews?plan_id=${planId}`);
  },

  // ---------------------------------------------------------------------------
  // Report
  // ---------------------------------------------------------------------------

  getReport(planId: string): Promise<ReportResponse> {
    return apiFetch<ReportResponse>(`/api/report/${planId}`);
  },

  getReportDownloadUrl(planId: string): string {
    return `/api/report/${planId}/download`;
  },

  // ---------------------------------------------------------------------------
  // Literature search
  // ---------------------------------------------------------------------------

  searchLiterature(query: string, limit = 10): Promise<LitSearchResponse> {
    return apiFetch<LitSearchResponse>("/api/literature/search", {
      method: "POST",
      body: JSON.stringify({ query, limit }),
    });
  },

  // ---------------------------------------------------------------------------
  // Health
  // ---------------------------------------------------------------------------

  health(): Promise<HealthResponse> {
    return apiFetch<HealthResponse>("/health");
  },
};
