# THIS SOURCE CODE IS DEVELOPED BY @MIGHTYAYUSH. FOLLOW @SOCIAL_BOTS FOR MORE DETAILS AND MEET THE DEVELOPER...
from __future__ import annotations
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from lang.manager import tr
from services.subscription import SubscriptionService
from utils.logging import get_logger

logger = get_logger("plugins.force_sub")

router = Router(name="force_sub_router")

@router.callback_query(F.data == "confirm_sub")
async def on_confirm_subscription(
    callback: CallbackQuery,
    bot: Bot,
    subscription_service: SubscriptionService,
    lang: str = "en",
) -> None:
    user = callback.from_user
    if not user:
        return

    missing = await subscription_service.get_missing_channels(bot, user.id, ignore_cache=True)

    if missing:
        keyboard = subscription_service.build_subscription_keyboard(missing, lang=lang)
        msg_text = tr("sub_still_missing", lang)
        try:
            if callback.message:
                await callback.message.edit_reply_markup(reply_markup=keyboard)
            await callback.answer(msg_text, show_alert=True)
        except Exception:
            await callback.answer(msg_text, show_alert=True)
    else:
        subscription_service.mark_subscribed(user.id)
        await callback.answer("✅ Verified!", show_alert=True)
        if callback.message:
            try:
                await callback.message.edit_text(
                    "🎉 <b>Subscription Verified!</b>\n\n"
                    "You have successfully joined all required channels.\n"
                    "Send any keywords now to search for files!",
                    parse_mode="HTML",
                    reply_markup=None,
                )
            except Exception:
                pass
