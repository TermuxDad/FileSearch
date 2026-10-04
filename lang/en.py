# THIS SOURCE CODE IS DEVELOPED BY @MIGHTYAYUSH. FOLLOW @SOCIAL_BOTS FOR MORE DETAILS AND MEET THE DEVELOPER...
from __future__ import annotations

STRINGS = {
    "welcome_text": (
        "👋 <b>Welcome, {first_name}!</b>\n\n"
        "I am your lightning-fast <b>File Search & Delivery Engine</b>.\n\n"
        "🔍 <b>How to Search:</b>\n"
        "Simply type the name, keywords, or hashtags of the file you want directly in this chat.\n\n"
        "⚡ <i>Instant search results, zero wait time, secure downloads!</i>"
    ),
    "welcome_dual_text": (
        "👋 <b>Welcome, {first_name}!</b>\n\n"
        "I am your lightning-fast <b>File Search & Indexing Engine</b>.\n\n"
        "🔍 <b>How to Search:</b>\n"
        "Type any title, keywords, or hashtags directly into this chat.\n\n"
        "📦 <b>File Delivery:</b>\n"
        "Your files will be dispatched directly to your private chat via @{delivery_username}.\n\n"
        "⚡ <i>Fast, reliable, and always up to date!</i>"
    ),

    "help_text": (
        "📖 <b>Bot User Guide & Navigation</b>\n\n"
        "🔍 <b>Searching for Files:</b>\n"
        "Just send any keywords or hashtags directly into this chat.\n"
        "<i>Examples:</i>\n"
        "• <code>Interstellar 1080p</code>\n"
        "• <code>#action #hindi</code>\n\n"
        "🤖 <b>Available Commands:</b>\n"
        "• /start - Restart bot & open main menu\n"
        "• /help - View this guide\n"
        "• /request - Request an unlisted file from admins\n"
        "• /cancel - Cancel active request\n\n"
        "📥 <b>File Delivery:</b>\n"
        "Click the <b>Get File</b> button on any search result to download directly."
    ),
    "help_text_owner": (
        "👑 <b>Bot Owner & Admin Panel</b>\n\n"
        "🤖 <b>User Commands:</b>\n"
        "• /start - Restart bot\n"
        "• /help - Open help guide\n"
        "• /request - Request unlisted file\n"
        "• /cancel - Cancel active operation\n\n"
        "🛠 <b>Owner Control Commands:</b>\n"
        "• /stats - View server hardware, RAM & CPU telemetry\n"
        "• /scan &lt;start&gt;-&lt;end&gt; - Scan group/channel for files with live progress\n"
        "• /maintain &lt;on/off&gt; - Toggle bot maintenance mode\n"
        "• /restart - Gracefully restart bot process\n"
        "• /block &lt;user_id&gt; [reason] - Block a user\n"
        "• /unblock &lt;user_id&gt; - Unblock a user\n"
        "• /blocked - View all blocked users"
    ),

    "group_restricted": (
        "⚠️ <b>Private Chat Only!</b>\n\n"
        "This bot only works in private chat to keep conversations clean and secure.\n"
        "Click the button below to start searching in private!"
    ),
    "btn_open_pm": "🚀 Open in Private Chat",
    "btn_support_group": "📢 Support Group",
    "btn_backup_channel": "🔗 Backup Channel",
    "btn_help": "📖 Help",
    "btn_back": "🔙 Back",

    "force_sub_prompt": (
        "👋 Hello <b>{first_name}</b>!\n\n"
        "To access our file search engine, please join our official update channels below.\n"
        "Once joined, tap <b>Confirm Joining</b> to start searching!"
    ),
    "btn_join_channel": "📢 Join Channel",
    "btn_confirm_sub": "✅ Confirm Joining",
    "sub_still_missing": "⚠️ You have not joined all required channels yet. Please join all of them and tap Confirm!",

    "search_too_short": "⚠️ Search query is too short. Please send at least 2 characters.",
    "search_too_long": "⚠️ Search query is too long. Please keep it under 100 characters.",
    "search_no_results": (
        "🔍 <b>No Results Found</b> for: <i>{query}</i>\n\n"
        "We couldn't find any files matching your keywords.\n"
        "Check for spelling mistakes or click below to submit a request to our admins!"
    ),
    "btn_request_file": "📝 Request This File",
    "search_results_header": "🔍 <b>Results for:</b> <i>{query}</i>\nFound <b>{total}</b> files (Page {page}/{pages}):\n\n<i>Tap any result below to retrieve your file:</i>",
    "btn_prev": "⬅️ Prev",
    "btn_next": "Next ➡️",
    "session_expired": "⚠️ Search session expired. Please send your query again.",
    "session_not_yours": "⛔ This search session belongs to another user.",

    "file_delivery_dual_redirect": (
        "📦 <b>File Link Detected!</b>\n\n"
        "Files are securely delivered by our <b>Delivery Bot</b>.\n"
        "<a href='{url}'>👉 Click here to retrieve your file on @{delivery_username}</a>"
    ),
    "file_delivery_caption": (
        "📁 <b>{file_name}</b>\n"
        "📦 Size: <code>{file_size}</code>\n\n"
        "⚠️ <i><b>Notice:</b> This file will be automatically deleted from this chat in 5 minutes! "
        "Please forward or save it to your <b>Saved Messages</b> immediately.</i>"
    ),
    "delivery_delete_notice": (
        "\n\n⚠️ <i><b>Notice:</b> This file will be automatically deleted in 5 minutes! "
        "Please forward or save it to your <b>Saved Messages</b> immediately.</i>"
    ),
    "delivery_invalid_token": "The requested link is invalid or malformed.",
    "delivery_expired_token": "This download link has expired. Please search again.",
    "delivery_file_missing": "The requested file is no longer available in the index.",
    "delivery_user_blocked": "⛔ Your account has been suspended from downloading files.",
    "btn_back_to_search": "🔍 Back to Search",

    "request_pm_only": "File requests can only be submitted in private chat with the bot.",
    "request_prompt": (
        "📝 <b>File Request Service</b>\n\n"
        "Please send the <b>title, year, or description</b> of the file you are looking for.\n"
        "<i>Example:</i> <code>Interstellar (2014) 1080p BluRay</code>\n\n"
        "To cancel at any time, type /cancel."
    ),
    "request_cancel_no_active": "There is no active operation to cancel.",
    "request_cancelled": "❌ Operation cancelled.",
    "request_text_only": "⚠️ Please send your request as text, or send /cancel to abort.",
    "request_too_short": "⚠️ Description is too short. Please provide at least 3 characters.",
    "request_too_long": "⚠️ Description is too long. Please keep it under 300 characters.",
    "request_submitted": (
        "✅ <b>Request Received!</b>\n\n"
        "<b>You requested:</b>\n"
        "<blockquote>{description}</blockquote>\n\n"
        "<b>Request ID:</b> <code>{request_id}</code>\n\n"
        "Our admins have been notified. You will receive an automated message here when your file is uploaded!"
    ),
    "request_completed_notify": (
        "🎉 <b>Good News! Your Requested File is Ready!</b>\n\n"
        "The file you requested has been uploaded:\n"
        "<blockquote>{description}</blockquote>\n\n"
        "You can now search for it using keywords from your request!"
    ),

    "user_blocked": "⛔ <b>Access Denied</b>\nYou have been blocked from using this bot.",
    "internal_error": "❌ An unexpected internal error occurred. Please try again later.",
    "maintenance_notice": (
        "🛠️ <b>Bot is Under Maintenance!</b>\n\n"
        "The bot is currently undergoing scheduled maintenance and system upgrades.\n"
        "Please wait for some moments. We will be back online shortly!\n\n"
        "Thank you for your patience and support. For updates, please join our official support channel below:"
    ),
    "maintenance_alert": "🛠️ The bot is currently under maintenance. Please wait for some moments!",
    "btn_support_channel": "📢 Official Support Channel",
}
