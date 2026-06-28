import type { Translations } from "../i18n";

interface FormBar {
  team: string;
  wins: number;
  draws: number;
  losses: number;
}

interface KeyStat {
  label: string;
  home: string;
  away: string;
}

interface PremiumInsights {
  form_bars?: FormBar[];
  h2h?: string;
  key_stats?: KeyStat[];
  trends?: string[];
  advanced_arguments?: string[];
}

interface PremiumSectionProps {
  t: Translations;
  premium: PremiumInsights | null | undefined;
  isUnlimited: boolean;
  onBuyUnlimited?: () => void;
  purchaseLoading?: boolean;
  priceLabel?: string;
}

function FormBarChart({ bar }: { bar: FormBar }) {
  const total = Math.max(bar.wins + bar.draws + bar.losses, 1);
  const segments = [
    { n: bar.wins, cls: "bg-accent" },
    { n: bar.draws, cls: "bg-textMuted/50" },
    { n: bar.losses, cls: "bg-danger/70" },
  ];
  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-xs text-textPrimary font-medium truncate">{bar.team}</span>
      <div className="flex h-2 rounded-full overflow-hidden bg-surfaceElevated">
        {segments.map((s, i) =>
          s.n > 0 ? (
            <div key={i} className={s.cls} style={{ width: `${(s.n / total) * 100}%` }} />
          ) : null
        )}
      </div>
      <span className="text-[10px] text-textMuted">
        W{bar.wins} · D{bar.draws} · L{bar.losses}
      </span>
    </div>
  );
}

export function PremiumSection({
  t,
  premium,
  isUnlimited,
  onBuyUnlimited,
  purchaseLoading,
  priceLabel,
}: PremiumSectionProps) {
  if (!premium) return null;

  const hasContent =
    (premium.form_bars?.length ?? 0) > 0 ||
    premium.h2h ||
    (premium.key_stats?.length ?? 0) > 0 ||
    (premium.trends?.length ?? 0) > 0 ||
    (premium.advanced_arguments?.length ?? 0) > 0;

  if (!hasContent) return null;

  const body = (
    <div className="flex flex-col gap-4">
      <span className="text-[10px] text-accent uppercase tracking-wider font-semibold">
        {t.result_premium_title}
      </span>

      {premium.form_bars && premium.form_bars.length > 0 && (
        <div className="flex flex-col gap-3">
          <span className="text-[10px] text-textMuted uppercase">{t.result_form}</span>
          {premium.form_bars.map((bar, i) => (
            <FormBarChart key={i} bar={bar} />
          ))}
        </div>
      )}

      {premium.h2h && (
        <div>
          <span className="text-[10px] text-textMuted uppercase">{t.result_h2h}</span>
          <p className="text-xs text-textPrimary/90 mt-1 leading-relaxed">{premium.h2h}</p>
        </div>
      )}

      {premium.key_stats && premium.key_stats.length > 0 && (
        <div className="flex flex-col gap-2">
          <span className="text-[10px] text-textMuted uppercase">{t.result_key_stats}</span>
          {premium.key_stats.map((stat, i) => (
            <div key={i} className="grid grid-cols-3 gap-2 text-xs p-2 bg-surfaceElevated rounded-lg">
              <span className="text-textMuted truncate">{stat.label}</span>
              <span className="text-center font-medium text-textPrimary">{stat.home}</span>
              <span className="text-center font-medium text-textPrimary">{stat.away}</span>
            </div>
          ))}
        </div>
      )}

      {premium.trends && premium.trends.length > 0 && (
        <ul className="flex flex-col gap-1.5 m-0 p-0 list-none">
          <span className="text-[10px] text-textMuted uppercase">{t.result_trends}</span>
          {premium.trends.map((item, i) => (
            <li key={i} className="text-xs text-textPrimary/90 flex gap-2">
              <span className="text-accent">→</span>
              {item}
            </li>
          ))}
        </ul>
      )}

      {premium.advanced_arguments && premium.advanced_arguments.length > 0 && (
        <ul className="flex flex-col gap-1.5 m-0 p-0 list-none">
          <span className="text-[10px] text-textMuted uppercase">{t.result_advanced}</span>
          {premium.advanced_arguments.map((item, i) => (
            <li key={i} className="text-xs text-textPrimary/90 flex gap-2">
              <span className="text-accent">+</span>
              {item}
            </li>
          ))}
        </ul>
      )}
    </div>
  );

  if (isUnlimited) {
    return (
      <div className="p-4 bg-surface border border-accent/20 rounded-containerLg">{body}</div>
    );
  }

  return (
    <div className="relative rounded-containerLg overflow-hidden border border-borderSubtle">
      <div className="p-4 blur-md select-none pointer-events-none opacity-80">{body}</div>
      <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 p-4 bg-appBg/60 backdrop-blur-sm">
        <p className="text-sm font-semibold text-textPrimary text-center">{t.premium_locked_title}</p>
        <p className="text-xs text-textMuted text-center leading-relaxed">{t.premium_locked_desc}</p>
        {onBuyUnlimited && (
          <button
            type="button"
            onClick={onBuyUnlimited}
            disabled={purchaseLoading}
            className="magnetic-btn bg-accent text-white text-xs font-semibold px-5 py-2.5 rounded-xl"
          >
            {purchaseLoading ? t.loading : `${t.premium_locked_cta}${priceLabel ? ` · ${priceLabel}` : ""}`}
          </button>
        )}
      </div>
    </div>
  );
}
