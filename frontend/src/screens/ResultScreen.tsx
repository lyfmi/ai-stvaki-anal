import { useEffect, useState } from "react";
import { AlertCircle, ArrowLeft, RefreshCw } from "lucide-react";
import { AdvancedSection, AnalyticsCharts, LockedContent } from "../components/PremiumSection";
import { SecondaryButton } from "../components/ui/PrimaryButton";
import { resolveDisplayStatus } from "../utils/matchStatus";
import type { Lang, Translations } from "../i18n";

interface ResultScreenProps {
  analysisId: string;
  apiCall: (endpoint: string, options?: RequestInit) => Promise<any>;
  cached?: any;
  t: Translations;
  onBack: () => void;
  isUnlimited?: boolean;
  settings?: any;
  lang?: Lang;
  onRefreshStatus?: () => Promise<void>;
}

export function ResultScreen({
  analysisId,
  apiCall,
  cached,
  t,
  onBack,
  isUnlimited = false,
  settings,
  lang = "ru",
  onRefreshStatus,
}: ResultScreenProps) {
  const [data, setData] = useState<any>(cached ?? null);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [purchaseLoading, setPurchaseLoading] = useState(false);

  useEffect(() => {
    const onVisible = () => {
      if (document.visibilityState !== "visible") return;
      void onRefreshStatus?.().then(() =>
        apiCall(`/user/analyses/${analysisId}`)
          .then(setData)
          .catch(() => undefined)
      );
    };
    document.addEventListener("visibilitychange", onVisible);
    return () => document.removeEventListener("visibilitychange", onVisible);
  }, [onRefreshStatus, analysisId, apiCall]);

  useEffect(() => {
    if (!isUnlimited) return;
    apiCall(`/user/analyses/${analysisId}`)
      .then(setData)
      .catch(() => undefined);
  }, [isUnlimited, analysisId, apiCall]);

  useEffect(() => {
    setLoading(true);
    apiCall(`/user/analyses/${analysisId}`)
      .then(setData)
      .catch((e: Error) => setErrorMsg(e.message))
      .finally(() => setLoading(false));
  }, [analysisId, apiCall]);

  const handlePurchase = async () => {
    try {
      setPurchaseLoading(true);
      const order = await apiCall("/payments/unlimited/create", { method: "POST" });
      if (order.error) throw new Error(order.error);
      const url = order.webapp_payment_url || order.payment_url;
      if (!url) throw new Error("Payment link unavailable");
      window.Telegram?.WebApp?.openLink(url) ?? window.open(url, "_blank");
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setPurchaseLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[40vh] gap-3 screen-enter">
        <RefreshCw className="w-7 h-7 text-accent animate-spin" />
        <p className="text-textMuted text-xs">{t.loading}</p>
      </div>
    );
  }

  if (errorMsg && !data) {
    return (
      <div className="p-6 bg-surface border border-danger/20 rounded-containerLg text-center flex flex-col gap-3 screen-enter">
        <AlertCircle className="w-8 h-8 text-danger mx-auto" />
        <p className="text-xs text-textMuted">{errorMsg || "Not found"}</p>
        <SecondaryButton onClick={onBack}>{t.result_back}</SecondaryButton>
      </div>
    );
  }

  if (!data) return null;

  const {
    recommendation,
    coefficient,
    probability_percent,
    risk,
    confidence,
    arguments: argsList,
    explanation,
    match_status_label,
    match_datetime_msk,
    is_betting_recommendation,
    analysis_mode,
    premium_insights,
  } = data;

  const displayStatus = resolveDisplayStatus(
    analysis_mode,
    match_status_label,
    match_datetime_msk,
    lang
  );
  const isPostMatch = displayStatus.isPostMatch || is_betting_recommendation === false;
  const isLive = displayStatus.isLive;
  const showBettingStats = !isPostMatch;

  const riskClass =
    risk?.toLowerCase() === "low"
      ? "text-success border-success/30 bg-successMuted"
      : risk?.toLowerCase() === "high"
        ? "text-danger border-danger/30 bg-danger/5"
        : "text-textMuted border-borderSubtle bg-surfaceElevated";

  const price = settings?.unlimited_price_amount || "4900";
  const currency = (settings?.unlimited_price_currency || "rub").toUpperCase();
  const priceLabel = `${price} ${currency}`;

  const lockedProps = {
    t,
    isUnlimited,
    onBuyUnlimited: handlePurchase,
    purchaseLoading,
    priceLabel,
  };

  const hasPremiumContent =
    premium_insights ||
    (argsList?.length ?? 0) > 0 ||
    explanation ||
    (premium_insights?.advanced_arguments?.length ?? 0) > 0;

  const statusBadgeClass = isPostMatch
    ? "border-textMuted/30 bg-surfaceElevated text-textMuted"
    : isLive
      ? "border-success/30 bg-successMuted text-success"
      : "border-accent/30 bg-accent/10 text-accent";

  return (
    <div className="flex flex-col gap-5 screen-enter">
      <h2 className="text-lg font-semibold text-textPrimary">{t.result_title}</h2>

      {(match_status_label || match_datetime_msk) && (
        <div className="flex flex-wrap gap-2">
          {displayStatus.label && (
            <span
              className={`text-[10px] uppercase font-medium px-2.5 py-1 rounded-lg border ${statusBadgeClass}`}
            >
              {displayStatus.label}
            </span>
          )}
          {match_datetime_msk && (
            <span className="text-[10px] uppercase font-medium px-2.5 py-1 rounded-lg border border-borderSubtle bg-surfaceElevated text-textMuted">
              {t.result_match_time}: {match_datetime_msk}
            </span>
          )}
        </div>
      )}

      {/* FREE: prognosis + coef + probability only */}
      <div className="p-5 bg-surface border border-borderSubtle rounded-containerLg flex flex-col gap-4">
        <div>
          <span className="text-[10px] text-textMuted uppercase tracking-wider">
            {isPostMatch ? t.result_match_finished : t.result_bet}
          </span>
          <p className="text-xl font-semibold text-textPrimary mt-1">{recommendation || "—"}</p>
        </div>

        {showBettingStats && (
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 bg-surfaceElevated rounded-xl">
              <span className="text-[10px] text-textMuted">{t.result_coef}</span>
              <p className="text-lg font-semibold text-accent mt-0.5">
                {coefficient != null ? `x${coefficient}` : "—"}
              </p>
            </div>
            <div className="p-3 bg-surfaceElevated rounded-xl">
              <span className="text-[10px] text-textMuted">{t.result_probability}</span>
              <p className="text-lg font-semibold text-success mt-0.5">
                {probability_percent != null ? `${probability_percent}%` : "—"}
              </p>
            </div>
          </div>
        )}

        {isUnlimited && (
          <div className="flex gap-2">
            <span className={`flex-1 py-2 px-3 rounded-xl border text-center text-[10px] uppercase font-medium ${riskClass}`}>
              {t.result_risk}: {risk || "—"}
            </span>
            <span className="flex-1 py-2 px-3 rounded-xl border border-borderSubtle bg-surfaceElevated text-center text-[10px] uppercase text-textMuted">
              {t.result_confidence}: {confidence || "—"}
            </span>
          </div>
        )}
      </div>

      {hasPremiumContent &&
        (isUnlimited ? (
          <div className="flex flex-col gap-4">
            <AnalyticsCharts t={t} premium={premium_insights} />
            {(argsList?.length > 0 || explanation) && (
              <div className="p-4 bg-surface border border-borderSubtle rounded-containerLg">
                {argsList?.length > 0 && (
                  <ul className="flex flex-col gap-2 m-0 p-0 list-none mb-3">
                    <span className="text-[10px] text-textMuted uppercase">{t.result_args}</span>
                    {argsList.map((arg: string, i: number) => (
                      <li key={i} className="text-xs text-textPrimary/90 flex gap-2">
                        <span className="text-accent">·</span>
                        {arg}
                      </li>
                    ))}
                  </ul>
                )}
                {explanation && (
                  <p className="text-xs text-textMuted leading-relaxed border-t border-borderSubtle pt-3">
                    {explanation}
                  </p>
                )}
              </div>
            )}
            <AdvancedSection
              t={t}
              items={premium_insights?.advanced_arguments}
              isUnlimited
              onBuyUnlimited={handlePurchase}
              purchaseLoading={purchaseLoading}
              priceLabel={priceLabel}
            />
          </div>
        ) : (
          <LockedContent {...lockedProps} title={t.premium_locked_title} desc={t.premium_locked_desc}>
            <AnalyticsCharts t={t} premium={premium_insights} embedded />

            {argsList?.length > 0 && (
              <ul className="flex flex-col gap-2 m-0 p-0 list-none mb-3 mt-4">
                <span className="text-[10px] text-textMuted uppercase">{t.result_args}</span>
                {argsList.map((arg: string, i: number) => (
                  <li key={i} className="text-xs text-textPrimary/90 flex gap-2">
                    <span className="text-accent">·</span>
                    {arg}
                  </li>
                ))}
              </ul>
            )}

            {explanation && (
              <p className="text-xs text-textMuted leading-relaxed border-t border-borderSubtle pt-3">
                {explanation}
              </p>
            )}

            {premium_insights?.advanced_arguments?.length > 0 && (
              <ul className="flex flex-col gap-1.5 m-0 p-0 list-none mt-3 border-t border-borderSubtle pt-3">
                <span className="text-[10px] text-textMuted uppercase">{t.result_advanced}</span>
                {premium_insights.advanced_arguments.map((item: string, i: number) => (
                  <li key={i} className="text-xs text-textPrimary/90 flex gap-2">
                    <span className="text-accent">+</span>
                    {item}
                  </li>
                ))}
              </ul>
            )}
          </LockedContent>
        ))}

      {errorMsg && <p className="text-xs text-danger text-center">{errorMsg}</p>}

      <SecondaryButton onClick={onBack} className="flex items-center justify-center gap-2">
        <ArrowLeft className="w-4 h-4" /> {t.result_back}
      </SecondaryButton>

      <p className="text-[10px] text-textMuted text-center leading-relaxed">{t.result_disclaimer}</p>
    </div>
  );
}
