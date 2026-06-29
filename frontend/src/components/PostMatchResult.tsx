import { Trophy } from "lucide-react";
import type { Translations } from "../i18n";

interface PostMatchResultProps {
  t: Translations;
  recommendation: string;
  finalScore?: string | null;
  winner?: string | null;
  matchDatetimeMsk?: string | null;
  statusLabel?: string | null;
  explanation?: string | null;
  arguments?: string[] | null;
}

export function PostMatchResult({
  t,
  recommendation,
  finalScore,
  winner,
  matchDatetimeMsk,
  statusLabel,
  explanation,
  arguments: argsList,
}: PostMatchResultProps) {
  const displayScore = finalScore || recommendation;
  const displayWinner = winner;

  return (
    <div className="flex flex-col gap-4">
      <div className="relative overflow-hidden p-5 bg-gradient-to-br from-surface via-surface to-brandDeep/40 border border-borderSubtle rounded-containerLg">
        <div className="absolute top-0 right-0 w-32 h-32 bg-accent/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/4 pointer-events-none" />

        <div className="flex flex-wrap items-center gap-2 mb-4">
          <span className="text-[10px] uppercase font-semibold tracking-wider px-2.5 py-1 rounded-lg border border-textMuted/30 bg-surfaceElevated text-textMuted">
            {statusLabel || t.result_post_match_badge}
          </span>
          {matchDatetimeMsk && (
            <span className="text-[10px] uppercase font-medium px-2.5 py-1 rounded-lg border border-borderSubtle bg-surfaceElevated/80 text-textMuted">
              {t.result_match_time}: {matchDatetimeMsk}
            </span>
          )}
        </div>

        <div className="flex items-start gap-3">
          <div className="shrink-0 w-10 h-10 rounded-xl bg-surfaceElevated border border-borderSubtle flex items-center justify-center">
            <Trophy className="w-5 h-5 text-textMuted" />
          </div>
          <div className="min-w-0 flex-1">
            {displayWinner && (
              <p className="text-[10px] text-textMuted uppercase tracking-wider mb-1">
                {t.result_winner}
              </p>
            )}
            {displayWinner && (
              <p className="text-lg font-semibold text-textPrimary leading-snug mb-2">{displayWinner}</p>
            )}
            <p className="text-[10px] text-textMuted uppercase tracking-wider mb-1">
              {t.result_final_score}
            </p>
            <p className="text-2xl font-bold text-textPrimary tracking-tight">{displayScore || "—"}</p>
            {!displayWinner && recommendation && recommendation !== displayScore && (
              <p className="text-sm text-textMuted mt-2 leading-relaxed">{recommendation}</p>
            )}
          </div>
        </div>
      </div>

      {(explanation || (argsList?.length ?? 0) > 0) && (
        <div className="p-5 bg-surface border border-borderSubtle rounded-containerLg flex flex-col gap-4">
          <span className="text-[10px] text-textMuted uppercase tracking-wider">
            {t.result_match_summary}
          </span>

          {argsList && argsList.length > 0 && (
            <ul className="flex flex-col gap-2 m-0 p-0 list-none">
              {argsList.map((arg, i) => (
                <li key={i} className="text-sm text-textPrimary/90 flex gap-2 leading-relaxed">
                  <span className="text-accent shrink-0 mt-0.5">·</span>
                  <span>{arg}</span>
                </li>
              ))}
            </ul>
          )}

          {explanation && (
            <p
              className={`text-sm text-textMuted leading-relaxed ${
                argsList?.length ? "border-t border-borderSubtle pt-4" : ""
              }`}
            >
              {explanation}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
