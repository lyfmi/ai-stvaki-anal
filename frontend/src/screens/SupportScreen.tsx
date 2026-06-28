import { HelpCircle } from "lucide-react";
import { SecondaryButton } from "../components/ui/PrimaryButton";
import type { Translations } from "../i18n";

interface SupportScreenProps {
  settings: any;
  t: Translations;
}

export function SupportScreen({ settings, t }: SupportScreenProps) {
  const url = settings?.support_url || "https://t.me/example";

  return (
    <div className="flex flex-col gap-5 screen-enter">
      <h2 className="text-lg font-semibold text-textPrimary">{t.support_btn}</h2>
      <div className="p-6 bg-surface border border-borderSubtle rounded-containerLg text-center flex flex-col gap-4">
        <HelpCircle className="w-10 h-10 text-accent mx-auto" />
        <p className="text-xs text-textMuted">{t.support_desc}</p>
        <SecondaryButton
          onClick={() => window.Telegram?.WebApp?.openLink(url) ?? window.open(url, "_blank")}
        >
          {t.support_open}
        </SecondaryButton>
      </div>
    </div>
  );
}
