import { useState } from "react";
import { AlertCircle, Crown, Zap } from "lucide-react";
import { PrimaryButton } from "../components/ui/PrimaryButton";
import type { Translations } from "../i18n";

interface UnlimitedScreenProps {
  user: any;
  settings: any;
  apiCall: (endpoint: string, options?: RequestInit) => Promise<any>;
  t: Translations;
}

export function UnlimitedScreen({ user, settings, apiCall, t }: UnlimitedScreenProps) {
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const price = settings?.unlimited_price_amount || "4900";
  const currency = (settings?.unlimited_price_currency || "rub").toUpperCase();
  const isUnlimited = user?.has_unlimited || user?.funnel_state === "UNLIMITED";

  const handlePurchase = async () => {
    try {
      setLoading(true);
      setErrorMsg(null);
      const order = await apiCall("/payments/unlimited/create", { method: "POST" });
      if (order.error) throw new Error(order.error);
      const url = order.webapp_payment_url || order.payment_url;
      if (!url) throw new Error("Payment link unavailable");
      window.Telegram?.WebApp?.openLink(url) ?? window.open(url, "_blank");
    } catch (e: any) {
      setErrorMsg(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-5 screen-enter">
      <h2 className="text-lg font-semibold text-textPrimary">{t.unlimited_title}</h2>

      {errorMsg && (
        <div className="p-3 bg-danger/10 border border-danger/20 text-danger text-xs rounded-container flex gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {errorMsg}
        </div>
      )}

      <div className="p-5 bg-surface border border-borderSubtle rounded-containerLg flex flex-col gap-4">
        <Crown className="w-8 h-8 text-accent" />
        <p className="text-xs text-textMuted leading-relaxed">{t.unlimited_desc}</p>

        {isUnlimited ? (
          <p className="text-sm text-accent font-medium text-center py-3">{t.unlimited_already}</p>
        ) : (
          <>
            <div className="flex justify-between text-sm">
              <span className="text-textMuted">{t.unlimited_price}</span>
              <span className="font-semibold text-accent">
                {price} {currency}
              </span>
            </div>
            <PrimaryButton onClick={handlePurchase} loading={loading}>
              <Zap className="w-4 h-4" /> {t.unlimited_pay_btn}
            </PrimaryButton>
          </>
        )}
      </div>
    </div>
  );
}
