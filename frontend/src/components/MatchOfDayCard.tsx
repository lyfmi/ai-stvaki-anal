import { useEffect, useState } from "react";
import { Calendar, Sparkles, Trophy } from "lucide-react";
import { ProcessingOverlay } from "./ui/ProcessingOverlay";
import type { Translations } from "../i18n";

interface MatchOfDayCardProps {
  t: Translations;
  apiCall: (endpoint: string, options?: RequestInit) => Promise<any>;
  canAnalyze: boolean;
  hasFullAccess: boolean;
  onResult: (analysisId: string) => void;
  onRefreshStatus: () => Promise<void>;
}

export function MatchOfDayCard({
  t,
  apiCall,
  canAnalyze,
  hasFullAccess,
  onResult,
  onRefreshStatus,
}: MatchOfDayCardProps) {
  const [match, setMatch] = useState<any>(null);
  const [loadingMatch, setLoadingMatch] = useState(true);
  const [predicting, setPredicting] = useState(false);
  const [predictStep, setPredictStep] = useState<1 | 2 | 3>(2);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!hasFullAccess) {
      setLoadingMatch(false);
      return;
    }
    apiCall("/user/match-of-day")
      .then(setMatch)
      .catch(() => setMatch(null))
      .finally(() => setLoadingMatch(false));
  }, [apiCall, hasFullAccess]);

  const handlePredict = async () => {
    if (!canAnalyze) return;
    setPredicting(true);
    setPredictStep(2);
    setErrorMsg(null);
    const searchTimer = setTimeout(() => setPredictStep(3), 5000);
    try {
      const data = await apiCall("/user/match-of-day/predict", { method: "POST" });
      clearTimeout(searchTimer);
      await onRefreshStatus();
      window.Telegram?.WebApp?.HapticFeedback.notificationOccurred("success");
      onResult(data.id);
    } catch (err: any) {
      clearTimeout(searchTimer);
      setErrorMsg(err.message || "Failed");
      setPredicting(false);
      window.Telegram?.WebApp?.HapticFeedback.notificationOccurred("error");
    }
  };

  if (!hasFullAccess || loadingMatch) return null;
  if (!match) return null;

  if (predicting) {
    return (
      <div className="home-fade">
        <ProcessingOverlay step={predictStep} t={t} />
      </div>
    );
  }

  return (
    <div className="home-fade p-4 rounded-containerLg border border-accent/20 bg-gradient-to-br from-surface to-accent/5 flex flex-col gap-3">
      <div className="flex items-center gap-2">
        <Sparkles className="w-4 h-4 text-accent" />
        <span className="text-[10px] uppercase tracking-wider text-accent font-semibold">{t.match_of_day}</span>
      </div>

      <div className="flex items-center justify-between gap-3">
        <div className="flex-1 min-w-0">
          <p className="text-[10px] text-textMuted uppercase">{match.league}</p>
          <p className="text-base font-semibold text-textPrimary mt-0.5 truncate">
            {match.home_team} — {match.away_team}
          </p>
        </div>
        <Trophy className="w-8 h-8 text-accent/40 shrink-0" />
      </div>

      <div className="flex items-center gap-1.5 text-xs text-textMuted">
        <Calendar className="w-3.5 h-3.5" />
        <span>{match.kickoff_msk}</span>
      </div>

      {match.teaser && (
        <p className="text-xs text-textMuted leading-relaxed">{match.teaser}</p>
      )}

      {errorMsg && <p className="text-xs text-danger">{errorMsg}</p>}

      <button
        type="button"
        onClick={handlePredict}
        disabled={!canAnalyze}
        className={`magnetic-btn w-full font-semibold py-3 rounded-xl text-sm disabled:opacity-100 ${
          canAnalyze
            ? "bg-accent text-white"
            : "bg-surfaceElevated text-textMuted border border-borderSubtle cursor-not-allowed"
        }`}
      >
        {t.match_get_prediction}
      </button>
    </div>
  );
}
