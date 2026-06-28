import type { Dispatch, SetStateAction } from "react";
import { AlertCircle, CheckCircle2, RefreshCw, Zap } from "lucide-react";
import { BottomTabBar } from "./BottomTabBar";
import { useAppRouter, isRootRoute } from "../../router/AppRouter";
import type { Route } from "../../router/types";
import type { Lang, Translations } from "../../i18n";
import { HomeScreen } from "../../screens/HomeScreen";
import { HistoryScreen } from "../../screens/HistoryScreen";
import { ProfileScreen } from "../../screens/ProfileScreen";
import { ResultScreen } from "../../screens/ResultScreen";
import { FunnelLockedScreen } from "../../screens/FunnelLockedScreen";
import { UnlimitedScreen } from "../../screens/UnlimitedScreen";
import { SupportScreen } from "../../screens/SupportScreen";
import { AdminHubScreen } from "../../screens/AdminHubScreen";

export interface AppContextProps {
  token: string | null;
  user: any;
  statusInfo: any;
  settings: any;
  lang: Lang;
  t: Translations;
  hasFullAccess: boolean;
  errorMsg: string | null;
  infoMsg: string | null;
  isLoading: boolean;
  showMockLogin: boolean;
  mockUserId: string;
  setMockUserId: (v: string) => void;
  onMockLogin: () => void;
  apiCall: (endpoint: string, options?: RequestInit) => Promise<any>;
  onLangChange: (l: Lang) => void;
  onRefreshStatus: () => void;
  analysisCache: Record<string, any>;
  setAnalysisCache: Dispatch<SetStateAction<Record<string, any>>>;
}

function DestinationView({
  route,
  ctx,
  onProfileNavigate,
}: {
  route: Route;
  ctx: AppContextProps;
  onProfileNavigate: (target: "support" | "unlimited" | "admin") => void;
}) {
  const { push, pop, activeTab } = useAppRouter();

  switch (route.type) {
    case "home":
      return (
        <HomeScreen
          t={ctx.t}
          token={ctx.token}
          hasFullAccess={ctx.hasFullAccess}
          statusInfo={ctx.statusInfo}
          onResult={(id) => {
            push({ type: "analyzeResult", id });
            ctx.onRefreshStatus();
          }}
        />
      );
    case "history":
      if (!ctx.hasFullAccess) return <FunnelLockedScreen t={ctx.t} />;
      return (
        <HistoryScreen
          apiCall={ctx.apiCall}
          t={ctx.t}
          lang={ctx.lang}
          onOpenResult={(id, item) => {
            ctx.setAnalysisCache((prev) => ({ ...prev, [id]: item }));
            push({ type: "analyzeResult", id });
          }}
        />
      );
    case "profile":
      return (
        <ProfileScreen
          user={ctx.user}
          lang={ctx.lang}
          t={ctx.t}
          onLangChange={ctx.onLangChange}
          onNavigate={onProfileNavigate}
        />
      );
    case "analyzeResult":
      if (!ctx.hasFullAccess) return <FunnelLockedScreen t={ctx.t} />;
      return (
        <ResultScreen
          analysisId={route.id}
          apiCall={ctx.apiCall}
          cached={ctx.analysisCache[route.id]}
          t={ctx.t}
          onBack={() => {
            if (activeTab === "home") pop();
            else pop();
          }}
        />
      );
    case "unlimited":
      return (
        <UnlimitedScreen user={ctx.user} settings={ctx.settings} apiCall={ctx.apiCall} t={ctx.t} />
      );
    case "support":
      return <SupportScreen settings={ctx.settings} t={ctx.t} />;
    case "admin":
      return <AdminHubScreen user={ctx.user} apiCall={ctx.apiCall} />;
    default:
      return null;
  }
}

export function AppShell(ctx: AppContextProps) {
  const { activeTab, currentRoute, push } = useAppRouter();

  const handleProfileNavigate = (target: "support" | "unlimited" | "admin") => {
    if (target === "support") push({ type: "support" });
    if (target === "unlimited") push({ type: "unlimited" });
    if (target === "admin") push({ type: "admin" });
  };

  if (ctx.isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <RefreshCw className="w-8 h-8 text-accent animate-spin" />
        <p className="text-textMuted text-sm">{ctx.t.loading}</p>
      </div>
    );
  }

  if (ctx.showMockLogin) {
    return (
      <div className="p-6 bg-surface rounded-containerLg border border-borderSubtle max-w-sm mx-auto mt-12 flex flex-col gap-4 text-center">
        <h2 className="text-lg font-semibold text-accent">Dev Auth</h2>
        <p className="text-xs text-textMuted">Enter Telegram User ID for local testing.</p>
        <input
          type="number"
          className="p-3 rounded-xl bg-appBg border border-borderSubtle text-textPrimary text-center"
          value={ctx.mockUserId}
          onChange={(e) => ctx.setMockUserId(e.target.value)}
        />
        <button
          type="button"
          onClick={ctx.onMockLogin}
          className="magnetic-btn w-full bg-accent text-appBg py-3 rounded-xl font-semibold flex items-center justify-center gap-2"
        >
          <Zap className="w-4 h-4" /> Start
        </button>
      </div>
    );
  }

  return (
    <>
      <div key={`${activeTab}-${currentRoute.type}`} className="screen-enter">
        <DestinationView
          route={currentRoute}
          ctx={ctx}
          onProfileNavigate={handleProfileNavigate}
        />
      </div>
    </>
  );
}

export function AppLayout(ctx: AppContextProps) {
  const { activeTab, navigate, currentRoute } = useAppRouter();
  const showTabBar = isRootRoute(currentRoute);

  return (
    <div className="relative min-h-screen bg-appBg overflow-x-hidden">
      <div className="noise-overlay" />

      <main className="w-full max-w-lg mx-auto px-4 pt-4 pb-24">
        {ctx.errorMsg && (
          <div className="mb-4 p-3 bg-danger/10 border border-danger/20 text-danger text-xs rounded-container flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <p>{ctx.errorMsg}</p>
          </div>
        )}
        {ctx.infoMsg && (
          <div className="mb-4 p-3 bg-accent/10 border border-accent/20 text-accent text-xs rounded-container flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <p>{ctx.infoMsg}</p>
          </div>
        )}

        <AppShell {...ctx} />
      </main>

      {showTabBar && !ctx.showMockLogin && !ctx.isLoading && (
        <BottomTabBar
          activeTab={activeTab}
          onNavigate={navigate}
          t={ctx.t}
          historyDisabled={!ctx.hasFullAccess}
        />
      )}
    </div>
  );
}
