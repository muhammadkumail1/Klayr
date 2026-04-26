import { useState } from "react";
import { PageHeader } from "./PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useLitSearchMutation } from "@/hooks/useApi";
import { toast } from "sonner";
import { BookOpen, ExternalLink, Loader2, Search } from "lucide-react";

const Literature = () => {
  const [query, setQuery] = useState("probiotic gut permeability");
  const searchMutation = useLitSearchMutation();

  const handleSearch = () => {
    if (!query.trim()) return;
    searchMutation.mutate({ query, limit: 10 });
  };

  const papers = searchMutation.data?.papers ?? [];

  return (
    <div className="px-5 py-6 sm:px-8 sm:py-8">
      <PageHeader
        eyebrow="Literature Search"
        title="Discover related work"
        description="The AI Scientist scans PubMed and Semantic Scholar to surface the closest precedents to your hypothesis."
      />

      <div className="mb-6 flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search keywords, authors, or DOI..."
            className="pl-9"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          />
        </div>
        <Button variant="hero" size="sm" onClick={handleSearch} disabled={searchMutation.isPending}>
          {searchMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <BookOpen className="h-4 w-4" />}
          {searchMutation.isPending ? "Searching…" : "Run Literature QC"}
        </Button>
      </div>

      {searchMutation.isError && (
        <p className="mb-4 rounded-xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          Search failed: {searchMutation.error.message}
        </p>
      )}

      {papers.length === 0 && !searchMutation.isPending && (
        <div className="rounded-2xl border border-dashed border-border bg-card p-12 text-center text-muted-foreground">
          <BookOpen className="mx-auto mb-3 h-8 w-8 opacity-40" />
          <p className="text-sm">Enter a search query and click <strong>Run Literature QC</strong> to discover related research.</p>
        </div>
      )}

      <section className="space-y-4">
        {papers.map((p) => (
          <article key={p.title} className="rounded-2xl border border-border bg-card p-6 shadow-card transition-colors hover:border-primary/30">
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <span className="badge-pill bg-sage-soft text-primary">{p.source}</span>
              <span className="text-xs text-muted-foreground">{p.year}</span>
            </div>
            <h3 className="font-serif-display text-lg font-medium leading-snug text-foreground">{p.title}</h3>
            <p className="mt-1 text-xs text-muted-foreground">{p.authors.join(", ")}</p>
            {p.abstract_summary && <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{p.abstract_summary}</p>}
            <div className="mt-4 flex items-center gap-2">
              {p.url && p.url !== "https://placeholder.url" ? (
                <Button variant="ghost_dark" size="sm" asChild>
                  <a href={p.url} target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="h-3.5 w-3.5" />Open paper
                  </a>
                </Button>
              ) : null}
              <Button variant="ghost" size="sm" onClick={() => toast.success("Saved to references!")}>
                Save to references
              </Button>
            </div>
          </article>
        ))}
      </section>
    </div>
  );
};

export default Literature;

