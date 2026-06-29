import { useEffect, useRef, useState } from "react";
import { AlertCircle, Crown, Upload, Zap } from "lucide-react";
import { gsap } from "gsap";
import { analyzeScreenshot } from "../api";
import { MatchOfDayCard } from "../components/MatchOfDayCard";
import { ImageCropper } from "../components/ImageCropper";
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
  onAnalysisComplete: (data: any) => void;
  onRefreshStatus: () => Promise<void>;
}

export function HomeScreen({
  t,
  token,
  hasFullAccess,
  statusInfo,
  settings,
  apiCall,
  onAnalysisComplete,
  onRefreshStatus,
}: HomeScreenProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [matchPredicting, setMatchPredicting] = useState(false);
  const [processStep, setProcessStep] = useState<1 | 2 | 3>(1);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [purchaseLoading, setPurchaseLoading] = useState(false);
  const [cropFile, setCropFile] = useState<File | null>(null);

  const statusReady = Boolean(statusInfo);
  const isUnlimited =
    statusInfo?.user?.has_unlimited || statusInfo?.user?.funnel_state === "UNLIMITED";
  const remaining = statusInfo?.attempts_remaining ?? 0;
  const dailyLimit = statusInfo?.daily_limit ?? 10;
  const limitReached = statusReady && hasFullAccess && !isUnlimited && remaining <= 0;
  const canAnalyze = statusReady && hasFullAccess && Boolean(statusInfo?.can_analyze) && !limitReached;
  const uploadDisabled = !hasFullAccess || limitReached;

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
        clearProps: "opacity,transform",
      });
    }, containerRef);
    return () => ctx.revert();
  }, []);

  const handleFileSelected = (file: File) => {
    setErrorMsg(null);
    setCropFile(file);
  };

  const handleCropConfirm = (cropped: File) => {
    setCropFile(null);
    setSelectedFile(cropped);
    setPreviewUrl(URL.createObjectURL(cropped));
    void runAnalysis(cropped);
  };

  const runAnalysis = async (file: File) => {
    if (!canAnalyze) return;

    setIsProcessing(true);
    setProcessStep(1);
    setErrorMsg(null);

    const visionTimer = setTimeout(() => setProcessStep(2), 4500);
    const searchTimer = setTimeout(() => setProcessStep(3), 9000);

    try {
      const data = await analyzeScreenshot(token, file);
      clearTimeout(visionTimer);
      clearTimeout(searchTimer);
      await onRefreshStatus();
      setIsProcessing(false);
      window.Telegram?.WebApp?.HapticFeedback.notificationOccurred("success");
      onAnalysisComplete(data);
    } catch (err: any) {
      clearTimeout(visionTimer);
      clearTimeout(searchTimer);
      setErrorMsg(err.message || "Analysis failed");
      setIsProcessing(false);
      window.Telegram?.WebApp?.HapticFeedback.notificationOccurred("error");
    }
  };

  const handleSubmit = async () => {
    if (!selectedFile || !canAnalyze) return;
    await runAnalysis(selectedFile);
  };

  const handleCropCancel = () => {
    setCropFile(null);
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

  const handleMatchPredict = () => {
    if (!canAnalyze) return;
    setMatchPredicting(true);
    setIsProcessing(true);
    setProcessStep(2);
    setErrorMsg(null);
    const searchTimer = setTimeout(() => setProcessStep(3), 5000);

    void apiCall("/user/match-of-day/predict", { method: "POST" })
      .then(async (data) => {
        clearTimeout(searchTimer);
        if (!data?.id) throw new Error("Не удалось получить результат анализа");
        await onRefreshStatus();
        setIsProcessing(false);
        setMatchPredicting(false);
        window.Telegram?.WebApp?.HapticFeedback.notificationOccurred("success");
        onAnalysisComplete(data);
      })
      .catch((err: any) => {
        clearTimeout(searchTimer);
        setErrorMsg(err.message || "Ошибка анализа матча");
        setIsProcessing(false);
        setMatchPredicting(false);
        window.Telegram?.WebApp?.HapticFeedback.notificationOccurred("error");
      });
  };

  const handleCloseBot = () => window.Telegram?.WebApp?.close();

  const price = settings?.unlimited_price_amount || "4900";
  const currency = (settings?.unlimited_price_currency || "rub").toUpperCase();

  return (
    <div ref={containerRef} className="flex flex-col gap-5">
      {cropFile && (
        <ImageCropper
          file={cropFile}
          t={t}
          onConfirm={handleCropConfirm}
          onCancel={handleCropCancel}
        />
      )}

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
            className="magnetic-btn w-full bg-accent text-white font-semibold py-3 rounded-xl flex items-center justify-center gap-2 text-sm"
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

      {!isProcessing && (
        <MatchOfDayCard
          t={t}
          apiCall={apiCall}
          canAnalyze={canAnalyze}
          hasFullAccess={hasFullAccess}
          onPredict={handleMatchPredict}
          predicting={matchPredicting}
        />
      )}

      {isProcessing ? (
        <div className="home-fade flex flex-col gap-6 py-4">
          <ProcessingOverlay step={processStep} t={t} />
          <StepPills t={t} activeStep={processStep} />
        </div>
      ) : (
        <>
          <div
            className={`home-fade border border-dashed rounded-containerLg p-6 flex flex-col items-center justify-center min-h-[220px] gap-4 transition-colors duration-300 ${
              !hasFullAccess
                ? "opacity-40 pointer-events-none border-borderSubtle bg-surface"
                : uploadDisabled
                  ? "pointer-events-none border-borderSubtle bg-surface opacity-100"
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
              if (e.dataTransfer.files[0]) handleFileSelected(e.dataTransfer.files[0]);
            }}
          >
            {previewUrl ? (
              <div className="relative w-full">
                <img src={previewUrl} alt="" className="max-h-44 w-full object-contain rounded-lg" />
                {hasFullAccess && !limitReached && (
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedFile(null);
                      setPreviewUrl(null);
                    }}
                    className="mt-2 text-[10px] text-accent font-medium"
                  >
                    {t.crop_change_photo}
                  </button>
                )}
              </div>
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
                  onChange={(e) => e.target.files?.[0] && handleFileSelected(e.target.files[0])}
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
