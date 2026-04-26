import { useState } from "react";
import { Link } from "react-router-dom";
import { PageHeader } from "./PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { StatusBadge } from "@/components/StatusBadge";
import { usePlans } from "@/hooks/useApi";
import { api } from "@/lib/api";
import { Download, Eye, Filter, Loader2, Plus, Search } from "lucide-react";

const Experiments = () => {
  const [search, setSearch] = useState("");
  const { data: plansData, isLoading } = usePlans(100, 0);

  const plans = (plansData?.plans ?? []).filter((p) =>
    p.hypothesis.toLowerCase().includes(search.toLowerCase())
  );

  const handleDownload = (planId: string) => window.open(api.getReportDownloadUrl(planId), "_blank");

  return (
    <div className="px-5 py-6 sm:px-8 sm:py-8">
      <PageHeader
        eyebrow="My Experiments"
        title="All research workflows"
        description="Browse, filter, and continue every experiment in your workspace."
      >
        <Button asChild variant="hero" size="sm">
          <Link to="/dashboard/new">
            <Plus className="h-4 w-4" />
            New Experiment
          </Link>
        </Button>
      </PageHeader>

      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative max-w-sm flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input placeholder="Search experiments..." className="pl-9" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <Button variant="ghost_dark" size="sm">
          <Filter className="h-4 w-4" />
          Filter
        </Button>
      </div>

      <section className="overflow-hidden rounded-2xl border border-border bg-card shadow-card">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-border text-[11px] uppercase tracking-widest text-muted-foreground">
                <th className="px-6 py-3 font-medium">Experiment</th>
                <th className="px-6 py-3 font-medium">Status</th>
                <th className="px-6 py-3 font-medium">Domain</th>
                <th className="px-6 py-3 font-medium">Quality</th>
                <th className="px-6 py-3 font-medium">Budget</th>
                <th className="px-6 py-3 text-right font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr><td colSpan={6} className="px-6 py-8 text-center text-muted-foreground"><Loader2 className="inline h-4 w-4 animate-spin mr-2" />Loading experiments…</td></tr>
              ) : plans.length === 0 ? (
                <tr><td colSpan={6} className="px-6 py-8 text-center text-muted-foreground">No experiments found. <Link to="/dashboard/new" className="text-primary hover:underline">Create your first one →</Link></td></tr>
              ) : plans.map((p) => {
                const status = (p.quality_score ?? 0) >= 80 ? "Completed" : p.feedback_incorporated ? "In Progress" : "Needs Review";
                const domain = p.experiment_domain.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
                const date = new Date(p.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
                return (
                  <tr key={p.plan_id} className="border-b border-border last:border-b-0 transition-colors hover:bg-sage-soft/40">
                    <td className="px-6 py-4">
                      <Link to={`/dashboard/experiments/${p.plan_id}`} className="max-w-xs truncate font-medium text-foreground hover:text-primary block">
                        {p.hypothesis.length > 80 ? p.hypothesis.slice(0, 80) + "…" : p.hypothesis}
                      </Link>
                      <div className="mt-0.5 text-xs text-muted-foreground">Created {date}</div>
                    </td>
                    <td className="px-6 py-4"><StatusBadge status={status as any} /></td>
                    <td className="px-6 py-4 text-muted-foreground">{domain}</td>
                    <td className="px-6 py-4 font-medium text-foreground">{(p.quality_score ?? 0).toFixed(0)}/100</td>
                    <td className="px-6 py-4 text-muted-foreground">—</td>
                    <td className="px-6 py-4">
                      <div className="flex items-center justify-end gap-1">
                        <Button asChild variant="ghost" size="icon" aria-label="View">
                          <Link to={`/dashboard/experiments/${p.plan_id}`}><Eye className="h-4 w-4" /></Link>
                        </Button>
                        <Button variant="ghost" size="icon" aria-label="Download" onClick={() => handleDownload(p.plan_id)}>
                          <Download className="h-4 w-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
};

export default Experiments;

