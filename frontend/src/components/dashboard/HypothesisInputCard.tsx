import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { ArrowRight, Lightbulb, Loader2, Zap } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { api } from "@/lib/api";
import type { SSEEvent } from "@/lib/api";
import { useQueryClient } from "@tanstack/react-query";

const DOMAIN_OPTIONS = [
  { value: "cell_biology", label: "Cell Biology" },
  { value: "molecular_biology", label: "Molecular Biology" },
  { value: "biochemistry", label: "Biochemistry" },
  { value: "microbiology", label: "Microbiology" },
  { value: "diagnostics", label: "Diagnostics" },
  { value: "pharmacology", label: "Pharmacology" },
  { value: "neuroscience", label: "Neuroscience" },
  { value: "chemistry", label: "Chemistry" },
  { value: "other", label: "Other" },
];

export const HypothesisInputCard = () => {
  const [value, setValue] = useState("");
  const [domain, setDomain] = useState("other");
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentNode, setCurrentNode] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const cancelRef = useRef<(() => void) | null>(null);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const nodeLabels: Record<string, string> = {
    refine_hypothesis: "Refining hypothesis…",
    literature_qc: "Scanning literature (PubMed + Semantic Scholar)…",
    generate_protocol: "Generating protocol…",
    generate_materials: "Listing materials & reagents…",
    generate_budget: "Estimating budget…",
    generate_timeline: "Building timeline…",
    generate_validation: "Designing validation plan…",
    assess_safety_and_risks: "Assessing biosafety & risks…",
  };

  const nodeOrder = Object.keys(nodeLabels);

  const handleAnalyze = () => {
    if (!value.trim()) {
      toast.error("Please enter a hypothesis to analyze.");
      return;
    }

    setIsStreaming(true);
    setProgress(0);
    setCurrentNode(null);
    const toastId = toast.loading("Initializing AI Scientist pipeline…");

    const cancel = api.streamPipeline(
      value.trim(),
      domain,
      (event: SSEEvent) => {
        if (event.type === "node_start" && event.node) {
          setCurrentNode(event.node);
          const idx = nodeOrder.indexOf(event.node);
          setProgress(idx >= 0 ? Math.round(((idx + 0.5) / nodeOrder.length) * 100) : progress);
          toast.loading(nodeLabels[event.node] ?? `Running ${event.node}…`, { id: toastId });
        }

        if (event.type === "node_complete" && event.node) {
          const idx = nodeOrder.indexOf(event.node);
          setProgress(idx >= 0 ? Math.round(((idx + 1) / nodeOrder.length) * 100) : progress);
        }

        if (event.type === "complete" && event.plan) {
          const plan = event.plan;
          setIsStreaming(false);
          setCurrentNode(null);
          setProgress(100);

          // Seed the plan into React Query cache
          queryClient.setQueryData(["plan", plan.plan_id], plan);
          queryClient.invalidateQueries({ queryKey: ["plans"] });

          toast.success("Experiment plan generated!", { id: toastId });
          navigate(`/dashboard/experiments/${plan.plan_id}`);
        }

        if (event.type === "error") {
          setIsStreaming(false);
          setCurrentNode(null);
          toast.error(`Pipeline error: ${event.error ?? "Unknown error"}`, { id: toastId });
        }
      },
      (err) => {
        setIsStreaming(false);
        setCurrentNode(null);
        // Fallback to synchronous run if SSE fails
        toast.loading("Streaming unavailable — running in sync mode…", { id: toastId });
        api.runPipeline(value.trim(), domain)
          .then((res) => {
            queryClient.setQueryData(["plan", res.plan_id], res.plan);
            queryClient.invalidateQueries({ queryKey: ["plans"] });
            toast.success("Experiment plan generated!", { id: toastId });
            navigate(`/dashboard/experiments/${res.plan_id}`);
          })
          .catch((e) => {
            toast.error(`Failed: ${e instanceof Error ? e.message : String(e)}`, { id: toastId });
          });
      }
    );

    cancelRef.current = cancel;
  };

  const handleCancel = () => {
    cancelRef.current?.();
    cancelRef.current = null;
    setIsStreaming(false);
    setCurrentNode(null);
    toast.info("Analysis cancelled.");
  };

  return (
    <section className="rounded-2xl border border-border bg-card p-6 shadow-card sm:p-8">
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-sage-soft text-primary">
          <Lightbulb className="h-4 w-4" strokeWidth={1.7} />
        </div>
        <div>
          <h2 className="font-serif-display text-2xl font-medium text-foreground">
            What is your hypothesis?
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Describe your research question in natural language. The AI Scientist will generate a
            complete, AI-powered experiment plan in real time.
          </p>
        </div>
      </div>

      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        rows={4}
        disabled={isStreaming}
        className="mt-5 w-full resize-none rounded-xl border border-input bg-background px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-60"
        placeholder="E.g., Does probiotic X improve gut permeability in inflammatory conditions?"
      />

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <label className="text-xs font-medium text-muted-foreground">Domain:</label>
        <select
          value={domain}
          onChange={(e) => setDomain(e.target.value)}
          disabled={isStreaming}
          className="rounded-lg border border-input bg-background px-3 py-1.5 text-xs text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-60"
        >
          {DOMAIN_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </div>

      {/* Progress bar */}
      {isStreaming && (
        <div className="mt-4 space-y-2">
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-border">
            <div
              className="h-full rounded-full bg-primary transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
          {currentNode && (
            <p className="flex items-center gap-2 text-xs text-muted-foreground">
              <Zap className="h-3 w-3 animate-pulse text-primary" />
              {nodeLabels[currentNode] ?? currentNode}
            </p>
          )}
        </div>
      )}

      <div className="mt-4 flex flex-col items-start justify-between gap-3 sm:flex-row sm:items-center">
        <p className="text-xs text-muted-foreground">
          <span className="font-medium text-foreground">Tip:</span> Be specific about population,
          intervention, and outcome for best results.
        </p>
        <div className="flex items-center gap-2">
          {isStreaming && (
            <Button variant="ghost_dark" size="lg" onClick={handleCancel}>
              Cancel
            </Button>
          )}
          <Button
            variant="hero"
            size="lg"
            onClick={handleAnalyze}
            disabled={isStreaming}
          >
            {isStreaming ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Analyzing…
              </>
            ) : (
              <>
                Analyze Hypothesis
                <ArrowRight className="h-4 w-4" />
              </>
            )}
          </Button>
        </div>
      </div>
    </section>
  );
};
