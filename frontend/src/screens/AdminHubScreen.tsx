import { useEffect, useState } from "react";
import { Copy, Link as LinkIcon, Megaphone, RefreshCw, Settings as SettingsIcon, Shield, Trash2, UserPlus } from "lucide-react";

interface AdminHubProps {
  user: any;
  apiCall: (endpoint: string, options?: RequestInit) => Promise<any>;
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

  if (loading) return <div className="text-center font-mono text-xs text-textMuted py-6">Loading stats...</div>;
  if (!stats) return <div className="text-center font-mono text-xs text-red-400 py-6">Stats load failed.</div>;

  return (
    <div className="flex flex-col gap-4 font-mono text-xs">
      <h3 className="font-bold text-textPrimary text-sm uppercase">Статистика проекта</h3>
      <div className="grid grid-cols-2 gap-3">
        <div className="p-3 bg-appBg border border-borderSubtle/40 rounded-xl">
          <div className="text-textMuted">Пользователей</div>
          <div className="text-lg font-bold text-textPrimary mt-1">{stats.total_users}</div>
        </div>
        <div className="p-3 bg-appBg border border-borderSubtle/40 rounded-xl">
          <div className="text-textMuted">Зарегистрировано</div>
          <div className="text-lg font-bold text-textPrimary mt-1">{stats.registered_users}</div>
        </div>
        <div className="p-3 bg-appBg border border-borderSubtle/40 rounded-xl">
          <div className="text-textMuted">Депозитов</div>
          <div className="text-lg font-bold text-textPrimary mt-1">{stats.deposited_users}</div>
        </div>
        <div className="p-3 bg-appBg border border-borderSubtle/40 rounded-xl">
          <div className="text-textMuted">С безлимитом</div>
          <div className="text-lg font-bold text-textPrimary mt-1">{stats.unlimited_users}</div>
        </div>
      </div>
      <div className="h-px bg-surface/20 my-1" />
      <div className="flex justify-between p-3 bg-appBg border border-borderSubtle/40 rounded-xl">
        <span className="text-textMuted">Анализов всего / сегодня:</span>
        <span className="text-accent font-bold">{stats.total_analyses} / {stats.analyses_today}</span>
      </div>
    </div>
  );
}

// Broadcast Subtab
function AdminBroadcastTab({ apiCall }: { apiCall: any }) {
  const [text, setText] = useState("");
  const [photos, setPhotos] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  const handlePhotosChange = (files: FileList | null) => {
    if (!files) return;
    const picked = Array.from(files).slice(0, 5);
    setPhotos(picked);
    setPreviews(picked.map((f) => URL.createObjectURL(f)));
  };

  const handleBroadcast = async () => {
    if (!text.trim()) return;
    try {
      setLoading(true);
      setResult(null);
      const formData = new FormData();
      formData.append("text", text);
      photos.forEach((photo) => formData.append("photos", photo));
      const res = await apiCall("/admin/broadcast", {
        method: "POST",
        body: formData,
      });
      setResult(`Готово! Отправлено: ${res.sent_count}, ошибок: ${res.failed_count}`);
      setText("");
      setPhotos([]);
      setPreviews([]);
    } catch (e: any) {
      setResult(`Ошибка: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <h3 className="font-bold text-textPrimary font-mono text-sm uppercase">Создать Рассылку</h3>
      <div className="flex flex-col gap-3 font-mono text-xs">
        <div className="flex flex-col gap-1">
          <span className="text-textMuted">Текст сообщения:</span>
          <textarea
            rows={4}
            className="p-3 rounded-xl bg-appBg border border-borderSubtle text-textPrimary resize-none"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Введите текст рассылки..."
          />
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-textMuted">Фото (до 5, необязательно):</span>
          <label className="magnetic-btn text-xs font-medium px-4 py-2.5 rounded-xl border border-borderSubtle bg-surfaceElevated cursor-pointer w-fit">
            Выбрать фото
            <input
              type="file"
              accept="image/*"
              multiple
              className="hidden"
              onChange={(e) => handlePhotosChange(e.target.files)}
            />
          </label>
          {previews.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-1">
              {previews.map((src) => (
                <img key={src} src={src} alt="" className="w-14 h-14 object-cover rounded-lg border border-borderSubtle" />
              ))}
            </div>
          )}
        </div>

        {result && <div className="p-3 bg-surface border border-accent/10 text-accent rounded-xl">{result}</div>}

        <button
          onClick={handleBroadcast}
          disabled={loading || !text.trim()}
          className="magnetic-btn w-full bg-accent text-white font-bold py-3 rounded-xl flex items-center justify-center gap-2"
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
      <h3 className="font-bold text-textPrimary text-sm uppercase">Настройки партнёрки БК</h3>
      <div className="flex flex-col gap-3">
        <div className="flex flex-col gap-1">
          <span className="text-textMuted">Реферальная ссылка:</span>
          <input 
            type="text" 
            className="p-3 rounded-xl bg-appBg border border-borderSubtle text-textPrimary"
            value={refUrl}
            onChange={(e) => setRefUrl(e.target.value)}
            placeholder="https://1x.com/ref..."
          />
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-textMuted">Промокод:</span>
          <input 
            type="text" 
            className="p-3 rounded-xl bg-appBg border border-borderSubtle text-textPrimary"
            value={promoCode}
            onChange={(e) => setPromoCode(e.target.value)}
            placeholder="AIBET776"
          />
        </div>

        {msg && <div className="text-accent font-bold">{msg}</div>}

        <button 
          onClick={handleUpdate}
          disabled={loading || !refUrl || !promoCode}
          className="magnetic-btn w-full bg-accent text-white font-bold py-3 rounded-xl flex items-center justify-center gap-2"
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
      <h3 className="font-bold text-textPrimary text-sm uppercase">Управление Безлимитом</h3>
      <div className="flex flex-col gap-3">
        <div className="flex flex-col gap-1">
          <span className="text-textMuted">Telegram User ID:</span>
          <input 
            type="number" 
            className="p-3 rounded-xl bg-appBg border border-borderSubtle text-textPrimary"
            value={tgId}
            onChange={(e) => setTgId(e.target.value)}
            placeholder="7649494487"
          />
        </div>

        {msg && <div className="text-accent font-bold">{msg}</div>}

        <div className="flex gap-2">
          <button 
            onClick={() => handleAction("grant")}
            disabled={loading || !tgId}
            className="flex-1 py-3 bg-accent text-white font-bold rounded-xl flex items-center justify-center gap-1.5"
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
      const res = await apiCall("/admin/settings");
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
      <h3 className="font-bold text-textPrimary text-sm uppercase">Системные Настройки</h3>
      <div className="flex flex-col gap-3">
        <div className="flex flex-col gap-1">
          <span className="text-textMuted">Ссылка на канал Telegram:</span>
          <input 
            type="text" 
            className="p-3 rounded-xl bg-appBg border border-borderSubtle text-textPrimary"
            value={settings.channel_url || ""}
            onChange={(e) => handleKeyChange("channel_url", e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-textMuted">Ссылка на техподдержку:</span>
          <input 
            type="text" 
            className="p-3 rounded-xl bg-appBg border border-borderSubtle text-textPrimary"
            value={settings.support_url || ""}
            onChange={(e) => handleKeyChange("support_url", e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-textMuted">Лимит анализов в сутки (обычные пользователи):</span>
          <input
            type="number"
            className="p-3 rounded-xl bg-appBg border border-borderSubtle text-textPrimary"
            value={settings.daily_attempts_limit || ""}
            onChange={(e) => handleKeyChange("daily_attempts_limit", e.target.value)}
          />
        </div>

        {msg && <div className="text-accent font-bold">{msg}</div>}

        <button 
          onClick={handleUpdate}
          disabled={loading}
          className="magnetic-btn w-full bg-accent text-white font-bold py-3 rounded-xl flex items-center justify-center gap-2"
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

  if (!urls) return <div className="text-center font-mono text-xs text-textMuted py-6">Loading links...</div>;

  return (
    <div className="flex flex-col gap-4 font-mono text-xs">
      <h3 className="font-bold text-textPrimary text-sm uppercase">Ссылки для Postback (БК)</h3>
      <p className="text-textMuted leading-normal">
        Вставьте эти URL в кабинет партнерской сети для автоматического отслеживания конверсий:
      </p>
      
      <div className="flex flex-col gap-3 mt-1 text-left">
        <div className="flex flex-col gap-1.5 p-3 bg-appBg border border-borderSubtle/40 rounded-xl">
          <span className="text-textMuted font-bold">1. Регистрация (Registration):</span>
          <div className="flex items-center gap-2 justify-between">
            <span className="text-[10px] text-textPrimary select-all break-all">{urls.registration}</span>
            <button onClick={() => handleCopy(urls.registration)} className="p-1 text-accent hover:text-textPrimary shrink-0">
              <Copy className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="flex flex-col gap-1.5 p-3 bg-appBg border border-borderSubtle/40 rounded-xl">
          <span className="text-textMuted font-bold">2. Депозит (Deposit):</span>
          <div className="flex items-center gap-2 justify-between">
            <span className="text-[10px] text-textPrimary select-all break-all">{urls.deposit}</span>
            <button onClick={() => handleCopy(urls.deposit)} className="p-1 text-accent hover:text-textPrimary shrink-0">
              <Copy className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Admins management Subtab
function AdminAdminsTab({ apiCall }: { apiCall: any }) {
  const [admins, setAdmins] = useState<any[]>([]);
  const [username, setUsername] = useState("");
  const [tgId, setTgId] = useState("");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  const loadAdmins = async () => {
    try {
      const data = await apiCall("/admin/admins");
      setAdmins(data);
    } catch (e) {
      console.error("Failed to load admins", e);
    }
  };

  useEffect(() => {
    loadAdmins();
  }, []);

  const handleAdd = async () => {
    if (!username.trim() && !tgId.trim()) return;
    try {
      setLoading(true);
      setMsg("");
      const body: Record<string, unknown> = {};
      if (tgId.trim()) body.telegram_id = parseInt(tgId);
      if (username.trim()) body.username = username.trim();
      await apiCall("/admin/admins", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      setMsg("Админ добавлен");
      setUsername("");
      setTgId("");
      await loadAdmins();
    } catch (e: any) {
      setMsg(`Ошибка: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRemove = async (telegramId: number) => {
    if (!confirm(`Удалить админа ${telegramId}?`)) return;
    try {
      setLoading(true);
      setMsg("");
      await apiCall("/admin/admins", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ telegram_id: telegramId }),
      });
      setMsg("Админ удалён");
      await loadAdmins();
    } catch (e: any) {
      setMsg(`Ошибка: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-4 font-mono text-xs">
      <h3 className="font-bold text-textPrimary text-sm uppercase">Управление админами</h3>

      <div className="flex flex-col gap-3">
        <div className="flex flex-col gap-1">
          <span className="text-textMuted">Username (@user):</span>
          <input
            type="text"
            className="p-3 rounded-xl bg-appBg border border-borderSubtle text-textPrimary"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="@username"
          />
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-textMuted">или Telegram ID:</span>
          <input
            type="number"
            className="p-3 rounded-xl bg-appBg border border-borderSubtle text-textPrimary"
            value={tgId}
            onChange={(e) => setTgId(e.target.value)}
            placeholder="1396107626"
          />
        </div>

        {msg && <div className="text-accent font-bold">{msg}</div>}

        <button
          onClick={handleAdd}
          disabled={loading || (!username.trim() && !tgId.trim())}
          className="magnetic-btn w-full bg-accent text-white font-bold py-3 rounded-xl flex items-center justify-center gap-2"
        >
          {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <UserPlus className="w-4 h-4" />}
          Добавить админа
        </button>
      </div>

      <div className="h-px bg-borderSubtle/40" />

      <div className="flex flex-col gap-2">
        {admins.length === 0 && <div className="text-textMuted">Нет админов</div>}
        {admins.map((admin) => (
          <div
            key={admin.telegram_id}
            className="flex items-center justify-between p-3 bg-appBg border border-borderSubtle/40 rounded-xl"
          >
            <div className="flex flex-col min-w-0">
              <span className="text-textPrimary font-bold">
                {admin.username ? `@${admin.username}` : admin.telegram_id}
              </span>
              <span className="text-[10px] text-textMuted">
                ID: {admin.telegram_id} · {admin.source === "env" ? "bootstrap" : "panel"}
              </span>
            </div>
            {admin.removable ? (
              <button
                type="button"
                onClick={() => handleRemove(admin.telegram_id)}
                disabled={loading}
                className="p-2 text-danger hover:bg-danger/10 rounded-lg shrink-0"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            ) : (
              <span title="Bootstrap admin" className="shrink-0">
                <Shield className="w-4 h-4 text-accent" />
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// Tribute settings Subtab
function AdminTributeTab({ apiCall }: { apiCall: any }) {
  const [settings, setSettings] = useState<any>({});
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  const loadSettings = async () => {
    try {
      const res = await apiCall("/admin/settings");
      setSettings(res);
    } catch (e) {
      console.error("Failed to load tribute settings", e);
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
          tribute_enabled: settings.tribute_enabled === "true" || settings.tribute_enabled === true,
          tribute_mode: settings.tribute_mode,
          tribute_api_key: settings.tribute_api_key,
          tribute_shop_id: settings.tribute_shop_id,
          tribute_webhook_secret: settings.tribute_webhook_secret,
          tribute_product_link: settings.tribute_product_link,
          unlimited_enabled: settings.unlimited_enabled === "true" || settings.unlimited_enabled === true,
          unlimited_price_amount: parseInt(settings.unlimited_price_amount),
          unlimited_price_currency: settings.unlimited_price_currency,
        }),
      });
      setMsg("Настройки Tribute сохранены!");
      await loadSettings();
    } catch (e: any) {
      setMsg(`Ошибка: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyChange = (key: string, val: string | boolean) => {
    setSettings((prev: any) => ({ ...prev, [key]: val }));
  };

  const boolVal = (key: string) => settings[key] === "true" || settings[key] === true;

  return (
    <div className="flex flex-col gap-4 font-mono text-xs">
      <h3 className="font-bold text-textPrimary text-sm uppercase">Tribute / Безлимит</h3>
      <div className="flex flex-col gap-3">
        <label className="flex items-center gap-2 text-textMuted">
          <input
            type="checkbox"
            checked={boolVal("tribute_enabled")}
            onChange={(e) => handleKeyChange("tribute_enabled", e.target.checked)}
          />
          Tribute включён
        </label>
        <label className="flex items-center gap-2 text-textMuted">
          <input
            type="checkbox"
            checked={boolVal("unlimited_enabled")}
            onChange={(e) => handleKeyChange("unlimited_enabled", e.target.checked)}
          />
          Продажа безлимита включена
        </label>
        <div className="flex flex-col gap-1">
          <span className="text-textMuted">Режим Tribute:</span>
          <select
            className="p-3 rounded-xl bg-appBg border border-borderSubtle text-textPrimary"
            value={settings.tribute_mode || "shop_api"}
            onChange={(e) => handleKeyChange("tribute_mode", e.target.value)}
          >
            <option value="shop_api">shop_api</option>
            <option value="product_link">product_link</option>
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-textMuted">Tribute API Key:</span>
          <input
            type="password"
            className="p-3 rounded-xl bg-appBg border border-borderSubtle text-textPrimary"
            value={settings.tribute_api_key || ""}
            onChange={(e) => handleKeyChange("tribute_api_key", e.target.value)}
            placeholder="Api-Key из Tribute"
          />
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-textMuted">Tribute Shop ID:</span>
          <input
            type="text"
            className="p-3 rounded-xl bg-appBg border border-borderSubtle text-textPrimary"
            value={settings.tribute_shop_id || ""}
            onChange={(e) => handleKeyChange("tribute_shop_id", e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-textMuted">Webhook Secret:</span>
          <input
            type="password"
            className="p-3 rounded-xl bg-appBg border border-borderSubtle text-textPrimary"
            value={settings.tribute_webhook_secret || ""}
            onChange={(e) => handleKeyChange("tribute_webhook_secret", e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-textMuted">Ссылка на продукт (product_link):</span>
          <input
            type="text"
            className="p-3 rounded-xl bg-appBg border border-borderSubtle text-textPrimary"
            value={settings.tribute_product_link || ""}
            onChange={(e) => handleKeyChange("tribute_product_link", e.target.value)}
            placeholder="https://t.me/tribute/..."
          />
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-textMuted">Цена безлимита:</span>
          <div className="flex gap-2">
            <input
              type="number"
              className="flex-1 p-3 rounded-xl bg-appBg border border-borderSubtle text-textPrimary"
              value={settings.unlimited_price_amount || ""}
              onChange={(e) => handleKeyChange("unlimited_price_amount", e.target.value)}
            />
            <input
              type="text"
              className="w-20 p-3 rounded-xl bg-appBg border border-borderSubtle text-textPrimary uppercase"
              value={settings.unlimited_price_currency || "rub"}
              onChange={(e) => handleKeyChange("unlimited_price_currency", e.target.value)}
            />
          </div>
        </div>

        {msg && <div className="text-accent font-bold">{msg}</div>}

        <button
          onClick={handleUpdate}
          disabled={loading}
          className="magnetic-btn w-full bg-accent text-white font-bold py-3 rounded-xl flex items-center justify-center gap-2"
        >
          {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <SettingsIcon className="w-4 h-4" />}
          Сохранить Tribute
        </button>
      </div>
    </div>
  );
}

export function AdminHubScreen({ user, apiCall }: AdminHubProps) {
  const [subTab, setSubTab] = useState<
    "stats" | "broadcast" | "affiliate" | "unlimited" | "settings" | "tribute" | "postback" | "admins"
  >("stats");

  if (!user?.is_admin) {
    return <div className="text-center py-10 text-sm text-danger">Forbidden</div>;
  }

  return (
    <div className="flex flex-col gap-5 text-left screen-enter">
      <div className="flex items-center gap-2 border-b border-borderSubtle pb-3">
        <SettingsIcon className="w-6 h-6 text-accent" />
        <h2 className="text-lg font-semibold text-textPrimary">Admin</h2>
      </div>

      <div className="flex flex-wrap gap-2">
        {(["stats", "broadcast", "affiliate", "unlimited", "settings", "tribute", "postback", "admins"] as const).map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => setSubTab(tab)}
            className={`text-xxs font-medium px-3 py-2 rounded-lg border transition-all uppercase ${
              subTab === tab
                ? "bg-accent text-white border-accent"
                : "border-borderSubtle text-textMuted"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="p-4 bg-surface border border-borderSubtle rounded-containerLg">
        {subTab === "stats" && <AdminStatsTab apiCall={apiCall} />}
        {subTab === "broadcast" && <AdminBroadcastTab apiCall={apiCall} />}
        {subTab === "affiliate" && <AdminAffiliateTab apiCall={apiCall} />}
        {subTab === "unlimited" && <AdminUnlimitedTab apiCall={apiCall} />}
        {subTab === "settings" && <AdminSettingsTab apiCall={apiCall} />}
        {subTab === "tribute" && <AdminTributeTab apiCall={apiCall} />}
        {subTab === "postback" && <AdminPostbackTab apiCall={apiCall} />}
        {subTab === "admins" && <AdminAdminsTab apiCall={apiCall} />}
      </div>
    </div>
  );
}
