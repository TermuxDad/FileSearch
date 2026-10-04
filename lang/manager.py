# THIS SOURCE CODE IS DEVELOPED BY @MIGHTYAYUSH. FOLLOW @SOCIAL_BOTS FOR MORE DETAILS AND MEET THE DEVELOPER...
from __future__ import annotations
from typing import Any
from lang.en import STRINGS

TRANSLATIONS = {"en": STRINGS}

def load_skin(bot_type: str = "porn") -> None:
    pass

def tr(key: str, lang: str = "en", **kwargs: Any) -> str:
    template = STRINGS.get(key, key)
    if kwargs:
        try:
            return template.format(**kwargs)
        except Exception:
            return template
    return template
