import { MethodicaLogo } from "@/components/MethodicaLogo";

const columns = [
  {
    title: "Product",
    links: ["Dashboard", "New Experiment", "Pricing", "Changelog"],
  },
  {
    title: "Features",
    links: ["Literature QC", "Experiment Planning", "Cost Optimizer", "Collaboration"],
  },
  {
    title: "Resources",
    links: ["Documentation", "Research Blog", "Method Library", "Support"],
  },
  {
    title: "Company",
    links: ["About", "Privacy", "Terms", "Contact"],
  },
];

export const LandingFooter = () => {
  return (
    <footer className="border-t border-border bg-sage-soft/40">
      <div className="container py-16">
        <div className="grid gap-10 lg:grid-cols-[1.4fr_repeat(4,1fr)]">
          <div>
            <MethodicaLogo />
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-muted-foreground">
              The calm, academic AI co-scientist for serious research workflows.
            </p>
          </div>
          {columns.map((col) => (
            <div key={col.title}>
              <div className="text-[11px] font-semibold uppercase tracking-widest text-primary">
                {col.title}
              </div>
              <ul className="mt-4 space-y-3">
                {col.links.map((l) => (
                  <li key={l}>
                    <a className="text-sm text-muted-foreground transition-colors hover:text-primary" href="#">
                      {l}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-12 flex flex-col items-start justify-between gap-3 border-t border-border pt-8 text-xs text-muted-foreground sm:flex-row sm:items-center">
          <div>© {new Date().getFullYear()} Methodica Research. All rights reserved.</div>
          <div>Built for serious science.</div>
        </div>
      </div>
    </footer>
  );
};
