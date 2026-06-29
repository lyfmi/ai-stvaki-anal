import { Camera, Globe, ShieldCheck } from "lucide-react";
import type { Translations } from "../../i18n";

interface StepPillProps {
  t: Translations;
  activeStep?: 1 | 2 | 3 | null;
}

const steps = [
  { key: "photo" as const, icon: Camera, step: 1 },
  { key: "research" as const, icon: Globe, step: 2 },
  { key: "risk" as const, icon: ShieldCheck, step: 3 },
];

export function StepPills({ t, activeStep = null }: StepPillProps) {
  const labels = {
    photo: t.home_step_photo,
    research: t.home_step_research,
    risk: t.home_step_risk,
  };

  return (
    <div className="relative w-full">
      <div
        className="pointer-events-none absolute left-[calc(100%/6)] right-[calc(100%/6)] top-[18px] flex"
        aria-hidden="true"
      >
        <div
          className={`h-px flex-1 ${
            activeStep !== null && activeStep > 1 ? "bg-accent/40" : "bg-borderSubtle"
          }`}
        />
        <div
          className={`h-px flex-1 ${
            activeStep !== null && activeStep > 2 ? "bg-accent/40" : "bg-borderSubtle"
          }`}
        />
      </div>

      <div className="grid grid-cols-3 w-full">
        {steps.map(({ key, icon: Icon, step }) => {
          const active = activeStep === step;
          const done = activeStep !== null && activeStep > step;

          return (
            <div
              key={key}
              className={`flex flex-col items-center transition-all duration-300 ${
                active ? "opacity-100" : done ? "opacity-70" : "opacity-40"
              }`}
            >
              <div
                className={`w-9 h-9 shrink-0 rounded-full border flex items-center justify-center transition-all duration-300 ${
                  active
                    ? "border-accent bg-accent/10 shadow-accent"
                    : done
                      ? "border-accent/50 bg-accent/5"
                      : "border-borderSubtle bg-surface"
                }`}
              >
                <Icon className={`w-4 h-4 ${active || done ? "text-accent" : "text-textMuted"}`} />
              </div>
              <span
                className={`mt-1.5 text-[10px] text-center leading-tight min-h-[2.5em] px-1 transition-all duration-300 ${
                  active ? "text-accent" : done ? "text-textMuted opacity-70" : "text-textMuted opacity-40"
                }`}
              >
                {labels[key]}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
