def build_affiliate_url(ref_url: str, sub_param: str, telegram_id: int) -> str:
    if "{telegram_id}" in ref_url:
        ref_url = ref_url.replace("{telegram_id}", str(telegram_id))
    if f"{sub_param}=" in ref_url:
        return ref_url
    separator = "&" if "?" in ref_url else "?"
    return f"{ref_url}{separator}{sub_param}={telegram_id}"
