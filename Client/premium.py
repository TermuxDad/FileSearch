EMOJI_IDS = {
    "home": "4904936030232117798",
    "help": "5960842268096073715",
    "settings": "5199864854558574332",
    "success": "5463122435425448565",
    "warning": "6041720006973067267",
    "lock": "6271537028307881531",
    "back": "5960842268096073715",
}

def premium_emoji(name, fallback="•"):
    emoji_id = EMOJI_IDS.get(name)
    if not emoji_id:
        return fallback
    return f"<tg-emoji emoji-id='{emoji_id}'>{fallback}</tg-emoji>"
