import { Link } from "react-router-dom";
import { PageHeader } from "./PageHeader";
import { Button } from "@/components/ui/button";
import { usePlans } from "@/hooks/useApi";
import { api } from "@/lib/api";
import { Download, Eye, FileText, Loader2 } from "lucide-react";

const Reports = () => {
  const { data: plansData, isLoading } = usePlans(100, 0);
  const plans = plansData?.plans ?? [];

  return (
    <div className="px-5 py-6 sm:px-8 sm:py-8">
      <PageHeader
        eyebrow="Reports"
        title="Export-ready research plans"
        description="Generate a complete, reproducible Markdown report for every experiment — protocol, materials, budget, validation, and references."
      />

      {isLoading ? (
        <div className="flex items-center justify-center py-16 text-muted-foreground gap-2">
          <Loader2 className="h-5 w-5 animate-spin" />Loading plans…
        </div>
      ) : plans.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-border bg-card p-16 text-center text-muted-foreground">
          <FileText className="mx-auto mb-3 h-8 w-8 opacity-40" />
          <p className="text-sm">No experiments yet. <Link to="/dashboard/new" className="text-primary hover:underline">Create your first →</Link></p>
        </div>
      ) : (
        <section className="grid gap-4 md:grid-cols-2">
          {plans.map((p) => {
            const domain = p.experiment_domain.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
            const date = new Date(p.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
            return (
              <article key={p.plan_id} className="flex flex-col rounded-2xl border border-border bg-card p-6 shadow-card">
                <div className="flex items-start gap-4">
                  <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-sage-soft text-primary">
                    <FileText className="h-5 w-5" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <h3 className="font-serif-display text-base font-medium leading-tight text-foreground line-clamp-2">
                      {p.hypothesis.length > 90 ? p.hypothesis.slice(0, 90) + "…" : p.hypothesis}
                    </h3>
                    <p className="mt-1 text-xs text-muted-foreground">{domain} · Created {date}</p>
                  </div>
                </div>
                <dl className="mt-5 grid grid-cols-2 gap-3 text-xs">
                  <div className="rounded-lg bg-sage-soft/60 px-3 py-2">
                    <dt className="text-muted-foreground">Quality Score</dt>
                    <dd className="mt-0.5 font-semibold text-foreground">{(p.quality_score ?? 0).toFixed(0)}/100</dd>
                  </div>
                  <div className="rounded-lg bg-sage-soft/60 px-3 py-2">
                    <dt className="text-muted-foreground">Feedback Loop</dt>
                    <dd className="mt-0.5 font-semibold text-foreground">{p.feedback_incorporated ? "Applied" : "Pending"}</dd>
                  </div>
                </dl>
                <div className="mt-5 flex items-center gap-2">
                  <Button variant="hero" size="sm" onClick={() => window.open(api.getReportPdfUrl(p.plan_id), "_blank")}>
                    <Download className="h-3.5 w-3.5" />Download PDF
                  </Button>
                  <Button variant="ghost_dark" size="sm" onClick={() => window.open(api.getReportDownloadUrl(p.plan_id), "_blank")}>
                    <Download className="h-3.5 w-3.5" />Markdown
                  </Button>
                  <Button asChild variant="ghost_dark" size="sm">
                    <Link to={`/dashboard/experiments/${p.plan_id}`}>
                      <Eye className="h-3.5 w-3.5" />Preview
                    </Link>
                  </Button>
                </div>
              </article>
            );
          })}
        </section>
      )}
    </div>
  );
};

export default Reports;

