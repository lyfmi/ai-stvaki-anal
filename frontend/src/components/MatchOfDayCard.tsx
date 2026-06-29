import { useCallback, useEffect, useState } from "react";
import { Calendar, Sparkles, Trophy } from "lucide-react";
import type { Translations } from "../i18n";

interface MatchOfDayCardProps {
  t: Translations;
  apiCall: (endpoint: string, options?: RequestInit) => Promise<any>;
  canAnalyze: boolean;
  hasFullAccess: boolean;
  onPredict: () => void;
  predicting: boolean;
}

export function MatchOfDayCard({
  t,
  apiCall,
  canAnalyze,
  hasFullAccess,
  onPredict,
  predicting,
}: MatchOfDayCardProps) {
  const [match, setMatch] = useState<any>(null);
  const [loadingMatch, setLoadingMatch] = useState(true);

  const loadMatch = useCallback(() => {
    return apiCall("/user/match-of-day")
      .then(setMatch)
      .catch(() => setMatch(null));
  }, [apiCall]);

  useEffect(() => {
    if (!hasFullAccess) {
      setLoadingMatch(false);
      return;
    }
    loadMatch().finally(() => setLoadingMatch(false));
  }, [hasFullAccess, loadMatch]);

  if (!hasFullAccess || loadingMatch) return null;
  if (!match) return null;

  const hasFixture = match.home_team && match.home_team !== "—";

  return (
    <div className="home-fade p-4 rounded-containerLg border border-accent/20 bg-gradient-to-br from-surface to-accent/5 flex flex-col gap-3">
      <div className="flex items-center gap-2">
        <Sparkles className="w-4 h-4 text-accent" />
        <span className="text-[10px] uppercase tracking-wider text-accent font-semibold">{t.match_of_day}</span>
        {match.is_live && (
          <span className="ml-auto text-[10px] uppercase font-medium text-success">LIVE</span>
        )}
      </div>

      {hasFixture ? (
        <>
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
        </>
      ) : (
        <p className="text-sm text-textMuted">{match.teaser}</p>
      )}

      {match.teaser && hasFixture && (
        <p className="text-xs text-textMuted leading-relaxed">{match.teaser}</p>
      )}

      {hasFixture && (
        <button
          type="button"
          onClick={onPredict}
          disabled={!canAnalyze || predicting}
          className={`magnetic-btn w-full font-semibold py-3 rounded-xl text-sm disabled:opacity-100 ${
            canAnalyze && !predicting
              ? "bg-accent text-white"
              : "bg-surfaceElevated text-textMuted border border-borderSubtle cursor-not-allowed"
          }`}
        >
          {predicting ? t.loading : t.match_get_prediction}
        </button>
      )}
    </div>
  );
}
