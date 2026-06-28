import { useCallback, useEffect, useMemo, useState } from "react";
import { AppRouterProvider, useAppRouter } from "./router/AppRouter";
import { AppLayout } from "./components/layout/AppShell";
import { apiCall as apiRequest, authenticateTelegram } from "./api";
import { i18n, type Lang } from "./i18n";

function AppContent() {
  const { pop, canGoBack } = useAppRouter();
  const [token, setToken] = useState<string | null>(() => localStorage.getItem("tg_auth_token"));
  const [user, setUser] = useState<any>(null);
  const [statusInfo, setStatusInfo] = useState<any>(null);
  const [settings, setSettings] = useState<any>(null);
  const [analysisCache, setAnalysisCache] = useState<Record<string, any>>({});
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [infoMsg, setInfoMsg] = useState<string | null>(null);
  const [lang, setLang] = useState<Lang>("ru");
  const [isLoading, setIsLoading] = useState(true);
  const [showMockLogin, setShowMockLogin] = useState(false);
  const [mockUserId, setMockUserId] = useState("7649494487");

  const t = i18n[lang];
  const hasFullAccess = Boolean(
    user &&
      (user.is_admin ||
        user.is_deposited ||
        user.has_unlimited ||
        ["ACTIVE", "UNLIMITED", "LIMIT_EXCEEDED"].includes(user.funnel_state))
  );

  const callApi = useCallback(
    (endpoint: string, options?: RequestInit) => apiRequest(endpoint, token, options),
    [token]
  );

  const fetchStatusAndSettings = useCallback(async () => {
    if (!token) return;
    try {
      const [statusRes, settingsRes] = await Promise.all([
        callApi("/user/status"),
        callApi("/user/settings"),
      ]);
      setUser(statusRes.user);
      setStatusInfo(statusRes);
      setSettings(settingsRes);
      setLang(statusRes.user.language === "en" ? "en" : "ru");
    } catch (e) {
      console.error(e);
    }
  }, [token, callApi]);

  useEffect(() => {
    if (window.Telegram?.WebApp) {
      window.Telegram.WebApp.ready();
      window.Telegram.WebApp.expand();
    }
  }, []);

  useEffect(() => {
    const authenticate = async () => {
      const initData = window.Telegram?.WebApp?.initData;
      if (initData) {
        try {
          const data = await authenticateTelegram(initData);
          setToken(data.token);
          localStorage.setItem("tg_auth_token", data.token);
          setUser(data.user);
          setLang(data.user.language === "en" ? "en" : "ru");
        } catch (e) {
          console.error(e);
        }
      } else if (!token) {
        setShowMockLogin(true);
      }
      setIsLoading(false);
    };
    authenticate();
  }, [token]);

  useEffect(() => {
    if (token) fetchStatusAndSettings();
  }, [token, fetchStatusAndSettings]);

  useEffect(() => {
    const backButton = window.Telegram?.WebApp?.BackButton;
    if (!backButton) return;

    if (canGoBack) backButton.show();
    else backButton.hide();

    const handleBack = () => pop();
    backButton.onClick(handleBack);
    return () => backButton.offClick(handleBack);
  }, [canGoBack, pop]);

  const handleMockLogin = () => {
    const mockToken = `stub-jwt-${mockUserId}`;
    setToken(mockToken);
    localStorage.setItem("tg_auth_token", mockToken);
    setShowMockLogin(false);
  };

  const handleLanguageChange = async (newLang: Lang) => {
    try {
      const updated = await callApi("/user/language", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ language: newLang }),
      });
      setLang(newLang);
      setUser(updated);
      setInfoMsg(i18n[newLang].lang_changed);
      setTimeout(() => setInfoMsg(null), 2500);
      await fetchStatusAndSettings();
    } catch (err: any) {
      setErrorMsg(err.message);
    }
  };

  const ctx = useMemo(
    () => ({
      token,
      user,
      statusInfo,
      settings,
      lang,
      t,
      hasFullAccess,
      errorMsg,
      infoMsg,
      isLoading,
      showMockLogin,
      mockUserId,
      setMockUserId,
      onMockLogin: handleMockLogin,
      apiCall: callApi,
      onLangChange: handleLanguageChange,
      onRefreshStatus: fetchStatusAndSettings,
      analysisCache,
      setAnalysisCache,
    }),
    [
      token,
      user,
      statusInfo,
      settings,
      lang,
      t,
      hasFullAccess,
      errorMsg,
      infoMsg,
      isLoading,
      showMockLogin,
      mockUserId,
      callApi,
      fetchStatusAndSettings,
      analysisCache,
    ]
  );

  return <AppLayout {...ctx} />;
}

export default function App() {
  return (
    <AppRouterProvider>
      <AppContent />
    </AppRouterProvider>
  );
}
