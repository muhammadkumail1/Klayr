import { cn } from "@/lib/utils";

interface MethodicaLogoProps {
  className?: string;
  variant?: "dark" | "light";
}

export const MethodicaLogo = ({ className, variant = "dark" }: MethodicaLogoProps) => {
  const color = variant === "dark" ? "hsl(var(--primary))" : "hsl(var(--primary-foreground))";
  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <svg width="28" height="28" viewBox="0 0 32 32" fill="none" aria-hidden>
        <circle cx="16" cy="16" r="14" stroke={color} strokeWidth="1.5" opacity="0.3" />
        <circle cx="16" cy="16" r="3" fill={color} />
        <circle cx="6" cy="10" r="2" fill={color} opacity="0.7" />
        <circle cx="26" cy="10" r="2" fill={color} opacity="0.7" />
        <circle cx="6" cy="22" r="2" fill={color} opacity="0.7" />
        <circle cx="26" cy="22" r="2" fill={color} opacity="0.7" />
        <line x1="6" y1="10" x2="16" y2="16" stroke={color} strokeWidth="1.2" opacity="0.5" />
        <line x1="26" y1="10" x2="16" y2="16" stroke={color} strokeWidth="1.2" opacity="0.5" />
        <line x1="6" y1="22" x2="16" y2="16" stroke={color} strokeWidth="1.2" opacity="0.5" />
        <line x1="26" y1="22" x2="16" y2="16" stroke={color} strokeWidth="1.2" opacity="0.5" />
      </svg>
      <span
        className="font-serif-display text-xl font-semibold tracking-tight"
        style={{ color }}
      >
        Methodica
      </span>
    </div>
  );
};
