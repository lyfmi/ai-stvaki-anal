import { History, Home, User } from "lucide-react";
import type { Translations } from "../../i18n";
import type { TabId } from "../../router/types";

interface BottomTabBarProps {
  activeTab: TabId;
  onNavigate: (tab: TabId) => void;
  t: Translations;
  historyDisabled?: boolean;
}

const tabs: { id: TabId; icon: typeof Home; labelKey: keyof Translations }[] = [
  { id: "home", icon: Home, labelKey: "tab_home" },
  { id: "history", icon: History, labelKey: "tab_history" },
  { id: "profile", icon: User, labelKey: "tab_profile" },
];

export function BottomTabBar({ activeTab, onNavigate, t, historyDisabled }: BottomTabBarProps) {
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 bg-appBg/90 backdrop-blur-xl border-t border-borderSubtle safe-area-pb">
      <div className="max-w-lg mx-auto flex items-stretch">
        {tabs.map(({ id, icon: Icon, labelKey }) => {
          const active = activeTab === id;
          const disabled = id === "history" && historyDisabled;
          return (
            <button
              key={id}
              type="button"
              disabled={disabled}
              onClick={() => !disabled && onNavigate(id)}
              className={`flex-1 flex flex-col items-center justify-center gap-1 py-3 transition-all duration-200 ${
                disabled
                  ? "opacity-30 cursor-not-allowed"
                  : active
                    ? "text-accent"
                    : "text-textMuted hover:text-textPrimary"
              }`}
            >
              <Icon className={`w-5 h-5 ${active ? "scale-110" : ""} transition-transform duration-200`} />
              <span className="text-[10px] font-medium">{t[labelKey]}</span>
              {active && <span className="w-1 h-1 rounded-full bg-accent pulse-dot" />}
            </button>
          );
        })}
      </div>
    </nav>
  );
}
