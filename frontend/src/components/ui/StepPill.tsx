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
    <div className="flex items-start w-full px-1">
      {steps.map(({ key, icon: Icon, step }, idx) => {
        const active = activeStep === step;
        const done = activeStep !== null && activeStep > step;
        const lineDone = activeStep !== null && activeStep > step;

        return (
          <div key={key} className="flex items-start flex-1 min-w-0">
            <div
              className={`flex flex-col items-center flex-1 min-w-0 transition-all duration-300 ${
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
                className={`mt-1.5 w-full text-[10px] text-center leading-tight min-h-[2.5em] block transition-all duration-300 ${
                  active ? "text-accent" : done ? "text-textMuted opacity-70" : "text-textMuted opacity-40"
                }`}
              >
                {labels[key]}
              </span>
            </div>

            {idx < steps.length - 1 && (
              <div className="shrink-0 flex items-center h-9 px-0.5 sm:px-1" aria-hidden="true">
                <div
                  className={`h-px w-full min-w-[1.5rem] sm:min-w-[2rem] max-w-[2.5rem] ${
                    lineDone ? "bg-accent/40" : "bg-borderSubtle"
                  }`}
                />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
