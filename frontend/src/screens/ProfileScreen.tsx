import { ChevronRight, Crown, HelpCircle, Languages, Settings, User as UserIcon } from "lucide-react";
import { ADMIN_TELEGRAM_ID } from "../constants";
import type { Translations, Lang } from "../i18n";

interface ProfileScreenProps {
  user: any;
  lang: Lang;
  t: Translations;
  onLangChange: (l: Lang) => void;
  onNavigate: (target: "support" | "unlimited" | "admin") => void;
}

export function ProfileScreen({ user, lang, t, onLangChange, onNavigate }: ProfileScreenProps) {
  if (!user) return null;

  const isUnlimited = user.has_unlimited || user.funnel_state === "UNLIMITED";
  const isAdmin = user.telegram_id === ADMIN_TELEGRAM_ID;

  const links = [
    { key: "support" as const, icon: HelpCircle, label: t.profile_support },
    { key: "unlimited" as const, icon: Crown, label: t.profile_unlimited },
    ...(isAdmin ? [{ key: "admin" as const, icon: Settings, label: t.profile_admin }] : []),
  ];

  return (
    <div className="flex flex-col gap-5 screen-enter">
      <h2 className="text-lg font-semibold text-textPrimary">{t.profile}</h2>

      <div className="p-4 bg-surface border border-borderSubtle rounded-containerLg flex items-center gap-3">
        <div className="w-11 h-11 rounded-full bg-accent/10 border border-accent/20 flex items-center justify-center">
          <UserIcon className="w-5 h-5 text-accent" />
        </div>
        <div className="flex flex-col min-w-0">
          <span className="text-sm font-medium text-textPrimary truncate">
            @{user.username || "user"}
          </span>
          <span className="text-[10px] text-textMuted">
            {isUnlimited ? t.home_unlimited : t.profile_status}
          </span>
        </div>
      </div>

      <div className="p-4 bg-surface border border-borderSubtle rounded-containerLg flex flex-col gap-2 text-xs">
        <div className="flex justify-between">
          <span className="text-textMuted">{t.profile_registered}</span>
          <span className="text-textPrimary">{user.is_registered ? t.yes : t.no}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-textMuted">{t.profile_deposited}</span>
          <span className="text-textPrimary">{user.is_deposited ? t.yes : t.no}</span>
        </div>
      </div>

      <div className="p-4 bg-surface border border-borderSubtle rounded-containerLg flex flex-col gap-3">
        <span className="text-xs font-medium text-textPrimary flex items-center gap-2">
          <Languages className="w-4 h-4 text-accent" /> {t.profile_lang}
        </span>
        <div className="flex gap-2">
          {(["ru", "en"] as Lang[]).map((l) => (
            <button
              key={l}
              type="button"
              onClick={() => onLangChange(l)}
              className={`flex-1 py-2.5 rounded-xl border text-xs font-medium transition-all ${
                lang === l
                  ? "bg-accent/10 border-accent text-accent"
                  : "border-borderSubtle text-textMuted"
              }`}
            >
              {l === "ru" ? "Русский" : "English"}
            </button>
          ))}
        </div>
      </div>

      <div className="flex flex-col gap-1">
        {links.map(({ key, icon: Icon, label }) => (
          <button
            key={key}
            type="button"
            onClick={() => onNavigate(key)}
            className="flex items-center justify-between p-4 bg-surface border border-borderSubtle rounded-container hover:border-accent/20 transition-colors"
          >
            <span className="flex items-center gap-3 text-sm text-textPrimary">
              <Icon className="w-4 h-4 text-accent" />
              {label}
            </span>
            <ChevronRight className="w-4 h-4 text-textMuted" />
          </button>
        ))}
      </div>
    </div>
  );
}
