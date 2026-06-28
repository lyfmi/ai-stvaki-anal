import { ShieldAlert } from "lucide-react";
import { SecondaryButton } from "../components/ui/PrimaryButton";
import type { Translations } from "../i18n";

export function FunnelLockedScreen({ t }: { t: Translations }) {
  return (
    <div className="flex flex-col items-center justify-center text-center gap-6 py-16 px-4 screen-enter">
      <ShieldAlert className="w-14 h-14 text-accent/70" />
      <div className="flex flex-col gap-2">
        <h2 className="text-lg font-semibold text-textPrimary">{t.funnel_locked_title}</h2>
        <p className="text-sm text-textMuted leading-relaxed">{t.funnel_locked_desc}</p>
      </div>
      <SecondaryButton onClick={() => window.Telegram?.WebApp?.close()} className="max-w-xs">
        {t.funnel_locked_bot}
      </SecondaryButton>
    </div>
  );
}
