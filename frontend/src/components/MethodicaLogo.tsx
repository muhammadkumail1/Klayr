import { cn } from "@/lib/utils";

interface MethodicaLogoProps {
  className?: string;
  variant?: "dark" | "light";
}

export const MethodicaLogo = ({ className }: MethodicaLogoProps) => {
  return (
    <div className={cn("flex items-center", className)}>
      <img src="/full_logo.png" alt="The AI Scientist" className="h-9 w-auto object-contain" />
    </div>
  );
};
