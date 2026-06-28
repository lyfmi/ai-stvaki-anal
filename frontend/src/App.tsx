import React, { useState, useEffect, useRef } from "react";
import { 
  Camera, Upload, History as HistoryIcon, User as UserIcon, ShieldAlert, CheckCircle2, 
  Crown, HelpCircle, Settings as SettingsIcon, Megaphone, Link as LinkIcon, 
  Copy, RefreshCw, Languages, ArrowLeft, ArrowRight, Zap, AlertCircle
} from "lucide-react";
import { gsap } from "gsap";

// Declare global Telegram interface for TypeScript
declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        ready: () => void;
        expand: () => void;
        close: () => void;
        initData: string;
        initDataUnsafe?: {
          user?: {
            id: number;
            first_name: string;
            last_name?: string;
            username?: string;
            language_code?: string;
          };
        };
        themeParams: {
          bg_color?: string;
          text_color?: string;
          hint_color?: string;
          link_color?: string;
          button_color?: string;
          button_text_color?: string;
          secondary_bg_color?: string;
        };
        MainButton: {
          text: string;
          color: string;
          textColor: string;
          isVisible: boolean;
          isActive: boolean;
          isProgressVisible: boolean;
          show: () => void;
          hide: () => void;
          enable: () => void;
          disable: () => void;
          showProgress: (leaveActive?: boolean) => void;
          hideProgress: () => void;
          onClick: (callback: () => void) => void;
          offClick: (callback: () => void) => void;
          setParams: (params: { text?: string; color?: string; text_color?: string; is_active?: boolean; is_visible?: boolean }) => void;
        };
        BackButton: {
          isVisible: boolean;
          show: () => void;
          hide: () => void;
          onClick: (callback: () => void) => void;
          offClick: (callback: () => void) => void;
        };
        HapticFeedback: {
          impactOccurred: (style: "light" | "medium" | "heavy" | "rigid" | "soft") => void;
          notificationOccurred: (type: "error" | "success" | "warning") => void;
          selectionChanged: () => void;
        };
        openLink: (url: string, options?: { try_instant_view?: boolean }) => void;
        openTelegramLink: (url: string) => void;
        openInvoice: (url: string, callback?: (status: string) => void) => void;
      };
    };
  }
}

// Translations structure
const i18n = {
  ru: {
    dashboard: "Дашборд",
    analyze: "Анализировать",
    history: "История",
    profile: "Профиль",
    unlimited: "Безлимит",
    admin: "Админ",
    welcome: "Добро пожаловать в",
    brand_sub: "AI-анализ ставок и прогнозирование спортивных исходов",
    attempts: "Доступно попыток",
    attempts_unlimited: "Безлимитный доступ активен",
    can_analyze: "Вы можете сделать анализ купона",
    cannot_analyze: "Анализ заблокирован. Завершите шаги воронки ниже.",
    funnel_sub: "Шаг 1: Подписка на Telegram-канал",
    funnel_sub_btn: "Проверить подписку",
    funnel_sub_ok: "Вы подписаны на канал",
    funnel_reg: "Шаг 2: Регистрация в БК партнёре",
    funnel_reg_desc: "Зарегистрируйтесь по нашей ссылке и введите промокод для активации AI-модели.",
    funnel_reg_btn: "Зарегистрироваться",
    funnel_reg_code: "Ваш промокод:",
    funnel_dep: "Шаг 3: Внесите депозит",
    funnel_dep_desc: "Пополните баланс в БК для активации бесплатного пакета прогнозов.",
    funnel_dep_btn: "Сделать депозит",
    funnel_active: "Все шаги пройдены! AI-модель готова к работе.",
    cta_analyze: "Анализировать скриншот купона",
    cta_get_unlimited: "Купить безлимитный доступ",
    upload_title: "Загрузка купона ставки",
    upload_desc: "Перетащите изображение купона или выберите файл из галереи (до 10 МБ). На скриншоте должен быть виден матч и коэффициенты.",
    upload_select: "Выбрать изображение",
    upload_camera: "Сделать снимок",
    upload_drop: "Отпустите скриншот для загрузки",
    uploading_vision: "Распознавание купона (Vision)...",
    uploading_search: "Поиск новостей и аналитики матча (Search)...",
    uploading_synthesis: "Синтез решения моделью AI...",
    result_title: "AI Результат Анализа",
    result_bet: "🎯 Прогноз:",
    result_coef: "Коэффициент:",
    result_risk: "⚠️ Риск:",
    result_probability: "📊 Вероятность:",
    result_confidence: "💪 Уверенность:",
    result_args: "Аргументы:",
    result_disclaimer: "Дисклеймер: Спортивные прогнозы ИИ носят рекомендательный характер. AI не даёт 100% гарантий.",
    result_back: "Вернуться на Главную",
    profile_lang: "Язык интерфейса",
    profile_status: "Ваш статус:",
    profile_state: "Состояние воронки:",
    profile_registered: "Регистрация подтверждена:",
    profile_deposited: "Депозит подтвержден:",
    support_btn: "Поддержка клиентов",
    support_desc: "Возникли вопросы или проблемы с оплатой? Свяжитесь с нами напрямую.",
    unlimited_title: "Безлимитный AI-Анализ",
    unlimited_desc: "Получите неограниченный доступ к прогнозированию без лимитов по времени и количеству купонов.",
    unlimited_price: "Стоимость подписки:",
    unlimited_pay_btn: "Купить Безлимит через Tribute",
    unlimited_already: "У вас уже активирован безлимитный доступ!",
    yes: "Да",
    no: "Нет",
    loading: "Загрузка...",
    lang_changed: "✅ Язык изменён",
    funnel_locked_title: "🔒 Mini App пока закрыт",
    funnel_locked_desc: "Сначала пройдите воронку в боте: подписка → регистрация в БК → депозит. После этого откроется анализ скриншотов.",
    funnel_locked_bot: "Вернуться в бот и продолжить",
  },
  en: {
    dashboard: "Dashboard",
    analyze: "Analyze",
    history: "History",
    profile: "Profile",
    unlimited: "Unlimited",
    admin: "Admin",
    welcome: "Welcome to",
    brand_sub: "AI-powered bet analysis and sports outcome forecasting",
    attempts: "Attempts remaining",
    attempts_unlimited: "Unlimited Access Active",
    can_analyze: "You can analyze bet screenshots",
    cannot_analyze: "Analysis locked. Please complete the funnel steps below.",
    funnel_sub: "Step 1: Subscribe to Telegram Channel",
    funnel_sub_btn: "Verify Subscription",
    funnel_sub_ok: "Subscribed to channel",
    funnel_reg: "Step 2: Register in Partner Bookmaker",
    funnel_reg_desc: "Register using our link and copy the promo code to activate the AI model.",
    funnel_reg_btn: "Register Now",
    funnel_reg_code: "Your Promo Code:",
    funnel_dep: "Step 3: Make a Deposit",
    funnel_dep_desc: "Top up your bookmaker account to unlock free AI prediction package.",
    funnel_dep_btn: "Make Deposit",
    funnel_active: "All steps completed! AI analysis is fully unlocked.",
    cta_analyze: "Analyze Bet Screenshot",
    cta_get_unlimited: "Get Unlimited Access",
    upload_title: "Upload Bet Coupon",
    upload_desc: "Drag & drop your coupon screenshot or browse gallery (max 10MB). Match events and odds should be visible.",
    upload_select: "Choose Image",
    upload_camera: "Take Photo",
    upload_drop: "Drop screenshot here",
    uploading_vision: "Parsing coupon image (Vision)...",
    uploading_search: "Searching match news & analytics...",
    uploading_synthesis: "Synthesizing AI prediction...",
    result_title: "AI Analysis Result",
    result_bet: "🎯 Prediction:",
    result_coef: "Odds:",
    result_risk: "⚠️ Risk:",
    result_probability: "📊 Probability:",
    result_confidence: "💪 Confidence:",
    result_args: "Key Arguments:",
    result_disclaimer: "Disclaimer: AI forecasts are for informational purposes only. Predictions are not 100% guaranteed.",
    result_back: "Return to Dashboard",
    profile_lang: "Interface Language",
    profile_status: "Your Status:",
    profile_state: "Funnel state:",
    profile_registered: "Registered:",
    profile_deposited: "Deposited:",
    support_btn: "Customer Support",
    support_desc: "Have questions or need payment help? Message our support desk.",
    unlimited_title: "Unlimited AI Analysis",
    unlimited_desc: "Get total lifetime access to AI bet parsing without daily constraints.",
    unlimited_price: "Subscription price:",
    unlimited_pay_btn: "Buy Unlimited via Tribute",
    unlimited_already: "You already have Unlimited access active!",
    yes: "Yes",
    no: "No",
    loading: "Loading...",
    lang_changed: "✅ Language updated",
    funnel_locked_title: "🔒 Mini App is locked",
    funnel_locked_desc: "Complete the bot funnel first: subscribe → register at the bookmaker → deposit. Then screenshot analysis will unlock.",
    funnel_locked_bot: "Return to bot to continue",
  }
};

// Custom API Host helper
const API_BASE = "/api";

export default function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem("tg_auth_token"));
  const [user, setUser] = useState<any>(null);
  const [statusInfo, setStatusInfo] = useState<any>(null);
  const [settings, setSettings] = useState<any>(null);
  const [currentRoute, setRoute] = useState<string>("/");
  const [activeAnalysis, setActiveAnalysis] = useState<any>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [infoMsg, setInfoMsg] = useState<string | null>(null);
  const [lang, setLang] = useState<"ru" | "en">("ru");
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Desktop Mocking setup for developer local test
  const [showMockLogin, setShowMockLogin] = useState<boolean>(false);
  const [mockUserId, setMockUserId] = useState<string>("7649494487"); // Admin default

  const t = i18n[lang];
  const ADMIN_TELEGRAM_ID = 7649494487;
  const hasFullAccess = Boolean(
    user &&
      (user.telegram_id === ADMIN_TELEGRAM_ID ||
        user.is_deposited ||
        user.has_unlimited ||
        ["ACTIVE", "UNLIMITED", "LIMIT_EXCEEDED"].includes(user.funnel_state))
  );
  const allowedLockedRoutes = ["/", "/profile", "/support"];

  // Helper for requests
  const apiCall = async (endpoint: string, options: RequestInit = {}) => {
    const headers = new Headers(options.headers || {});
    
    // Auth Token header
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }

    // Try to extract initData if in Telegram
    const initData = window.Telegram?.WebApp?.initData;
    if (initData) {
      headers.set("X-Telegram-Init-Data", initData);
    }

    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers,
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(errData.detail || `HTTP Error ${response.status}`);
      }

      return await response.json();
    } catch (err: any) {
      console.error(`API Call failed to ${endpoint}:`, err);
      throw err;
    }
  };

  // Telegram Ready
  useEffect(() => {
    if (window.Telegram?.WebApp) {
      window.Telegram.WebApp.ready();
      window.Telegram.WebApp.expand();
    }
  }, []);

  // Fetch initial configs, settings, and login
  useEffect(() => {
    const authenticate = async () => {
      const initData = window.Telegram?.WebApp?.initData;
      if (initData) {
        try {
          const authRes = await fetch(`${API_BASE}/auth/telegram`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ init_data: initData }),
          });

          if (authRes.ok) {
            const data = await authRes.json();
            setToken(data.token);
            localStorage.setItem("tg_auth_token", data.token);
            setUser(data.user);
            setLang(data.user.language === "en" ? "en" : "ru");
            setErrorMsg(null);
          } else {
            console.error("Telegram initData authentication failed");
          }
        } catch (e) {
          console.error("Auth call error", e);
        }
      } else {
        // Not in Telegram WebApp
        if (!token) {
          setShowMockLogin(true);
        }
      }
    };

    authenticate().finally(() => {
      setIsLoading(false);
    });
  }, [token]);

  // Fetch status and settings if authenticated
  const fetchStatusAndSettings = async () => {
    if (!token) return;
    try {
      const [statusRes, settingsRes] = await Promise.all([
        apiCall("/user/status"),
        apiCall("/user/settings"),
      ]);
      setUser(statusRes.user);
      setStatusInfo(statusRes);
      setSettings(settingsRes);
      setLang(statusRes.user.language === "en" ? "en" : "ru");
    } catch (e: any) {
      console.error("Failed to load status / settings", e);
    }
  };

  useEffect(() => {
    if (token) {
      fetchStatusAndSettings();
    }
  }, [token]);

  // Block premium routes until funnel is complete
  useEffect(() => {
    if (!user || hasFullAccess) return;
    if (!allowedLockedRoutes.includes(currentRoute) && !currentRoute.startsWith("/analyze/result/")) {
      setRoute("/");
    }
  }, [user, hasFullAccess, currentRoute]);

  // BackButton management
  useEffect(() => {
    const backButton = window.Telegram?.WebApp?.BackButton;
    if (!backButton) return;

    if (currentRoute === "/") {
      backButton.hide();
    } else {
      backButton.show();
    }

    const handleBack = () => {
      if (currentRoute.startsWith("/analyze/result/")) {
        setRoute("/history");
      } else {
        setRoute("/");
      }
    };

    backButton.onClick(handleBack);
    return () => {
      backButton.offClick(handleBack);
    };
  }, [currentRoute]);

  // Mock Developer Login helper
  const handleMockLogin = async () => {
    try {
      setIsLoading(true);
      // Stub jwt structure we support
      const mockToken = `stub-jwt-${mockUserId}`;
      setToken(mockToken);
      localStorage.setItem("tg_auth_token", mockToken);
      setShowMockLogin(false);
    } catch (e) {
      setErrorMsg("Failed to simulate login");
    } finally {
      setIsLoading(false);
    }
  };

  // Toggle Language Handler
  const handleLanguageChange = async (newLang: "ru" | "en") => {
    try {
      const updated = await apiCall("/user/language", {
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
      setErrorMsg(err.message || "Failed to set language");
    }
  };

  // Check Subscription Handler
  const handleCheckSubscription = async () => {
    try {
      const res = await apiCall("/user/check-subscription", { method: "POST" });
      setUser(res);
      fetchStatusAndSettings();
      setInfoMsg(lang === "ru" ? "Статус подписки проверен!" : "Subscription checked successfully!");
      setTimeout(() => setInfoMsg(null), 3000);
    } catch (err: any) {
      setErrorMsg(err.message || "Subscription check failed");
      setTimeout(() => setErrorMsg(null), 3000);
    }
  };

  // Reset attempt messages helper
  const getResetCountdown = () => {
    if (!statusInfo?.attempts_reset_at) return "";
    const resetTime = new Date(statusInfo.attempts_reset_at).getTime();
    const diff = resetTime - Date.now();
    if (diff <= 0) return "";
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    return lang === "ru" ? `Сброс через ${hours}ч ${mins}м` : `Resets in ${hours}h ${mins}m`;
  };

  // Render content depending on route
  const renderScreen = () => {
    if (isLoading) {
      return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
          <RefreshCw className="w-8 h-8 text-champagne animate-spin" />
          <p className="text-slate-400 text-sm font-mono">{t.loading}</p>
        </div>
      );
    }

    if (showMockLogin) {
      return (
        <div className="p-6 bg-slateCustom/30 rounded-container border border-champagne/10 max-w-sm mx-auto mt-12 flex flex-col gap-4 text-center">
          <h2 className="text-xl font-bold font-sans text-champagne">Developer Sandbox Auth</h2>
          <p className="text-xs text-slate-400">
            Please enter a Telegram User ID to mock the environment (not running inside Telegram Web App).
          </p>
          <input
            type="number"
            className="p-3 rounded-xl bg-obsidian border border-slateCustom text-white text-center font-mono"
            value={mockUserId}
            onChange={(e) => setMockUserId(e.target.value)}
            placeholder="Telegram User ID"
          />
          <button
            onClick={handleMockLogin}
            className="magnetic-btn w-full bg-champagne text-obsidian py-3 rounded-xl font-bold font-sans flex items-center justify-center gap-2"
          >
            <Zap className="w-4 h-4" /> Start Sandbox Session
          </button>
        </div>
      );
    }

    switch (currentRoute) {
      case "/":
        return (
          <DashboardScreen 
            user={user} 
            statusInfo={statusInfo} 
            settings={settings}
            setRoute={setRoute} 
            onCheckSub={handleCheckSubscription}
            getResetCountdown={getResetCountdown}
            lang={lang}
            t={t}
            hasFullAccess={hasFullAccess}
          />
        );
      case "/analyze":
        if (!hasFullAccess) {
          return <FunnelLockedScreen t={t} />;
        }
        return (
          <UploadScreen 
            token={token} 
            onSuccess={(analysisId) => {
              setRoute(`/analyze/result/${analysisId}`);
            }}
            lang={lang}
            t={t}
          />
        );
      case "/history":
        if (!hasFullAccess) {
          return <FunnelLockedScreen t={t} />;
        }
        return (
          <HistoryScreen 
            apiCall={apiCall}
            setRoute={setRoute} 
            setActiveAnalysis={setActiveAnalysis}
            lang={lang}
            t={t}
          />
        );
      case "/profile":
        return (
          <ProfileScreen 
            user={user} 
            lang={lang}
            onLangChange={handleLanguageChange}
            t={t}
          />
        );
      case "/unlimited":
        return (
          <UnlimitedScreen 
            user={user} 
            settings={settings} 
            apiCall={apiCall}
            t={t}
          />
        );
      case "/support":
        return (
          <SupportScreen 
            settings={settings} 
            lang={lang}
            t={t}
          />
        );
      case "/admin":
        return (
          <AdminHubScreen 
            user={user}
            apiCall={apiCall}
          />
        );
      default:
        if (currentRoute.startsWith("/analyze/result/")) {
          if (!hasFullAccess) {
            return <FunnelLockedScreen t={t} />;
          }
          const analysisId = currentRoute.split("/").pop() || "";
          return (
            <ResultScreen 
              analysisId={analysisId}
              apiCall={apiCall}
              activeAnalysis={activeAnalysis}
              setActiveAnalysis={setActiveAnalysis}
              setRoute={setRoute}
              t={t}
            />
          );
        }
        return <div className="text-center py-10 font-mono text-sm text-slate-400">404 - Not Found</div>;
    }
  };

  return (
    <div className="relative min-h-screen pb-20 overflow-x-hidden">
      {/* Global CSS noise overlay */}
      <div className="noise-overlay" />

      {/* Header / Navbar (The Floating Island) */}
      <header className="fixed top-3 left-1/2 transform -translate-x-1/2 z-50 w-[92%] max-w-lg bg-obsidian/75 backdrop-blur-xl border border-champagne/15 py-2.5 px-4 rounded-full flex items-center justify-between shadow-2xl transition-all duration-300">
        <div className="flex items-center gap-2 cursor-pointer" onClick={() => setRoute("/")}>
          <span className="font-drama italic text-champagne text-lg font-bold">Luxe</span>
          <span className="font-mono text-slate-400 text-xxs tracking-widest uppercase">Bet AI</span>
        </div>
        
        <nav className="flex items-center gap-3">
          <button 
            onClick={() => setRoute("/")} 
            className={`text-xs font-medium px-2.5 py-1.5 rounded-full transition-all duration-200 ${currentRoute === "/" ? "bg-champagne/10 text-champagne" : "text-slate-400 hover:text-white"}`}
          >
            {t.dashboard}
          </button>
          <button 
            onClick={() => hasFullAccess && setRoute("/history")} 
            disabled={!hasFullAccess}
            className={`text-xs font-medium px-2.5 py-1.5 rounded-full transition-all duration-200 ${!hasFullAccess ? "text-slate-600 cursor-not-allowed opacity-50" : currentRoute.startsWith("/history") || currentRoute.startsWith("/analyze/result") ? "bg-champagne/10 text-champagne" : "text-slate-400 hover:text-white"}`}
          >
            {t.history}
          </button>
          <button 
            onClick={() => setRoute("/profile")} 
            className={`text-xs font-medium px-2.5 py-1.5 rounded-full transition-all duration-200 ${currentRoute === "/profile" ? "bg-champagne/10 text-champagne" : "text-slate-400 hover:text-white"}`}
          >
            {t.profile}
          </button>
          {user && user.telegram_id === 7649494487 && (
            <button 
              onClick={() => setRoute("/admin")} 
              className={`text-xs font-bold px-2.5 py-1.5 rounded-full border border-champagne/30 text-champagne hover:bg-champagne/10`}
            >
              {t.admin}
            </button>
          )}
        </nav>
      </header>

      {/* Main Container */}
      <main className="w-full max-w-lg mx-auto px-4 pt-20 pb-4">
        {errorMsg && (
          <div className="mb-4 p-3 bg-red-950/40 border border-red-500/20 text-red-300 text-xs rounded-xl flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
            <p className="font-mono">{errorMsg}</p>
          </div>
        )}
        {infoMsg && (
          <div className="mb-4 p-3 bg-emerald-950/40 border border-emerald-500/20 text-emerald-300 text-xs rounded-xl flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
            <p className="font-mono">{infoMsg}</p>
          </div>
        )}

        {renderScreen()}
      </main>

      {/* Footer System Operational status */}
      <footer className="w-full max-w-lg mx-auto px-4 py-6 border-t border-slateCustom/20 mt-12 flex flex-col items-center gap-3">
        <div className="flex items-center gap-2 font-mono text-[10px] text-slate-500">
          <span className="w-2 h-2 rounded-full bg-emerald-500 pulse-dot" />
          SYSTEM OPERATIONAL v2.4
        </div>
        <div className="flex gap-4 text-xxs text-slate-600 font-mono">
          <button onClick={() => setRoute("/support")} className="hover:text-champagne transition-colors">Support</button>
          <span>•</span>
          <button onClick={() => setRoute("/unlimited")} className="hover:text-champagne transition-colors">Unlimited Access</button>
        </div>
      </footer>
    </div>
  );
}

// ---------------------------------------------------------
// FUNNEL LOCKED SCREEN
// ---------------------------------------------------------
function FunnelLockedScreen({ t }: { t: (typeof i18n)["ru"] }) {
  const handleClose = () => {
    window.Telegram?.WebApp?.close();
  };

  return (
    <div className="flex flex-col items-center justify-center text-center gap-6 py-16 px-4">
      <ShieldAlert className="w-16 h-16 text-champagne/80" />
      <div className="flex flex-col gap-2">
        <h2 className="text-xl font-bold text-white">{t.funnel_locked_title}</h2>
        <p className="text-sm text-slate-400 leading-relaxed">{t.funnel_locked_desc}</p>
      </div>
      <button
        onClick={handleClose}
        className="magnetic-btn bg-champagne text-obsidian font-bold py-3 px-6 rounded-2xl"
      >
        {t.funnel_locked_bot}
      </button>
    </div>
  );
}

// ---------------------------------------------------------
// DASHBOARD SCREEN
// ---------------------------------------------------------
interface DashboardProps {
  user: any;
  statusInfo: any;
  settings: any;
  setRoute: (r: string) => void;
  onCheckSub: () => void;
  getResetCountdown: () => string;
  lang: "ru" | "en";
  t: any;
  hasFullAccess: boolean;
}

function DashboardScreen({ user, statusInfo, settings, setRoute, onCheckSub, getResetCountdown, lang, t, hasFullAccess }: DashboardProps) {
  // Entrances Animations with GSAP
  const dashboardRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.from(".fade-up-item", {
        y: 20,
        opacity: 0,
        stagger: 0.08,
        duration: 0.6,
        ease: "power3.out"
      });
    }, dashboardRef);
    return () => ctx.revert();
  }, []);

  const isUnlimited = user?.has_unlimited || user?.funnel_state === "UNLIMITED";
  const limitReached = statusInfo?.attempts_remaining <= 0 && !isUnlimited;
  const affiliateUrl = settings?.affiliate_ref_url || "https://example.com/ref";
  const promoCode = settings?.affiliate_promo_code || "AIBET776";

  const handleOpenAffiliate = () => {
    if (window.Telegram?.WebApp) {
      window.Telegram.WebApp.openLink(affiliateUrl);
    } else {
      window.open(affiliateUrl, "_blank");
    }
  };

  const handleCopyCode = () => {
    navigator.clipboard.writeText(promoCode);
    window.Telegram?.WebApp?.HapticFeedback.notificationOccurred("success");
    alert(lang === "ru" ? "Промокод скопирован!" : "Promo code copied!");
  };

  // Resolve funnel state to instruct user on the exact next step
  const renderFunnelGuides = () => {
    if (!user) return null;

    const state = user.funnel_state;

    // Helper for visual step checking
    const checkIcon = (passed: boolean) => {
      return passed ? (
        <CheckCircle2 className="w-5 h-5 text-champagne shrink-0" />
      ) : (
        <div className="w-5 h-5 rounded-full border border-slateCustom shrink-0" />
      );
    };

    // Subscribed Step
    const step1Passed = user.is_channel_subscribed || ["CHANNEL_SUBSCRIBED", "REGISTRATION_PENDING", "REGISTERED", "DEPOSIT_PENDING", "DEPOSIT_CONFIRMED", "ACTIVE", "LIMIT_EXCEEDED", "UNLIMITED"].includes(state);
    // Registered Step
    const step2Passed = user.is_registered || ["REGISTERED", "DEPOSIT_PENDING", "DEPOSIT_CONFIRMED", "ACTIVE", "LIMIT_EXCEEDED", "UNLIMITED"].includes(state);
    // Deposited Step
    const step3Passed = user.is_deposited || ["DEPOSIT_CONFIRMED", "ACTIVE", "LIMIT_EXCEEDED", "UNLIMITED"].includes(state);

    return (
      <div className="flex flex-col gap-4 mt-6">
        {/* Step 1: Channel Subscription */}
        <div className={`p-4 rounded-2xl border transition-all duration-300 ${step1Passed ? "bg-slateCustom/10 border-slateCustom/20 opacity-60" : "bg-slateCustom/30 border-champagne/20"}`}>
          <div className="flex items-start gap-3">
            {checkIcon(step1Passed)}
            <div className="flex-1">
              <h4 className="text-sm font-bold text-white">{t.funnel_sub}</h4>
              {!step1Passed && (
                <div className="mt-3 flex flex-col gap-2">
                  <a 
                    href={settings?.channel_url || "https://t.me/example"} 
                    target="_blank" 
                    rel="noreferrer"
                    className="magnetic-btn inline-flex items-center justify-center gap-2 bg-champagne text-obsidian text-xs font-bold py-2 px-4 rounded-xl"
                  >
                    <Crown className="w-3.5 h-3.5" /> Подписаться на канал
                  </a>
                  <button 
                    onClick={onCheckSub}
                    className="magnetic-btn border border-champagne/30 text-champagne text-xs font-bold py-2 px-4 rounded-xl hover:bg-champagne/5"
                  >
                    {t.funnel_sub_btn}
                  </button>
                </div>
              )}
              {step1Passed && <p className="text-xs text-slate-400 mt-1">{t.funnel_sub_ok}</p>}
            </div>
          </div>
        </div>

        {/* Step 2: Bookmaker Registration */}
        <div className={`p-4 rounded-2xl border transition-all duration-300 ${!step1Passed ? "opacity-30 pointer-events-none" : step2Passed ? "bg-slateCustom/10 border-slateCustom/20 opacity-60" : "bg-slateCustom/30 border-champagne/20"}`}>
          <div className="flex items-start gap-3">
            {checkIcon(step2Passed)}
            <div className="flex-1">
              <h4 className="text-sm font-bold text-white">{t.funnel_reg}</h4>
              <p className="text-xs text-slate-400 mt-1">{t.funnel_reg_desc}</p>
              {!step2Passed && step1Passed && (
                <div className="mt-3 flex flex-col gap-2.5">
                  <button 
                    onClick={handleOpenAffiliate}
                    className="magnetic-btn inline-flex items-center justify-center gap-2 bg-champagne text-obsidian text-xs font-bold py-2 px-4 rounded-xl"
                  >
                    {t.funnel_reg_btn} <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                  <div className="flex items-center justify-between bg-obsidian border border-slateCustom p-2 rounded-xl">
                    <span className="text-[11px] font-mono text-slate-400">{t.funnel_reg_code}</span>
                    <button 
                      onClick={handleCopyCode}
                      className="flex items-center gap-1.5 text-xs text-champagne font-bold font-mono hover:text-white"
                    >
                      {promoCode} <Copy className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Step 3: Deposit Verification */}
        <div className={`p-4 rounded-2xl border transition-all duration-300 ${!step2Passed ? "opacity-30 pointer-events-none" : step3Passed ? "bg-slateCustom/10 border-slateCustom/20 opacity-60" : "bg-slateCustom/30 border-champagne/20"}`}>
          <div className="flex items-start gap-3">
            {checkIcon(step3Passed)}
            <div className="flex-1">
              <h4 className="text-sm font-bold text-white">{t.funnel_dep}</h4>
              <p className="text-xs text-slate-400 mt-1">{t.funnel_dep_desc}</p>
              {!step3Passed && step2Passed && (
                <button 
                  onClick={handleOpenAffiliate}
                  className="magnetic-btn mt-3 inline-flex items-center justify-center gap-2 bg-champagne text-obsidian text-xs font-bold py-2 px-4 rounded-xl"
                >
                  {t.funnel_dep_btn}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div ref={dashboardRef} className="flex flex-col gap-6">
      {!hasFullAccess && (
        <div className="fade-up-item p-4 rounded-2xl border border-amber-500/30 bg-amber-950/20 flex items-start gap-3 text-left">
          <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <h3 className="text-sm font-bold text-amber-200">{t.funnel_locked_title}</h3>
            <p className="text-xs text-slate-400 mt-1">{t.funnel_locked_desc}</p>
          </div>
        </div>
      )}

      {/* Hero Header */}
      <div className="fade-up-item relative rounded-container-large overflow-hidden border border-champagne/10 min-h-[30vh] flex flex-col justify-end p-6 bg-gradient-to-t from-obsidian via-obsidian/60 to-transparent">
        <div className="absolute inset-0 z-0 bg-[url('https://images.unsplash.com/photo-1540747737956-37872404a82f?q=80&w=600')] bg-cover bg-center opacity-20 filter grayscale contrast-125" />
        
        <div className="relative z-10 flex flex-col gap-2 text-left">
          <div className="flex items-center gap-2">
            <Crown className="w-5 h-5 text-champagne animate-pulse" />
            <span className="font-mono text-xs text-champagne font-bold tracking-widest uppercase">PREMIUM SIGNAL ATELIER</span>
          </div>
          <h1 className="text-3xl font-black font-sans leading-none tracking-tight text-white m-0">
            «AI Анализ Ставок»
          </h1>
          <p className="text-xs italic text-slate-300 font-drama tracking-wide m-0">
            Precision modeling meets sporting intelligence.
          </p>
        </div>
      </div>

      {/* Attempts Counter & Can Analyze Callout */}
      <div className="fade-up-item bg-slateCustom/30 border border-slateCustom/40 p-5 rounded-container flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <div className="flex flex-col text-left">
            <span className="text-xs text-slate-400 font-mono uppercase tracking-wider">{t.attempts}</span>
            <span className="text-2xl font-bold font-sans text-white">
              {isUnlimited ? "∞" : `${statusInfo?.attempts_remaining || 0} / ${statusInfo?.daily_limit || 10}`}
            </span>
          </div>
          {isUnlimited ? (
            <div className="bg-champagne/10 border border-champagne/20 text-champagne font-bold font-sans text-xs px-3 py-1.5 rounded-full flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 fill-champagne" /> Premium Unlimited
            </div>
          ) : (
            limitReached && (
              <div className="flex flex-col items-end">
                <span className="bg-red-950/50 border border-red-500/20 text-red-400 font-mono text-[10px] px-2.5 py-1 rounded-full uppercase">
                  Limit Exceeded
                </span>
                <span className="text-[10px] text-slate-400 font-mono mt-1">{getResetCountdown()}</span>
              </div>
            )
          )}
        </div>

        <div className="h-px bg-slateCustom/30 my-1" />

        <div className="flex items-center gap-3 text-left">
          {statusInfo?.can_analyze ? (
            <>
              <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0 pulse-dot" />
              <p className="text-xs text-slate-300">{t.can_analyze}</p>
            </>
          ) : (
            <>
              <ShieldAlert className="w-5 h-5 text-red-400 shrink-0" />
              <p className="text-xs text-slate-300">{t.cannot_analyze}</p>
            </>
          )}
        </div>
      </div>

      {/* Interactive Value Propositions Bento Cards */}
      <div className="fade-up-item grid grid-cols-1 gap-4">
        {/* Card 1: Diagnostic Shuffler */}
        <div className="bg-slateCustom/25 border border-slateCustom/30 p-5 rounded-container flex flex-col gap-4 text-left relative overflow-hidden">
          <div>
            <h3 className="text-sm font-bold text-champagne font-sans uppercase tracking-wider">01 // DATA MODEL INGESTION</h3>
            <p className="text-xs text-slate-400 mt-1">Точный AI-анализ исходов на основе свежих спортивных данных.</p>
          </div>
          <DiagnosticShuffler lang={lang} />
        </div>

        {/* Card 2: Telemetry Typewriter */}
        <div className="bg-slateCustom/25 border border-slateCustom/30 p-5 rounded-container flex flex-col gap-4 text-left relative overflow-hidden">
          <div>
            <h3 className="text-sm font-bold text-champagne font-sans uppercase tracking-wider">02 // TELEMETRY EXTRACTION</h3>
            <p className="text-xs text-slate-400 mt-1">Распознавание скриншотов любых букмекерских контор за секунды.</p>
          </div>
          <TelemetryTypewriter lang={lang} />
        </div>

        {/* Card 3: Cursor Protocol Scheduler */}
        <div className="bg-slateCustom/25 border border-slateCustom/30 p-5 rounded-container flex flex-col gap-4 text-left relative overflow-hidden">
          <div>
            <h3 className="text-sm font-bold text-champagne font-sans uppercase tracking-wider">03 // RISK MITIGATION ENGINE</h3>
            <p className="text-xs text-slate-400 mt-1">Подробная аргументация прогнозов и оценка рисков.</p>
          </div>
          <CursorProtocolScheduler lang={lang} />
        </div>
      </div>

      {/* Action CTA Buttons */}
      <div className="fade-up-item flex flex-col gap-3 mt-4">
        {hasFullAccess && statusInfo?.can_analyze && !limitReached ? (
          <button 
            onClick={() => setRoute("/analyze")} 
            className="magnetic-btn w-full bg-champagne text-obsidian font-extrabold font-sans py-4 px-6 rounded-2xl flex items-center justify-center gap-2 shadow-xl interactive-lift"
          >
            <Camera className="w-5 h-5" /> {t.cta_analyze}
          </button>
        ) : hasFullAccess ? (
          <button 
            onClick={() => setRoute("/unlimited")} 
            className="magnetic-btn w-full bg-gradient-to-r from-champagne via-amber-500 to-champagne text-obsidian font-extrabold font-sans py-4 px-6 rounded-2xl flex items-center justify-center gap-2 shadow-xl interactive-lift"
          >
            <Crown className="w-5 h-5 fill-obsidian" /> {t.cta_get_unlimited}
          </button>
        ) : null}
      </div>

      {/* Funnel Steps State Machine */}
      <div className="fade-up-item text-left mt-4 border-t border-slateCustom/20 pt-4">
        <h3 className="text-base font-bold font-sans text-white">Статус воронки активации</h3>
        <p className="text-xs text-slate-400 mt-1">
          Выполните все шаги для разблокировки безлимитного искусственного интеллекта.
        </p>
        {renderFunnelGuides()}
      </div>
    </div>
  );
}

// ---------------------------------------------------------
// CARD 1: DIAGNOSTIC SHUFFLER COMPONENT
// ---------------------------------------------------------
function DiagnosticShuffler({ lang }: { lang: "ru" | "en" }) {
  const cardsRu = [
    "Сбор последних новостей о командах...",
    "Анализ статистики личных встреч...",
    "Оценка движения коэффициентов букмекеров..."
  ];
  const cardsEn = [
    "Compiling team news & alerts...",
    "Analyzing historical head-to-head stats...",
    "Parsing odds fluctuations in bookmakers..."
  ];

  const initialCards = lang === "ru" ? cardsRu : cardsEn;
  const [items, setItems] = useState<string[]>(initialCards);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const timer = setInterval(() => {
      // Bounce animation of elements
      gsap.to(".shuffle-card", {
        y: -15,
        opacity: 0,
        duration: 0.35,
        ease: "power2.inOut",
        stagger: 0.05,
        onComplete: () => {
          setItems(prev => {
            const next = [...prev];
            const popped = next.pop();
            if (popped) next.unshift(popped);
            return next;
          });
          gsap.fromTo(".shuffle-card", 
            { y: 15, opacity: 0 },
            { y: 0, opacity: 1, duration: 0.45, ease: "back.out(1.5)" }
          );
        }
      });
    }, 4500);

    return () => clearInterval(timer);
  }, []);

  return (
    <div ref={containerRef} className="h-28 flex flex-col gap-2 justify-center py-2 relative">
      {items.map((item, idx) => {
        // Render overlapping cards with depth
        const scale = 1 - idx * 0.05;
        const opacity = 1 - idx * 0.35;
        const zIndex = 10 - idx;
        const top = idx * 12;

        return (
          <div 
            key={item} 
            className="shuffle-card absolute left-0 right-0 p-3 rounded-xl border border-champagne/10 bg-obsidian/90 shadow-lg flex items-center gap-3 transition-all duration-300"
            style={{
              transform: `scale(${scale})`,
              opacity: opacity,
              zIndex: zIndex,
              top: `${top}px`,
            }}
          >
            <div className="w-2 h-2 rounded-full bg-champagne animate-pulse" />
            <span className="text-[11px] font-mono text-slate-300 leading-snug">{item}</span>
          </div>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------
// CARD 2: TELEMETRY TYPEWRITER COMPONENT
// ---------------------------------------------------------
function TelemetryTypewriter({ lang }: { lang: "ru" | "en" }) {
  const linesRu = [
    "[SYSTEM] Сканирование изображения купона...",
    "[SYSTEM] Найден матч: Arsenal vs Chelsea",
    "[SYSTEM] Фиксация коэффициента: 1.92",
    "[SYSTEM] Поиск спортивных инсайдов...",
    "[SYSTEM] Оценка рисков: СРЕДНИЙ"
  ];
  const linesEn = [
    "[SYSTEM] Scanning bet coupon screenshot...",
    "[SYSTEM] Match found: Arsenal vs Chelsea",
    "[SYSTEM] Locked odd: 1.92",
    "[SYSTEM] Checking sport headlines...",
    "[SYSTEM] Estimating margins: MEDIUM RISK"
  ];

  const lines = lang === "ru" ? linesRu : linesEn;
  const [currentLineIdx, setLineIdx] = useState(0);
  const [displayText, setDisplayText] = useState("");
  const timerRef = useRef<any>(null);

  useEffect(() => {
    let charIdx = 0;
    const targetText = lines[currentLineIdx];
    setDisplayText("");

    const typeChar = () => {
      if (charIdx < targetText.length) {
        setDisplayText(targetText.substring(0, charIdx + 1));
        charIdx++;
        timerRef.current = setTimeout(typeChar, 35);
      } else {
        // Finished typing this line, wait 2.5s and move to next
        timerRef.current = setTimeout(() => {
          setLineIdx((prev) => (prev + 1) % lines.length);
        }, 2500);
      }
    };

    typeChar();

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [currentLineIdx, lang]);

  return (
    <div className="bg-obsidian border border-slateCustom/60 rounded-xl p-3.5 h-20 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <span className="w-1.5 h-1.5 rounded-full bg-red-500 pulse-dot" />
        <span className="text-[11px] font-mono text-slate-300 leading-none">{displayText}</span>
        <span className="w-1 h-3.5 bg-champagne animate-pulse shrink-0" />
      </div>
      <div className="text-[9px] font-mono text-slate-500 uppercase tracking-widest">LIVE FEED</div>
    </div>
  );
}

// ---------------------------------------------------------
// CARD 3: CURSOR PROTOCOL SCHEDULER COMPONENT
// ---------------------------------------------------------
function CursorProtocolScheduler({ lang }: { lang: "ru" | "en" }) {
  const days = ["S", "M", "T", "W", "T", "F", "S"];
  const [activeDay, setActiveDay] = useState<number | null>(null);
  const [saveClicked, setSaveClicked] = useState(false);
  const cursorRef = useRef<HTMLDivElement>(null);
  const schedulerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const cycleCursor = () => {
      if (!cursorRef.current || !schedulerRef.current) return;

      const cursor = cursorRef.current;
      const dayCells = schedulerRef.current.querySelectorAll(".day-cell");
      const saveBtn = schedulerRef.current.querySelector(".save-btn") as HTMLElement;

      if (!dayCells.length || !saveBtn) return;

      // Reset states
      setActiveDay(null);
      setSaveClicked(false);

      // Random target day
      const targetDayIdx = 3; // Wednesday (W)
      const targetCell = dayCells[targetDayIdx] as HTMLElement;

      const tl = gsap.timeline({
        repeat: -1,
        repeatDelay: 2
      });

      // 1. Enter cursor
      tl.fromTo(cursor, 
        { x: -50, y: 50, opacity: 0 },
        { x: targetCell.offsetLeft + 10, y: targetCell.offsetTop + 10, opacity: 1, duration: 1.2, ease: "power2.out" }
      );

      // 2. Click cell
      tl.to(cursor, { scale: 0.8, duration: 0.15 })
        .call(() => {
          setActiveDay(targetDayIdx);
          window.Telegram?.WebApp?.HapticFeedback.selectionChanged();
        })
        .to(cursor, { scale: 1, duration: 0.15 });

      // 3. Move to Save button
      tl.to(cursor, { 
        x: saveBtn.offsetLeft + 40, 
        y: saveBtn.offsetTop + 12, 
        duration: 1.0, 
        ease: "power2.inOut" 
      });

      // 4. Click Save
      tl.to(cursor, { scale: 0.8, duration: 0.15 })
        .call(() => {
          setSaveClicked(true);
          window.Telegram?.WebApp?.HapticFeedback.notificationOccurred("success");
        })
        .to(cursor, { scale: 1, duration: 0.15 });

      // 5. Fade out cursor
      tl.to(cursor, { opacity: 0, duration: 0.4 });
    };

    cycleCursor();
  }, []);

  return (
    <div ref={schedulerRef} className="relative bg-obsidian border border-slateCustom/60 rounded-xl p-3 flex flex-col gap-3 h-24 select-none">
      {/* Calendar Grid */}
      <div className="flex justify-between items-center px-1">
        {days.map((day, idx) => (
          <div 
            key={idx} 
            className={`day-cell w-7 h-7 rounded-lg border text-xs font-bold flex items-center justify-center transition-all duration-300 ${activeDay === idx ? "bg-champagne/15 border-champagne text-champagne" : "border-slateCustom/30 text-slate-400"}`}
          >
            {day}
          </div>
        ))}
      </div>

      {/* Action btn */}
      <div className="flex justify-between items-center mt-0.5">
        <span className="text-[10px] text-slate-500 font-mono">
          {lang === "ru" ? "АВТО-АНАЛИЗ РИСКА" : "AUTOMATED MARGINING"}
        </span>
        <button 
          className={`save-btn text-[10px] font-bold font-mono px-3 py-1.5 rounded-lg border transition-all duration-300 ${saveClicked ? "bg-emeraldCustom/10 border-emerald-500 text-emerald-400" : "border-champagne/30 text-champagne"}`}
        >
          {saveClicked ? (lang === "ru" ? "ГОТОВО ✓" : "RESOLVED ✓") : (lang === "ru" ? "СОХРАНИТЬ" : "SAVE CONFIG")}
        </button>
      </div>

      {/* Simulated SVG Mouse Cursor */}
      <div 
        ref={cursorRef} 
        className="absolute pointer-events-none z-30 transform -translate-x-1/2 -translate-y-1/2"
        style={{ opacity: 0 }}
      >
        <svg width="15" height="15" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M0 0V100L29.3333 70.6667L97.3333 70.6667L0 0Z" fill="#C9A84C" stroke="black" strokeWidth="5"/>
        </svg>
      </div>
    </div>
  );
}

// ---------------------------------------------------------
// UPLOAD SCREEN ( Vision -> Search -> Synthesis loader )
// ---------------------------------------------------------
interface UploadProps {
  token: string | null;
  onSuccess: (id: string) => void;
  lang: "ru" | "en";
  t: any;
}

function UploadScreen({ token, onSuccess, lang, t }: UploadProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadStep, setUploadStep] = useState<number>(0); // 0: Idle, 1: Vision, 2: Search, 3: Synthesis
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Auto handle main button in Telegram Web App
  useEffect(() => {
    const mainBtn = window.Telegram?.WebApp?.MainButton;
    if (!mainBtn) return;

    if (selectedFile && !isUploading) {
      mainBtn.setParams({
        text: lang === "ru" ? "ОТПРАВИТЬ НА АНАЛИЗ" : "SEND FOR ANALYSIS",
        color: "#C9A84C",
        text_color: "#0D0D12",
        is_visible: true,
        is_active: true
      });
    } else {
      mainBtn.hide();
    }

    const handleMainClick = () => {
      handleSubmitAnalysis();
    };

    mainBtn.onClick(handleMainClick);
    return () => {
      mainBtn.offClick(handleMainClick);
      mainBtn.hide();
    };
  }, [selectedFile, isUploading, lang]);

  const handleFileChange = (file: File) => {
    if (!file.type.startsWith("image/")) {
      setErrorMsg(lang === "ru" ? "Пожалуйста, выберите файл изображения (PNG, JPEG)" : "Please select an image file");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setErrorMsg(lang === "ru" ? "Файл слишком большой (макс 10 МБ)" : "File too large (max 10MB)");
      return;
    }
    setErrorMsg(null);
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleSubmitAnalysis = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setErrorMsg(null);
    setUploadStep(1); // Vision step

    // Cycle progress text simulating vision-search-synthesis (up to 15s max)
    const visionTimer = setTimeout(() => setUploadStep(2), 4500); // Search step
    const searchTimer = setTimeout(() => setUploadStep(3), 9000); // Synthesis step

    const formData = new FormData();
    formData.append("screenshot", selectedFile);

    try {
      const headers = new Headers();
      if (token) {
        headers.set("Authorization", `Bearer ${token}`);
      }
      const initData = window.Telegram?.WebApp?.initData;
      if (initData) {
        headers.set("X-Telegram-Init-Data", initData);
      }

      const res = await fetch(`${API_BASE}/user/analyze`, {
        method: "POST",
        headers,
        body: formData,
      });

      // Clear fake progress trackers
      clearTimeout(visionTimer);
      clearTimeout(searchTimer);

      if (!res.ok) {
        const errorDetail = await res.json().catch(() => ({ detail: "Analysis failed" }));
        throw new Error(errorDetail.detail || `Server responded with ${res.status}`);
      }

      const data = await res.json();
      
      // Haptic feedback successful
      window.Telegram?.WebApp?.HapticFeedback.notificationOccurred("success");
      onSuccess(data.id);
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.message || "Failed to analyze screenshot");
      setIsUploading(false);
      window.Telegram?.WebApp?.HapticFeedback.notificationOccurred("error");
    }
  };

  return (
    <div className="flex flex-col gap-6 text-left">
      <h2 className="text-2xl font-bold font-sans text-white">{t.upload_title}</h2>
      
      {errorMsg && (
        <div className="p-3 bg-red-950/30 border border-red-500/20 text-red-300 text-xs rounded-xl flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
          <p className="font-mono">{errorMsg}</p>
        </div>
      )}

      {isUploading ? (
        // Premium Processing Interface
        <div className="p-6 bg-slateCustom/20 border border-slateCustom/30 rounded-container flex flex-col items-center justify-center min-h-[35vh] gap-6 text-center">
          <RefreshCw className="w-10 h-10 text-champagne animate-spin" />
          
          <div className="flex flex-col gap-2">
            <h3 className="text-base font-bold font-sans text-white">
              {uploadStep === 1 && t.uploading_vision}
              {uploadStep === 2 && t.uploading_search}
              {uploadStep === 3 && t.uploading_synthesis}
            </h3>
            <p className="text-xs text-slate-400 font-mono">
              {uploadStep === 1 && "Vision pipeline parsing betting slip..."}
              {uploadStep === 2 && "Querying live odds and team injuries..."}
              {uploadStep === 3 && "Running LLM agent model for optimal betting picks..."}
            </p>
          </div>

          {/* Core visual progress indicator bar */}
          <div className="w-full max-w-xs h-1 bg-slateCustom rounded-full overflow-hidden">
            <div className="h-full bg-champagne animate-progress" />
          </div>
        </div>
      ) : (
        // Dropzone Interface
        <div className="flex flex-col gap-5">
          <div 
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-container p-8 flex flex-col items-center justify-center min-h-[30vh] gap-4 cursor-pointer transition-all duration-300 ${isDragging ? "border-champagne bg-champagne/5" : previewUrl ? "border-slateCustom/60 bg-slateCustom/10" : "border-slateCustom/40 bg-slateCustom/5 hover:border-champagne/30"}`}
          >
            {previewUrl ? (
              <div className="relative w-full max-h-56 overflow-hidden rounded-xl">
                <img src={previewUrl} className="w-full h-full object-contain" alt="Coupon Preview" />
              </div>
            ) : (
              <>
                <Upload className="w-10 h-10 text-slate-500" />
                <div className="text-center flex flex-col gap-1">
                  <p className="text-sm font-bold text-slate-300">
                    {isDragging ? t.upload_drop : t.upload_select}
                  </p>
                  <p className="text-xxs text-slate-500 max-w-[240px] leading-normal">{t.upload_desc}</p>
                </div>
              </>
            )}

            <div className="flex gap-3">
              <label className="magnetic-btn bg-slateCustom border border-slateCustom/60 hover:border-champagne/20 text-white font-bold font-sans text-xs px-4 py-2.5 rounded-xl cursor-pointer">
                {t.upload_select}
                <input 
                  type="file" 
                  accept="image/*" 
                  className="hidden" 
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) handleFileChange(e.target.files[0]);
                  }}
                />
              </label>
              
              <label className="magnetic-btn bg-slateCustom border border-slateCustom/60 hover:border-champagne/20 text-white font-bold font-sans text-xs px-4 py-2.5 rounded-xl cursor-pointer flex items-center gap-1.5">
                <Camera className="w-3.5 h-3.5" /> {t.upload_camera}
                <input 
                  type="file" 
                  accept="image/*" 
                  capture="environment"
                  className="hidden" 
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) handleFileChange(e.target.files[0]);
                  }}
                />
              </label>
            </div>
          </div>

          {selectedFile && (
            <button 
              onClick={handleSubmitAnalysis}
              className="magnetic-btn w-full bg-champagne text-obsidian font-extrabold font-sans py-4 rounded-xl shadow-xl flex items-center justify-center gap-2"
            >
              <Zap className="w-4 h-4" /> ОТПРАВИТЬ НА АНАЛИЗ
            </button>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------
// RESULT SCREEN ( Odds, Probability, Explanation, Arguments )
// ---------------------------------------------------------
interface ResultProps {
  analysisId: string;
  apiCall: (endpoint: string, options?: any) => Promise<any>;
  activeAnalysis: any;
  setActiveAnalysis: (a: any) => void;
  setRoute: (r: string) => void;
  t: any;
}

function ResultScreen({ analysisId, apiCall, activeAnalysis, setActiveAnalysis, setRoute, t }: ResultProps) {
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    const loadAnalysis = async () => {
      try {
        setLoading(true);
        const data = await apiCall(`/user/analyses/${analysisId}`);
        setActiveAnalysis(data);
      } catch (err: any) {
        setErrorMsg(err.message || "Failed to fetch analysis details");
      } finally {
        setLoading(false);
      }
    };
    loadAnalysis();
  }, [analysisId]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[40vh] gap-4">
        <RefreshCw className="w-8 h-8 text-champagne animate-spin" />
        <p className="text-slate-400 text-xs font-mono">{t.loading}</p>
      </div>
    );
  }

  if (errorMsg || !activeAnalysis) {
    return (
      <div className="p-6 bg-red-950/20 border border-red-500/20 rounded-container text-center flex flex-col gap-3">
        <AlertCircle className="w-8 h-8 text-red-400 mx-auto" />
        <h3 className="text-lg font-bold text-white">Error</h3>
        <p className="text-xs text-red-300 font-mono">{errorMsg || "Analysis details not available"}</p>
        <button onClick={() => setRoute("/")} className="magnetic-btn mt-2 border border-champagne/20 text-champagne py-2.5 px-5 rounded-xl font-bold font-sans">
          {t.result_back}
        </button>
      </div>
    );
  }

  const { recommendation, coefficient, probability_percent, risk, confidence, arguments: argsList, explanation } = activeAnalysis;

  // Visual highlights based on Risk value
  const getRiskBadgeColor = (riskVal: string) => {
    switch (riskVal?.toLowerCase()) {
      case "low": return "bg-emeraldCustom/10 border-emerald-500/30 text-emerald-400";
      case "high": return "bg-red-950/40 border-red-500/30 text-red-400";
      default: return "bg-amber-950/40 border-amber-500/30 text-amber-400";
    }
  };

  return (
    <div className="flex flex-col gap-6 text-left animate-fade-in">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold font-sans text-white">{t.result_title}</h2>
        <span className="text-[10px] font-mono text-slate-500">ID: {analysisId.substring(0, 8)}...</span>
      </div>

      {/* Main Signal Card (The Instrument Design) */}
      <div className="p-6 bg-slateCustom/25 border border-champagne/15 rounded-container flex flex-col gap-5 shadow-2xl relative overflow-hidden">
        {/* Decorative gold accent corner */}
        <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl from-champagne/10 to-transparent pointer-events-none" />

        {/* Prediction recommendation */}
        <div className="flex flex-col gap-1.5">
          <span className="text-xxs text-slate-400 font-mono uppercase tracking-widest">{t.result_bet}</span>
          <span className="text-2xl font-black font-sans text-white">{recommendation || "N/A"}</span>
        </div>

        {/* Odds & Confidence Grid */}
        <div className="grid grid-cols-2 gap-4">
          <div className="p-3 bg-obsidian/40 border border-slateCustom/40 rounded-xl flex flex-col">
            <span className="text-xxs text-slate-500 font-mono uppercase tracking-wider">{t.result_coef}</span>
            <span className="text-lg font-bold font-sans text-champagne">{coefficient ? `x${coefficient}` : "N/A"}</span>
          </div>

          <div className="p-3 bg-obsidian/40 border border-slateCustom/40 rounded-xl flex flex-col">
            <span className="text-xxs text-slate-500 font-mono uppercase tracking-wider">{t.result_probability}</span>
            <span className="text-lg font-bold font-sans text-white">{probability_percent ? `${probability_percent}%` : "N/A"}</span>
          </div>
        </div>

        {/* Risk & Confidence Badges */}
        <div className="flex gap-3">
          <div className={`flex-1 p-2.5 rounded-xl border text-center font-mono text-[10px] uppercase font-bold ${getRiskBadgeColor(risk)}`}>
            {t.result_risk} {risk || "MEDIUM"}
          </div>

          <div className="flex-1 p-2.5 bg-slateCustom/40 border border-slateCustom/60 text-slate-300 rounded-xl text-center font-mono text-[10px] uppercase font-bold">
            {t.result_confidence}: {confidence || "MEDIUM"}
          </div>
        </div>

        <div className="h-px bg-slateCustom/30 my-1" />

        {/* Arguments bullet list */}
        <div className="flex flex-col gap-2">
          <span className="text-xxs text-slate-500 font-mono uppercase tracking-wider">{t.result_args}</span>
          <ul className="flex flex-col gap-2 p-0 m-0">
            {argsList && argsList.length > 0 ? (
              argsList.map((arg: string, idx: number) => (
                <li key={idx} className="flex gap-2 text-xs text-slate-300 leading-normal">
                  <span className="text-champagne shrink-0">•</span>
                  <span>{arg}</span>
                </li>
              ))
            ) : (
              <li className="text-xs text-slate-500 italic">No detailed arguments parsed.</li>
            )}
          </ul>
        </div>

        <div className="h-px bg-slateCustom/30 my-1" />

        {/* Explanation text */}
        <div className="flex flex-col gap-2">
          <span className="text-xxs text-slate-500 font-mono uppercase tracking-wider">AI Explanation</span>
          <p className="text-xs text-slate-300 leading-relaxed font-sans font-light">
            {explanation || "Detailed analysis was generated successfully based on historic events."}
          </p>
        </div>
      </div>

      {/* Action return button */}
      <button 
        onClick={() => setRoute("/")}
        className="magnetic-btn w-full border border-champagne/30 text-champagne font-bold font-sans py-3.5 rounded-xl flex items-center justify-center gap-2 hover:bg-champagne/5"
      >
        <ArrowLeft className="w-4 h-4" /> {t.result_back}
      </button>

      {/* Visible disclaimer */}
      <p className="text-[10px] text-slate-500 font-mono text-center leading-normal max-w-xs mx-auto">
        {t.result_disclaimer}
      </p>
    </div>
  );
}

// ---------------------------------------------------------
// HISTORY SCREEN
// ---------------------------------------------------------
interface HistoryProps {
  apiCall: (endpoint: string) => Promise<any>;
  setRoute: (r: string) => void;
  setActiveAnalysis: (a: any) => void;
  lang: "ru" | "en";
  t: any;
}

function HistoryScreen({ apiCall, setRoute, setActiveAnalysis, lang, t }: HistoryProps) {
  const [list, setList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        setLoading(true);
        const data = await apiCall("/user/analyses");
        setList(data || []);
      } catch (e) {
        console.error("Failed to load analyses history", e);
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, []);

  const formatDate = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString(lang === "ru" ? "ru-RU" : "en-US", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit"
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="flex flex-col gap-6 text-left">
      <h2 className="text-2xl font-bold font-sans text-white">{t.history}</h2>

      {loading ? (
        <div className="flex flex-col items-center justify-center min-h-[30vh] gap-3">
          <RefreshCw className="w-8 h-8 text-champagne animate-spin" />
          <span className="text-slate-400 text-xs font-mono">{t.loading}</span>
        </div>
      ) : list.length === 0 ? (
        <div className="p-8 bg-slateCustom/15 border border-slateCustom/25 rounded-container text-center text-slate-400 flex flex-col items-center gap-3">
          <HistoryIcon className="w-8 h-8 text-slate-500" />
          <p className="text-xs font-mono">
            {lang === "ru" ? "У вас пока нет истории анализов." : "You have no analysis history yet."}
          </p>
          <button 
            onClick={() => setRoute("/analyze")} 
            className="magnetic-btn border border-champagne/30 text-champagne text-xs font-bold py-2 px-4 rounded-xl mt-2 hover:bg-champagne/5"
          >
            {t.cta_analyze}
          </button>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {list.map((item) => (
            <div 
              key={item.id}
              onClick={() => {
                setActiveAnalysis(item);
                setRoute(`/analyze/result/${item.id}`);
              }}
              className="p-4 bg-slateCustom/20 border border-slateCustom/30 hover:border-champagne/25 rounded-2xl flex items-center justify-between cursor-pointer transition-all duration-200 interactive-lift"
            >
              <div className="flex flex-col gap-1">
                <span className="text-xs font-bold text-white leading-snug">
                  {item.recommendation || "N/A"}
                </span>
                <div className="flex items-center gap-2 text-[10px] font-mono text-slate-500">
                  <span>{formatDate(item.created_at)}</span>
                  <span>•</span>
                  <span>odds: x{item.coefficient || "N/A"}</span>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-xxs text-champagne font-mono font-bold">{item.probability_percent}%</span>
                <ArrowRight className="w-4 h-4 text-slate-500" />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------
// PROFILE SCREEN
// ---------------------------------------------------------
interface ProfileProps {
  user: any;
  lang: "ru" | "en";
  onLangChange: (l: "ru" | "en") => void;
  t: any;
}

function ProfileScreen({ user, lang, onLangChange, t }: ProfileProps) {
  if (!user) return null;

  return (
    <div className="flex flex-col gap-6 text-left">
      <h2 className="text-2xl font-bold font-sans text-white">{t.profile}</h2>

      {/* User Information Card */}
      <div className="p-5 bg-slateCustom/25 border border-slateCustom/30 rounded-container flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-champagne/10 border border-champagne/20 flex items-center justify-center text-champagne">
            <UserIcon className="w-6 h-6" />
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-bold text-white">@{user.username || "Anonymous"}</span>
            <span className="text-[10px] font-mono text-slate-500">TG ID: {user.telegram_id}</span>
          </div>
        </div>

        <div className="h-px bg-slateCustom/30" />

        {/* System States details */}
        <div className="flex flex-col gap-2.5 font-mono text-xs text-slate-300">
          <div className="flex justify-between">
            <span className="text-slate-500">{t.profile_status}</span>
            <span className="text-white font-bold">{user.has_unlimited ? "Premium Unlimited" : "Standard Free"}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">{t.profile_state}</span>
            <span className="text-champagne font-bold">{user.funnel_state}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">{t.profile_registered}</span>
            <span className="text-white">{user.is_registered ? t.yes : t.no}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">{t.profile_deposited}</span>
            <span className="text-white">{user.is_deposited ? t.yes : t.no}</span>
          </div>
        </div>
      </div>

      {/* Language Toggle */}
      <div className="p-5 bg-slateCustom/20 border border-slateCustom/30 rounded-container flex flex-col gap-3">
        <span className="text-xs font-bold text-white flex items-center gap-2">
          <Languages className="w-4 h-4 text-champagne" /> {t.profile_lang}
        </span>
        
        <div className="flex gap-2">
          <button 
            onClick={() => onLangChange("ru")}
            className={`flex-1 py-2.5 rounded-xl border font-bold text-xs transition-all duration-300 ${lang === "ru" ? "bg-champagne/10 border-champagne text-champagne" : "border-slateCustom/30 text-slate-400"}`}
          >
            Русский (RU)
          </button>
          <button 
            onClick={() => onLangChange("en")}
            className={`flex-1 py-2.5 rounded-xl border font-bold text-xs transition-all duration-300 ${lang === "en" ? "bg-champagne/10 border-champagne text-champagne" : "border-slateCustom/30 text-slate-400"}`}
          >
            English (EN)
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------
// UNLIMITED / PRICING SCREEN
// ---------------------------------------------------------
interface UnlimitedProps {
  user: any;
  settings: any;
  apiCall: (endpoint: string, options?: any) => Promise<any>;
  t: any;
}

function UnlimitedScreen({ user, settings, apiCall, t }: UnlimitedProps) {
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const price = settings?.unlimited_price_amount || "4900";
  const currency = (settings?.unlimited_price_currency || "rub").toUpperCase();

  const handlePurchase = async () => {
    try {
      setLoading(true);
      setErrorMsg(null);
      
      const order = await apiCall("/payments/unlimited/create", { method: "POST" });
      if (order.error) {
        throw new Error(order.error);
      }

      const invoiceUrl = order.webapp_payment_url || order.payment_url;
      if (!invoiceUrl) {
        throw new Error("Payment link not available. Contact admin.");
      }

      if (window.Telegram?.WebApp) {
        window.Telegram.WebApp.openLink(invoiceUrl);
      } else {
        window.open(invoiceUrl, "_blank");
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to initialize payment");
    } finally {
      setLoading(false);
    }
  };

  const isUnlimited = user?.has_unlimited || user?.funnel_state === "UNLIMITED";

  return (
    <div className="flex flex-col gap-6 text-left">
      <h2 className="text-2xl font-bold font-sans text-white">{t.unlimited}</h2>

      {errorMsg && (
        <div className="p-3 bg-red-950/30 border border-red-500/20 text-red-300 text-xs rounded-xl flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
          <p className="font-mono">{errorMsg}</p>
        </div>
      )}

      <div className="p-6 bg-slateCustom/25 border border-champagne/20 rounded-container flex flex-col gap-5 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-champagne/10 to-transparent pointer-events-none" />
        
        <Crown className="w-10 h-10 text-champagne" />

        <div className="flex flex-col gap-1.5">
          <h3 className="text-lg font-bold text-white font-sans">{t.unlimited_title}</h3>
          <p className="text-xs text-slate-400 leading-relaxed font-light">{t.unlimited_desc}</p>
        </div>

        <div className="h-px bg-slateCustom/30 my-1" />

        {isUnlimited ? (
          <div className="p-4 bg-emeraldCustom/10 border border-emerald-500/20 rounded-xl text-center text-xs text-emerald-400 font-bold font-sans">
            {t.unlimited_already}
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between font-mono text-sm">
              <span className="text-slate-500">{t.unlimited_price}</span>
              <span className="text-xl font-bold text-champagne">{price} {currency}</span>
            </div>

            <button 
              onClick={handlePurchase}
              disabled={loading}
              className="magnetic-btn w-full bg-champagne text-obsidian font-extrabold font-sans py-4 rounded-xl shadow-xl flex items-center justify-center gap-2"
            >
              {loading ? <RefreshCw className="w-5 h-5 animate-spin" /> : <Zap className="w-5 h-5" />} 
              {t.unlimited_pay_btn}
            </button>
          </>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------
// SUPPORT SCREEN
// ---------------------------------------------------------
interface SupportProps {
  settings: any;
  lang: "ru" | "en";
  t: any;
}

function SupportScreen({ settings, lang, t }: SupportProps) {
  const supportUrl = settings?.support_url || "https://t.me/example";

  const handleSupportOpen = () => {
    if (window.Telegram?.WebApp) {
      window.Telegram.WebApp.openLink(supportUrl);
    } else {
      window.open(supportUrl, "_blank");
    }
  };

  return (
    <div className="flex flex-col gap-6 text-left">
      <h2 className="text-2xl font-bold font-sans text-white">{t.support_btn}</h2>

      <div className="p-6 bg-slateCustom/25 border border-slateCustom/30 rounded-container flex flex-col gap-4 text-center">
        <HelpCircle className="w-10 h-10 text-champagne mx-auto" />
        <h3 className="text-base font-bold text-white font-sans">{t.support_btn}</h3>
        <p className="text-xs text-slate-400 max-w-xs mx-auto leading-relaxed">{t.support_desc}</p>
        
        <button 
          onClick={handleSupportOpen}
          className="magnetic-btn w-full bg-slateCustom border border-champagne/30 text-champagne font-bold font-sans py-3.5 rounded-xl hover:bg-champagne/10 mt-3"
        >
          {lang === "ru" ? "Открыть Чат Поддержки" : "Open Support Chat"}
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------
// ADMIN SCREEN
// ---------------------------------------------------------
interface AdminHubProps {
  user: any;
  apiCall: (endpoint: string, options?: any) => Promise<any>;
}

function AdminHubScreen({ user, apiCall }: AdminHubProps) {
  const [subTab, setSubTab] = useState<"stats" | "broadcast" | "affiliate" | "unlimited" | "settings" | "postback">("stats");

  if (!user || user.telegram_id !== 7649494487) {
    return <div className="text-center py-10 font-mono text-sm text-red-400">Forbidden - Admin check failed</div>;
  }

  return (
    <div className="flex flex-col gap-5 text-left">
      <div className="flex items-center gap-2 border-b border-slateCustom/20 pb-3">
        <SettingsIcon className="w-6 h-6 text-champagne" />
        <h2 className="text-2xl font-bold font-sans text-white">Админ-Панель</h2>
      </div>

      {/* Admin Tab buttons */}
      <div className="flex flex-wrap gap-2">
        {(["stats", "broadcast", "affiliate", "unlimited", "settings", "postback"] as const).map((tab) => (
          <button 
            key={tab}
            onClick={() => setSubTab(tab)}
            className={`text-xxs font-bold font-mono px-3 py-2 rounded-lg border transition-all duration-150 uppercase ${subTab === tab ? "bg-champagne text-obsidian border-champagne" : "border-slateCustom/40 text-slate-400"}`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Render subcomponents based on selected admin tab */}
      <div className="p-5 bg-slateCustom/20 border border-slateCustom/30 rounded-container">
        {subTab === "stats" && <AdminStatsTab apiCall={apiCall} />}
        {subTab === "broadcast" && <AdminBroadcastTab apiCall={apiCall} />}
        {subTab === "affiliate" && <AdminAffiliateTab apiCall={apiCall} />}
        {subTab === "unlimited" && <AdminUnlimitedTab apiCall={apiCall} />}
        {subTab === "settings" && <AdminSettingsTab apiCall={apiCall} />}
        {subTab === "postback" && <AdminPostbackTab apiCall={apiCall} />}
      </div>
    </div>
  );
}

// Stats Subtab
function AdminStatsTab({ apiCall }: { apiCall: any }) {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadStats = async () => {
      try {
        setLoading(true);
        const data = await apiCall("/admin/stats");
        setStats(data);
      } catch (e) {
        console.error("Failed to load admin stats", e);
      } finally {
        setLoading(false);
      }
    };
    loadStats();
  }, []);

  if (loading) return <div className="text-center font-mono text-xs text-slate-500 py-6">Loading stats...</div>;
  if (!stats) return <div className="text-center font-mono text-xs text-red-400 py-6">Stats load failed.</div>;

  return (
    <div className="flex flex-col gap-4 font-mono text-xs">
      <h3 className="font-bold text-white text-sm uppercase">Статистика проекта</h3>
      <div className="grid grid-cols-2 gap-3">
        <div className="p-3 bg-obsidian border border-slateCustom/40 rounded-xl">
          <div className="text-slate-500">Пользователей</div>
          <div className="text-lg font-bold text-white mt-1">{stats.total_users}</div>
        </div>
        <div className="p-3 bg-obsidian border border-slateCustom/40 rounded-xl">
          <div className="text-slate-500">Зарегистрировано</div>
          <div className="text-lg font-bold text-white mt-1">{stats.registered_users}</div>
        </div>
        <div className="p-3 bg-obsidian border border-slateCustom/40 rounded-xl">
          <div className="text-slate-500">Депозитов</div>
          <div className="text-lg font-bold text-white mt-1">{stats.deposited_users}</div>
        </div>
        <div className="p-3 bg-obsidian border border-slateCustom/40 rounded-xl">
          <div className="text-slate-500">С безлимитом</div>
          <div className="text-lg font-bold text-white mt-1">{stats.unlimited_users}</div>
        </div>
      </div>
      <div className="h-px bg-slateCustom/20 my-1" />
      <div className="flex justify-between p-3 bg-obsidian border border-slateCustom/40 rounded-xl">
        <span className="text-slate-500">Анализов всего / сегодня:</span>
        <span className="text-champagne font-bold">{stats.total_analyses} / {stats.analyses_today}</span>
      </div>
    </div>
  );
}

// Broadcast Subtab
function AdminBroadcastTab({ apiCall }: { apiCall: any }) {
  const [text, setText] = useState("");
  const [photoUrl, setPhotoUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  const handleBroadcast = async () => {
    if (!text.trim()) return;
    try {
      setLoading(true);
      setResult(null);
      const res = await apiCall("/admin/broadcast", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, photo_url: photoUrl.trim() || null })
      });
      setResult(`Успешно! ID Рассылки: ${res.id}`);
      setText("");
      setPhotoUrl("");
    } catch (e: any) {
      setResult(`Ошибка: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <h3 className="font-bold text-white font-mono text-sm uppercase">Создать Рассылку</h3>
      <div className="flex flex-col gap-3 font-mono text-xs">
        <div className="flex flex-col gap-1">
          <span className="text-slate-500">Текст сообщения:</span>
          <textarea 
            rows={4}
            className="p-3 rounded-xl bg-obsidian border border-slateCustom text-white resize-none"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Введите текст рассылки..."
          />
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-slate-500">URL изображения (необязательно):</span>
          <input 
            type="text" 
            className="p-3 rounded-xl bg-obsidian border border-slateCustom text-white"
            value={photoUrl}
            onChange={(e) => setPhotoUrl(e.target.value)}
            placeholder="https://example.com/photo.jpg"
          />
        </div>

        {result && <div className="p-3 bg-slateCustom border border-champagne/10 text-champagne rounded-xl">{result}</div>}

        <button 
          onClick={handleBroadcast}
          disabled={loading || !text.trim()}
          className="magnetic-btn w-full bg-champagne text-obsidian font-bold py-3 rounded-xl flex items-center justify-center gap-2"
        >
          {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Megaphone className="w-4 h-4" />}
          Запустить рассылку
        </button>
      </div>
    </div>
  );
}

// Affiliate parameters Subtab
function AdminAffiliateTab({ apiCall }: { apiCall: any }) {
  const [refUrl, setRefUrl] = useState("");
  const [promoCode, setPromoCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  const handleUpdate = async () => {
    try {
      setLoading(true);
      await apiCall("/admin/affiliate", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ref_url: refUrl, promo_code: promoCode })
      });
      setMsg("Партнерские параметры обновлены!");
    } catch (e: any) {
      setMsg(`Ошибка: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-4 font-mono text-xs">
      <h3 className="font-bold text-white text-sm uppercase">Настройки партнёрки БК</h3>
      <div className="flex flex-col gap-3">
        <div className="flex flex-col gap-1">
          <span className="text-slate-500">Реферальная ссылка:</span>
          <input 
            type="text" 
            className="p-3 rounded-xl bg-obsidian border border-slateCustom text-white"
            value={refUrl}
            onChange={(e) => setRefUrl(e.target.value)}
            placeholder="https://1x.com/ref..."
          />
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-slate-500">Промокод:</span>
          <input 
            type="text" 
            className="p-3 rounded-xl bg-obsidian border border-slateCustom text-white"
            value={promoCode}
            onChange={(e) => setPromoCode(e.target.value)}
            placeholder="AIBET776"
          />
        </div>

        {msg && <div className="text-champagne font-bold">{msg}</div>}

        <button 
          onClick={handleUpdate}
          disabled={loading || !refUrl || !promoCode}
          className="magnetic-btn w-full bg-champagne text-obsidian font-bold py-3 rounded-xl flex items-center justify-center gap-2"
        >
          {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <LinkIcon className="w-4 h-4" />}
          Сохранить параметры
        </button>
      </div>
    </div>
  );
}

// Unlimited Grant/Revoke Subtab
function AdminUnlimitedTab({ apiCall }: { apiCall: any }) {
  const [tgId, setTgId] = useState("");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  const handleAction = async (action: "grant" | "revoke") => {
    if (!tgId) return;
    try {
      setLoading(true);
      setMsg("");
      const res = await apiCall(`/admin/unlimited/${action}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ telegram_id: parseInt(tgId) })
      });
      setMsg(`Готово! Состояние пользователя: ${res.funnel_state}`);
      setTgId("");
    } catch (e: any) {
      setMsg(`Ошибка: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-4 font-mono text-xs">
      <h3 className="font-bold text-white text-sm uppercase">Управление Безлимитом</h3>
      <div className="flex flex-col gap-3">
        <div className="flex flex-col gap-1">
          <span className="text-slate-500">Telegram User ID:</span>
          <input 
            type="number" 
            className="p-3 rounded-xl bg-obsidian border border-slateCustom text-white"
            value={tgId}
            onChange={(e) => setTgId(e.target.value)}
            placeholder="7649494487"
          />
        </div>

        {msg && <div className="text-champagne font-bold">{msg}</div>}

        <div className="flex gap-2">
          <button 
            onClick={() => handleAction("grant")}
            disabled={loading || !tgId}
            className="flex-1 py-3 bg-champagne text-obsidian font-bold rounded-xl flex items-center justify-center gap-1.5"
          >
            Выдать Безлимит
          </button>
          <button 
            onClick={() => handleAction("revoke")}
            disabled={loading || !tgId}
            className="flex-1 py-3 bg-red-950/50 border border-red-500/20 text-red-400 font-bold rounded-xl flex items-center justify-center gap-1.5"
          >
            Отозвать
          </button>
        </div>
      </div>
    </div>
  );
}

// App Settings Subtab
function AdminSettingsTab({ apiCall }: { apiCall: any }) {
  const [settings, setSettings] = useState<any>({});
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  const loadSettings = async () => {
    try {
      const res = await apiCall("/user/settings");
      setSettings(res);
    } catch (e) {
      console.error("Failed to load settings", e);
    }
  };

  useEffect(() => {
    loadSettings();
  }, []);

  const handleUpdate = async () => {
    try {
      setLoading(true);
      setMsg("");
      await apiCall("/admin/settings", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          channel_url: settings.channel_url,
          support_url: settings.support_url,
          unlimited_price_amount: parseInt(settings.unlimited_price_amount),
          daily_attempts_limit: parseInt(settings.daily_attempts_limit),
        })
      });
      setMsg("Настройки сохранены!");
    } catch (e: any) {
      setMsg(`Ошибка: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyChange = (key: string, val: string) => {
    setSettings((prev: any) => ({ ...prev, [key]: val }));
  };

  return (
    <div className="flex flex-col gap-4 font-mono text-xs">
      <h3 className="font-bold text-white text-sm uppercase">Системные Настройки</h3>
      <div className="flex flex-col gap-3">
        <div className="flex flex-col gap-1">
          <span className="text-slate-500">Ссылка на канал Telegram:</span>
          <input 
            type="text" 
            className="p-3 rounded-xl bg-obsidian border border-slateCustom text-white"
            value={settings.channel_url || ""}
            onChange={(e) => handleKeyChange("channel_url", e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-slate-500">Ссылка на техподдержку:</span>
          <input 
            type="text" 
            className="p-3 rounded-xl bg-obsidian border border-slateCustom text-white"
            value={settings.support_url || ""}
            onChange={(e) => handleKeyChange("support_url", e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-slate-500">Стоимость Безлимита (Tribute):</span>
          <input 
            type="number" 
            className="p-3 rounded-xl bg-obsidian border border-slateCustom text-white"
            value={settings.unlimited_price_amount || ""}
            onChange={(e) => handleKeyChange("unlimited_price_amount", e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-slate-500">Лимит попыток в сутки:</span>
          <input 
            type="number" 
            className="p-3 rounded-xl bg-obsidian border border-slateCustom text-white"
            value={settings.daily_attempts_limit || ""}
            onChange={(e) => handleKeyChange("daily_attempts_limit", e.target.value)}
          />
        </div>

        {msg && <div className="text-champagne font-bold">{msg}</div>}

        <button 
          onClick={handleUpdate}
          disabled={loading}
          className="magnetic-btn w-full bg-champagne text-obsidian font-bold py-3 rounded-xl flex items-center justify-center gap-2"
        >
          {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <SettingsIcon className="w-4 h-4" />}
          Сохранить настройки
        </button>
      </div>
    </div>
  );
}

// Postbacks copy Subtab
function AdminPostbackTab({ apiCall }: { apiCall: any }) {
  const [urls, setUrls] = useState<any>(null);

  useEffect(() => {
    const fetchUrls = async () => {
      try {
        const data = await apiCall("/admin/postback-urls");
        setUrls(data);
      } catch (e) {
        console.error("Failed to load postback urls", e);
      }
    };
    fetchUrls();
  }, []);

  const handleCopy = (txt: string) => {
    navigator.clipboard.writeText(txt);
    window.Telegram?.WebApp?.HapticFeedback.notificationOccurred("success");
    alert("Ссылка скопирована!");
  };

  if (!urls) return <div className="text-center font-mono text-xs text-slate-500 py-6">Loading links...</div>;

  return (
    <div className="flex flex-col gap-4 font-mono text-xs">
      <h3 className="font-bold text-white text-sm uppercase">Ссылки для Postback (БК)</h3>
      <p className="text-slate-400 leading-normal">
        Вставьте эти URL в кабинет партнерской сети для автоматического отслеживания конверсий:
      </p>
      
      <div className="flex flex-col gap-3 mt-1 text-left">
        <div className="flex flex-col gap-1.5 p-3 bg-obsidian border border-slateCustom/40 rounded-xl">
          <span className="text-slate-500 font-bold">1. Регистрация (Registration):</span>
          <div className="flex items-center gap-2 justify-between">
            <span className="text-[10px] text-white select-all break-all">{urls.registration}</span>
            <button onClick={() => handleCopy(urls.registration)} className="p-1 text-champagne hover:text-white shrink-0">
              <Copy className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="flex flex-col gap-1.5 p-3 bg-obsidian border border-slateCustom/40 rounded-xl">
          <span className="text-slate-500 font-bold">2. Депозит (Deposit):</span>
          <div className="flex items-center gap-2 justify-between">
            <span className="text-[10px] text-white select-all break-all">{urls.deposit}</span>
            <button onClick={() => handleCopy(urls.deposit)} className="p-1 text-champagne hover:text-white shrink-0">
              <Copy className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
