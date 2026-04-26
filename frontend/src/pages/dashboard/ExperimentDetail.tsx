import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/StatusBadge";
import { toast } from "sonner";
import {
  usePlan,
  useOptimizeMutation,
  useCollaborators,
  useReviews,
  useSubmitReview,
  useReport,
} from "@/hooks/useApi";
import { api } from "@/lib/api";
import type { OptimizeResponse } from "@/lib/api";
import {
  ArrowLeft,
  Beaker,
  CheckCircle2,
  ChevronRight,
  Clock,
  Download,
  FileText,
  ListChecks,
  Loader2,
  Package,
  RefreshCw,
  Sparkles,
  Star,
  TrendingDown,
  Users,
  Wallet,
} from "lucide-react";

const tabs = [
  "Overview",
  "Literature QC",
  "Protocol",
  "Materials",
  "Budget",
  "Cost Optimizer",
  "Timeline",
  "Validation",
  "Collaboration",
  "Scientist Review",
  "Final Report",
];

const ExperimentDetail = () => {
  const { id } = useParams<{ id: string }>();
  const planId = id ?? "";

  // Core plan
  const { data: plan, isLoading, isError } = usePlan(planId);

  // Cost optimizer
  const [optimizeMode, setOptimizeMode] = useState<"lean" | "standard" | "premium">("standard");
  const [optimizeData, setOptimizeData] = useState<OptimizeResponse | null>(null);
  const optimizeMutation = useOptimizeMutation();

  const handleOptimize = (mode: "lean" | "standard" | "premium") => {
    setOptimizeMode(mode);
    optimizeMutation.mutate(
      { planId, mode },
      {
        onSuccess: (data) => {
          setOptimizeData(data);
          toast.success(`${mode.charAt(0).toUpperCase() + mode.slice(1)} optimization complete!`);
        },
        onError: (err) => toast.error(`Optimization failed: ${err.message}`),
      }
    );
  };

  // Collaboration
  const { data: collabData, isLoading: collabLoading, refetch: refetchCollab } =
    useCollaborators({ plan_id: planId, enabled: true });

  // Reviews
  const { data: reviewsData } = useReviews(planId);
  const submitReviewMutation = useSubmitReview();
  const [reviewState, setReviewState] = useState({
    rating: 4,
    section: "Protocol",
    comment: "",
    correction: "",
    reviewer_name: "Dr. Researcher",
  });

  const handleSubmitReview = () => {
    if (!reviewState.comment.trim()) {
      toast.error("Please add a comment before submitting.");
      return;
    }
    submitReviewMutation.mutate(
      { plan_id: planId, ...reviewState },
      {
        onSuccess: () => {
          toast.success("Review submitted!");
          setReviewState((s) => ({ ...s, comment: "", correction: "" }));
        },
        onError: (err) => toast.error(`Submit failed: ${err.message}`),
      }
    );
  };

  // Final Report
  const [reportEnabled, setReportEnabled] = useState(false);
  const { data: reportData, isLoading: reportLoading, refetch: refetchReport } =
    useReport(planId, reportEnabled);

  const handleGenerateReport = () => {
    setReportEnabled(true);
    if (reportData) refetchReport();
  };

  const handleDownloadReport = () => window.open(api.getReportDownloadUrl(planId), "_blank");

  const handleExportJSON = () => {
    if (!plan) return;
    const blob = new Blob([JSON.stringify(plan, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `experiment_${planId.slice(0, 8)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center px-8">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <span className="ml-3 text-muted-foreground">Loading experiment plan…</span>
      </div>
    );
  }

  if (isError || !plan) {
    return (
      <div className="px-8 py-12 text-center">
        <p className="text-lg font-medium text-foreground">Plan not found.</p>
        <p className="mt-2 text-sm text-muted-foreground">This plan may not exist or was generated in a previous session.</p>
        <Button asChild variant="hero" className="mt-5">
          <Link to="/dashboard/new">Create a new experiment</Link>
        </Button>
      </div>
    );
  }

  const noveltyScore =
    plan.literature_result.novelty_signal === "not_found" ? 9.2
    : plan.literature_result.novelty_signal === "similar_work_exists" ? 6.8
    : 3.5;

  const noveltyLabel: Record<string, string> = {
    not_found: "Novel — no direct prior work found",
    similar_work_exists: "Moderate novelty — related work exists",
    exact_match_found: "Low novelty — direct replication detected",
  };

  const totalBudget = plan.budget.grand_total_usd;
  const domainLabel = plan.experiment_domain.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  const status = (plan.quality_score ?? 0) >= 80 ? "Completed" : plan.feedback_incorporated ? "In Progress" : "Needs Review";
  const createdDate = new Date(plan.created_at).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
  const totalDays = plan.timeline.reduce((s, p) => s + p.duration_days, 0);
  const durationLabel = totalDays >= 7 ? `${Math.round(totalDays / 7)} weeks` : `${totalDays} days`;

  return (
    <div className="px-5 py-6 sm:px-8 sm:py-8">
      {/* Breadcrumb */}
      <nav className="mb-5 flex items-center gap-1.5 text-xs text-muted-foreground" aria-label="Breadcrumb">
        <Link to="/dashboard" className="hover:text-primary">Dashboard</Link>
        <ChevronRight className="h-3 w-3" />
        <Link to="/dashboard/experiments" className="hover:text-primary">Experiments</Link>
        <ChevronRight className="h-3 w-3" />
        <span className="max-w-xs truncate text-foreground">{plan.refined_hypothesis || plan.hypothesis}</span>
      </nav>

      {/* Header */}
      <header className="rounded-2xl border border-border bg-card p-6 shadow-card sm:p-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-3">
              <Button asChild variant="ghost" size="icon" aria-label="Back">
                <Link to="/dashboard"><ArrowLeft className="h-4 w-4" /></Link>
              </Button>
              <h1 className="font-serif-display line-clamp-2 text-2xl font-medium text-foreground sm:text-3xl">
                {plan.refined_hypothesis || plan.hypothesis}
              </h1>
            </div>
            <div className="mt-3 flex flex-wrap items-center gap-3 pl-12">
              <StatusBadge status={status as any} />
              <span className="text-xs text-muted-foreground">Plan ID · {planId.slice(0, 8)}…</span>
              <span className="h-1 w-1 rounded-full bg-border" />
              <span className="text-xs text-muted-foreground">{domainLabel}</span>
              <span className="h-1 w-1 rounded-full bg-border" />
              <span className="text-xs text-muted-foreground">Duration · {durationLabel}</span>
              <span className="h-1 w-1 rounded-full bg-border" />
              <span className="text-xs text-muted-foreground">Created · {createdDate}</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost_dark" size="sm" onClick={handleExportJSON}>
              <Download className="h-4 w-4" />
              Export JSON
            </Button>
            <Button variant="hero" size="sm" onClick={handleGenerateReport}>
              <FileText className="h-4 w-4" />
              Final Report
            </Button>
          </div>
        </div>

        <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {[
            { label: "Protocol Steps", value: plan.protocol_steps.length, icon: ListChecks },
            { label: "Materials", value: plan.materials.length, icon: Package },
            {
              label: optimizeData ? "Optimized Budget" : "Budget",
              value: `$${(optimizeData ? optimizeData.total_optimized_usd : totalBudget).toLocaleString(undefined, { maximumFractionDigits: 0 })}`,
              icon: TrendingDown,
              accent: true,
            },
            { label: "Quality Score", value: `${(plan.quality_score ?? 0).toFixed(0)}/100`, icon: Sparkles },
          ].map((m) => (
            <div key={m.label} className="rounded-xl border border-border bg-sage-soft/40 p-4">
              <div className="flex items-center justify-between">
                <span className="text-[11px] uppercase tracking-widest text-muted-foreground">{m.label}</span>
                <m.icon className="h-3.5 w-3.5 text-primary" />
              </div>
              <div className={`mt-2 font-serif-display text-2xl font-medium ${m.accent ? "text-success" : "text-foreground"}`}>
                {m.value}
              </div>
            </div>
          ))}
        </div>
      </header>

      {/* Tabs */}
      <Tabs defaultValue="Overview" className="mt-6">
        <div className="overflow-x-auto">
          <TabsList className="h-auto w-max gap-1 rounded-xl border border-border bg-card p-1.5">
            {tabs.map((t) => (
              <TabsTrigger
                key={t}
                value={t}
                className="rounded-lg px-3.5 py-2 text-xs font-medium text-muted-foreground transition-colors data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-card"
              >
                {t}
              </TabsTrigger>
            ))}
          </TabsList>
        </div>

        {/* ── Overview ── */}
        <TabsContent value="Overview" className="mt-6 space-y-5">
          <Card title="Hypothesis" icon={Sparkles}>
            <p className="text-sm leading-relaxed text-foreground">{plan.refined_hypothesis || plan.hypothesis}</p>
            {plan.sub_hypotheses.length > 0 && (
              <div className="mt-4">
                <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-muted-foreground">Sub-hypotheses</p>
                <ul className="space-y-1">
                  {plan.sub_hypotheses.map((h, i) => (
                    <li key={i} className="flex gap-2 text-sm text-foreground"><span className="text-primary">•</span>{h}</li>
                  ))}
                </ul>
              </div>
            )}
            {plan.expected_outcomes.length > 0 && (
              <div className="mt-4">
                <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-muted-foreground">Expected Outcomes</p>
                <ul className="space-y-1">
                  {plan.expected_outcomes.map((o, i) => (
                    <li key={i} className="flex gap-2 text-sm text-foreground"><span className="text-primary">→</span>{o}</li>
                  ))}
                </ul>
              </div>
            )}
          </Card>

          <div className="grid gap-5 lg:grid-cols-2">
            <Card title="Validation Metrics" icon={CheckCircle2}>
              <dl className="space-y-2 text-sm">
                <Row label="Primary endpoint" value={plan.validation?.primary_metric ?? "—"} />
                <Row label="Success threshold" value={plan.validation?.success_threshold ?? "—"} />
                <Row label="Statistical test" value={plan.validation?.statistical_test ?? "—"} />
                {plan.validation?.sample_size_per_group && <Row label="Sample size / group" value={String(plan.validation.sample_size_per_group)} />}
                {plan.validation?.power && <Row label="Statistical power" value={`${(plan.validation.power * 100).toFixed(0)}%`} />}
                {plan.validation?.alpha && <Row label="Alpha" value={String(plan.validation.alpha)} />}
              </dl>
            </Card>
            <Card title="Novelty Signal" icon={Star}>
              <div className="flex items-end gap-2">
                <span className="font-serif-display text-4xl font-medium text-primary">{noveltyScore}</span>
                <span className="pb-1 text-sm text-muted-foreground">/ 10</span>
              </div>
              <p className="mt-2 text-sm text-muted-foreground">{noveltyLabel[plan.literature_result.novelty_signal]}</p>
              {plan.literature_result.gap_analysis && (
                <p className="mt-3 text-sm leading-relaxed text-foreground">{plan.literature_result.gap_analysis}</p>
              )}
            </Card>
          </div>

          {plan.biosafety && (
            <Card title={`Biosafety — ${plan.biosafety.level}`} icon={Beaker}>
              <div className="grid gap-4 sm:grid-cols-2 text-sm">
                {plan.biosafety.required_ppe.length > 0 && (
                  <div>
                    <p className="mb-1 text-xs font-semibold uppercase tracking-widest text-muted-foreground">Required PPE</p>
                    <ul className="space-y-0.5">{plan.biosafety.required_ppe.map((p, i) => <li key={i} className="text-foreground">• {p}</li>)}</ul>
                  </div>
                )}
                {plan.biosafety.hazardous_materials.length > 0 && (
                  <div>
                    <p className="mb-1 text-xs font-semibold uppercase tracking-widest text-muted-foreground">Hazardous Materials</p>
                    <ul className="space-y-0.5">{plan.biosafety.hazardous_materials.map((m, i) => <li key={i} className="text-foreground">• {m}</li>)}</ul>
                  </div>
                )}
              </div>
              {plan.biosafety.waste_disposal_protocol && (
                <p className="mt-3 text-sm text-muted-foreground"><span className="font-medium text-foreground">Disposal:</span> {plan.biosafety.waste_disposal_protocol}</p>
              )}
            </Card>
          )}
        </TabsContent>

        {/* ── Literature QC ── */}
        <TabsContent value="Literature QC" className="mt-6 space-y-5">
          <Card title="Top References" icon={FileText}>
            {plan.literature_result.references.length === 0 ? (
              <p className="text-sm text-muted-foreground">No references found.</p>
            ) : (
              <ul className="divide-y divide-border">
                {plan.literature_result.references.map((ref, i) => (
                  <li key={i} className="flex items-start justify-between gap-4 py-4 first:pt-0 last:pb-0">
                    <div className="min-w-0">
                      <div className="font-medium text-foreground">{ref.title}</div>
                      <div className="mt-0.5 text-xs text-muted-foreground">
                        {ref.authors.slice(0, 3).join(", ")}{ref.authors.length > 3 ? " et al." : ""} · {ref.year} · {ref.source}
                      </div>
                      {ref.abstract_summary && <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{ref.abstract_summary}</p>}
                    </div>
                    {ref.url && ref.url !== "https://placeholder.url" && (
                      <a href={ref.url} target="_blank" rel="noopener noreferrer" className="shrink-0 text-xs font-medium text-primary hover:underline">View →</a>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </Card>
          {plan.literature_result.gap_analysis && (
            <Card title="Gap Analysis" icon={Sparkles}>
              <p className="text-sm leading-relaxed text-foreground">{plan.literature_result.gap_analysis}</p>
            </Card>
          )}
        </TabsContent>

        {/* ── Protocol ── */}
        <TabsContent value="Protocol" className="mt-6">
          <Card title="Protocol Steps" icon={ListChecks}>
            {plan.protocol_steps.length === 0 ? (
              <p className="text-sm text-muted-foreground">No protocol steps generated.</p>
            ) : (
              <ol className="space-y-4">
                {plan.protocol_steps.map((s) => (
                  <li key={s.step_number} className="flex gap-4">
                    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-border bg-sage-soft text-xs font-semibold text-primary">{s.step_number}</span>
                    <div className="min-w-0 pt-0.5">
                      <p className="font-medium text-foreground">{s.title}</p>
                      <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{s.description}</p>
                      <div className="mt-2 flex flex-wrap gap-3 text-xs text-muted-foreground">
                        <span>⏱ {s.duration_minutes} min</span>
                        {s.equipment_needed.length > 0 && <span>🔬 {s.equipment_needed.join(", ")}</span>}
                        {s.notes && <span className="italic">Note: {s.notes}</span>}
                      </div>
                    </div>
                  </li>
                ))}
              </ol>
            )}
          </Card>
        </TabsContent>

        {/* ── Materials ── */}
        <TabsContent value="Materials" className="mt-6">
          <Card title="Materials & Reagents" icon={Package}>
            {plan.materials.length === 0 ? (
              <p className="text-sm text-muted-foreground">No materials listed.</p>
            ) : (
              <DataTable
                headers={["#", "Name", "Supplier", "Catalog #", "Qty", "Unit Cost", "Total", "Hazard"]}
                rows={plan.materials.map((m, i) => [
                  String(i + 1), m.name, m.supplier, m.catalog_number, m.quantity,
                  `$${m.unit_cost_usd.toFixed(2)}`, `$${m.total_cost_usd.toFixed(2)}`, m.hazard_class ?? "—",
                ])}
              />
            )}
          </Card>
        </TabsContent>

        {/* ── Budget ── */}
        <TabsContent value="Budget" className="mt-6 space-y-5">
          <div className="grid gap-4 sm:grid-cols-3">
            <BudgetTile label="Grand Total" value={`$${totalBudget.toLocaleString(undefined, { maximumFractionDigits: 0 })}`} tone="muted" />
            {optimizeData ? (
              <>
                <BudgetTile label="Optimized Total" value={`$${optimizeData.total_optimized_usd.toLocaleString(undefined, { maximumFractionDigits: 0 })}`} tone="primary" />
                <BudgetTile label="Savings" value={`${optimizeData.total_savings_pct.toFixed(1)}%`} tone="success" />
              </>
            ) : (
              <div className="col-span-2 flex items-center justify-center rounded-xl border border-dashed border-border p-4">
                <p className="text-sm text-muted-foreground">Go to <strong>Cost Optimizer</strong> tab to see savings.</p>
              </div>
            )}
          </div>
          <Card title="Budget Breakdown" icon={Wallet}>
            <DataTable
              headers={["Category", "Description", "Cost (USD)"]}
              rows={plan.budget.line_items.map((l) => [
                l.category.charAt(0).toUpperCase() + l.category.slice(1),
                l.description,
                `$${l.cost_usd.toLocaleString(undefined, { maximumFractionDigits: 2 })}`,
              ])}
            />
            <div className="mt-3 flex justify-end border-t border-border pt-3">
              <span className="text-sm font-semibold text-foreground">Total: ${totalBudget.toLocaleString(undefined, { maximumFractionDigits: 2 })}</span>
            </div>
            <p className="mt-1 text-right text-xs text-muted-foreground">{plan.budget.currency_note}</p>
          </Card>
        </TabsContent>

        {/* ── Cost Optimizer ── */}
        <TabsContent value="Cost Optimizer" className="mt-6">
          <Card title="Cost Optimization Plan" icon={TrendingDown}>
            <div className="mb-5 flex flex-wrap gap-2">
              {(["lean", "standard", "premium"] as const).map((mode) => (
                <button
                  key={mode}
                  onClick={() => handleOptimize(mode)}
                  disabled={optimizeMutation.isPending}
                  className={`badge-pill cursor-pointer transition-colors ${
                    optimizeMode === mode && optimizeData
                      ? "bg-primary text-primary-foreground"
                      : "border border-border bg-card text-muted-foreground hover:bg-accent"
                  }`}
                >
                  {mode.charAt(0).toUpperCase() + mode.slice(1)}
                </button>
              ))}
              <Button variant="ghost_dark" size="sm" onClick={() => handleOptimize(optimizeMode)} disabled={optimizeMutation.isPending}>
                {optimizeMutation.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
                {optimizeMutation.isPending ? "Optimizing…" : "Run Optimizer"}
              </Button>
            </div>
            {optimizeData ? (
              <>
                <div className="mb-4 grid grid-cols-3 gap-3">
                  <BudgetTile label="Original" value={`$${optimizeData.total_original_usd.toLocaleString(undefined, { maximumFractionDigits: 0 })}`} tone="muted" />
                  <BudgetTile label="Optimized" value={`$${optimizeData.total_optimized_usd.toLocaleString(undefined, { maximumFractionDigits: 0 })}`} tone="primary" />
                  <BudgetTile label="Savings" value={`${optimizeData.total_savings_pct.toFixed(1)}%`} tone="success" />
                </div>
                <DataTable
                  headers={["Item", "Original Supplier", "Alternative", "Original", "Optimized", "Savings", "Risk"]}
                  rows={optimizeData.optimizations.map((o) => [
                    o.item, o.original_supplier, o.alt_supplier,
                    `$${o.original_cost.toLocaleString(undefined, { maximumFractionDigits: 0 })}`,
                    `$${o.optimized_cost.toLocaleString(undefined, { maximumFractionDigits: 0 })}`,
                    `${o.savings_pct.toFixed(1)}%`, o.risk,
                  ])}
                />
              </>
            ) : (
              <p className="text-sm text-muted-foreground">Select a mode and click <strong>Run Optimizer</strong> to generate AI-powered cost-saving alternatives for your materials.</p>
            )}
          </Card>
        </TabsContent>

        {/* ── Timeline ── */}
        <TabsContent value="Timeline" className="mt-6">
          <Card title="Project Timeline" icon={Clock}>
            {plan.timeline.length === 0 ? (
              <p className="text-sm text-muted-foreground">No timeline generated.</p>
            ) : (
              <ol className="relative space-y-5 border-l-2 border-border pl-6">
                {plan.timeline.map((phase, i) => (
                  <li key={i} className="relative">
                    <span className="absolute -left-[31px] flex h-5 w-5 items-center justify-center rounded-full border-2 border-card bg-primary text-[10px] font-semibold text-primary-foreground">{i + 1}</span>
                    <div className="text-[11px] font-semibold uppercase tracking-widest text-primary">{phase.phase_name} · {phase.duration_days}d</div>
                    {phase.milestone && <div className="mt-0.5 text-xs font-medium text-muted-foreground">🏁 {phase.milestone}</div>}
                    <ul className="mt-1.5 space-y-0.5">
                      {phase.tasks.map((t, j) => <li key={j} className="text-sm text-foreground">• {t}</li>)}
                    </ul>
                    {phase.depends_on.length > 0 && <div className="mt-1 text-xs text-muted-foreground">Depends on: {phase.depends_on.join(", ")}</div>}
                  </li>
                ))}
              </ol>
            )}
          </Card>
        </TabsContent>

        {/* ── Validation ── */}
        <TabsContent value="Validation" className="mt-6 space-y-5">
          <Card title="Validation Plan" icon={Beaker}>
            {!plan.validation ? (
              <p className="text-sm text-muted-foreground">No validation plan generated.</p>
            ) : (
              <dl className="grid gap-4 sm:grid-cols-2">
                <Row label="Primary metric" value={plan.validation.primary_metric} />
                <Row label="Success threshold" value={plan.validation.success_threshold} />
                <Row label="Statistical test" value={plan.validation.statistical_test} />
                {plan.validation.sample_size_per_group && <Row label="Sample size / group" value={String(plan.validation.sample_size_per_group)} />}
                {plan.validation.power && <Row label="Statistical power" value={`${(plan.validation.power * 100).toFixed(0)}%`} />}
                {plan.validation.alpha && <Row label="Significance α" value={String(plan.validation.alpha)} />}
                {plan.validation.effect_size_estimate && <Row label="Effect size" value={plan.validation.effect_size_estimate} />}
                {plan.validation.controls.length > 0 && (
                  <div className="col-span-full">
                    <dt className="text-xs text-muted-foreground">Controls</dt>
                    <dd className="mt-1 text-sm text-foreground">{plan.validation.controls.join(" · ")}</dd>
                  </div>
                )}
              </dl>
            )}
          </Card>
          {plan.risks.length > 0 && (
            <Card title="Risk Assessment" icon={CheckCircle2}>
              <DataTable
                headers={["Risk", "Severity", "Likelihood", "Mitigation"]}
                rows={plan.risks.map((r) => [
                  r.description,
                  r.severity.charAt(0).toUpperCase() + r.severity.slice(1),
                  r.likelihood.charAt(0).toUpperCase() + r.likelihood.slice(1),
                  r.mitigation,
                ])}
              />
            </Card>
          )}
        </TabsContent>

        {/* ── Collaboration ── */}
        <TabsContent value="Collaboration" className="mt-6">
          <Card title="Suggested Collaborators" icon={Users}>
            {collabLoading ? (
              <div className="flex items-center gap-2 text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin" />Finding researchers…</div>
            ) : collabData && collabData.collaborators.length > 0 ? (
              <ul className="grid gap-4 sm:grid-cols-2">
                {collabData.collaborators.map((c) => (
                  <li key={c.name} className="rounded-xl border border-border bg-sage-soft/30 p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="font-medium text-foreground">{c.name}</div>
                        <div className="text-xs text-muted-foreground">{c.institution}</div>
                        {c.department && <div className="text-xs text-muted-foreground">{c.department}</div>}
                      </div>
                      <span className="badge-pill bg-success-soft text-success shrink-0">{c.match_pct}%</span>
                    </div>
                    <p className="mt-3 text-xs text-muted-foreground">"{c.topic}"</p>
                    {c.recent_publication && <p className="mt-1 text-xs italic text-muted-foreground line-clamp-2">Recent: {c.recent_publication}</p>}
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      {c.domains.map((d) => (
                        <span key={d} className="rounded-full border border-border bg-card px-2 py-0.5 text-[11px] text-muted-foreground">{d}</span>
                      ))}
                    </div>
                    <Button size="sm" variant="hero" className="mt-4 w-full" onClick={() => toast.success(`Connection request sent to ${c.name}!`)}>
                      Request Collaboration
                    </Button>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="space-y-3">
                <p className="text-sm text-muted-foreground">Click below to find researchers working in similar areas.</p>
                <Button variant="hero" size="sm" onClick={() => refetchCollab()} disabled={collabLoading}>
                  <Users className="h-4 w-4" />Find Collaborators
                </Button>
              </div>
            )}
          </Card>
        </TabsContent>

        {/* ── Scientist Review ── */}
        <TabsContent value="Scientist Review" className="mt-6 space-y-5">
          {reviewsData && reviewsData.reviews.length > 0 && (
            <Card title={`Reviews (${reviewsData.count})`} icon={Star}>
              <ul className="divide-y divide-border">
                {reviewsData.reviews.map((r) => (
                  <li key={r.review_id} className="flex items-start gap-4 py-4 first:pt-0 last:pb-0">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-sage text-xs font-semibold text-primary">{r.initials}</div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <div className="flex">
                          {[1, 2, 3, 4, 5].map((n) => <Star key={n} className={`h-3.5 w-3.5 ${n <= r.rating ? "fill-warning text-warning" : "text-border"}`} />)}
                        </div>
                        <span className="text-sm font-semibold">{r.rating}</span>
                        <span className="text-xs text-muted-foreground">· {r.section} · {r.reviewer_name}</span>
                      </div>
                      <p className="mt-1 text-sm text-muted-foreground">{r.comment}</p>
                      {r.correction && <p className="mt-1 text-sm text-foreground"><span className="font-medium">Suggestion:</span> {r.correction}</p>}
                    </div>
                  </li>
                ))}
              </ul>
            </Card>
          )}

          <Card title="Submit Feedback" icon={Star}>
            <div className="space-y-5">
              <div>
                <label className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Reviewer Name</label>
                <input type="text" value={reviewState.reviewer_name} onChange={(e) => setReviewState((s) => ({ ...s, reviewer_name: e.target.value }))}
                  className="mt-2 w-full rounded-xl border border-input bg-background px-4 py-2.5 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring" placeholder="Your name…" />
              </div>
              <div>
                <label className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Overall Rating</label>
                <div className="mt-2 flex items-center gap-1">
                  {[1, 2, 3, 4, 5].map((n) => (
                    <button key={n} onClick={() => setReviewState((s) => ({ ...s, rating: n }))} aria-label={`Rate ${n}`}>
                      <Star className={`h-6 w-6 cursor-pointer transition-colors ${n <= reviewState.rating ? "fill-warning text-warning" : "text-border hover:text-warning"}`} />
                    </button>
                  ))}
                  <span className="ml-2 text-sm text-muted-foreground">{reviewState.rating}.0</span>
                </div>
              </div>
              <div>
                <label className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Section</label>
                <div className="mt-2 flex flex-wrap gap-2">
                  {["Protocol", "Materials", "Budget", "Timeline", "Validation"].map((s) => (
                    <button key={s} onClick={() => setReviewState((prev) => ({ ...prev, section: s }))}
                      className={`badge-pill cursor-pointer transition-colors ${reviewState.section === s ? "bg-primary text-primary-foreground" : "border border-border bg-card text-muted-foreground hover:bg-accent"}`}>
                      {s}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Comment</label>
                <textarea rows={4} value={reviewState.comment} onChange={(e) => setReviewState((s) => ({ ...s, comment: e.target.value }))}
                  className="mt-2 w-full resize-none rounded-xl border border-input bg-background px-4 py-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring" placeholder="Share your structured feedback…" />
              </div>
              <div>
                <label className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Suggested Correction (optional — improves future plans)</label>
                <textarea rows={2} value={reviewState.correction} onChange={(e) => setReviewState((s) => ({ ...s, correction: e.target.value }))}
                  className="mt-2 w-full resize-none rounded-xl border border-input bg-background px-4 py-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring" placeholder="Optional concrete suggestion…" />
              </div>
              <Button variant="hero" onClick={handleSubmitReview} disabled={submitReviewMutation.isPending}>
                {submitReviewMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Star className="h-4 w-4" />}
                Submit Feedback
              </Button>
            </div>
          </Card>
        </TabsContent>

        {/* ── Final Report ── */}
        <TabsContent value="Final Report" className="mt-6">
          <Card title="Final Report" icon={FileText}>
            <p className="text-sm text-muted-foreground">
              A complete, ready-to-run experiment plan combining hypothesis, literature, protocol, materials, budget, timeline, validation, biosafety, and risk assessment.
            </p>
            <div className="mt-5 flex flex-wrap gap-2">
              <Button variant="hero" onClick={handleGenerateReport} disabled={reportLoading}>
                {reportLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
                {reportLoading ? "Generating…" : reportData ? "Regenerate Report" : "Generate Report"}
              </Button>
              {reportData && (
                <Button variant="ghost_dark" onClick={handleDownloadReport}>
                  <Download className="h-4 w-4" />Download Markdown
                </Button>
              )}
              <Button variant="ghost_dark" onClick={handleExportJSON}>
                <Download className="h-4 w-4" />Export JSON
              </Button>
            </div>
            {reportData && (
              <div className="mt-6">
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">
                    {reportData.word_count.toLocaleString()} words · Generated {new Date(reportData.created_at).toLocaleString()}
                  </span>
                </div>
                <pre className="max-h-[60vh] overflow-auto rounded-xl border border-border bg-muted/40 p-5 text-xs leading-relaxed text-foreground whitespace-pre-wrap">
                  {reportData.markdown}
                </pre>
              </div>
            )}
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

/* ----- helpers ----- */

const Card = ({
  title,
  icon: Icon,
  children,
}: {
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  children: React.ReactNode;
}) => (
  <section className="rounded-2xl border border-border bg-card p-6 shadow-card">
    <div className="mb-4 flex items-center gap-2.5">
      <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-sage-soft text-primary">
        <Icon className="h-4 w-4" />
      </span>
      <h2 className="text-base font-semibold text-foreground">{title}</h2>
    </div>
    {children}
  </section>
);

const Row = ({ label, value }: { label: string; value: string }) => (
  <div className="flex items-center justify-between gap-3 border-b border-border py-2 last:border-b-0">
    <dt className="text-xs uppercase tracking-widest text-muted-foreground">{label}</dt>
    <dd className="text-sm font-medium text-foreground">{value}</dd>
  </div>
);

const DataTable = ({ headers, rows }: { headers: string[]; rows: string[][] }) => (
  <div className="overflow-x-auto">
    <table className="w-full text-left text-sm">
      <thead>
        <tr className="border-b border-border text-[11px] uppercase tracking-widest text-muted-foreground">
          {headers.map((h) => <th key={h} className="py-2 pr-4 font-medium">{h}</th>)}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => (
          <tr key={i} className="border-b border-border/50 last:border-0">
            {row.map((c, j) => <td key={j} className="py-2.5 pr-4 text-foreground">{c}</td>)}
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

const BudgetTile = ({ label, value, tone }: { label: string; value: string; tone: "muted" | "primary" | "success" }) => {
  const colorMap = { muted: "text-foreground", primary: "text-primary", success: "text-success" };
  return (
    <div className="rounded-xl border border-border bg-sage-soft/40 p-4 text-center">
      <div className="text-[11px] uppercase tracking-widest text-muted-foreground">{label}</div>
      <div className={`mt-2 font-serif-display text-2xl font-medium ${colorMap[tone]}`}>{value}</div>
    </div>
  );
};
export default ExperimentDetail;
