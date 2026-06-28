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
    <div className="flex items-center justify-between gap-2">
      {steps.map(({ key, icon: Icon, step }, idx) => {
        const active = activeStep === step;
        const done = activeStep !== null && activeStep > step;
        return (
          <div key={key} className="flex items-center flex-1 min-w-0">
            <div
              className={`flex flex-col items-center gap-1.5 flex-1 transition-all duration-300 ${
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
              <span className={`text-[10px] truncate ${active ? "text-accent" : "text-textMuted"}`}>
                {labels[key]}
              </span>
            </div>
            {idx < steps.length - 1 && (
              <div className={`h-px flex-1 mx-1 mb-5 ${done ? "bg-accent/40" : "bg-borderSubtle"}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}
