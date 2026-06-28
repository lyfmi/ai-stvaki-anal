_translations_cache: dict[str, dict] = {}


def clear_translation_cache(locale: str | None = None) -> None:
    if locale:
        _translations_cache.pop(locale, None)
    else:
        _translations_cache.clear()


async def get_t(locale: str, *, force: bool = False) -> dict:
    if force or locale not in _translations_cache or not _translations_cache.get(locale):
        from app.api_client import BackendClient

        backend = BackendClient()
        try:
            data = await backend.get_translations(locale)
            if data:
                _translations_cache[locale] = data
        except Exception:
            if locale not in _translations_cache:
                _translations_cache[locale] = {}
    return _translations_cache.get(locale) or {}


def format_analysis(result: dict, locale: str = "ru") -> str:
    args = result.get("arguments") or []
    args_text = "\n".join(f"• {a}" for a in args) if args else "—"
    if locale == "en":
        risk_labels = {"low": "low", "medium": "medium", "high": "high"}
        conf_labels = {"low": "low", "medium": "medium", "high": "high"}
        header = "🎯 Bet"
        risk_h = "⚠️ Risk"
        prob_h = "📊 Probability"
        conf_h = "💪 Confidence"
        args_h = "Arguments"
    else:
        risk_labels = {"low": "низкий", "medium": "средний", "high": "высокий"}
        conf_labels = {"low": "низкая", "medium": "средняя", "high": "высокая"}
        header = "🎯 Ставка"
        risk_h = "⚠️ Риск"
        prob_h = "📊 Вероятность"
        conf_h = "💪 Уверенность"
        args_h = "Аргументы"

    risk = risk_labels.get(result.get("risk", "medium"), result.get("risk", "medium"))
    conf = conf_labels.get(result.get("confidence", "medium"), result.get("confidence", "medium"))

    return (
        f"{header}: {result.get('recommendation', '—')}"
        f" (кф {result.get('coefficient', '—')})\n"
        f"{risk_h}: {risk}\n"
        f"{prob_h}: {result.get('probability_percent', '—')}%\n"
        f"{conf_h}: {conf}\n\n"
        f"{args_h}:\n{args_text}\n\n"
        f"{result.get('explanation', '')}"
    )
