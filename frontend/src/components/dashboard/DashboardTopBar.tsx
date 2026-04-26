import { Bell, ChevronDown, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MethodicaLogo } from "@/components/MethodicaLogo";

export const DashboardTopBar = () => {
  return (
    <header className="border-b border-border bg-background/80 backdrop-blur">
      <div className="flex h-16 items-center justify-between gap-4 px-5 sm:px-8">
        <div className="flex min-w-0 items-center gap-3">
          <div className="lg:hidden">
            <MethodicaLogo />
          </div>
          <div className="hidden min-w-0 items-center gap-3 lg:flex">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-sage-soft text-primary">
              <Sparkles className="h-4 w-4" />
            </div>
            <div className="min-w-0">
              <div className="truncate text-sm font-semibold text-foreground">
                Good morning, Researcher
              </div>
              <div className="truncate text-xs text-muted-foreground">
                Let's turn your hypothesis into breakthrough science.
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" aria-label="Notifications" className="relative">
            <Bell className="h-4 w-4" />
            <span className="absolute right-2.5 top-2.5 h-1.5 w-1.5 rounded-full bg-warning" />
          </Button>
          <button className="flex items-center gap-2 rounded-full border border-border bg-card py-1 pl-1 pr-3 transition-colors hover:bg-accent">
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-green text-xs font-semibold text-primary-foreground">
              DR
            </span>
            <span className="hidden text-sm font-medium text-foreground sm:inline">
              Dr. Researcher
            </span>
            <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
          </button>
        </div>
      </div>
    </header>
  );
};
