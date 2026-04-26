import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/StatusBadge";
import { experiments } from "@/data/mockData";
import { Download, Eye, MoreHorizontal } from "lucide-react";

export const RecentExperimentsTable = () => {
  return (
    <section className="rounded-2xl border border-border bg-card shadow-card">
      <div className="flex items-center justify-between border-b border-border px-6 py-4">
        <div>
          <h3 className="font-serif-display text-lg font-medium text-foreground">
            Recent Experiments
          </h3>
          <p className="text-xs text-muted-foreground">Your latest research workflows.</p>
        </div>
        <Button variant="ghost" size="sm" asChild>
          <Link to="/dashboard/experiments">View all</Link>
        </Button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-border text-[11px] uppercase tracking-widest text-muted-foreground">
              <th className="px-6 py-3 font-medium">Experiment</th>
              <th className="px-6 py-3 font-medium">Status</th>
              <th className="px-6 py-3 font-medium">Created</th>
              <th className="px-6 py-3 font-medium">Last Updated</th>
              <th className="px-6 py-3 text-right font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {experiments.map((exp) => (
              <tr
                key={exp.id}
                className="border-b border-border last:border-b-0 transition-colors hover:bg-sage-soft/40"
              >
                <td className="px-6 py-4">
                  <Link
                    to={`/dashboard/experiments/${exp.id}`}
                    className="font-medium text-foreground hover:text-primary"
                  >
                    {exp.title}
                  </Link>
                  <div className="mt-0.5 text-xs text-muted-foreground">{exp.domain}</div>
                </td>
                <td className="px-6 py-4">
                  <StatusBadge status={exp.status} />
                </td>
                <td className="px-6 py-4 text-muted-foreground">{exp.created}</td>
                <td className="px-6 py-4 text-muted-foreground">{exp.updated}</td>
                <td className="px-6 py-4">
                  <div className="flex items-center justify-end gap-1">
                    <Button asChild variant="ghost" size="icon" aria-label="View">
                      <Link to={`/dashboard/experiments/${exp.id}`}>
                        <Eye className="h-4 w-4" />
                      </Link>
                    </Button>
                    <Button variant="ghost" size="icon" aria-label="Download">
                      <Download className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon" aria-label="More">
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
};
