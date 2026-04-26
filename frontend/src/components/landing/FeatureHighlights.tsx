import { BookOpen, FlaskConical, Wallet, Users } from "lucide-react";

const features = [
  {
    icon: BookOpen,
    title: "Literature QC",
    body: "Detect similar work and surface top references to ground every hypothesis.",
  },
  {
    icon: FlaskConical,
    title: "Experiment Planning",
    body: "Generate protocols, materials, budget, timeline and validation in one flow.",
  },
  {
    icon: Wallet,
    title: "Cost Optimizer",
    body: "Compare original vs optimized costs with savings and risk levels.",
  },
  {
    icon: Users,
    title: "Collaboration Finder",
    body: "Match researchers working on similar hypotheses without exposing details.",
  },
];

export const FeatureHighlights = () => {
  return (
    <section id="features" className="py-20 md:py-28">
      <div className="container">
        <div className="mx-auto max-w-2xl text-center">
          <span className="badge-pill bg-sage text-primary">Capabilities</span>
          <h2 className="font-serif-display mt-5 text-display font-medium">
            A complete research planning suite
          </h2>
          <p className="mt-4 text-muted-foreground">
            Four focused modules that turn a single sentence into a review-ready experiment.
          </p>
        </div>

        <div className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {features.map((f) => (
            <article
              key={f.title}
              className="group rounded-2xl border border-border/70 bg-card p-6 shadow-card transition-all hover:-translate-y-1 hover:border-primary/30 hover:shadow-soft"
            >
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-sage-soft text-primary transition-colors group-hover:bg-sage">
                <f.icon className="h-5 w-5" strokeWidth={1.6} />
              </div>
              <h3 className="mt-5 text-base font-semibold text-foreground">{f.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{f.body}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
};
