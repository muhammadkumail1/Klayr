import { PageHeader } from "./PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";

const Settings = () => {
  return (
    <div className="px-5 py-6 sm:px-8 sm:py-8">
      <PageHeader
        eyebrow="Settings"
        title="Workspace preferences"
        description="Manage your profile, defaults, and how Methodica works for your lab."
      />

      <div className="grid gap-6 lg:grid-cols-3">
        <section className="rounded-2xl border border-border bg-card p-6 shadow-card lg:col-span-2">
          <h3 className="font-serif-display text-lg font-medium text-foreground">Profile</h3>
          <p className="text-xs text-muted-foreground">Visible to potential collaborators.</p>
          <div className="mt-5 grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="name">Full name</Label>
              <Input id="name" defaultValue="Dr. Researcher" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="title">Title</Label>
              <Input id="title" defaultValue="Principal Investigator" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="institution">Institution</Label>
              <Input id="institution" defaultValue="University Research Lab" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" defaultValue="researcher@lab.edu" />
            </div>
          </div>
          <div className="mt-6 flex justify-end">
            <Button variant="hero" size="sm">Save changes</Button>
          </div>
        </section>

        <section className="rounded-2xl border border-border bg-card p-6 shadow-card">
          <h3 className="font-serif-display text-lg font-medium text-foreground">Preferences</h3>
          <p className="text-xs text-muted-foreground">Tune how Methodica plans for you.</p>
          <ul className="mt-5 space-y-4">
            {[
              { label: "Lean cost mode by default", desc: "Optimize for the lowest viable budget." },
              { label: "Auto-run literature QC", desc: "Trigger on every new hypothesis." },
              { label: "Suggest collaborators", desc: "Surface matches with each plan." },
              { label: "Email weekly digest", desc: "Summary of activity every Monday." },
            ].map((p, i) => (
              <li key={p.label} className="flex items-start justify-between gap-4">
                <div>
                  <div className="text-sm font-medium text-foreground">{p.label}</div>
                  <div className="text-xs text-muted-foreground">{p.desc}</div>
                </div>
                <Switch defaultChecked={i !== 3} />
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
};

export default Settings;
