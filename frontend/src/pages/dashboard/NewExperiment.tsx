import { PageHeader } from "./PageHeader";
import { HypothesisInputCard } from "@/components/dashboard/HypothesisInputCard";
import { ScienceWave } from "@/components/ScienceWave";

const NewExperiment = () => {
  return (
    <div className="px-5 py-6 sm:px-8 sm:py-8">
      <PageHeader
        eyebrow="New Experiment"
        title="Start a new investigation"
        description="Describe your hypothesis in natural language. Methodica will generate a literature check, protocol, materials, budget, and validation plan."
      />

      <section className="relative mb-8 overflow-hidden rounded-2xl border border-border bg-gradient-hero p-8 shadow-card">
        <div className="absolute inset-0 hero-grid-bg opacity-40" aria-hidden />
        <div className="relative grid gap-6 md:grid-cols-[1.3fr_1fr] md:items-center">
          <div>
            <h2 className="font-serif-display text-2xl font-medium leading-tight text-foreground">
              From a single sentence
              <br />
              <span className="italic text-primary">to a full research plan.</span>
            </h2>
            <p className="mt-3 max-w-md text-sm text-muted-foreground">
              Be specific about the molecule, organism, condition, or outcome you care about for best results.
            </p>
          </div>
          <div className="hidden md:block">
            <ScienceWave className="h-40" showLabels={false} />
          </div>
        </div>
      </section>

      <HypothesisInputCard />
    </div>
  );
};

export default NewExperiment;
