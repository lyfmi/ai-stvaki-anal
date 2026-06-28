import { useEffect, useRef, useState } from "react";
import { AlertCircle, Upload } from "lucide-react";
import { gsap } from "gsap";
import { analyzeScreenshot } from "../api";
import { ScreenHeader } from "../components/layout/ScreenHeader";
import { CameraCapture } from "../components/ui/CameraCapture";
import { PrimaryButton } from "../components/ui/PrimaryButton";
import { ProcessingOverlay } from "../components/ui/ProcessingOverlay";
import { StepPills } from "../components/ui/StepPill";
import type { Translations } from "../i18n";

interface HomeScreenProps {
  t: Translations;
  token: string | null;
  hasFullAccess: boolean;
  statusInfo: any;
  onResult: (analysisId: string) => void;
}

export function HomeScreen({ t, token, hasFullAccess, statusInfo, onResult }: HomeScreenProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStep, setUploadStep] = useState<1 | 2 | 3>(1);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const isUnlimited =
    statusInfo?.user?.has_unlimited || statusInfo?.user?.funnel_state === "UNLIMITED";
  const remaining = statusInfo?.attempts_remaining ?? 0;
  const dailyLimit = statusInfo?.daily_limit ?? 10;
  const canAnalyze = hasFullAccess && statusInfo?.can_analyze;

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
              !hasFullAccess
                ? "opacity-40 pointer-events-none border-borderSubtle bg-surface"
                : isDragging
                  ? "border-accent bg-accent/5"
                  : previewUrl
                    ? "border-borderSubtle bg-surface"
                    : "border-borderSubtle bg-surface hover:border-accent/30"
            }`}
            onDragOver={(e) => {
              e.preventDefault();
              if (hasFullAccess) setIsDragging(true);
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

            {hasFullAccess && (
              <div className="flex gap-2">
                <label className="magnetic-btn text-xs font-medium px-4 py-2.5 rounded-xl border border-borderSubtle bg-surfaceElevated cursor-pointer">
                  {t.home_upload_select}
                  <input
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={(e) => e.target.files?.[0] && handleFileChange(e.target.files[0])}
                  />
                </label>
                <CameraCapture
                  t={t}
                  disabled={!hasFullAccess}
                  onCapture={handleFileChange}
                />
              </div>
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

          <p className="home-fade text-center text-xs text-textMuted">
            {isUnlimited
              ? t.home_unlimited
              : `${remaining} / ${dailyLimit} ${t.home_requests}`}
          </p>

          <div className="home-fade pt-2">
            <StepPills t={t} />
          </div>

          <p className="home-fade text-center text-[11px] text-textMuted/80 pb-2">{t.home_trust}</p>
        </>
      )}
    </div>
  );
}
