import random
from datetime import datetime, timezone, timedelta
from .data import ZOMBIES, WEAPONS, ARMOR, LOCATIONS, weapon_attack, armor_defense

def xp_for_level(level):
    return 100 + ((level - 1) * 75)

def apply_xp(player, amount):
    level = int(player["level"])
    xp = int(player["xp"]) + amount
    leveled = 0
    while xp >= xp_for_level(level):
        xp -= xp_for_level(level)
        level += 1
        leveled += 1
    if leveled:
        max_hp = 100 + (level - 1) * 8
        max_energy = 100 + (level - 1) * 3
        return xp, level, max_hp, max_energy, leveled
    return xp, level, player["max_hp"], player["max_energy"], 0

def make_zombie(level, location_multiplier=1):
    candidates = [z for z in ZOMBIES if z[2] <= max(45, level * 18)]
    if not candidates:
        candidates = ZOMBIES[:3]
    z = random.choice(candidates)
    scale = max(1.0, 1 + (level - 1) * 0.035) * location_multiplier
    return {
        "id": z[0], "name": z[1],
        "max_hp": int(z[2] * scale),
        "hp": int(z[2] * scale),
        "attack": max(1, int(z[3] * scale)),
        "coins": int(z[4] * scale),
        "xp": int(z[5] * scale),
    }

def weapon_upgrade_cost(level):
    level = max(0, int(level))
    return 1000 * (level + 1) ** 2

def armor_upgrade_cost(level):
    level = max(0, int(level))
    return 1200 * (level + 1) ** 2

def player_attack(player):
    base = weapon_attack(player["weapon"])
    upgrade = max(0, int(player.get("weapon_upgrade", 0)))
    base = int(base * (1 + (upgrade * 0.08)))
    return max(1, int(base * random.uniform(0.85, 1.15)))

def player_defense(player):
    base = armor_defense(player["armor"])
    upgrade = max(0, int(player.get("armor_upgrade", 0)))
    return int(base * (1 + (upgrade * 0.08)))

def random_loot(level):
    loot = {}
    scrap = random.randint(1, max(2, level + 2))
    loot["scrap"] = scrap
    if random.random() < 0.12:
        loot["medkit"] = 1
    return loot

def location_info(level):
    available = [x for x in LOCATIONS if x[2] <= level]
    return available or [LOCATIONS[0]]

def daily_available(last_daily):
    if not last_daily:
        return True
    now = datetime.now(timezone.utc)
    return now.date() > last_daily.date()

def regen_energy(player):
    last = player.get("last_energy")
    if not last:
        return 0

    now = datetime.now(timezone.utc)

    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    else:
        last = last.astimezone(timezone.utc)

    elapsed = int((now - last).total_seconds() // 300)

    if elapsed <= 0:
        return 0

    gain = min(
        elapsed * 5,
        player["max_energy"] - player["energy"]
    )

    return max(0, gain)
