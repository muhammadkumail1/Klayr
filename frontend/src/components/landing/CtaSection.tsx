import { Button } from "@/components/ui/button";
import { ArrowRight, Lock } from "lucide-react";
import { Link } from "react-router-dom";

export const CtaSection = () => {
  return (
    <section className="py-20 md:py-28">
      <div className="container">
        <div className="relative overflow-hidden rounded-[2rem] bg-gradient-green px-8 py-16 text-center shadow-elevated md:px-16 md:py-20">
          <div
            className="absolute inset-0 opacity-[0.07]"
            style={{
              backgroundImage:
                "radial-gradient(circle at 1px 1px, white 1px, transparent 0)",
              backgroundSize: "28px 28px",
            }}
            aria-hidden
          />
          <div className="relative">
            <h2 className="font-serif-display text-display font-medium text-primary-foreground">
              Start your next experiment
              <br />
              <span className="italic opacity-90">with The AI Scientist.</span>
            </h2>

            <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
              <Button asChild size="lg" className="bg-card text-primary hover:bg-card/90">
                <Link to="/dashboard">
                  Get Started
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
              <Button
                asChild
                size="lg"
                variant="ghost"
                className="text-primary-foreground hover:bg-primary-foreground/10"
              >
                <Link to="/login">Login</Link>
              </Button>
            </div>

            <div className="mt-10 inline-flex items-center gap-2 text-xs uppercase tracking-widest text-primary-foreground/70">
              <Lock className="h-3.5 w-3.5" />
              Secure · Private · Built for Research
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
