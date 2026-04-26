import { Link } from "react-router-dom";
import { PageHeader } from "./PageHeader";
import { Button } from "@/components/ui/button";
import { usePlans, useReviews } from "@/hooks/useApi";
import { Loader2, Star } from "lucide-react";

// Aggregated review feed: load latest plan's reviews as sample
const LatestPlanReviews = ({ planId }: { planId: string }) => {
  const { data, isLoading } = useReviews(planId);
  if (isLoading) return <li className="px-6 py-4 text-sm text-muted-foreground flex gap-2"><Loader2 className="h-4 w-4 animate-spin" />Loading…</li>;
  if (!data || data.reviews.length === 0) return <li className="px-6 py-4 text-sm text-muted-foreground">No reviews yet for this plan.</li>;
  return (
    <>
      {data.reviews.map((r) => (
        <li key={r.review_id} className="flex items-start gap-4 px-6 py-4">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-sage text-xs font-semibold text-primary">{r.initials}</div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              {[1,2,3,4,5].map((n) => <Star key={n} className={`h-3.5 w-3.5 ${n <= r.rating ? "fill-warning text-warning" : "text-border"}`} />)}
              <span className="text-sm font-semibold text-foreground">{r.rating}</span>
              <span className="text-xs text-muted-foreground">· {r.section} · {r.reviewer_name}</span>
            </div>
            <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{r.comment}</p>
            {r.correction && <p className="mt-1 text-xs text-foreground"><span className="font-medium">Suggestion:</span> {r.correction}</p>}
          </div>
          <Button asChild variant="ghost" size="sm">
            <Link to={`/dashboard/experiments/${planId}?tab=review`}>View</Link>
          </Button>
        </li>
      ))}
    </>
  );
};

const Reviews = () => {
  const { data: plansData, isLoading: plansLoading } = usePlans(1, 0);
  const latestPlanId = plansData?.plans[0]?.plan_id;

  return (
    <div className="px-5 py-6 sm:px-8 sm:py-8">
      <PageHeader
        eyebrow="Reviews & Feedback"
        title="Expert input on your work"
        description="Aggregate scientist reviews across all your experiments and track improvements over time."
      />

      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-border bg-card p-5 shadow-card">
          <div className="text-xs uppercase tracking-widest text-muted-foreground">Total Plans</div>
          <div className="mt-2 font-serif-display text-3xl font-medium text-foreground">
            {plansData?.total ?? "—"}
          </div>
          <p className="mt-1 text-xs text-muted-foreground">Experiment plans generated</p>
        </div>
        <div className="rounded-2xl border border-border bg-card p-5 shadow-card">
          <div className="text-xs uppercase tracking-widest text-muted-foreground">Under Review</div>
          <div className="mt-2 font-serif-display text-3xl font-medium text-foreground">
            {plansData?.plans.filter((p) => !p.feedback_incorporated && (p.quality_score ?? 0) < 80).length ?? "—"}
          </div>
          <p className="mt-1 text-xs text-muted-foreground">Awaiting feedback</p>
        </div>
        <div className="rounded-2xl border border-border bg-card p-5 shadow-card">
          <div className="text-xs uppercase tracking-widest text-muted-foreground">Feedback Incorporated</div>
          <div className="mt-2 font-serif-display text-3xl font-medium text-foreground">
            {plansData?.plans.filter((p) => p.feedback_incorporated).length ?? "—"}
          </div>
          <p className="mt-1 text-xs text-muted-foreground">Plans improved via reviews</p>
        </div>
      </div>

      <section className="rounded-2xl border border-border bg-card shadow-card">
        <div className="border-b border-border px-6 py-4">
          <h3 className="font-serif-display text-lg font-medium text-foreground">Recent reviews</h3>
        </div>
        <ul className="divide-y divide-border">
          {plansLoading ? (
            <li className="flex items-center gap-2 px-6 py-4 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />Loading plans…
            </li>
          ) : !latestPlanId ? (
            <li className="px-6 py-6 text-center text-sm text-muted-foreground">
              No experiments yet. <Link to="/dashboard/new" className="text-primary hover:underline">Create your first →</Link>
            </li>
          ) : (
            <LatestPlanReviews planId={latestPlanId} />
          )}
        </ul>
      </section>
    </div>
  );
};

export default Reviews;

