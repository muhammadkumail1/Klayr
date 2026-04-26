import { NavLink } from "@/components/NavLink";
import { MethodicaLogo } from "@/components/MethodicaLogo";
import {
  LayoutDashboard,
  FlaskConical,
  ClipboardList,
  BookOpen,
  Users,
  MessageSquareText,
  FileText,
  Settings,
  Lock,
} from "lucide-react";

const navItems = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/dashboard/new", label: "New Experiment", icon: FlaskConical },
  { to: "/dashboard/experiments", label: "My Experiments", icon: ClipboardList },
  { to: "/dashboard/literature", label: "Literature Search", icon: BookOpen },
  { to: "/dashboard/collaboration", label: "Collaboration Finder", icon: Users },
  { to: "/dashboard/reviews", label: "Reviews & Feedback", icon: MessageSquareText },
  { to: "/dashboard/reports", label: "Reports", icon: FileText },
  { to: "/dashboard/settings", label: "Settings", icon: Settings },
];

export const DashboardSidebar = () => {
  return (
    <aside className="hidden w-[260px] shrink-0 flex-col border-r border-sidebar-border bg-gradient-sage lg:flex">
      <div className="px-6 pb-4 pt-6">
        <MethodicaLogo />
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4" aria-label="Main">
        <div className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
          Workspace
        </div>
        <ul className="space-y-1">
          {navItems.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={item.end}
                className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-sidebar-foreground transition-colors hover:bg-sidebar-accent"
                activeClassName="!bg-primary !text-primary-foreground shadow-card hover:!bg-primary-glow"
              >
                <item.icon className="h-4 w-4" strokeWidth={1.7} />
                <span>{item.label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      <div className="space-y-3 border-t border-sidebar-border p-4">
        {/* Today's progress */}
        <div className="rounded-xl bg-card/70 p-4 shadow-card">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-foreground">Today's Progress</span>
            <span className="text-primary">3/6</span>
          </div>
          <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-sage">
            <div className="h-full w-1/2 rounded-full bg-primary" />
          </div>
          <div className="mt-2 text-[11px] text-muted-foreground">
            Cost optimization in progress
          </div>
        </div>

        {/* User card */}
        <div className="flex items-center gap-3 rounded-xl bg-card/70 p-3 shadow-card">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-green text-sm font-semibold text-primary-foreground">
            DR
          </div>
          <div className="min-w-0 flex-1">
            <div className="truncate text-sm font-semibold text-foreground">Dr. Researcher</div>
            <div className="truncate text-[11px] text-muted-foreground">Principal Investigator</div>
          </div>
        </div>

        {/* Privacy badge */}
        <div className="flex items-start gap-2 rounded-lg bg-sage-soft/70 px-3 py-2">
          <Lock className="mt-0.5 h-3 w-3 shrink-0 text-primary" />
          <span className="text-[10px] leading-snug text-muted-foreground">
            Secure. Private. Built for Research.
          </span>
        </div>
      </div>
    </aside>
  );
};
