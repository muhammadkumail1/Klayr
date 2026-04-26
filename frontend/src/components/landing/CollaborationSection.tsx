import { Button } from "@/components/ui/button";
import { ArrowRight, Sparkles } from "lucide-react";

export const CollaborationSection = () => {
  return (
    <section id="collaboration" className="py-20 md:py-28">
      <div className="container grid items-center gap-12 lg:grid-cols-2 lg:gap-20">
        <div>
          <span className="badge-pill bg-sage text-primary">Differentiator</span>
          <h2 className="font-serif-display mt-5 text-display font-medium">
            Research should not happen in isolation.
          </h2>
          <p className="mt-5 max-w-xl text-lg leading-relaxed text-muted-foreground">
            Methodica detects when another researcher is working on a similar idea and
            suggests a safe collaboration match — without exposing private project details.
          </p>
          <Button variant="hero" size="lg" className="mt-8">
            Explore Collaboration Finder
            <ArrowRight className="h-4 w-4" />
          </Button>
        </div>

        {/* Mock collaboration card */}
        <div className="relative">
          <div className="absolute -inset-6 rounded-[2rem] bg-gradient-sage opacity-70 blur-2xl" aria-hidden />
          <div className="relative rounded-2xl border border-border/70 bg-card p-6 shadow-elevated">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-green text-primary-foreground font-serif-display text-lg">
                  EM
                </div>
                <div>
                  <div className="font-semibold text-foreground">Dr. Elena Marquez</div>
                  <div className="text-xs text-muted-foreground">Stanford University · Microbiome Lab</div>
                </div>
              </div>
              <span className="badge-pill bg-success-soft text-success">
                <Sparkles className="h-3 w-3" />
                92% match
              </span>
            </div>

            <div className="mt-5 rounded-xl bg-sage-soft/70 p-4">
              <div className="text-[10px] font-semibold uppercase tracking-widest text-primary/70">
                Shared topic
              </div>
              <div className="mt-1 text-sm font-medium text-foreground">
                Probiotic-mediated modulation of intestinal barrier function
              </div>
            </div>

            <div className="mt-4 flex flex-wrap gap-2">
              {["gut permeability", "inflammation", "Lactobacillus", "tight junctions"].map((tag) => (
                <span
                  key={tag}
                  className="rounded-full border border-border bg-background px-3 py-1 text-xs text-muted-foreground"
                >
                  {tag}
                </span>
              ))}
            </div>

            <div className="mt-6 flex items-center justify-between border-t border-border pt-5">
              <div className="text-xs text-muted-foreground">3 papers cited in common</div>
              <Button variant="hero" size="sm">
                Request Collaboration
              </Button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
