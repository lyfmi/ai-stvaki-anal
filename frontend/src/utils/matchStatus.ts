/** Parse "DD.MM.YYYY HH:MM МСК" to Date (local MSK approximation via UTC offset +3). */
export function parseMskDatetime(text: string | null | undefined): Date | null {
  if (!text) return null;
  const m = text.match(/(\d{1,2})\.(\d{1,2})\.(\d{4})\s+(\d{1,2}):(\d{2})/);
  if (!m) return null;
  const [, day, month, year, hour, minute] = m;
  // MSK = UTC+3
  return new Date(Date.UTC(+year, +month - 1, +day, +hour - 3, +minute));
}

export function resolveDisplayStatus(
  analysisMode: string | null | undefined,
  matchStatusLabel: string | null | undefined,
  matchDatetimeMsk: string | null | undefined,
  lang: "ru" | "en" = "ru"
): { label: string; mode: string; isLive: boolean; isPostMatch: boolean } {
  const kickoff = parseMskDatetime(matchDatetimeMsk);
  const now = Date.now();
  const labels = lang === "en"
    ? { pre: "Upcoming", live: "Live now", post: "Match finished" }
    : { pre: "Скоро", live: "Идёт сейчас", post: "Матч завершён" };

  if (kickoff) {
    const kick = kickoff.getTime();
    if (kick > now + 10 * 60 * 1000) {
      return { label: labels.pre, mode: "pre_match", isLive: false, isPostMatch: false };
    }
    if (kick <= now - 130 * 60 * 1000) {
      return { label: labels.post, mode: "post_match", isLive: false, isPostMatch: true };
    }
    if (kick <= now && now < kick + 130 * 60 * 1000) {
      return { label: labels.live, mode: "live", isLive: true, isPostMatch: false };
    }
    return { label: labels.pre, mode: "pre_match", isLive: false, isPostMatch: false };
  }

  const mode = analysisMode || "pre_match";
  const isPostMatch = mode === "post_match";
  const isLive = mode === "live";
  return {
    label: matchStatusLabel || labels.pre,
    mode,
    isLive,
    isPostMatch,
  };
}
