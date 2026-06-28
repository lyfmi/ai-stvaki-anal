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
    <div className="w-full px-1">
      <div className="grid grid-cols-[1fr_auto_1fr_auto_1fr] items-center">
        {steps.map(({ key, icon: Icon, step }, idx) => {
          const active = activeStep === step;
          const done = activeStep !== null && activeStep > step;
          const lineDone = activeStep !== null && activeStep > step;
          return (
            <div key={key} className="contents">
              <div
                className={`flex justify-center transition-all duration-300 ${
                  active ? "opacity-100" : done ? "opacity-70" : "opacity-40"
                }`}
              >
                <div
                  className={`w-9 h-9 rounded-full border flex items-center justify-center transition-all duration-300 ${
                    active
                      ? "border-accent bg-accent/10 shadow-[0_0_12px_#00FF9D33]"
                      : done
                        ? "border-accent/50 bg-accent/5"
                        : "border-borderSubtle bg-surface"
                  }`}
                >
                  <Icon className={`w-4 h-4 ${active || done ? "text-accent" : "text-textMuted"}`} />
                </div>
              </div>
              {idx < steps.length - 1 && (
                <div
                  className={`h-px w-8 sm:w-10 mx-1 ${
                    lineDone ? "bg-accent/40" : "bg-borderSubtle"
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-3 mt-1.5">
        {steps.map(({ key, step }) => {
          const active = activeStep === step;
          const done = activeStep !== null && activeStep > step;
          return (
            <span
              key={key}
              className={`text-[10px] text-center leading-tight min-h-[2.5em] px-0.5 transition-all duration-300 ${
                active ? "text-accent" : done ? "text-textMuted opacity-70" : "text-textMuted opacity-40"
              }`}
            >
              {labels[key]}
            </span>
          );
        })}
      </div>
    </div>
  );
}
