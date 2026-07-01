import type { Lang } from "../i18n";

export function displayLevel(value: string | null | undefined, lang: Lang): string {
  if (!value) return "—";
  const v = value.trim().toLowerCase();
  if (lang === "ru") {
    if (v === "high" || v === "высокая") return "Высокая";
    if (v === "medium" || v === "средняя") return "Средняя";
    if (v === "low" || v === "низкая") return "Низкая";
    return value;
  }
  if (v === "высокая") return "High";
  if (v === "средняя") return "Medium";
  if (v === "низкая") return "Low";
  if (v === "high") return "High";
  if (v === "medium") return "Medium";
  if (v === "low") return "Low";
  return value;
}
