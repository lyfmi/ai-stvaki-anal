import type { ReactNode } from "react";
import { Crown, Zap } from "lucide-react";
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

export interface PremiumInsights {
  form_bars?: FormBar[];
  h2h?: string;
  key_stats?: KeyStat[];
  trends?: string[];
  advanced_arguments?: string[];
}

function FormBarChart({ bar }: { bar: FormBar }) {
  const total = Math.max(bar.wins + bar.draws + bar.losses, 1);
  const segments = [
    { n: bar.wins, cls: "bg-success" },
    { n: bar.draws, cls: "bg-textMuted/50" },
    { n: bar.losses, cls: "bg-danger/70" },
  ];
  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-xs text-textPrimary font-medium truncate">{bar.team}</span>
      <div className="flex h-2.5 rounded-full overflow-hidden bg-surfaceElevated">
        {segments.map((s, i) =>
          s.n > 0 ? (
            <div key={i} className={s.cls} style={{ width: `${(s.n / total) * 100}%` }} />
          ) : null
        )}
      </div>
      <div className="flex gap-3 text-[10px]">
        <span className="text-success">W{bar.wins}</span>
        <span className="text-textMuted">D{bar.draws}</span>
        <span className="text-danger/80">L{bar.losses}</span>
      </div>
    </div>
  );
}

function StatCompareBar({ label, home, away }: KeyStat) {
  const h = parseFloat(home) || 0;
  const a = parseFloat(away) || 0;
  const total = Math.max(h + a, 0.01);
  return (
    <div className="flex flex-col gap-1.5 p-3 bg-surfaceElevated rounded-xl">
      <span className="text-[10px] text-textMuted uppercase">{label}</span>
      <div className="flex justify-between text-xs font-semibold">
        <span className="text-success">{home}</span>
        <span className="text-accent">{away}</span>
      </div>
      <div className="flex h-2 rounded-full overflow-hidden gap-0.5">
        <div className="bg-success/80 rounded-l-full" style={{ width: `${(h / total) * 100}%` }} />
        <div className="bg-accent/80 rounded-r-full" style={{ width: `${(a / total) * 100}%` }} />
      </div>
    </div>
  );
}

interface AnalyticsChartsProps {
  t: Translations;
  premium: PremiumInsights | null | undefined;
  embedded?: boolean;
}

/** Charts and stats — shown inside LockedContent on free tier */
export function AnalyticsCharts({ t, premium, embedded = false }: AnalyticsChartsProps) {
  if (!premium) return null;
  const hasCharts =
    (premium.form_bars?.length ?? 0) > 0 ||
    (premium.key_stats?.length ?? 0) > 0 ||
    (premium.trends?.length ?? 0) > 0 ||
    premium.h2h;

  if (!hasCharts) return null;

  const inner = (
    <>
      {!embedded && (
        <span className="text-[10px] text-success uppercase tracking-wider font-semibold">
          {t.result_analytics_title}
        </span>
      )}

      {embedded && (
        <span className="text-[10px] text-success uppercase tracking-wider font-semibold block mb-3">
          {t.result_analytics_title}
        </span>
      )}

      {premium.form_bars && premium.form_bars.length > 0 && (
        <div className="flex flex-col gap-3">
          <span className="text-[10px] text-textMuted uppercase">{t.result_form}</span>
          {premium.form_bars.map((bar, i) => (
            <FormBarChart key={i} bar={bar} />
          ))}
        </div>
      )}

      {premium.key_stats && premium.key_stats.length > 0 && (
        <div className="grid grid-cols-1 gap-2">
          <span className="text-[10px] text-textMuted uppercase">{t.result_key_stats}</span>
          {premium.key_stats.map((stat, i) => (
            <StatCompareBar key={i} {...stat} />
          ))}
        </div>
      )}

      {premium.h2h && (
        <div className="p-3 rounded-xl bg-successMuted border border-success/20">
          <span className="text-[10px] text-success uppercase">{t.result_h2h}</span>
          <p className="text-xs text-textPrimary/90 mt-1 leading-relaxed">{premium.h2h}</p>
        </div>
      )}

      {premium.trends && premium.trends.length > 0 && (
        <ul className="flex flex-col gap-1.5 m-0 p-0 list-none">
          <span className="text-[10px] text-textMuted uppercase">{t.result_trends}</span>
          {premium.trends.map((item, i) => (
            <li key={i} className="text-xs text-textPrimary/90 flex gap-2 items-start">
              <span className="text-success shrink-0">▲</span>
              {item}
            </li>
          ))}
        </ul>
      )}
    </>
  );

  if (embedded) return <div className="flex flex-col gap-4">{inner}</div>;

  return (
    <div className="p-4 bg-surface border border-success/20 rounded-containerLg flex flex-col gap-4">
      {inner}
    </div>
  );
}

interface LockedContentProps {
  t: Translations;
  children: ReactNode;
  isUnlimited: boolean;
  onBuyUnlimited?: () => void;
  purchaseLoading?: boolean;
  priceLabel?: string;
  title?: string;
  desc?: string;
}

export function LockedContent({
  t,
  children,
  isUnlimited,
  onBuyUnlimited,
  purchaseLoading,
  priceLabel,
  title,
  desc,
}: LockedContentProps) {
  if (isUnlimited) {
    return <div className="p-4 bg-surface border border-borderSubtle rounded-containerLg">{children}</div>;
  }

  return (
    <div className="relative rounded-containerLg overflow-hidden border border-borderSubtle">
      <div className="p-4 blur-md select-none pointer-events-none opacity-90">{children}</div>
      <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 p-4 bg-appBg/70 backdrop-blur-sm">
        <Crown className="w-6 h-6 text-accent" />
        <p className="text-sm font-semibold text-textPrimary text-center">
          {title || t.premium_locked_args_title}
        </p>
        <p className="text-xs text-textMuted text-center leading-relaxed">
          {desc || t.premium_locked_args_desc}
        </p>
        {onBuyUnlimited && (
          <button
            type="button"
            onClick={onBuyUnlimited}
            disabled={purchaseLoading}
            className="magnetic-btn bg-accent text-white text-xs font-semibold px-5 py-2.5 rounded-xl flex items-center gap-2"
          >
            <Zap className="w-3.5 h-3.5" />
            {purchaseLoading ? t.loading : `${t.premium_locked_cta}${priceLabel ? ` · ${priceLabel}` : ""}`}
          </button>
        )}
      </div>
    </div>
  );
}

interface AdvancedSectionProps {
  t: Translations;
  items: string[] | undefined;
  isUnlimited: boolean;
  onBuyUnlimited?: () => void;
  purchaseLoading?: boolean;
  priceLabel?: string;
}

export function AdvancedSection({
  t,
  items,
  isUnlimited,
  onBuyUnlimited,
  purchaseLoading,
  priceLabel,
}: AdvancedSectionProps) {
  if (!items?.length) return null;

  const body = (
    <ul className="flex flex-col gap-1.5 m-0 p-0 list-none">
      <span className="text-[10px] text-textMuted uppercase">{t.result_advanced}</span>
      {items.map((item, i) => (
        <li key={i} className="text-xs text-textPrimary/90 flex gap-2">
          <span className="text-accent">+</span>
          {item}
        </li>
      ))}
    </ul>
  );

  if (isUnlimited) {
    return (
      <div className="p-4 bg-surface border border-accent/20 rounded-containerLg">{body}</div>
    );
  }

  return (
    <LockedContent
      t={t}
      isUnlimited={false}
      onBuyUnlimited={onBuyUnlimited}
      purchaseLoading={purchaseLoading}
      priceLabel={priceLabel}
    >
      {body}
    </LockedContent>
  );
}
