import { cn } from "@/lib/utils";

interface ScienceWaveProps {
  className?: string;
  showLabels?: boolean;
}

/**
 * Calm scientific data visual — thin wave lines, faint grid, connected nodes,
 * soft bar fade. Sage/green palette only. No germ/cell illustration.
 */
export const ScienceWave = ({ className, showLabels = true }: ScienceWaveProps) => {
  return (
    <div className={cn("relative w-full", className)}>
      <svg
        viewBox="0 0 600 420"
        className="h-full w-full"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden
      >
        {/* faint dotted grid */}
        <defs>
          <pattern id="dotgrid" x="0" y="0" width="24" height="24" patternUnits="userSpaceOnUse">
            <circle cx="1" cy="1" r="1" fill="hsl(var(--primary))" opacity="0.08" />
          </pattern>
          <linearGradient id="barFade" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity="0.18" />
            <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity="0" />
          </linearGradient>
          <linearGradient id="waveStroke" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity="0.2" />
            <stop offset="50%" stopColor="hsl(var(--primary))" stopOpacity="0.9" />
            <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity="0.2" />
          </linearGradient>
        </defs>

        <rect width="600" height="420" fill="url(#dotgrid)" />

        {/* soft bar chart fade */}
        {[60, 130, 200, 270, 340, 410, 480].map((x, i) => {
          const h = 60 + (i % 3) * 30 + (i === 3 ? 40 : 0);
          return (
            <rect
              key={x}
              x={x}
              y={380 - h}
              width="40"
              height={h}
              rx="6"
              fill="url(#barFade)"
            />
          );
        })}

        {/* primary thin wave */}
        <path
          d="M 20 240 Q 100 180 180 220 T 340 200 T 500 230 T 600 210"
          stroke="url(#waveStroke)"
          strokeWidth="2"
          fill="none"
          strokeLinecap="round"
          strokeDasharray="1000"
          className="animate-draw-line"
        />

        {/* secondary thin wave */}
        <path
          d="M 0 290 Q 120 250 240 280 T 480 270 T 600 290"
          stroke="hsl(var(--primary))"
          strokeWidth="1"
          strokeOpacity="0.35"
          fill="none"
          strokeLinecap="round"
        />

        {/* connected nodes */}
        {[
          { x: 100, y: 160, label: "HYPOTHESIS" },
          { x: 300, y: 110, label: "ANALYZE" },
          { x: 500, y: 150, label: "INSIGHT" },
        ].map((n, i) => (
          <g key={n.label}>
            {i < 2 && (
              <line
                x1={n.x}
                y1={n.y}
                x2={[300, 500][i]}
                y2={[110, 150][i]}
                stroke="hsl(var(--primary))"
                strokeWidth="1"
                strokeOpacity="0.35"
                strokeDasharray="3 4"
              />
            )}
            <circle cx={n.x} cy={n.y} r="14" fill="hsl(var(--soft-sage))" stroke="hsl(var(--primary))" strokeOpacity="0.4" />
            <circle cx={n.x} cy={n.y} r="5" fill="hsl(var(--primary))" />
            {showLabels && (
              <text
                x={n.x}
                y={n.y - 26}
                textAnchor="middle"
                fontSize="9"
                fontWeight="600"
                letterSpacing="1.5"
                fill="hsl(var(--primary))"
                opacity="0.7"
                fontFamily="Inter, sans-serif"
              >
                {n.label}
              </text>
            )}
          </g>
        ))}

        {/* satellite dots */}
        {[
          { x: 60, y: 90 },
          { x: 220, y: 60 },
          { x: 400, y: 80 },
          { x: 560, y: 100 },
          { x: 180, y: 340 },
          { x: 420, y: 320 },
        ].map((d, i) => (
          <circle
            key={i}
            cx={d.x}
            cy={d.y}
            r="2.5"
            fill="hsl(var(--primary))"
            opacity="0.4"
            className="animate-pulse-soft"
            style={{ animationDelay: `${i * 0.4}s` }}
          />
        ))}
      </svg>
    </div>
  );
};
