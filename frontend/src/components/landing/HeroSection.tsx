import { Button } from "@/components/ui/button";
import { ScienceWave } from "@/components/ScienceWave";
import { ArrowRight, PlayCircle } from "lucide-react";
import { Link } from "react-router-dom";

export const HeroSection = () => {
  return (
    <section className="relative overflow-hidden">
      <div className="absolute inset-0 hero-grid-bg opacity-50" aria-hidden />
      <div className="container relative grid gap-12 py-20 md:py-28 lg:grid-cols-2 lg:items-center lg:gap-16">
        <div className="animate-fade-in-up">
          <span className="badge-pill border border-primary/15 bg-sage-soft text-primary">
            <span className="h-1.5 w-1.5 rounded-full bg-primary" />
            AI Co-Scientist
          </span>

          <h1 className="font-serif-display mt-6 text-hero font-medium text-foreground">
            From Hypothesis
            <br />
            <span className="italic text-primary">to Breakthrough</span>
          </h1>

          <p className="mt-6 max-w-xl text-lg leading-relaxed text-muted-foreground">
            Methodica is your AI co-scientist that helps researchers validate ideas,
            generate experiment plans, optimize costs, and discover collaborators.
          </p>

          <div className="mt-10 flex flex-wrap items-center gap-4">
            <Button asChild variant="hero" size="lg">
              <Link to="/dashboard">
                Start Experiment
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button variant="ghost_dark" size="lg">
              <PlayCircle className="h-4 w-4" />
              View Demo
            </Button>
          </div>

          <div className="mt-10 flex items-center gap-6 text-xs uppercase tracking-widest text-muted-foreground">
            <span>Hypothesis</span>
            <span className="h-px w-8 bg-border" />
            <span>Analyze</span>
            <span className="h-px w-8 bg-border" />
            <span>Insight</span>
          </div>
        </div>

        <div className="relative">
          <div className="absolute -inset-8 rounded-[2rem] bg-gradient-hero opacity-60 blur-3xl" aria-hidden />
          <div className="relative rounded-[2rem] border border-border/60 bg-card/70 p-6 shadow-soft backdrop-blur">
            <ScienceWave className="aspect-[4/3]" />
          </div>
        </div>
      </div>
    </section>
  );
};
