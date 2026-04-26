import { workflowModules } from "@/data/mockData";
import { StatusBadge } from "@/components/StatusBadge";
import {
  BookOpen,
  ClipboardList,
  TrendingDown,
  Users,
  MessageSquareText,
  FileText,
} from "lucide-react";

const icons = {
  literature: BookOpen,
  plan: ClipboardList,
  cost: TrendingDown,
  collab: Users,
  review: MessageSquareText,
  report: FileText,
};

export const WorkflowModules = () => {
  return (
    <section>
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h3 className="font-serif-display text-xl font-medium text-foreground">
            Workflow Modules
          </h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Six steps from hypothesis to a review-ready plan.
          </p>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {workflowModules.map((m) => {
          const Icon = icons[m.key as keyof typeof icons];
          return (
            <article
              key={m.key}
              className="group rounded-2xl border border-border bg-card p-5 shadow-card transition-all hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-soft"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <span className="flex h-9 w-9 items-center justify-center rounded-full border border-border bg-sage-soft text-xs font-semibold text-primary">
                    {String(m.num).padStart(2, "0")}
                  </span>
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-sage-soft text-primary">
                    <Icon className="h-4 w-4" strokeWidth={1.7} />
                  </div>
                </div>
                <StatusBadge status={m.status} />
              </div>

              <h4 className="mt-4 text-base font-semibold text-foreground">{m.title}</h4>
              <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">
                {m.description}
              </p>
            </article>
          );
        })}
      </div>
    </section>
  );
};
