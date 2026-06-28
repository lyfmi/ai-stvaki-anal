import { useEffect, useRef, useState } from "react";
import { AlertCircle, Crown, Upload, Zap } from "lucide-react";
import { gsap } from "gsap";
import { analyzeScreenshot } from "../api";
import { ScreenHeader } from "../components/layout/ScreenHeader";
import { PrimaryButton } from "../components/ui/PrimaryButton";
import { ProcessingOverlay } from "../components/ui/ProcessingOverlay";
import { StepPills } from "../components/ui/StepPill";
import type { Translations } from "../i18n";

interface HomeScreenProps {
  t: Translations;
  token: string | null;
  hasFullAccess: boolean;
  statusInfo: any;
  settings: any;
  apiCall: (endpoint: string, options?: RequestInit) => Promise<any>;
  onResult: (analysisId: string) => void;
  onRefreshStatus: () => Promise<void>;
}

export function HomeScreen({
  t,
  token,
  hasFullAccess,
  statusInfo,
  settings,
  apiCall,
  onResult,
  onRefreshStatus,
}: HomeScreenProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStep, setUploadStep] = useState<1 | 2 | 3>(1);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [purchaseLoading, setPurchaseLoading] = useState(false);

  const isUnlimited =
    statusInfo?.user?.has_unlimited || statusInfo?.user?.funnel_state === "UNLIMITED";
  const remaining = statusInfo?.attempts_remaining ?? 0;
  const dailyLimit = statusInfo?.daily_limit ?? 10;
  const limitReached = hasFullAccess && !isUnlimited && remaining <= 0;
  const canAnalyze = hasFullAccess && statusInfo?.can_analyze && !limitReached;

  useEffect(() => {
    if (hasFullAccess) {
      void onRefreshStatus();
    }
  }, [hasFullAccess, onRefreshStatus]);

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.from(".home-fade", {
        y: 16,
        opacity: 0,
        stagger: 0.06,
        duration: 0.5,
        ease: "power3.out",
      });
    }, containerRef);
    return () => ctx.revert();
  }, []);

  const handleFileChange = (file: File) => {
    setErrorMsg(null);
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
  };

  const handlePurchase = async () => {
    try {
      setPurchaseLoading(true);
      setErrorMsg(null);
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

  const handleSubmit = async () => {
    if (!selectedFile || !canAnalyze) return;

    setIsUploading(true);
    setUploadStep(1);
    setErrorMsg(null);

    const visionTimer = setTimeout(() => setUploadStep(2), 4500);
    const searchTimer = setTimeout(() => setUploadStep(3), 9000);

    try {
      const data = await analyzeScreenshot(token, selectedFile);
      clearTimeout(visionTimer);
      clearTimeout(searchTimer);
      await onRefreshStatus();
      window.Telegram?.WebApp?.HapticFeedback.notificationOccurred("success");
      onResult(data.id);
    } catch (err: any) {
      clearTimeout(visionTimer);
      clearTimeout(searchTimer);
      setErrorMsg(err.message || "Analysis failed");
      setIsUploading(false);
      window.Telegram?.WebApp?.HapticFeedback.notificationOccurred("error");
    }
  };

  const handleCloseBot = () => window.Telegram?.WebApp?.close();

  const price = settings?.unlimited_price_amount || "4900";
  const currency = (settings?.unlimited_price_currency || "rub").toUpperCase();

  return (
    <div ref={containerRef} className="flex flex-col gap-5">
      <div className="home-fade">
        <ScreenHeader t={t} />
      </div>

      {!hasFullAccess && (
        <div className="home-fade p-4 rounded-container border border-borderSubtle bg-surface flex flex-col gap-3">
          <p className="text-sm font-medium text-textPrimary">{t.funnel_locked_title}</p>
          <p className="text-xs text-textMuted leading-relaxed">{t.funnel_locked_desc}</p>
          <button
            type="button"
            onClick={handleCloseBot}
            className="text-xs text-accent font-medium text-left"
          >
            {t.funnel_locked_bot}
          </button>
        </div>
      )}

      {limitReached && (
        <div className="home-fade p-4 rounded-container border border-accent/30 bg-accent/10 flex flex-col gap-3">
          <div className="flex items-start gap-2">
            <Crown className="w-5 h-5 text-accent shrink-0 mt-0.5" />
            <div className="flex flex-col gap-1">
              <p className="text-sm font-semibold text-accent">{t.home_limit_exceeded}</p>
              <p className="text-xs text-textMuted leading-relaxed">{t.home_limit_exceeded_desc}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={handlePurchase}
            disabled={purchaseLoading}
            className="magnetic-btn w-full bg-accent text-appBg font-semibold py-3 rounded-xl flex items-center justify-center gap-2 text-sm"
          >
            {purchaseLoading ? (
              t.loading
            ) : (
              <>
                <Zap className="w-4 h-4" />
                {t.home_limit_buy} · {price} {currency}
              </>
            )}
          </button>
        </div>
      )}

      {errorMsg && (
        <div className="home-fade p-3 bg-danger/10 border border-danger/20 text-danger text-xs rounded-container flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <p>{errorMsg}</p>
        </div>
      )}

      {isUploading ? (
        <div className="home-fade">
          <ProcessingOverlay step={uploadStep} t={t} />
          <div className="mt-6">
            <StepPills t={t} activeStep={uploadStep} />
          </div>
        </div>
      ) : (
        <>
          <div
            className={`home-fade border border-dashed rounded-containerLg p-6 flex flex-col items-center justify-center min-h-[220px] gap-4 transition-all duration-300 ${
              !hasFullAccess || limitReached
                ? "opacity-40 pointer-events-none border-borderSubtle bg-surface"
                : isDragging
                  ? "border-accent bg-accent/5"
                  : previewUrl
                    ? "border-borderSubtle bg-surface"
                    : "border-borderSubtle bg-surface hover:border-accent/30"
            }`}
            onDragOver={(e) => {
              e.preventDefault();
              if (hasFullAccess && !limitReached) setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setIsDragging(false);
              if (e.dataTransfer.files[0]) handleFileChange(e.dataTransfer.files[0]);
            }}
          >
            {previewUrl ? (
              <img src={previewUrl} alt="" className="max-h-44 w-full object-contain rounded-lg" />
            ) : (
              <>
                <Upload className="w-8 h-8 text-textMuted" />
                <p className="text-sm text-textMuted text-center">{t.home_upload_hint}</p>
              </>
            )}

            {hasFullAccess && !limitReached && (
              <label className="magnetic-btn text-xs font-medium px-4 py-2.5 rounded-xl border border-borderSubtle bg-surfaceElevated cursor-pointer">
                {t.home_upload_select}
                <input
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={(e) => e.target.files?.[0] && handleFileChange(e.target.files[0])}
                />
              </label>
            )}
          </div>

          <div className="home-fade">
            <PrimaryButton
              onClick={handleSubmit}
              disabled={!selectedFile || !canAnalyze}
              loading={false}
            >
              {t.home_analyze}
            </PrimaryButton>
          </div>

          {!limitReached && (
            <p className="home-fade text-center text-xs text-textMuted">
              {isUnlimited
                ? t.home_unlimited
                : `${remaining} / ${dailyLimit} ${t.home_requests}`}
            </p>
          )}

          <div className="home-fade pt-2">
            <StepPills t={t} />
          </div>

          <p className="home-fade text-center text-[11px] text-textMuted/80 pb-2">{t.home_trust}</p>
        </>
      )}
    </div>
  );
}
