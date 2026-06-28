_translations_cache: dict[str, dict] = {}


async def get_t(locale: str) -> dict:
    if locale not in _translations_cache:
        from app.api_client import BackendClient

        backend = BackendClient()
        try:
            _translations_cache[locale] = await backend.get_translations(locale)
        except Exception:
            _translations_cache[locale] = {}
    return _translations_cache[locale]


def format_analysis(result: dict, locale: str = "ru") -> str:
    args = result.get("arguments") or []
    args_text = "\n".join(f"• {a}" for a in args) if args else "—"
    risk_labels = {"low": "низкий", "medium": "средний", "high": "высокий"}
    conf_labels = {"low": "низкая", "medium": "средняя", "high": "высокая"}
    risk = risk_labels.get(result.get("risk", "medium"), result.get("risk", "medium"))
    conf = conf_labels.get(result.get("confidence", "medium"), result.get("confidence", "medium"))
    if locale == "en":
        risk_labels = {"low": "low", "medium": "medium", "high": "high"}
        conf_labels = {"low": "low", "medium": "medium", "high": "high"}
        risk = risk_labels.get(result.get("risk", "medium"), result.get("risk", "medium"))
        conf = conf_labels.get(result.get("confidence", "medium"), result.get("confidence", "medium"))

    return (
        f"🎯 Ставка: {result.get('recommendation', '—')}"
        f" (кф {result.get('coefficient', '—')})\n"
        f"⚠️ Риск: {risk}\n"
        f"📊 Вероятность: {result.get('probability_percent', '—')}%\n"
        f"💪 Уверенность: {conf}\n\n"
        f"Аргументы:\n{args_text}\n\n"
        f"{result.get('explanation', '')}"
    )
