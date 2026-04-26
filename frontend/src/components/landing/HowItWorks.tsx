import { Lightbulb, Search, ClipboardList, TrendingDown, Users, FileText } from "lucide-react";

const steps = [
  { num: "01", icon: Lightbulb, title: "Enter Hypothesis" },
  { num: "02", icon: Search, title: "Check Literature" },
  { num: "03", icon: ClipboardList, title: "Generate Plan" },
  { num: "04", icon: TrendingDown, title: "Optimize Cost" },
  { num: "05", icon: Users, title: "Find Collaborators" },
  { num: "06", icon: FileText, title: "Export Report" },
];

export const HowItWorks = () => {
  return (
    <section id="how-it-works" className="bg-sage-soft/40 py-20 md:py-28">
      <div className="container">
        <div className="mx-auto max-w-2xl text-center">
          <span className="badge-pill bg-card text-primary border border-border">Workflow</span>
          <h2 className="font-serif-display mt-5 text-display font-medium">How Methodica works</h2>
          <p className="mt-4 text-muted-foreground">
            Six calm steps from natural-language idea to a publishable plan.
          </p>
        </div>

        <div className="relative mt-14">
          {/* connecting line */}
          <div
            className="absolute left-0 right-0 top-7 hidden h-px bg-gradient-to-r from-transparent via-primary/25 to-transparent lg:block"
            aria-hidden
          />

          <ol className="grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6">
            {steps.map((step) => (
              <li
                key={step.num}
                className="relative rounded-2xl border border-border/70 bg-card p-5 text-center shadow-card"
              >
                <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-sage-soft ring-4 ring-card">
                  <step.icon className="h-5 w-5 text-primary" strokeWidth={1.6} />
                </div>
                <div className="mt-3 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                  Step {step.num}
                </div>
                <div className="mt-1 text-sm font-semibold text-foreground">{step.title}</div>
              </li>
            ))}
          </ol>
        </div>
      </div>
    </section>
  );
};
