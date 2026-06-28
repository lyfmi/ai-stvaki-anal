import { RefreshCw } from "lucide-react";
import type { Translations } from "../../i18n";

interface ProcessingOverlayProps {
  step: 1 | 2 | 3;
  t: Translations;
}

export function ProcessingOverlay({ step, t }: ProcessingOverlayProps) {
  return (
    <div className="p-6 bg-surface border border-borderSubtle rounded-containerLg flex flex-col items-center justify-center min-h-[280px] gap-6 text-center">
      <RefreshCw className="w-10 h-10 text-accent animate-spin" />

      <div className="flex flex-col gap-2">
        <h3 className="text-base font-semibold text-textPrimary">
          {step === 1 && t.uploading_vision}
          {step === 2 && t.uploading_search}
          {step === 3 && t.uploading_synthesis}
        </h3>
      </div>

      <div className="w-full max-w-xs h-0.5 bg-borderSubtle rounded-full overflow-hidden">
        <div className="h-full bg-accent animate-progress" />
      </div>
    </div>
  );
}
