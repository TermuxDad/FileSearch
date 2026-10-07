ZOMBIES = [
    ("walker", "🧟 Walker", 35, 8, 35, 30),
    ("crawler", "🕷️ Crawler", 28, 10, 45, 35),
    ("runner", "🏃 Runner", 45, 12, 55, 40),
    ("brute", "💪 Brute", 80, 18, 90, 60),
    ("spitter", "🤢 Spitter", 55, 16, 75, 55),
    ("screamer", "😱 Screamer", 60, 15, 80, 60),
    ("stalker", "👤 Stalker", 70, 20, 100, 75),
    ("mutant", "☣️ Mutant", 120, 25, 180, 110),
    ("tank", "🧟‍♂️ Tank", 180, 30, 260, 160),
    ("ghoul", "👹 Ghoul", 95, 22, 135, 90),
    ("biter", "🧟 Biter", 42, 11, 50, 38),
    ("burner", "🔥 Burner", 75, 19, 115, 80),
    ("frost", "❄️ Frost Zombie", 90, 21, 130, 95),
    ("toxic", "☠️ Toxic Zombie", 105, 24, 160, 105),
    ("hunter", "🎯 Hunter Zombie", 110, 27, 175, 115),
    ("warden", "🚨 Warden", 150, 29, 230, 145),
    ("reaper", "💀 Reaper", 200, 35, 340, 220),
    ("alpha", "👑 Alpha Zombie", 260, 40, 500, 300),
    ("abomination", "🧬 Abomination", 350, 48, 750, 450),
    ("overlord", "☣️ Zombie Overlord", 600, 60, 1500, 900),
]

WEAPONS = {
    "rusty_knife": ("🔪 Rusty Knife", 10, 0),
    "pipe": ("🔧 Metal Pipe", 18, 350),
    "bat": ("🏏 Baseball Bat", 25, 650),
    "machete": ("🗡️ Machete", 34, 1200),
    "pistol": ("🔫 Pistol", 42, 2200),
    "revolver": ("🔫 Revolver", 50, 3000),
    "shotgun": ("💥 Shotgun", 65, 4800),
    "smg": ("🔫 SMG", 78, 7000),
    "rifle": ("🎯 Rifle", 92, 9500),
    "crossbow": ("🏹 Crossbow", 100, 11000),
    "ar": ("⚔️ Assault Rifle", 120, 15000),
    "carbine": ("🔫 Carbine", 135, 18000),
    "lmg": ("💣 LMG", 155, 22000),
    "sniper": ("🎯 Sniper", 180, 28000),
    "plasma": ("⚡ Plasma Rifle", 220, 40000),
    "laser": ("🔴 Laser Gun", 260, 55000),
    "railgun": ("⚡ Railgun", 310, 75000),
    "doomblade": ("☠️ Doom Blade", 350, 100000),
    "phoenix": ("🔥 Phoenix Cannon", 420, 150000),
    "apocalypse": ("☢️ Apocalypse", 500, 250000),
    "titan": ("🤖 Titan Weapon", 600, 400000),
    "storm": ("🌩️ Storm Rifle", 720, 650000),
    "void": ("🌀 Void Blaster", 850, 900000),
    "omega": ("👑 Omega Cannon", 1000, 1500000),
    "neutron": ("☢️ Neutron Gun", 1150, 2200000),
    "galaxy": ("🌌 Galaxy Breaker", 1300, 3500000),
    "eclipse": ("🌑 Eclipse", 1500, 5000000),
    "singularity": ("🕳️ Singularity", 1800, 8000000),
    "infinity": ("♾️ Infinity Edge", 2200, 12000000),
    "godslayer": ("👑 Godslayer", 2800, 20000000),
}

ARMOR = {
    "torn_jacket": ("🧥 Torn Jacket", 0, 0),
    "leather": ("🥋 Leather Armor", 8, 500),
    "kevlar": ("🦺 Kevlar Vest", 15, 1800),
    "riot": ("🛡️ Riot Armor", 25, 5000),
    "tactical": ("🥷 Tactical Suit", 40, 12000),
    "military": ("🪖 Military Armor", 55, 25000),
    "heavy": ("🛡️ Heavy Armor", 75, 50000),
    "juggernaut": ("🤖 Juggernaut Suit", 100, 100000),
    "titanium": ("⚙️ Titanium Armor", 135, 250000),
    "nano": ("✨ Nano Armor", 175, 600000),
    "exosuit": ("🤖 Exosuit", 230, 1200000),
    "voidarmor": ("🌀 Void Armor", 300, 2500000),
    "apocalypse": ("☢️ Apocalypse Armor", 400, 5000000),
    "omegaarmor": ("👑 Omega Armor", 550, 10000000),
    "godarmor": ("🌟 God Armor", 750, 25000000),
    "infinityarmor": ("♾️ Infinity Armor", 1000, 50000000),
    "celestial": ("🌌 Celestial Armor", 1400, 100000000),
    "eternal": ("✨ Eternal Armor", 1900, 250000000),
    "mythic": ("👑 Mythic Armor", 2500, 500000000),
    "divine": ("💫 Divine Armor", 3500, 1000000000),
}

LOCATIONS = [
    ("🏚️", "Abandoned House", 1, 1),
    ("🏪", "Old Supermarket", 3, 2),
    ("🏥", "Ruined Hospital", 5, 3),
    ("🏭", "Dead Factory", 8, 4),
    ("🚉", "Underground Station", 12, 5),
    ("🪖", "Military Base", 18, 7),
    ("☣️", "Toxic Zone", 25, 10),
    ("🏰", "Zombie Fortress", 35, 15),
]

SPECIALS = {
    "adrenaline": ("💉 Adrenaline", 500),
    "smoke": ("💨 Smoke Bomb", 700),
    "rage": ("🩸 Rage Serum", 1200),
}

def weapon_attack(key):
    return WEAPONS.get(key, WEAPONS["rusty_knife"])[1]

def armor_defense(key):
    return ARMOR.get(key, ARMOR["torn_jacket"])[1]
