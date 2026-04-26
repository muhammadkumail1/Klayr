import { useState } from "react";
import { PageHeader } from "./PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useCollaboratorsMutation } from "@/hooks/useApi";
import { toast } from "sonner";
import { Loader2, Mail, MessageSquare, Search, UserPlus } from "lucide-react";

const Collaboration = () => {
  const [query, setQuery] = useState("");
  const [domain, setDomain] = useState("");
  const searchMutation = useCollaboratorsMutation();

  const handleSearch = () => {
    searchMutation.mutate({ query: query || undefined, domain: domain || undefined });
  };

  const collabs = searchMutation.data?.collaborators ?? [];

  return (
    <div className="px-5 py-6 sm:px-8 sm:py-8">
      <PageHeader
        eyebrow="Collaboration Finder"
        title="Researchers working in your space"
        description="AI-matched researchers scored by topic overlap, methodology, and recent publication activity."
      />

      <div className="mb-6 flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input placeholder="Research topic or keyword…" className="pl-9" value={query} onChange={(e) => setQuery(e.target.value)} />
        </div>
        <Input placeholder="Domain (optional)…" className="sm:max-w-[200px]" value={domain} onChange={(e) => setDomain(e.target.value)} />
        <Button variant="hero" size="sm" onClick={handleSearch} disabled={searchMutation.isPending}>
          {searchMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <UserPlus className="h-4 w-4" />}
          {searchMutation.isPending ? "Searching…" : "Find Collaborators"}
        </Button>
      </div>

      {collabs.length === 0 && !searchMutation.isPending && (
        <div className="rounded-2xl border border-dashed border-border bg-card p-12 text-center text-muted-foreground">
          <UserPlus className="mx-auto mb-3 h-8 w-8 opacity-40" />
          <p className="text-sm">Enter a topic and click <strong>Find Collaborators</strong> to discover matching researchers.</p>
        </div>
      )}

      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        {collabs.map((c) => {
          const initials = c.name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase();
          return (
            <article key={c.name} className="rounded-2xl border border-border bg-card p-6 shadow-card">
              <div className="flex items-start justify-between">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-green text-sm font-semibold text-primary-foreground">{initials}</div>
                <span className="badge-pill bg-sage-soft text-primary">{c.match_pct}% match</span>
              </div>
              <h3 className="font-serif-display mt-4 text-lg font-medium text-foreground">{c.name}</h3>
              <p className="text-xs text-muted-foreground">{c.institution}</p>
              {c.department && <p className="text-xs text-muted-foreground">{c.department}</p>}
              <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{c.topic}</p>
              {c.recent_publication && (
                <p className="mt-2 text-xs italic text-muted-foreground line-clamp-2">Recent: {c.recent_publication}</p>
              )}
              <div className="mt-3 flex flex-wrap gap-1.5">
                {c.domains.map((d) => (
                  <span key={d} className="rounded-full border border-border bg-muted px-2 py-0.5 text-[11px] text-muted-foreground">{d}</span>
                ))}
              </div>
              <div className="mt-5 flex items-center gap-2">
                <Button variant="hero" size="sm" className="flex-1" onClick={() => toast.success(`Connection request sent to ${c.name}!`)}>
                  <UserPlus className="h-3.5 w-3.5" />Connect
                </Button>
                <Button variant="ghost_dark" size="icon" aria-label="Message" onClick={() => toast.info("Messaging coming soon!")}>
                  <MessageSquare className="h-4 w-4" />
                </Button>
                <Button variant="ghost_dark" size="icon" aria-label="Email" onClick={() => toast.info("Email coming soon!")}>
                  <Mail className="h-4 w-4" />
                </Button>
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
};

export default Collaboration;

