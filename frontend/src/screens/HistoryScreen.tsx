import { useEffect, useState } from "react";
import { ArrowRight, History as HistoryIcon, RefreshCw } from "lucide-react";
import type { Translations, Lang } from "../i18n";

interface HistoryScreenProps {
  apiCall: (endpoint: string, options?: RequestInit) => Promise<any>;
  t: Translations;
  lang: Lang;
  onOpenResult: (id: string, item: any) => void;
}

export function HistoryScreen({ apiCall, t, lang, onOpenResult }: HistoryScreenProps) {
  const [list, setList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiCall("/user/analyses")
      .then((data) => setList(data || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [apiCall]);

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString(lang === "ru" ? "ru-RU" : "en-US", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="flex flex-col gap-5 screen-enter">
      <h2 className="text-lg font-semibold text-textPrimary">{t.history}</h2>

      {loading ? (
        <div className="flex flex-col items-center justify-center min-h-[40vh] gap-3">
          <RefreshCw className="w-7 h-7 text-accent animate-spin" />
          <span className="text-textMuted text-xs">{t.loading}</span>
        </div>
      ) : list.length === 0 ? (
        <div className="p-10 bg-surface border border-borderSubtle rounded-containerLg text-center flex flex-col items-center gap-3">
          <HistoryIcon className="w-8 h-8 text-textMuted" />
          <p className="text-xs text-textMuted">{t.history_empty}</p>
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          {list.map((item) => {
            const isPostMatch =
              item.analysis_mode === "post_match" || item.is_betting_recommendation === false;
            return (
            <button
              key={item.id}
              type="button"
              onClick={() => onOpenResult(item.id, item)}
              className="p-4 bg-surface border border-borderSubtle hover:border-accent/25 rounded-container flex items-center justify-between text-left interactive-lift transition-colors"
            >
              <div className="flex flex-col gap-1 min-w-0 flex-1">
                <span className="text-sm font-medium text-textPrimary truncate">
                  {item.recommendation || "—"}
                </span>
                <span className="text-[10px] text-textMuted">
                  {formatDate(item.created_at)}
                  {isPostMatch
                    ? ` · ${t.history_finished}`
                    : ` · x${item.coefficient ?? "—"}`}
                </span>
              </div>
              <div className="flex items-center gap-2 shrink-0 ml-3">
                {isPostMatch ? (
                  <span className="text-[10px] uppercase font-medium text-textMuted px-2 py-0.5 rounded border border-borderSubtle">
                    {t.history_finished}
                  </span>
                ) : (
                  <span className="text-xs text-accent font-medium">
                    {item.probability_percent != null ? `${item.probability_percent}%` : "—"}
                  </span>
                )}
                <ArrowRight className="w-4 h-4 text-textMuted" />
              </div>
            </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
