import { CheckCircle2 } from "lucide-react";

const points = [
  "Uses scientific literature sources",
  "Produces structured experiment plans",
  "Supports scientist review and correction",
  "Keeps collaboration privacy-aware",
];

const partners = ["MIT", "Stanford", "Johns Hopkins", "Fulcrum Science", "ETH Zürich"];

export const TrustSection = () => {
  return (
    <section className="bg-sage-soft/40 py-20 md:py-24">
      <div className="container">
        <div className="mx-auto max-w-2xl text-center">
          <span className="badge-pill bg-card text-primary border border-border">Trust</span>
          <h2 className="font-serif-display mt-5 text-display font-medium">
            Built for serious research workflows.
          </h2>
        </div>

        <ul className="mx-auto mt-12 grid max-w-3xl gap-4 sm:grid-cols-2">
          {points.map((p) => (
            <li
              key={p}
              className="flex items-start gap-3 rounded-xl border border-border/70 bg-card px-5 py-4 shadow-card"
            >
              <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-primary" strokeWidth={1.6} />
              <span className="text-sm text-foreground">{p}</span>
            </li>
          ))}
        </ul>

        <div className="mt-14">
          <div className="text-center text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
            Inspired by research from
          </div>
          <div className="mt-6 flex flex-wrap items-center justify-center gap-x-12 gap-y-4 opacity-70">
            {partners.map((p) => (
              <span key={p} className="font-serif-display text-lg text-primary/70">
                {p}
              </span>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};
