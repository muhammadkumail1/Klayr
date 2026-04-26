import { Button } from "@/components/ui/button";
import { collaborators, recentReviews, workflowModules } from "@/data/mockData";
import { ArrowRight, Star, TrendingDown } from "lucide-react";
import { StatusBadge } from "@/components/StatusBadge";

export const InsightPanel = () => {
  return (
    <aside className="space-y-5">
      {/* Plan summary */}
      <div className="rounded-2xl border border-border bg-card p-5 shadow-card">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-foreground">Plan Summary</h3>
          <span className="text-[10px] uppercase tracking-widest text-muted-foreground">
            Live
          </span>
        </div>
        <ul className="space-y-2.5">
          {workflowModules.map((m) => (
            <li key={m.key} className="flex items-center justify-between gap-3 text-sm">
              <span className="truncate text-foreground">{m.title}</span>
              <StatusBadge status={m.status} />
            </li>
          ))}
        </ul>
      </div>

      {/* Cost optimization */}
      <div className="rounded-2xl border border-border bg-card p-5 shadow-card">
        <div className="mb-4 flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-success-soft text-success">
            <TrendingDown className="h-4 w-4" />
          </span>
          <h3 className="text-sm font-semibold text-foreground">Cost Optimization</h3>
        </div>
        <dl className="space-y-2 text-sm">
          <div className="flex items-center justify-between">
            <dt className="text-muted-foreground">Original Estimate</dt>
            <dd className="font-medium text-foreground line-through opacity-70">$12,450</dd>
          </div>
          <div className="flex items-center justify-between">
            <dt className="text-muted-foreground">Optimized Estimate</dt>
            <dd className="font-semibold text-foreground">$8,980</dd>
          </div>
          <div className="flex items-center justify-between rounded-lg bg-success-soft px-3 py-2">
            <dt className="text-success">Potential Savings</dt>
            <dd className="font-serif-display text-lg font-medium text-success">27.8%</dd>
          </div>
        </dl>
        <Button variant="ghost_dark" size="sm" className="mt-4 w-full">
          See Full Optimization
          <ArrowRight className="h-3.5 w-3.5" />
        </Button>
      </div>

      {/* Collaborations */}
      <div className="rounded-2xl border border-border bg-card p-5 shadow-card">
        <h3 className="mb-4 text-sm font-semibold text-foreground">Potential Collaborations</h3>
        <ul className="space-y-3">
          {collaborators.map((c) => (
            <li key={c.name} className="flex items-center gap-3">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-green text-xs font-semibold text-primary-foreground">
                {c.initials}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-2">
                  <div className="truncate text-sm font-medium text-foreground">{c.name}</div>
                  <span className="badge-pill bg-sage-soft text-primary">{c.match}%</span>
                </div>
                <div className="truncate text-[11px] text-muted-foreground">
                  {c.institution}
                </div>
              </div>
            </li>
          ))}
        </ul>
        <Button variant="ghost_dark" size="sm" className="mt-4 w-full">
          View & Connect
          <ArrowRight className="h-3.5 w-3.5" />
        </Button>
      </div>

      {/* Recent reviews */}
      <div className="rounded-2xl border border-border bg-card p-5 shadow-card">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-foreground">Recent Reviews</h3>
          <div className="flex items-center gap-1 text-xs">
            <Star className="h-3.5 w-3.5 fill-warning text-warning" />
            <span className="font-semibold text-foreground">4.6</span>
            <span className="text-muted-foreground">avg</span>
          </div>
        </div>
        <ul className="space-y-3">
          {recentReviews.map((r, i) => (
            <li key={i} className="flex items-start gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-sage text-[11px] font-semibold text-primary">
                {r.initials}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1.5">
                  <Star className="h-3 w-3 fill-warning text-warning" />
                  <span className="text-xs font-semibold text-foreground">{r.rating}</span>
                </div>
                <p className="mt-0.5 text-xs leading-snug text-muted-foreground">{r.summary}</p>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </aside>
  );
};
