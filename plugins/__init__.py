# THIS SOURCE CODE IS DEVELOPED BY @MIGHTYAYUSH. FOLLOW @SOCIAL_BOTS FOR MORE DETAILS AND MEET THE DEVELOPER...
from plugins.start import router as start_router
from plugins.help import router as help_router
from plugins.search import router as search_router
from plugins.request import router as request_router
from plugins.file_delivery import router as file_delivery_router
from plugins.force_sub import router as force_sub_router
from plugins.block import router as block_router
from plugins.stats import router as stats_router
from plugins.callbacks import router as callbacks_router
from plugins.errors import router as errors_router

__all__ = [
    "start_router",
    "help_router",
    "search_router",
    "request_router",
    "file_delivery_router",
    "force_sub_router",
    "block_router",
    "stats_router",
    "callbacks_router",
    "errors_router",
]
