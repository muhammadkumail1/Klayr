import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { MethodicaLogo } from "@/components/MethodicaLogo";
import { ScienceWave } from "@/components/ScienceWave";
import { Lock, Microscope, Sparkles, Users, Wallet, ArrowRight } from "lucide-react";
import { FormEvent } from "react";

const valueBullets = [
  { icon: Microscope, label: "Smarter Literature Insights" },
  { icon: Sparkles, label: "AI-Powered Experiment Planning" },
  { icon: Wallet, label: "Cost Optimization" },
  { icon: Users, label: "Scientist-in-the-Loop Review" },
];

const Login = () => {
  const navigate = useNavigate();

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    navigate("/dashboard");
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="grid min-h-screen lg:grid-cols-2">
        {/* Left side */}
        <div className="relative hidden flex-col justify-between overflow-hidden bg-gradient-hero p-10 lg:flex">
          <div className="absolute inset-0 hero-grid-bg opacity-40" aria-hidden />
          <div className="relative">
            <Link to="/">
              <MethodicaLogo />
            </Link>
          </div>

          <div className="relative max-w-md">
            <h1 className="font-serif-display text-5xl font-medium leading-[1.05] text-foreground">
              From Hypothesis
              <br />
              <span className="italic text-primary">to Breakthrough</span>
            </h1>
            <p className="mt-5 text-base leading-relaxed text-muted-foreground">
              Methodica is your AI co-scientist that helps you discover, plan,
              optimize, and collaborate on better experiments.
            </p>

            <ul className="mt-8 space-y-3">
              {valueBullets.map((b) => (
                <li key={b.label} className="flex items-center gap-3">
                  <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-card text-primary shadow-card">
                    <b.icon className="h-4 w-4" strokeWidth={1.6} />
                  </span>
                  <span className="text-sm font-medium text-foreground">{b.label}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="relative -mb-16 -ml-6 opacity-90">
            <ScienceWave className="h-56" showLabels={false} />
          </div>
        </div>

        {/* Right side */}
        <div className="flex items-center justify-center p-6 sm:p-10">
          <div className="w-full max-w-md">
            <div className="lg:hidden mb-8">
              <Link to="/">
                <MethodicaLogo />
              </Link>
            </div>

            <div className="rounded-2xl border border-border bg-card p-7 shadow-soft sm:p-9">
              <h2 className="font-serif-display text-3xl font-medium">Welcome back</h2>
              <p className="mt-2 text-sm text-muted-foreground">
                Sign in to continue your research.
              </p>

              <div className="mt-7 space-y-2.5">
                <Button variant="outline" className="w-full" size="lg">
                  <GoogleIcon />
                  Continue with Google
                </Button>
                <Button variant="outline" className="w-full" size="lg">
                  <MicrosoftIcon />
                  Continue with Microsoft
                </Button>
              </div>

              <div className="my-6 flex items-center gap-3 text-xs uppercase tracking-widest text-muted-foreground">
                <span className="h-px flex-1 bg-border" />
                or with email
                <span className="h-px flex-1 bg-border" />
              </div>

              <form className="space-y-4" onSubmit={handleSubmit}>
                <div className="space-y-1.5">
                  <Label htmlFor="email">Email address</Label>
                  <Input id="email" type="email" placeholder="researcher@university.edu" required />
                </div>
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="password">Password</Label>
                    <a href="#" className="text-xs font-medium text-primary hover:underline">
                      Forgot password?
                    </a>
                  </div>
                  <Input id="password" type="password" placeholder="••••••••" required />
                </div>

                <Button type="submit" variant="hero" size="lg" className="w-full">
                  Login
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </form>

              <p className="mt-6 text-center text-sm text-muted-foreground">
                New to Methodica?{" "}
                <Link to="/dashboard" className="font-medium text-primary hover:underline">
                  Sign up
                </Link>
              </p>
            </div>

            <div className="mt-5 flex items-start gap-3 rounded-xl border border-border bg-sage-soft/60 p-4">
              <Lock className="mt-0.5 h-4 w-4 shrink-0 text-primary" strokeWidth={1.8} />
              <p className="text-xs leading-relaxed text-muted-foreground">
                Your data is encrypted and never used to train public models.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const GoogleIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" aria-hidden>
    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
  </svg>
);

const MicrosoftIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" aria-hidden>
    <rect x="1" y="1" width="10" height="10" fill="#F25022" />
    <rect x="13" y="1" width="10" height="10" fill="#7FBA00" />
    <rect x="1" y="13" width="10" height="10" fill="#00A4EF" />
    <rect x="13" y="13" width="10" height="10" fill="#FFB900" />
  </svg>
);

export default Login;
