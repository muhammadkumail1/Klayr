import { cn } from "@/lib/utils";
import type { ExperimentStatus } from "@/data/mockData";

const styles: Record<ExperimentStatus, string> = {
  Pending: "bg-muted text-muted-foreground",
  "In Progress": "bg-info-soft text-info",
  Completed: "bg-success-soft text-success",
  "Needs Review": "bg-warning-soft text-warning",
};

interface StatusBadgeProps {
  status: ExperimentStatus;
  className?: string;
}

export const StatusBadge = ({ status, className }: StatusBadgeProps) => {
  return (
    <span className={cn("badge-pill", styles[status], className)}>
      <span className="h-1.5 w-1.5 rounded-full bg-current opacity-70" />
      {status}
    </span>
  );
};
