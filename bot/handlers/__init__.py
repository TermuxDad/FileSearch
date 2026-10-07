from .start import register
from .game import register as register_game
from .profile import register as register_profile
from .shop import register as register_shop
from .missions import register as register_missions
from .leaderboard import register as register_leaderboard
from .raid import register as register_raid
from .admin import register as register_admin
from .backup import register as register_backup
from .help_handler import register_help


def register_handlers(app, db, config):
    register(app, db)
    register_profile(app, db)
    register_game(app, db)
    register_shop(app, db)
    register_missions(app, db)
    register_leaderboard(app, db)
    register_raid(app, db)
    register_admin(app, db, config)
    register_backup(app, db, config)
    register_help(app, db)
