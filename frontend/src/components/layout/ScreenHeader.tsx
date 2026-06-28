import type { Translations } from "../../i18n";

export function ScreenHeader({ t, showBrand = true }: { t: Translations; showBrand?: boolean }) {
  if (!showBrand) return null;
  return (
    <header className="pt-2 pb-6">
      <h1 className="text-lg font-semibold tracking-[0.2em] text-textPrimary uppercase">{t.brand}</h1>
    </header>
  );
}
