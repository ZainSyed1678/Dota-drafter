"""
Dota 2 Hero Knowledge Base: Beginner-Friendly Mechanics, Counters & Synergies
Provides deep 'How and Why' explanations for match recommendations.
"""

# ── 1. Hero Complexity & Role Categorization ─────────────────────────────────
CARRY_HEROES = {
    "Anti-Mage", "Arc Warden", "Bloodseeker", "Chaos Knight", "Clinkz", "Drow Ranger",
    "Faceless Void", "Gyrocopter", "Juggernaut", "Kez", "Lifestealer", "Lone Druid",
    "Luna", "Medusa", "Monkey King", "Morphling", "Naga Siren", "Phantom Assassin",
    "Phantom Lancer", "Razor", "Riki", "Slark", "Sniper", "Spectre", "Sven",
    "Terrorblade", "Troll Warlord", "Ursa", "Weaver", "Wraith King", "Alchemist",
    "Bristleback", "Dragon Knight", "Huskar", "Legion Commander", "Lycan", "Marci",
    "Meepo", "Muerta", "Templar Assassin", "Tiny", "Nature's Prophet", "Shadow Fiend"
}

MID_HEROES = {
    "Invoker", "Storm Spirit", "Ember Spirit", "Void Spirit", "Puck", "Queen of Pain",
    "Shadow Fiend", "Tinker", "Lina", "Leshrac", "Zeus", "Death Prophet", "Necrophos",
    "Templar Assassin", "Outworld Destroyer", "Huskar", "Meepo", "Arc Warden", "Sniper",
    "Viper", "Dragon Knight", "Kunkka", "Pangolier", "Razor", "Batrider", "Tiny",
    "Windranger", "Monkey King", "Earth Spirit", "Magnus", "Primal Beast", "Pudge",
    "Dawnbreaker", "Mars", "Doom", "Alchemist"
}

OFFLANE_HEROES = {
    "Axe", "Centaur Warrunner", "Mars", "Slardar", "Tidehunter", "Timbersaw",
    "Underlord", "Beastmaster", "Bristleback", "Dark Seer", "Doom", "Dragon Knight",
    "Legion Commander", "Lycan", "Magnus", "Night Stalker", "Pangolier", "Primal Beast",
    "Sand King", "Brewmaster", "Dawnbreaker", "Death Prophet", "Necrophos", "Viper",
    "Razor", "Chaos Knight", "Abaddon", "Kunkka", "Enigma", "Spirit Breaker",
    "Earthshaker", "Pudge", "Clockwerk", "Broodmother", "Nature's Prophet", "Omniknight"
}

SOFT_SUPPORTS = {
    "Earthshaker", "Rubick", "Mirana", "Tusk", "Clockwerk", "Hoodwink",
    "Earth Spirit", "Spirit Breaker", "Bounty Hunter", "Nyx Assassin",
    "Marci", "Phoenix", "Dark Willow", "Snapfire", "Techies", "Pudge",
    "Lion", "Shadow Shaman", "Skywrath Mage", "Tiny", "Ringmaster",
    "Keeper of the Light", "Windranger", "Grimstroke", "Venomancer",
    "Vengeful Spirit", "Winter Wyvern", "Batrider", "Muerta", "Monkey King",
    "Riki", "Treant Protector", "Weaver", "Zeus", "Enigma", "Nature's Prophet", "Elder Titan", "Visage"
}

HARD_SUPPORTS = {
    "Crystal Maiden", "Dazzle", "Oracle", "Lich", "Jakiro",
    "Treant Protector", "Bane", "Disruptor", "Undying", "Shadow Demon",
    "Warlock", "Keeper of the Light", "Silencer", "Io", "Chen",
    "Abaddon", "Ogre Magi", "Witch Doctor", "Winter Wyvern",
    "Ancient Apparition", "Omniknight", "Shadow Shaman", "Grimstroke",
    "Pugna", "Enchantress", "Vengeful Spirit", "Lion", "Elder Titan", "Visage"
}

HERO_DIFFICULTY = {
    # High micro / High mechanical complexity
    "Meepo": "Hard", "Invoker": "Hard", "Chen": "Hard", "Morphling": "Hard",
    "Arc Warden": "Hard", "Lone Druid": "Hard", "Earth Spirit": "Hard",
    "Visage": "Hard", "Brewmaster": "Hard", "Tinker": "Hard", "Io": "Hard",
    "Puck": "Moderate", "Storm Spirit": "Moderate", "Ember Spirit": "Moderate",
    "Void Spirit": "Moderate", "Shadow Fiend": "Moderate", "Terrorblade": "Moderate",
    "Slark": "Moderate", "Timbersaw": "Moderate", "Anti-Mage": "Moderate",
    "Kunkka": "Moderate", "Rubick": "Moderate", "Elder Titan": "Moderate",
    "Batrider": "Moderate", "Phoenix": "Moderate", "Enigma": "Moderate",
    "Oracle": "Moderate", "Pangolier": "Moderate", "Muerta": "Moderate",
    "Dark Willow": "Moderate", "Monkey King": "Moderate", "Mirana": "Moderate",
    "Naga Siren": "Moderate", "Grimstroke": "Moderate", "Techies": "Moderate",
    "Primal Beast": "Moderate", "Marci": "Moderate", "Beastmaster": "Moderate",
    "Lycan": "Moderate", "Broodmother": "Moderate", "Keeper of the Light": "Moderate",
    # All others default to Easy (Beginner Friendly)
}

def get_hero_difficulty(hero: str) -> str:
    return HERO_DIFFICULTY.get(hero, "Easy")

# ── 2. Hero Overviews (1-line plain English role summary) ────────────────────
HERO_OVERVIEWS = {
    "Axe": "Frontline initiator who taunts enemies with Berserker's Call, spinning to deal massive physical damage when hit.",
    "Anti-Mage": "Hyper-mobile late-game agility carry who burns enemy mana pools and explodes casters with Mana Void.",
    "Earthshaker": "Teamfight disabler who punishes grouped enemies and illusion armies with devastating Echo Slam shockwaves.",
    "Juggernaut": "Versatile right-click carry with built-in spell immunity (Blade Fury) and untargetable Omnislash damage.",
    "Pudge": "Tanky ganker who hooks enemies out of position and suppresses them with Meat Hook and Dismember.",
    "Sniper": "Long-range marksman who dishes out constant physical damage from extreme safety if well protected.",
    "Drow Ranger": "Precision archer who silences casters, slows pursuers, and pierces high base armor with Marksmanship.",
    "Viper": "Lane-dominating ranged corrosive carry who breaks passive abilities and slows targets to a crawl.",
    "Crystal Maiden": "Frost mage support providing global team mana regeneration and channeled Freezing Field teamfight slow.",
    "Lion": "Hard lockdown support featuring instant Hex, stun, and lethal Finger of Death magical burst.",
    "Tidehunter": "Indestructible tank who shrugs off debuffs with Kraken Shell and stuns entire teams with Ravage.",
    "Slardar": "Aggressive physical bruiser who sprints down targets, bashes frequently, and strips all armor with Corrosive Haze.",
    "Wraith King": "Newbie-friendly durable carry who reincarnates upon death and commands critical striking skeleton minions.",
    "Bristleback": "Relentless tank who takes vastly reduced damage from behind and stacks armor-shredding Quill Sprays.",
    "Silencer": "Anti-spellcaster intelligence hero who halts all enemy spellcasting globally with Global Silence.",
    "Faceless Void": "Time-bending carry who locks all units inside Chronosphere to safely eliminate primary targets.",
    "Witch Doctor": "Support who drops bouncing stuns, heals allies, and channels catastrophic Death Ward physical damage.",
    "Zeus": "Global lightning god who dishes out massive percentage-based magic damage and reveals invisible enemies.",
    "Spirit Breaker": "Global map-charger who barrels across the map to knock down and bash isolated targets.",
    "Legion Commander": "Dueling warrior who locks enemies in combat to permanently gain bonus attack damage upon victory.",
    "Phantom Assassin": "High-burst assassin with phantom blink, natural evasion, and screen-shattering Coup de Grace critical hits.",
    "Ursa": "Fierce melee bear who shreds Roshan and individual heroes by stacking exponential Fury Swipes attack damage.",
    "Ogre Magi": "Beefy frontline support with luck-based Multicast that duplicates stuns, slows, and Bloodlust buffs.",
    "Necrophos": "Sustained magic aura carrier whose Reaper's Scythe executes low-health enemies and extends death timers.",
    "Ancient Apparition": "Ranged frost support whose global Ice Blast completely negates all healing and lifesteal.",
    "Disruptor": "Positioning controller who pulls escaping heroes back with Glimpse and mutes them inside Static Storm.",
    "Lina": "Fiery burst carry/mid with blistering attack speed stacks and instant single-target Laguna Blade execution.",
    "Sven": "Gigantic cleaving carry who boosts team armor and turns on God's Strength to wipe grouped teams in 2 hits.",
    "Centaur Warrunner": "High-HP initiator who reflects damage with Retaliate and grants maximum team movement speed with Stampede.",
    "Shadow Shaman": "Objective pusher who pins enemies with lengthy Shackles/Hex and summons Mass Serpent Wards for towers.",
    "Jakiro": "Dual-headed dragon who controls lanes and chokepoints with heavy ice stuns and melting fire pools.",
    "Underlord": "Macro-strategy tank who reduces enemy attack damage, controls lanes with Firestorm, and warps the whole team.",
    "Bounty Hunter": "Invisible tracker who grants bonus gold to the entire team on kills and reveals stealth targets.",
    "Nyx Assassin": "Stealth assassin who turns enemy attacks into stuns with Spiked Carapace and bursts casters with Mind Flare.",
    "Troll Warlord": "Relentless fighter who roots and perma-bashes targets in melee stance while surviving burst with Battle Trance.",
    "Meepo": "Multi-clone core who roots targets continuously with chain Earthbind and overwhelms heroes with Poof burst.",
    "Visage": "Familiar commander who steals enemy speed with Grave Chill and drops heavy physical burst with gargoyle familiars.",
    "Vengeful Spirit": "Tactical support/core who swaps positions with Nether Swap, lowers armor with Wave of Terror, and stuns.",
    "Outworld Destroyer": "High-intellect carry who deals massive pure damage with Arcane Orb and saves allies with Astral Imprisonment.",
    "Enigma": "Game-changing teamfight initiator whose Black Hole pierces spell immunity to lock down entire enemy teams.",
    "Muerta": "Gunslinger carry who fears enemies with Dead Shot and fires double physical/magical shots with Pierce the Veil.",
    "Riki": "Agile stealth assassin who silences enemies in Smoke Screen and slices through backlines with Tricks of the Trade.",
    "Dragon Knight": "Indestructible dragon knight who delivers long-duration Dragon Tail stuns and burns towers with splash damage.",
    "Spectre": "Global late-game phantom who deals pure damage with Desolate, reflects damage with Dispersion, and haunts the map.",
    "Leshrac": "High-tempo disco pony who destroys towers with physical Diabolic Edict and melts teamfights with Pulse Nova.",
    "Phoenix": "Sun god who cripples enemy attack speed with Fire Spirits, beams percentage damage, and revives with Supernova.",
    "Dazzle": "Lifesaving priest who prevents death with Shallow Grave, slows enemies with Poison Touch, and heals with Shadow Wave.",
    "Omniknight": "Holy paladin who grants full physical damage immunity with Guardian Angel and purifies allies with burst heals.",
    "Abaddon": "Unholy knight who dispels debuffs with Aphotic Shield and turns enemy damage into healing with Borrowed Time.",
    "Mars": "God of war who traps foes inside Arena of Blood, pins them with Spear of Mars, and deflects attacks with Bulwark.",
    "Timbersaw": "Tree-shredding bruiser who cuts base attributes and deals pure damage with Whirling Death and Chakram.",
    "Invoker": "Versatile master mage commanding 10 spells including Cataclysm Sunstrikes, Tornado, and EMP mana drainage.",
    "Storm Spirit": "Electrifying zip initiator who traverses the entire map with Ball Lightning to pick off isolated targets.",
    "Ember Spirit": "Sleek flame swordsman who dodges spells with Sleight of Fist and jumps between Fire Remnants across fights.",
    "Void Spirit": "Astral void fighter who phases through dimensions with Dissimilate and steps through enemies with Astral Step.",
    "Puck": "Elusive fairy dragon who leashes enemies with Dream Coil, silences with Waning Rift, and phase shifts incoming spells.",
    "Shadow Fiend": "Soul-harvesting nuker who lands triple Shadowraze bursts, lowers enemy armor, and channels massive Requiem damage.",
    "Queen of Pain": "High-mobility succubus who blinks into backlines to unleash pure damage Sonic Wave scream bursts.",
    "Tinker": "Defensive laser specialist who blinds right-clickers with Laser, fires tracking Warp Flare, and re-arms items.",
    "Templar Assassin": "Psionic burst carry who blocks damage with Refraction, melts armor with Meld, and sets vision traps.",
    "Huskar": "Fierce berserker who sacrifices health to fling Burning Spears and leaps into battle with Life Break.",
    "Doom": "Infernal lord whose Doom completely silences, mutes, and neutralizes a priority enemy core out of the fight.",
    "Night Stalker": "Terror of the night who hunts down backlines with massive night movement speed and AoE Crippling Fear silence.",
    "Dark Seer": "Battlefield manipulator who accelerates allies with Surge and pulls teams into Wall of Replica with Vacuum.",
    "Beastmaster": "Primal commander whose roar pierces spell immunity to stun targets while summons scout and slow enemies.",
    "Pangolier": "Swashbuckling fencer who rolls through teamfights with Rolling Thunder, disarming and bouncing through lines.",
    "Primal Beast": "Raging behemoth who tramples through terrain and pummels targets repeatedly into the ground with Pulverize.",
    "Sand King": "Desert scorpion who stuns lines with Burrowstrike, channels Epicenter earthquakes, and hides in Sand Storm.",
    "Brewmaster": "Drunken brawler who splits into four elemental spirits with unique stuns, dispels, and cyclone disables.",
    "Dawnbreaker": "Cosmic warrior who lands Starbreaker hammer combos and slams globally across the map with Solar Guardian.",
    "Razor": "Plasma revenant who drains enemy attack damage down to zero with Static Link while moving at max speed.",
    "Chaos Knight": "RNG-based powerhouse who pulls enemies with Reality Rift and summons catastrophic critical striking Phantasms.",
    "Broodmother": "Spider queen who swarms towers with spiderlings, dominates lanes, and slows targets with Silken Bola.",
    "Nature's Prophet": "Global commander who sprouts trees, summons Treant push armies, and teleports anywhere on the map.",
    "Slark": "Slippery fish carry who leashes targets with Pounce, steals permanent agility stats, and purges all disables.",
    "Medusa": "Impenetrable late-game tank who turns incoming damage into mana loss with Mana Shield and petrifies with Stone Gaze.",
    "Morphling": "Agility morpher who shifts stats to gain max HP or blistering attack speed, copying enemy hero spells.",
    "Phantom Lancer": "Illusion swarm carry who multiplies into dozens of clones with each hit, exhausting single-target spells.",
    "Terrorblade": "Demon carry who creates high-damage illusions, ranges enemies with Metamorphosis, and swaps HP with Sunder.",
    "Weaver": "Time-skipping insect who swarms enemies with armor-shredding beetles and rewinds time/HP with Time Lapse.",
    "Alchemist": "Greedy chemical brawler who stacks exponential gold with Greevil's Greed and heals through Chemical Rage.",
    "Bane": "Nightmare controller who locks down target cores through spell immunity with continuous Fiend's Grip channels.",
    "Chen": "Holy priest who commands jungle creep armies with unique auras and heals the entire team globally with Hand of God.",
    "Dark Willow": "Fae trickster who roots with Brambles, untargetably fires Shadow Realm magic, and terrifies with Terrorize.",
    "Earth Spirit": "Geomancer stone roller who kicks stone stuns, pulls silence grips, and spreads Magnetize across fights.",
    "Elder Titan": "World-shaper whose Natural Order strips 100% of base armor and magic resistance while Earth Splitter cracks HP.",
    "Enchantress": "Untouchable forest nymph who slows enemy attacks, commands creeps, and fires lethal Impetus pure damage.",
    "Hoodwink": "Forest ranger who shoots Acorn Shot ricochets, ties enemies to trees with Bushwhack, and snipes with Sharpshooter.",
    "Io": "Tether companion who overcharges carry attack speed and relocates allies globally for coordinated strikes.",
    "Keeper of the Light": "Radiant elder who blasts creeping waves with Illuminate, refunds team mana, and blinds with Blinding Light.",
    "Lich": "Frost archmage who shields cores with Frost Shield armor and bounces catastrophic Chain Frost through clumps.",
    "Lifestealer": "Parasitic carry with built-in spell immunity Rage, lifesteal Feast, and Infest inside allied tanks.",
    "Lone Druid": "Bear master who commands a durable second hero Spirit Bear equipped with entangles and full item inventories.",
    "Lycan": "Pack leader who turns into an unslowable wolf with Shapeshift, running down backlines with boosted wolves.",
    "Marci": "Loyal powerhouse who throws enemies with Dispose, jumps across allies with Rebound, and unleashes rapid fury punches.",
    "Mirana": "Priestess of the Moon who lands long-range Sacred Arrows and grants teamwide invisibility with Moonlight Shadow.",
    "Monkey King": "Trickster king who leaps across treetops, stuns with Boundless Strike, and summons Wukong's Command soldier rings.",
    "Oracle": "Prophetic savior who delays fatal damage with False Promise, disarms foes, and dispels buffs with Fortune's End.",
    "Pugna": "Nether mage whose Nether Ward zaps enemy casters and Life Drain siphons health rapidly to allies or self.",
    "Ringmaster": "Carnival controller whose Wheel of Wonder hypnotizes enemies and Tame the Beasts whips area fear.",
    "Shadow Demon": "Banishment controller who disrupts allies from death, poisons lanes, and removes enemy passives with Demonic Purge.",
    "Skywrath Mage": "High-burst mage who silences with Ancient Seal and drops catastrophic Mystic Flare magic damage in seconds.",
    "Snapfire": "Dragon toad grandma who fires scatterblasts, grants carry attack speed with Lil' Shredder, and lobs Mortimer Kisses.",
    "Techies": "Explosives expert who silences and disarms with Sticky Bombs, leaps into fights with Blast Off!, and controls chokepoints.",
    "Tiny": "Rock giant who tosses enemies out of position, lands Avalanche stun combos, and tree-cleaves through teams.",
    "Treant Protector": "Living tree who repairs structures globally with Living Armor and roots entire teams in place with Overgrowth.",
    "Tusk": "Brawling walrus who gathers allies inside Snowball to dodge spells, walls terrain with Ice Shards, and Walrus PUNCHES.",
    "Undying": "Flesh golem who siphons enemy strength with Decay and drops Tombstone to spawn endless slowing zombies.",
    "Venomancer": "Toxic slug who litters lanes with Plague Wards, slows enemies to a crawl with Venomous Gale, and poisons with Nova.",
    "Warlock": "Dark summoner who links enemy teams with Fatal Bonds and drops massive stunning Chaotic Offering Golems.",
    "Winter Wyvern": "Ice dragon who saves cores from physical attacks with Cold Embrace and forces enemies to kill each other with Winter's Curse.",
}

def get_hero_overview(hero: str) -> str:
    if hero in HERO_OVERVIEWS:
        return HERO_OVERVIEWS[hero]
    tags = HERO_TAGS.get(hero, [])
    if tags:
        tag_desc = ", ".join(t.replace("_", " ") for t in tags[:2])
        return f"A dependable pick specializing in {tag_desc} with impactful teamfight presence."
    return "A versatile pick offering dependable lane presence and teamfight utility."

# ── 3. Specific Handcrafted Counter Matchups (How & Why) ─────────────────────
SPECIFIC_COUNTERS = {
    ("Huskar", "Anti-Mage"): {
        "one_liner": "Huskar uses health instead of mana for abilities, rendering Anti-Mage's Mana Break useless while Burning Spears melts him.",
        "how_and_why": "Huskar casts abilities using health rather than mana, neutralizing Anti-Mage's Mana Break and Mana Void completely while Burning Spears shreds Anti-Mage's low physical health pool.",
        "abilities": ["Burning Spears", "Life Break", "Berserker's Blood"],
        "tip": "Aggressively trade with Anti-Mage in the early game before he gets his farming items online."
    },
    ("Disruptor", "Anti-Mage"): {
        "one_liner": "Static Storm silences Anti-Mage to prevent Blink escapes, while Glimpse drags him back after he leaps away.",
        "how_and_why": "Disruptor completely shuts down Anti-Mage's mobility. Static Storm prevents him from Blinking or activating Counterspell, and Glimpse resets any successful escape.",
        "abilities": ["Static Storm", "Glimpse", "Kinetic Field"],
        "tip": "Catch Anti-Mage inside Kinetic Field and drop Static Storm before he can activate Counterspell."
    },
    ("Legion Commander", "Anti-Mage"): {
        "one_liner": "Duel forces Anti-Mage into physical combat, locking down Blink and melting his low health pool with Blade Mail.",
        "how_and_why": "Duel prevents Anti-Mage from Blinking or using Counterspell. Combined with Blade Mail, Anti-Mage kills himself on his own physical damage.",
        "abilities": ["Duel", "Overwhelming Odds", "Press the Attack"],
        "tip": "Blink and Duel Anti-Mage immediately from fog before he has time to react with Counterspell."
    },
    ("Bloodseeker", "Anti-Mage"): {
        "one_liner": "Rupture forces Anti-Mage to remain stationary or take fatal pure damage if he Blinks, while Thirst tracks his escapes.",
        "how_and_why": "Rupture deals lethal pure damage based on distance moved, completely countering Blink. Thirst also grants vision of Anti-Mage whenever he is low health in jungle.",
        "abilities": ["Rupture", "Blood Rite", "Thirst"],
        "tip": "Rupture Anti-Mage in fights; if he Blinks away, the distance traveled will instantly kill him."
    },
    ("Axe", "Anti-Mage"): {
        "one_liner": "Berserker's Call pierces Counterspell to lock down Anti-Mage and shred him with pure physical Counter Helix spins.",
        "how_and_why": "Berserker's Call taunts through Counterspell and magic resistance, forcing Anti-Mage to trigger Counter Helix spins that shred his fragile physical health.",
        "abilities": ["Berserker's Call", "Counter Helix", "Culling Blade"],
        "tip": "Blink-Call Anti-Mage with Blade Mail active to burst him down before he can Blink."
    },
    ("Slardar", "Anti-Mage"): {
        "one_liner": "Corrosive Haze removes Anti-Mage's armor and tracks him, while continuous bashes prevent him from escaping.",
        "how_and_why": "Anti-Mage relies on base armor rather than HP. Corrosive Haze shreds his armor down to negative values and gives true sight, allowing Slardar to bash him down in seconds.",
        "abilities": ["Corrosive Haze", "Slithereen Crush", "Bash of the Deep"],
        "tip": "Keep Corrosive Haze active on Anti-Mage at all times so he cannot hide in the trees or juke."
    },
    ("Outworld Destroyer", "Anti-Mage"): {
        "one_liner": "Arcane Orb deals heavy pure damage that ignores Anti-Mage's magic resist, melting his low health pool.",
        "how_and_why": "Anti-Mage is designed to resist magic damage, but Outworld Destroyer deals massive pure damage with Arcane Orb, completely ignoring Counterspell's passive resistance.",
        "abilities": ["Arcane Orb", "Astral Imprisonment", "Sanity's Eclipse"],
        "tip": "Hit Anti-Mage with Arcane Orb to melt him; use Astral to save teammates targeted by Mana Void."
    },
    ("Meepo", "Anti-Mage"): {
        "one_liner": "Chain Earthbind roots Anti-Mage continuously to stop Blink while clone burst damage eliminates him instantly.",
        "how_and_why": "Earthbind completely disables Blink and can be chained indefinitely across clones, while Poof and right-click burst overwhelm Anti-Mage before he comes online.",
        "abilities": ["Earthbind", "Poof", "Divided We Stand"],
        "tip": "Throw Earthbind to root Anti-Mage and stack Poof damage before he can react."
    },
    ("Shadow Shaman", "Anti-Mage"): {
        "one_liner": "Massive chain-lockdown with Hex and Shackles prevents Anti-Mage from casting Blink or Counterspell.",
        "how_and_why": "Shadow Shaman provides instant Hex followed by Shackles, locking Anti-Mage down for over 7 seconds without giving him an opportunity to Blink or reflect spells.",
        "abilities": ["Hex", "Shackles", "Mass Serpent Ward"],
        "tip": "Initiate from fog with Hex first so Anti-Mage cannot reflect your disable with Counterspell."
    },
    ("Grimstroke", "Anti-Mage"): {
        "one_liner": "Soulbind leashes Anti-Mage to prevent Blink and duplicates ally disables directly onto him.",
        "how_and_why": "Soulbind leashes Anti-Mage to an allied hero, making Blink impossible, and doubles all single-target targeted spells cast by your team.",
        "abilities": ["Soulbind", "Phantom's Embrace", "Stroke of Fate"],
        "tip": "Cast Soulbind on Anti-Mage when an enemy is nearby to tether him and silence him with Phantom's Embrace."
    },
    ("Troll Warlord", "Anti-Mage"): {
        "one_liner": "Troll Warlord roots Anti-Mage with Whirling Axes and perma-bashes him in melee form, preventing Blink while surviving with Battle Trance.",
        "how_and_why": "Troll Warlord easily locks down Anti-Mage with melee Net roots and high-speed Fervor bashes, stopping him from Blinking away while Battle Trance prevents Troll from dying to burst.",
        "abilities": ["Whirling Axes (Melee)", "Fervor", "Battle Trance"],
        "tip": "Stay in melee stance to continuously bash and root Anti-Mage when he tries to turn on you."
    },
    ("Nyx Assassin", "Anti-Mage"): {
        "one_liner": "Spiked Carapace reflects Mana Break and Mana Void to stun Anti-Mage, while Vendetta burst and Mind Flare punish him.",
        "how_and_why": "Spiked Carapace turns Anti-Mage's own right-click mana burns into instant self-stuns. Vendetta and Mind Flare deal massive burst before AM can pop Counterspell.",
        "abilities": ["Spiked Carapace", "Vendetta", "Mind Flare"],
        "tip": "Pop Spiked Carapace the instant Anti-Mage attacks you to stun him and interrupt his attack chain."
    },
    ("Bounty Hunter", "Anti-Mage"): {
        "one_liner": "Track provides continuous true sight to prevent Anti-Mage from escaping into the jungle, while Jinada steals his gold in lane.",
        "how_and_why": "Track keeps Anti-Mage revealed wherever he Blinks across the map, granting movement speed to pursuers, while Jinada harasses him and siphons away his farm.",
        "abilities": ["Track", "Jinada", "Shadow Walk"],
        "tip": "Keep Anti-Mage Tracked at all times so your team can hunt him down inside his own jungle camps."
    },
    ("Phoenix", "Anti-Mage"): {
        "one_liner": "Fire Spirits drastically slows Anti-Mage's attack speed, crippling his Mana Break trading and ability to farm waves.",
        "how_and_why": "Fire Spirits imposes a massive attack speed slow that prevents Anti-Mage from hitting attacks or burning mana, while Sun Ray deals percentage damage.",
        "abilities": ["Fire Spirits", "Sun Ray", "Supernova"],
        "tip": "Land Fire Spirits on Anti-Mage at the start of skirmishes to completely neutralize his right-click damage."
    },
    ("Crystal Maiden", "Anti-Mage"): {
        "one_liner": "Frostbite roots Anti-Mage in place to disable his Blink, giving allies time to collapse and burst him down.",
        "how_and_why": "Frostbite applies a hard root that completely disables Anti-Mage's Blink, leaving him immobile and allowing physical carries to burst him down.",
        "abilities": ["Frostbite", "Crystal Nova", "Freezing Field"],
        "tip": "Cast Frostbite from behind your core so Anti-Mage is rooted before he can jump on you."
    },
    ("Dazzle", "Anti-Mage"): {
        "one_liner": "Shallow Grave saves allies from lethal Mana Void explosions while Poison Touch slows and kites Anti-Mage continuously.",
        "how_and_why": "Shallow Grave prevents Anti-Mage from executing low-mana allies with Mana Void, while Poison Touch keeps him slowed to a crawl in teamfights.",
        "abilities": ["Shallow Grave", "Poison Touch", "Shadow Wave"],
        "tip": "Hold Shallow Grave for the ally Anti-Mage targets with Mana Void."
    },
    ("Ancient Apparition", "Anti-Mage"): {
        "one_liner": "Ice Blast prevents Anti-Mage from healing with Vladmir's or Satanic, while Cold Feet forces him to Blink away from fights.",
        "how_and_why": "Ice Blast completely halts all health regeneration and lifesteal, preventing Anti-Mage from sustaining through teamfights with lifesteal items.",
        "abilities": ["Ice Blast", "Cold Feet", "Ice Vortex"],
        "tip": "Launch Ice Blast across the teamfight when Anti-Mage commits with Manta Style."
    },
    ("Enigma", "Anti-Mage"): {
        "one_liner": "Black Hole pierces Counterspell to lock down Anti-Mage completely, while Midnight Pulse percentage damage melts him.",
        "how_and_why": "Black Hole pierces all magic resistance and Counterspell reflections, holding Anti-Mage completely stationary while Midnight Pulse shreds his health pool.",
        "abilities": ["Black Hole", "Midnight Pulse", "Malefice"],
        "tip": "Wait for Anti-Mage to commit into your team before catching him inside Black Hole."
    },
    ("Visage", "Anti-Mage"): {
        "one_liner": "Grave Chill steals Anti-Mage's attack and move speed, while Familiars deal heavy physical damage that ignores magic resist.",
        "how_and_why": "Grave Chill slows Anti-Mage while boosting Visage's speed, and Familiars deliver heavy physical drop burst that bypasses Anti-Mage's high magic resistance.",
        "abilities": ["Grave Chill", "Summon Familiars", "Soul Assumption"],
        "tip": "Cast Grave Chill to slow Anti-Mage and order your Familiars to focus him with Stone Form stuns."
    },
    ("Omniknight", "Anti-Mage"): {
        "one_liner": "Guardian Angel grants immunity to physical right-clicks while Purification burst heals allies through Mana Break trades.",
        "how_and_why": "Guardian Angel completely negates Anti-Mage's primary damage source (physical right-clicks), making your entire team immune to his attacks during fights.",
        "abilities": ["Guardian Angel", "Purification", "Repel"],
        "tip": "Cast Guardian Angel the moment Anti-Mage pops Manta Style to jump an ally."
    },
    ("Abaddon", "Anti-Mage"): {
        "one_liner": "Aphotic Shield dispels burns and absorbs Mana Void burst, while Borrowed Time allows Abaddon to tank Anti-Mage indefinitely.",
        "how_and_why": "Aphotic Shield absorbs burst damage and dispels debuffs, while Borrowed Time converts Anti-Mage's heavy attacks into pure health regeneration.",
        "abilities": ["Aphotic Shield", "Borrowed Time", "Mist Coil"],
        "tip": "Put Aphotic Shield on allies that Anti-Mage blinks onto to absorb his opening attack burst."
    },
    ("Sven", "Anti-Mage"): {
        "one_liner": "Storm Hammer provides reliable ranged lockdown while God's Strength right-clicks cleave down Anti-Mage and his illusions in 2 hits.",
        "how_and_why": "Sven's God's Strength and Great Cleave wipe Anti-Mage and his Manta illusions in seconds, using physical burst that ignores magic resistance.",
        "abilities": ["God's Strength", "Great Cleave", "Storm Hammer"],
        "tip": "Pop God's Strength and BKB, stun Anti-Mage with Storm Hammer, and cleave him down."
    },
    ("Spectre", "Anti-Mage"): {
        "one_liner": "Desolate deals pure damage through Counterspell, while Haunt allows Spectre to instantly jump onto Anti-Mage anywhere on the map.",
        "how_and_why": "Desolate adds pure damage that bypasses Anti-Mage's high magic resistance, while Haunt prevents Anti-Mage from split-pushing or farming in peace.",
        "abilities": ["Haunt", "Desolate", "Dispersion"],
        "tip": "Press Haunt whenever Anti-Mage shows on a split wave to jump him and shut down his farm."
    },
    ("Dragon Knight", "Anti-Mage"): {
        "one_liner": "Dragon Tail delivers an undodgeable long stun while high base armor and Corrosive Breath neutralize Anti-Mage's attacks.",
        "how_and_why": "Dragon Tail provides a massive, reliable stun in Elder Dragon Form, while Dragon Blood's armor makes DK nearly impervious to Anti-Mage's physical attacks.",
        "abilities": ["Dragon Tail", "Elder Dragon Form", "Dragon Blood"],
        "tip": "Blink in with Dragon Form active to land an immediate ranged Dragon Tail stun."
    },
    ("Riki", "Anti-Mage"): {
        "one_liner": "Smoke Screen silences Anti-Mage and causes 75% miss chance, preventing Blink and shutting down his physical trading.",
        "how_and_why": "Smoke Screen applies an inescapable AoE silence and massive blind, trapping Anti-Mage inside without the ability to Blink away or hit back.",
        "abilities": ["Smoke Screen", "Tricks of the Trade", "Blink Strike"],
        "tip": "Drop Smoke Screen directly on top of Anti-Mage so he cannot cast Blink to escape."
    },
    ("Muerta", "Anti-Mage"): {
        "one_liner": "Dead Shot fears Anti-Mage out of position while Gunslinger delivers overwhelming physical and magical hybrid burst.",
        "how_and_why": "Dead Shot forces Anti-Mage to run in fear, interrupting his attack flow, while Gunslinger duplicate shots overwhelm him at long range.",
        "abilities": ["Dead Shot", "Gunslinger", "The Calling"],
        "tip": "Use Dead Shot off trees to ricochet and fear Anti-Mage back toward your team."
    },
    ("Night Stalker", "Anti-Mage"): {
        "one_liner": "Crippling Fear silences Anti-Mage for up to 6 seconds in the night, preventing Blink escapes while Dark Ascension shreds him.",
        "how_and_why": "Crippling Fear applies an undispellable AoE silence aura that follows Night Stalker, making it impossible for Anti-Mage to Blink away while Night Stalker flies through trees with max movement speed.",
        "abilities": ["Crippling Fear", "Dark Ascension", "Void"],
        "tip": "Activate Dark Ascension and run directly onto Anti-Mage with Crippling Fear active."
    },
    ("Beastmaster", "Anti-Mage"): {
        "one_liner": "Primal Roar pierces Counterspell to lock down Anti-Mage through spell immunity, allowing Boar slows and team follow-up to kill him.",
        "how_and_why": "Primal Roar delivers an undodgeable BKB-piercing stun through Counterspell, while Boar poison slows Anti-Mage's movement and attack speed.",
        "abilities": ["Primal Roar", "Call of the Wild Boar", "Wild Axes"],
        "tip": "Roar Anti-Mage the instant he blinks in so your team can chain-stun him before he can escape."
    },
    ("Chaos Knight", "Anti-Mage"): {
        "one_liner": "Reality Rift pulls Anti-Mage in and lowers armor while Phantasm illusions and Chaos Bolt stun burst him before he can react.",
        "how_and_why": "Chaos Knight's physical burst tears through Anti-Mage's low base HP pool. Reality Rift pulls him in and reduces armor, while Phantasm illusions deal 300%+ extra physical critical damage.",
        "abilities": ["Phantasm", "Reality Rift", "Chaos Bolt"],
        "tip": "Pop Phantasm and cast Reality Rift on Anti-Mage to strike him with all illusions simultaneously."
    },
    ("Dark Seer", "Anti-Mage"): {
        "one_liner": "Wall of Replica creates high-damage Anti-Mage illusions with full Mana Break that burn Anti-Mage's own mana pool.",
        "how_and_why": "Wall of Replica creates illusions of Anti-Mage that deal 100%+ damage and carry his full Mana Break passive, turning his own mana drain back on him and exploding him with Ion Shell.",
        "abilities": ["Wall of Replica", "Vacuum", "Ion Shell"],
        "tip": "Vacuum Anti-Mage through Wall of Replica so the created illusion attacks and burns his mana."
    },
    ("Dawnbreaker", "Anti-Mage"): {
        "one_liner": "Solar Guardian provides global team save against Mana Void, while Starbreaker physical hammer hits bypass magic resistance.",
        "how_and_why": "Solar Guardian heals and stuns in a global AoE around allies targeted by Anti-Mage, while Starbreaker deals pure physical damage that bypasses his magic resistance.",
        "abilities": ["Solar Guardian", "Starbreaker", "Celestial Hammer"],
        "tip": "Land Solar Guardian directly on the ally Anti-Mage jumps to heal them and stun Anti-Mage."
    },
    ("Pudge", "Anti-Mage"): {
        "one_liner": "Dismember pierces spell reflection to suppress Anti-Mage in place, while Meat Hook drags him out of teamfight position.",
        "how_and_why": "Dismember pierces spell immunity and Counterspell to lock Anti-Mage in place for 3 seconds, giving allies guaranteed setup to eliminate him.",
        "abilities": ["Dismember", "Meat Hook", "Rot"],
        "tip": "Blink directly onto Anti-Mage and press Dismember immediately so he cannot Blink."
    },
    ("Magnus", "Anti-Mage"): {
        "one_liner": "Reverse Polarity pierces Counterspell to pull Anti-Mage into a 3.5-second stun, while Empower grants cleave to burn his illusions.",
        "how_and_why": "Reverse Polarity pierces spell immunity and Counterspell to drag Anti-Mage into a 3.5-second stun, while Empower gives physical cleave to wipe his Manta illusions.",
        "abilities": ["Reverse Polarity", "Empower", "Skewer"],
        "tip": "Blink into Anti-Mage and cast Reverse Polarity before he can pop Counterspell."
    },
    ("Invoker", "Anti-Mage"): {
        "one_liner": "EMP drains massive mana while Tornado and Cold Snap continuously interrupt Anti-Mage's attack flow and escape attempts.",
        "how_and_why": "Cold Snap continuously interrupts Anti-Mage on every damage tick, while EMP drains his mana pool to prevent Blink and Cataclysm deals pure damage.",
        "abilities": ["Cold Snap", "EMP", "Tornado", "Cataclysm"],
        "tip": "Apply Cold Snap to Anti-Mage so every allied attack interrupts his attack and cast animations."
    },
    ("Sniper", "Anti-Mage"): {
        "one_liner": "Headshot continuously knocks Anti-Mage out of attack range, while Concussive Grenade disarms his Mana Break.",
        "how_and_why": "Sniper stays hundreds of units away, utilizing Headshot knockbacks and Concussive Grenade knockbacks/disarms to prevent Anti-Mage from ever getting into melee range.",
        "abilities": ["Headshot", "Concussive Grenade", "Take Aim"],
        "tip": "Use Concussive Grenade the moment Anti-Mage blinks on top of you to push him away and disarm him."
    },
    ("Lion", "Anti-Mage"): {
        "one_liner": "Instant Hex and Earth Spike chain-stun Anti-Mage before he can pop Counterspell, setting up lethal burst.",
        "how_and_why": "Lion features an instant cast Hex that Anti-Mage cannot reflect on reaction, followed by Earth Spike and Mana Drain to lock him down completely.",
        "abilities": ["Hex", "Earth Spike", "Finger of Death"],
        "tip": "Initiate from fog or with Blink Dagger directly using Hex so Counterspell cannot trigger."
    },
    ("Underlord", "Anti-Mage"): {
        "one_liner": "Pit of Malice roots Anti-Mage repeatedly to disable Blink, while Atrophy Aura heavily reduces his right-click damage.",
        "how_and_why": "Pit of Malice continuously roots units that step inside, preventing Blink escapes, while Atrophy Aura removes a huge percentage of Anti-Mage's attack damage.",
        "abilities": ["Pit of Malice", "Atrophy Aura", "Firestorm"],
        "tip": "Place Pit of Malice right where Anti-Mage is standing to prevent him from Blinking away."
    },
    ("Mars", "Anti-Mage"): {
        "one_liner": "Arena of Blood traps Anti-Mage inside physical walls while Spear of Mars pins him to prevent Blink escapes.",
        "how_and_why": "Arena of Blood blocks Anti-Mage from walking out and deflects his attacks, while Spear of Mars stuns him against the arena walls.",
        "abilities": ["Arena of Blood", "Spear of Mars", "God's Rebuke"],
        "tip": "Trap Anti-Mage inside Arena of Blood and pin him with Spear against the arena soldiers."
    },
    ("Centaur Warrunner", "Anti-Mage"): {
        "one_liner": "Hoof Stomp stuns Anti-Mage while Retaliate returns heavy physical damage on every attack he attempts.",
        "how_and_why": "Anti-Mage takes heavy physical damage from Retaliate every time he right-clicks Centaur, while Stampede lets your team chase down any Blink attempt.",
        "abilities": ["Hoof Stomp", "Retaliate", "Stampede"],
        "tip": "Turn on Blade Mail when Anti-Mage attacks to reflect both Retaliate and incoming damage."
    },
    ("Tidehunter", "Anti-Mage"): {
        "one_liner": "Anchor Smash reduces Anti-Mage's attack damage by up to 60%, while Ravage provides massive AoE stun lockdown.",
        "how_and_why": "Anchor Smash cripples Anti-Mage's physical damage output, while Kraken Shell shrugs off his debuffs and Ravage locks him down.",
        "abilities": ["Anchor Smash", "Ravage", "Gush"],
        "tip": "Spam Anchor Smash continuously on Anti-Mage in fights to drastically weaken his DPS."
    },
    ("Clinkz", "Anti-Mage"): {
        "one_liner": "Tar Bomb and Strafe unleash lethal physical attack speed, bursting Anti-Mage before he can react or Blink.",
        "how_and_why": "Clinkz deals immense single-target physical burst from invisibility with Tar Bomb and Strafe, melting Anti-Mage's low physical HP before he can react with Counterspell.",
        "abilities": ["Tar Bomb", "Strafe", "Burning Army"],
        "tip": "Attack Anti-Mage from Skeleton Walk with Tar Bomb to melt his HP instantly."
    },
    ("Naga Siren", "Anti-Mage"): {
        "one_liner": "Ensnare applies an undispellable root that prevents Blink, while Mirror Image illusions and Rip Tide shred his armor.",
        "how_and_why": "Ensnare completely disables Anti-Mage's Blink and pierces spell immunity with Aghanim's, while dozens of Rip Tide procs reduce his armor to negative numbers.",
        "abilities": ["Ensnare", "Mirror Image", "Rip Tide"],
        "tip": "Cast Ensnare on Anti-Mage the instant he shows; he cannot Blink or escape while rooted."
    },
    ("Vengeful Spirit", "Anti-Mage"): {
        "one_liner": "Nether Swap pulls Anti-Mage out of position and pierces spell immunity, while Magic Missile stuns and Wave of Terror shreds armor.",
        "how_and_why": "Nether Swap pierces Counterspell to instantly isolate Anti-Mage into the middle of your team, while Wave of Terror reduces his physical armor.",
        "abilities": ["Nether Swap", "Magic Missile", "Wave of Terror"],
        "tip": "Swap Anti-Mage directly into your team when he tries to jump a backline ally."
    },
    ("Techies", "Anti-Mage"): {
        "one_liner": "Sticky Bombs attach to Anti-Mage to slow and disarm him, while Blast Off! silences him to completely shut down Blink.",
        "how_and_why": "Blast Off! applies an undodgeable AoE silence that shuts down Blink, while Sticky Bombs disarm Anti-Mage and Proximity Mines punish his jump attempts.",
        "abilities": ["Blast Off!", "Sticky Bomb", "Proximity Mines"],
        "tip": "Jump Anti-Mage with Blast Off! from fog so he is silenced and cannot Blink away."
    },
    ("Pugna", "Anti-Mage"): {
        "one_liner": "Nether Ward punishes Anti-Mage's spell casts with instant magical zap damage, while Decrepify disarms his physical attacks.",
        "how_and_why": "Decrepify completely disarms Anti-Mage, preventing him from attacking to burn mana, while Nether Ward zaps him whenever he attempts to Blink or cast Mana Void.",
        "abilities": ["Decrepify", "Nether Ward", "Life Drain"],
        "tip": "Decrepify Anti-Mage or his target carry to neutralize his physical right-click damage."
    },
    ("Ogre Magi", "Anti-Mage"): {
        "one_liner": "Ignite applies heavy continuous slows while Fireblast stuns and Bloodlust hyper-buffs allied carry right-clicks against him.",
        "how_and_why": "Ogre Magi is naturally tanky with high base armor and HP, making him resistant to Anti-Mage, while Bloodlust turns allied physical carries into Anti-Mage melting machines.",
        "abilities": ["Bloodlust", "Fireblast", "Ignite"],
        "tip": "Keep Bloodlust on your physical carry so they can right-click Anti-Mage down before he can escape."
    },
    ("Timbersaw", "Anti-Mage"): {
        "one_liner": "Whirling Death and Chakram deal massive pure damage that completely ignores Anti-Mage's magic resistance.",
        "how_and_why": "Timbersaw's entire kit consists of pure damage and reactive physical armor, bypassing Anti-Mage's Counterspell magic resistance completely.",
        "abilities": ["Whirling Death", "Chakram", "Reactive Armor"],
        "tip": "Fight near trees so Whirling Death deals pure damage and cuts Anti-Mage's primary attributes."
    },
    ("Bristleback", "Anti-Mage"): {
        "one_liner": "Viscous Nasal Goo strips Anti-Mage's armor while Quill Spray stacks physical damage that ignores magic resist.",
        "how_and_why": "Quill Spray deals pure physical damage that bypasses magic resistance, and Bristleback's passive reduction makes it suicidal for Anti-Mage to attack from behind.",
        "abilities": ["Quill Spray", "Viscous Nasal Goo", "Bristleback"],
        "tip": "Turn your back to Anti-Mage when he attacks so Quill Spray triggers automatically."
    },
    ("Witch Doctor", "Anti-Mage"): {
        "one_liner": "Paralyzing Cask bounces stuns between Anti-Mage and his Manta illusions while Death Ward deals pure physical burst.",
        "how_and_why": "Death Ward deals pure physical damage that shreds Anti-Mage without caring about Counterspell, while Paralyzing Cask bounces endlessly on his illusions.",
        "abilities": ["Death Ward", "Paralyzing Cask", "Maledict"],
        "tip": "Drop Death Ward from fog or behind allies when Anti-Mage commits on a teammate."
    },
    ("Oracle", "Anti-Mage"): {
        "one_liner": "False Promise prevents Anti-Mage from bursting down allies with Mana Void, doubling heals to keep them alive.",
        "how_and_why": "False Promise delays all incoming damage, neutralizing Anti-Mage's instant Mana Void burst, while Fate's Edict disarms him for up to 5 seconds.",
        "abilities": ["False Promise", "Fate's Edict", "Purifying Flames"],
        "tip": "Cast Fate's Edict on Anti-Mage when he jumps to disarm him and prevent him from burning mana."
    },
    ("Earthshaker", "Anti-Mage"): {
        "one_liner": "Echo Slam shockwaves multiply off Anti-Mage's Manta illusions, while Fissure chain-stuns him to prevent Blink.",
        "how_and_why": "Earthshaker chain-stuns Anti-Mage through Fissure, Enchant Totem, and Aftershock, while Echo Slam punishes Manta Style with devastating shockwaves.",
        "abilities": ["Echo Slam", "Fissure", "Aftershock"],
        "tip": "Wait for Anti-Mage to pop Manta Style before blinking in with Echo Slam."
    },
    ("Leshrac", "Anti-Mage"): {
        "one_liner": "Diabolic Edict deals massive physical explosion damage that bypasses Anti-Mage's Counterspell magic resistance.",
        "how_and_why": "Diabolic Edict consists entirely of physical explosions that completely ignore Anti-Mage's high magic resistance, melting him in close quarters.",
        "abilities": ["Diabolic Edict", "Split Earth", "Pulse Nova"],
        "tip": "Run alongside Anti-Mage with Diabolic Edict active so the concentrated physical explosions burst him."
    },
    ("Anti-Mage", "Medusa"): {
        "how_and_why": "Medusa relies on Mana Shield to absorb 98% of incoming damage. Anti-Mage's Mana Break burns her mana pool in seconds, leaving her with zero effective HP, followed by a lethal Mana Void blast.",
        "abilities": ["Mana Break", "Mana Void"],
        "tip": "Once you get Manta Style, jump Medusa with illusions to drain her entire mana pool before she can stone gaze."
    },
    ("Anti-Mage", "Storm Spirit"): {
        "how_and_why": "Storm Spirit burns huge amounts of mana to zip around. Anti-Mage burns what little mana Storm has left and drops Mana Void for massive AoE damage based on his missing mana.",
        "abilities": ["Mana Break", "Counterspell", "Mana Void"],
        "tip": "Save Mana Void for when Storm finishes a long zip and has nearly zero mana."
    },
    ("Axe", "Phantom Lancer"): {
        "how_and_why": "Phantom Lancer overwhelms single-target heroes with dozens of illusions. Axe's Berserker's Call forces every illusion to attack Axe at once, triggering non-stop Counter Helix spins that shred PL instantly.",
        "abilities": ["Berserker's Call", "Counter Helix", "Culling Blade"],
        "tip": "Buy Blink Dagger + Blade Mail. Jump right into the middle of the illusion army and press Call."
    },
    ("Axe", "Dazzle"): {
        "how_and_why": "Dazzle keeps dying carries alive with Shallow Grave (prevents HP from dropping below 1). Axe's Culling Blade completely bypasses and punches straight through Shallow Grave to instantly execute the target.",
        "abilities": ["Culling Blade"],
        "tip": "Dunk the graved hero as soon as their HP drops below the execution threshold."
    },
    ("Earthshaker", "Phantom Lancer"): {
        "how_and_why": "Echo Slam generates an extra shockwave damage burst for EVERY unit hit. Phantom Lancer's massive illusion swarm causes Echo Slam to deal catastrophic, instant one-shot damage.",
        "abilities": ["Echo Slam", "Fissure", "Aftershock"],
        "tip": "Blink into the thickest clump of illusions and immediately cast Echo Slam."
    },
    ("Earthshaker", "Broodmother"): {
        "how_and_why": "Broodmother's spiderlings create dozens of extra targets that multiply Earthshaker's Echo Slam shockwaves into lethal team-wiping damage.",
        "abilities": ["Echo Slam", "Fissure"],
        "tip": "Hold your Echo Slam until Broodmother commits her spiderling army into the fight."
    },
    ("Ancient Apparition", "Huskar"): {
        "how_and_why": "Huskar stays alive at low health through extreme Inner Fire and Berserker's Blood health regeneration. Ice Blast completely disables ALL healing, regeneration, and lifesteal, leaving him unable to sustain.",
        "abilities": ["Ice Blast"],
        "tip": "Fire Ice Blast into the teamfight as soon as Huskar leaps in with Life Break."
    },
    ("Ancient Apparition", "Morphling"): {
        "how_and_why": "Morphling survives burst by shifting agility into strength to rapidly gain max HP. Ice Blast halts all HP gain from Attribute Shift, causing him to shatter under simple follow-up damage.",
        "abilities": ["Ice Blast"],
        "tip": "Tag Morphling with Ice Blast when he begins taking damage so he cannot heal through shift."
    },
    ("Ancient Apparition", "Alchemist"): {
        "how_and_why": "Alchemist relies on Chemical Rage's extreme HP regeneration to tank entire teams. Ice Blast stops 100% of that regeneration, making him squishy and easy to burst down.",
        "abilities": ["Ice Blast"],
        "tip": "Launch Ice Blast across the map whenever Chemical Rage is popped in teamfights."
    },
    ("Silencer", "Enigma"): {
        "how_and_why": "Enigma needs to channel Black Hole uninterrupted. Silencer's Global Silence immediately interrupts Black Hole from anywhere on the map, even through Black King Bar if cast strategically.",
        "abilities": ["Global Silence"],
        "tip": "Stay far back in teamfights and wait for Enigma to cast Black Hole, then immediately press Global Silence."
    },
    ("Silencer", "Tidehunter"): {
        "how_and_why": "Tidehunter's Kraken Shell dispels stuns, but Silencer's Global Silence silences him before he can counter-initiate with Ravage.",
        "abilities": ["Global Silence", "Last Word"],
        "tip": "Use Global Silence right as your team initiates to prevent Tidehunter from clicking Ravage."
    },
    ("Viper", "Bristleback"): {
        "how_and_why": "Bristleback takes 40% reduced damage from behind due to his passive back armor. Viper's Nethertoxin applies Break, completely disabling Bristleback's passive and allowing your team to kill him effortlessly.",
        "abilities": ["Nethertoxin", "Viper Strike"],
        "tip": "Drop Nethertoxin directly under Bristleback and pelt him with Poison Attack while he is Broken."
    },
    ("Viper", "Phantom Assassin"): {
        "how_and_why": "Phantom Assassin relies heavily on Blur's 50% passive physical evasion. Viper's Nethertoxin applies Break, disabling her evasion so she takes full damage from all physical attacks.",
        "abilities": ["Nethertoxin", "Corrosive Skin"],
        "tip": "Keep PA standing inside Nethertoxin during fights to nullify her evasion and crits."
    },
    ("Spirit Breaker", "Sniper"): {
        "how_and_why": "Sniper relies on sitting thousands of units away in the backline. Spirit Breaker's Charge of Darkness ignores all terrain and vision, barreling straight to Sniper and stun-locking him.",
        "abilities": ["Charge of Darkness", "Nether Strike", "Greater Bash"],
        "tip": "Cast Charge of Darkness directly on Sniper as soon as he shows on the minimap."
    },
    ("Clockwerk", "Sniper"): {
        "how_and_why": "Sniper has zero built-in escape abilities. Clockwerk's Hookshot closes the gap across the screen, and Power Cogs traps Sniper in place while Battery Assault constantly interrupts his attacks.",
        "abilities": ["Hookshot", "Power Cogs", "Battery Assault"],
        "tip": "Fire Hookshot into Sniper in the backline, trap him in Cogs, and turn on Battery Assault."
    },
    ("Razor", "Ursa"): {
        "how_and_why": "Ursa is a purely melee right-clicker who must stay on top of targets. Razor's Static Link drains all of Ursa's attack damage down to zero while Razor runs at maximum movement speed.",
        "abilities": ["Static Link", "Eye of the Storm"],
        "tip": "Link Ursa the second he runs at you and keep running with him to siphon away all his damage."
    },
    ("Slardar", "Riki"): {
        "how_and_why": "Riki depends entirely on permanent invisibility to survive. Slardar's Corrosive Haze provides undispellable True Sight, revealing Riki wherever he runs while destroying his armor.",
        "abilities": ["Corrosive Haze", "Slithereen Crush"],
        "tip": "Cast Corrosive Haze on Riki the instant he reveals himself, making it impossible for him to re-enter stealth."
    },
    ("Zeus", "Tinker"): {
        "how_and_why": "Tinker hides in tree lines to channel Rearm and cast long-range spells. Zeus's Lightning Bolt and Wrath of Nature grant flying vision and true sight over trees, revealing and interrupting Tinker.",
        "abilities": ["Lightning Bolt", "Thundergod's Wrath"],
        "tip": "Drop Lightning Bolt into tree pockets where Tinker is blinking to reveal and burst him."
    },
    ("Bloodseeker", "Slark"): {
        "how_and_why": "Slark regenerates health rapidly when out of enemy vision (Shadow Dance passive). Bloodseeker's Thirst grants true sight of low-HP heroes globally, completely preventing Slark from healing in the dark.",
        "abilities": ["Thirst", "Rupture"],
        "tip": "Rupture Slark so he takes massive pure damage if he tries to Pounce away."
    },
    ("Bloodseeker", "Puck"): {
        "how_and_why": "Puck relies on Illusory Orb and Jaunt for high mobility. Bloodseeker's Rupture deals lethal damage when moving, trapping Puck in place or forcing them to take huge damage on blinks.",
        "abilities": ["Rupture", "Blood Rite"],
        "tip": "Cast Rupture on Puck early in the fight to prevent them from zipping through your team."
    },
    ("Timbersaw", "Strength Carries"): {
        "how_and_why": "Whirling Death reduces base Strength by 13-15%. Against Strength heroes (Centaur, Axe, Sven, Slardar), this drains massive chunks of their max health and attack damage.",
        "abilities": ["Whirling Death", "Reactive Armor"],
        "tip": "Use Whirling Death in melee range near trees to deal pure damage and strip Strength."
    },
    ("Necrophos", "Huskar"): {
        "how_and_why": "Huskar constantly fights at sub-30% health to maximize his attack speed. Necrophos's Reaper's Scythe deals damage proportional to missing health, executing Huskar immediately.",
        "abilities": ["Reaper's Scythe", "Ghost Shroud"],
        "tip": "Activate Ghost Shroud to become immune to Huskar's physical spears, then cast Reaper's Scythe."
    },
    ("Juggernaut", "Lion"): {
        "how_and_why": "Lion relies on chain-stunning with Earth Spike and Hex. Juggernaut's Blade Fury grants full spell immunity on demand, allowing him to spin through Lion's disables and murder him.",
        "abilities": ["Blade Fury", "Omnislash"],
        "tip": "Press Blade Fury as soon as Lion approaches to dodge his disable combo completely."
    },
}

# ── 4. Specific Handcrafted Synergy Matchups (How & Why) ─────────────────────
SPECIFIC_SYNERGIES = {
    ("Faceless Void", "Witch Doctor"): {
        "how_and_why": "Faceless Void's Chronosphere freezes multiple enemies in place. Witch Doctor can place his Death Ward right outside the sphere to bounce uninterrupted physical damage onto the trapped targets.",
        "abilities": ["Chronosphere", "Death Ward", "Maledict"],
        "tip": "Place Death Ward right on the edge of the bubble so it attacks heroes trapped inside."
    },
    ("Faceless Void", "Cataclysm / Invoker"): {
        "how_and_why": "Trapping multiple enemies inside Chronosphere provides stationary targets for Invoker to drop Cataclysm double Sunstrikes directly onto their heads for guaranteed lethal burst.",
        "abilities": ["Chronosphere", "Cataclysm"],
        "tip": "Call out your Chronosphere so your Invoker can queue Cataclysm at the exact moment."
    },
    ("Slardar", "Lifestealer"): {
        "how_and_why": "Slardar's Corrosive Haze removes massive amounts of enemy armor, enabling Lifestealer's physical attacks to shred enemy tanks in seconds while Lifestealer infests Slardar for fast ganks.",
        "abilities": ["Corrosive Haze", "Infest"],
        "tip": "Have Lifestealer infest you while you sprint into enemies with Guardian Sprint, then jump together."
    },
    ("Magnus", "Phantom Assassin"): {
        "how_and_why": "Magnus's Empower gives PA 50%+ bonus base attack damage and cleave. Her massive Coup de Grace crits will cleave through entire enemy teams during Reverse Polarity.",
        "abilities": ["Empower", "Reverse Polarity", "Coup de Grace"],
        "tip": "Keep Empower refreshed on PA continuously so she can farm waves instantly."
    },
    ("Magnus", "Sven"): {
        "how_and_why": "Stacking Magnus's Empower with Sven's Great Cleave and God's Strength results in over 120% cleave damage, instantly wiping groups pulled into Reverse Polarity.",
        "abilities": ["Empower", "Reverse Polarity", "God's Strength"],
        "tip": "Pull enemies with Reverse Polarity and let Sven cleave down the entire group in 2 swings."
    },
    ("Dazzle", "Huskar"): {
        "how_and_why": "Huskar deals maximum damage when fighting at 10% health. Dazzle's Shallow Grave prevents Huskar from dying for 5 seconds, allowing Huskar to shred opponents with maximum Berserker's Blood stacks.",
        "abilities": ["Shallow Grave", "Shadow Wave", "Berserker's Blood"],
        "tip": "Wait until Huskar's HP drops into the red zone before casting Shallow Grave."
    },
    ("Oracle", "Huskar"): {
        "how_and_why": "Oracle's False Promise delays all incoming damage and doubles all healing on Huskar, allowing Huskar to fight at max attack speed without dropping dead.",
        "abilities": ["False Promise", "Purifying Flames"],
        "tip": "Cast False Promise on Huskar as soon as the enemy focuses him, then spam Purifying Flames heals."
    },
    ("Ogre Magi", "Sniper"): {
        "how_and_why": "Sniper has huge attack range but mediocre attack speed early. Ogre Magi's Bloodlust grants huge attack speed and movement speed buffs, turning Sniper into a machine gun.",
        "abilities": ["Bloodlust", "Take Aim"],
        "tip": "Keep Bloodlust on Sniper 100% of the time so he can kite and shoot from extreme range."
    },
    ("Vengeful Spirit", "Drow Ranger"): {
        "how_and_why": "Vengeance Aura gives Drow Ranger bonus base attack damage and range, while Nether Swap can save Drow if an enemy initiator jumps on top of her.",
        "abilities": ["Vengeance Aura", "Nether Swap"],
        "tip": "Stay near Drow in teamfights; if an enemy jumps her, swap her out to safety immediately."
    },
    ("Tidehunter", "Jakiro"): {
        "how_and_why": "Tidehunter's Ravage stuns an entire screen of enemies, allowing Jakiro to lay down Macropyre and Ice Path for guaranteed prolonged lockdown and burning damage.",
        "abilities": ["Ravage", "Macropyre", "Ice Path"],
        "tip": "Cast Macropyre and Ice Path the instant Ravage tentacles hit the floor."
    },
}

# ── 5. Generic Fallback Mechanic Generator ───────────────────────────────────
HERO_TAGS = {
    "Anti-Mage": ["mana_burn", "high_mobility", "anti_caster"],
    "Axe": ["taunt_initiator", "anti_illusions", "pure_execute"],
    "Earthshaker": ["aoe_burst", "anti_illusions", "chain_stuns"],
    "Juggernaut": ["spell_immunity", "physical_burst"],
    "Pudge": ["hook_displacement", "suppression_lockdown", "tank"],
    "Sniper": ["long_range_physical", "squishy_backline"],
    "Drow Ranger": ["silence", "armor_piercing", "physical_ranged"],
    "Viper": ["passive_break", "heavy_slow", "magic_dps"],
    "Crystal Maiden": ["global_mana", "root_stun", "aoe_slow"],
    "Lion": ["instant_hex", "mana_drain", "burst_finger"],
    "Tidehunter": ["massive_aoe_stun", "debuff_purge", "tank"],
    "Slardar": ["armor_reduction", "physical_bash", "true_sight"],
    "Wraith King": ["reincarnation", "single_stun", "easy_carry"],
    "Bristleback": ["tank_damage_reduction", "stacking_quills"],
    "Silencer": ["global_silence", "anti_spellcaster"],
    "Faceless Void": ["stationary_bubble", "time_lock"],
    "Witch Doctor": ["channeled_physical_ult", "bouncing_stun", "maledict"],
    "Zeus": ["global_true_sight", "percentage_magic_burst"],
    "Spirit Breaker": ["global_gap_close", "bkb_piercing_bash"],
    "Legion Commander": ["duel_lockdown", "dispel_heal"],
    "Phantom Assassin": ["physical_evasion", "burst_crit", "gap_close"],
    "Ursa": ["burst_swipes", "roshan_killer", "damage_reduction"],
    "Ogre Magi": ["buff_bloodlust", "tanky_support", "multicast"],
    "Necrophos": ["execute_scythe", "hp_regen_aura", "anti_tank"],
    "Ancient Apparition": ["anti_heal", "frost_slow"],
    "Disruptor": ["position_recall", "silence_field"],
    "Sven": ["massive_cleave", "warcry_armor", "stun"],
    "Centaur Warrunner": ["team_speed", "damage_reflection", "initiator"],
    "Shadow Shaman": ["pushing_wards", "extended_lockdown"],
    "Jakiro": ["ground_denial", "tower_liquid_fire", "ice_stun"],
    "Underlord": ["damage_reduction_aura", "percent_damage", "team_teleport"],
    "Bounty Hunter": ["stealth_vision", "track_gold", "slow"],
    "Medusa": ["mana_shield_tank", "split_shot", "stone_gaze"],
    "Storm Spirit": ["mana_reliant_zip", "burst_ganker"],
    "Phantom Lancer": ["illusion_army", "elusive"],
    "Huskar": ["low_hp_regen", "magic_resist", "life_break"],
    "Morphling": ["stat_shift_heal", "high_burst"],
    "Alchemist": ["chemical_rage_regen", "fast_farm"],
    "Enigma": ["channeled_black_hole", "midnight_pulse"],
    "Riki": ["permanent_stealth", "smoke_screen"],
    "Tinker": ["rearm_burst", "tree_camper"],
    "Slark": ["dark_regen_passive", "dispels"],
}

def explain_counter(hero: str, enemy: str, wr_delta: float) -> dict:
    """Generate structured beginner explanation for why hero counters enemy."""
    # Check specific handcrafted pair first
    key = (hero, enemy)
    if key in SPECIFIC_COUNTERS:
        spec = SPECIFIC_COUNTERS[key]
        one_liner = spec.get("one_liner")
        if not one_liner:
            one_liner = spec["how_and_why"].split(". ")[0].strip() + "."
        return {
            "summary": f"Counters {enemy} ({wr_delta:+.1%} WR)",
            "target_hero": enemy,
            "reason_type": "counter",
            "one_liner": one_liner,
            "how_and_why": spec["how_and_why"],
            "key_abilities": spec["abilities"],
            "beginner_tip": spec["tip"]
        }

    # Generic intelligent fallback using tags
    h_tags = HERO_TAGS.get(hero, [])
    e_tags = HERO_TAGS.get(enemy, [])
    overview = get_hero_overview(hero)
    short_role = overview.split(".")[0].strip()

    if enemy == "Anti-Mage":
        how = f"{hero} counters Anti-Mage's gameplan through core kit advantages: {overview}"
        one_liner = f"{hero} counters Anti-Mage's mobility and farm reliance as a {short_role.lower()}."
        tip = "Coordinate with your team to initiate and control Anti-Mage before he can pop Counterspell or Blink."
    else:
        how = f"{hero} matches up favorably into {enemy} ({wr_delta:+.1%} WR advantage). {overview}"
        one_liner = f"{hero} controls the matchup against {enemy} by utilizing their kit as a {short_role.lower()}."
        tip = f"Play around your team's initiation and prioritize shutting down {enemy} in skirmishes."

    abilities: list[str] = []

    if "anti_illusions" in h_tags and "illusion_army" in e_tags:
        how = f"{hero}'s AoE abilities clear {enemy}'s illusion swarm instantly, stripping away their main defense and damage."
        tip = f"Hold your key AoE spells until {enemy} summons their full illusion army."
        one_liner = f"{hero}'s AoE abilities instantly clear {enemy}'s illusions, removing their primary damage and defense."
    elif "mana_burn" in h_tags and "mana_reliant_zip" in e_tags:
        how = f"{hero}'s mana draining spells deplete {enemy}'s mana pool, removing their ability to escape or cast spells."
        tip = f"Drain {enemy}'s mana early in the engagement so they are left stranded."
        one_liner = f"{hero} drains {enemy}'s mana pool, removing their mobility and leaving them stranded."
    elif "anti_heal" in h_tags and "low_hp_regen" in e_tags:
        how = f"{hero} disables {enemy}'s ability to heal or lifesteal, cutting off their main survival mechanic."
        tip = f"Land your anti-heal abilities right when {enemy} engages into combat."
        one_liner = f"{hero} shuts down {enemy}'s healing and regeneration, neutralizing their primary survival mechanic."
    elif "global_gap_close" in h_tags and "squishy_backline" in e_tags:
        how = f"{hero} easily bypasses the frontline to jump straight onto {enemy}, eliminating their long-range safety advantage."
        tip = f"Target {enemy} in the backline before they can free-hit your teammates."
        one_liner = f"{hero} easily jumps straight onto {enemy} in the backline, eliminating their long-range safety advantage."
    elif "armor_reduction" in h_tags:
        how = f"{hero} strips {enemy}'s armor, allowing allied physical damage to burst them down much faster."
        tip = "Apply your armor reduction debuffs first before your physical carry commits."
        one_liner = f"{hero} shreds {enemy}'s physical armor, leaving them vulnerable to fast physical burst."
    elif "passive_break" in h_tags:
        how = f"{hero} breaks {enemy}'s strong passive abilities, severely weakening their defensive and offensive stats."
        tip = f"Ensure {enemy} is afflicted with Break before dumping high-damage abilities into them."
        one_liner = f"{hero} breaks {enemy}'s passives, heavily diminishing their stats and survivability."

    return {
        "summary": f"Counters {enemy} ({wr_delta:+.1%} WR)",
        "target_hero": enemy,
        "reason_type": "counter",
        "one_liner": one_liner,
        "how_and_why": how,
        "key_abilities": abilities,
        "beginner_tip": tip
    }

def explain_synergy(hero: str, ally: str, wr_delta: float) -> dict:
    """Generate structured beginner explanation for why hero synergizes with ally."""
    key = (hero, ally)
    if key in SPECIFIC_SYNERGIES:
        spec = SPECIFIC_SYNERGIES[key]
        one_liner = spec.get("one_liner")
        if not one_liner:
            one_liner = spec["how_and_why"].split(". ")[0].strip() + "."
        return {
            "summary": f"Synergizes with {ally} ({wr_delta:+.1%} WR)",
            "target_hero": ally,
            "reason_type": "synergy",
            "one_liner": one_liner,
            "how_and_why": spec["how_and_why"],
            "key_abilities": spec["abilities"],
            "beginner_tip": spec["tip"]
        }

    # Generic intelligent fallback
    h_tags = HERO_TAGS.get(hero, [])
    a_tags = HERO_TAGS.get(ally, [])

    how = f"{hero} forms an effective combination with {ally}, boosting team win probability by {wr_delta:+.1%}."
    abilities: list[str] = []
    tip = f"Coordinate spell timings and target focus together with {ally} during lane and teamfights."
    one_liner = f"Synergizes strongly with {ally} ({wr_delta:+.1%} WR), combining control and follow-up damage in fights."

    if ("stationary_bubble" in h_tags or "massive_aoe_stun" in h_tags) and ("channeled_physical_ult" in a_tags or "aoe_burst" in a_tags):
        how = f"{hero} provides heavy AoE crowd control that holds enemies stationary, allowing {ally} to land high-impact spells with 100% accuracy."
        tip = f"Wait for {hero} to initiate and lock targets down before casting your big teamfight spells."
        one_liner = f"{hero} provides stationary AoE crowd control so {ally} can land high-impact spells with guaranteed accuracy."
    elif "armor_reduction" in h_tags and "physical_burst" in a_tags:
        how = f"{hero}'s armor shred dramatically amplifies {ally}'s physical right-click burst damage."
        tip = f"Attack whichever target {hero} has debuffed with armor reduction."
        one_liner = f"{hero}'s armor shred dramatically amplifies {ally}'s physical right-click burst damage."

    return {
        "summary": f"Synergizes with {ally} ({wr_delta:+.1%} WR)",
        "target_hero": ally,
        "reason_type": "synergy",
        "one_liner": one_liner,
        "how_and_why": how,
        "key_abilities": abilities,
        "beginner_tip": tip
    }


# ── 6. Role Fit, Disables & Movement Knowledge ──────────────────────────────
HERO_TACTICAL_KITS = {
    "Abaddon": {
        "stuns_disables": "Curse of Avernus stacking silence and movement slow",
        "movement": "high base movement speed and Aphotic Shield debuff purge",
        "key_abilities": ["Aphotic Shield", "Borrowed Time", "Curse of Avernus", "Mist Coil"],
        "role_notes": {
            "support": "babysits allied cores by purging stuns with Aphotic Shield and healing through Mist Coil while absorbing damage with Borrowed Time",
            "offlane": "frontlines aggressively with Aphotic Shield and Curse of Avernus slows, diving towers without fear due to Borrowed Time"
        },
        "beginner_tip": "Save Aphotic Shield to instantly dispel stuns or silences from your allied carry in teamfights."
    },
    "Alchemist": {
        "stuns_disables": "Unstable Concoction long-duration charging physical stun",
        "movement": "Chemical Rage bonus movement speed and extreme health regeneration",
        "key_abilities": ["Chemical Rage", "Unstable Concoction", "Acid Spray", "Greevil's Greed"],
        "role_notes": {
            "carry": "accelerates farm exponentially with Greevil's Greed and leads early pushes with high Chemical Rage movement speed and Concoction stuns",
            "mid": "secures fast rune control and level advantage, rotating to side lanes with fully charged Unstable Concoction stuns"
        },
        "beginner_tip": "Throw Unstable Concoction before the timer hits 0.5s to avoid stunning yourself."
    },
    "Ancient Apparition": {
        "stuns_disables": "Cold Feet delayed freezing stun and Ice Vortex movement slows",
        "movement": "safe long-range spell artillery and Ice Vortex vision scouting",
        "key_abilities": ["Ice Blast", "Cold Feet", "Ice Vortex", "Chilling Touch"],
        "role_notes": {
            "support": "completely shuts down enemy healing and lifesteal with global Ice Blast while locking down slowed enemies with Cold Feet"
        },
        "beginner_tip": "Cast Ice Vortex under enemies first to slow them and amplify your team's magic damage."
    },
    "Anti-Mage": {
        "stuns_disables": "Mana Void ministun and massive missing-mana AoE burst explosion",
        "movement": "short-cooldown Blink for hyper-mobile farming and backline flanking",
        "key_abilities": ["Blink", "Mana Void", "Mana Break", "Counterspell"],
        "role_notes": {
            "carry": "blinks across jungle camps to achieve peak farming velocity, flanking enemy spellcasters and executing them with Mana Void"
        },
        "beginner_tip": "Use Counterspell reactively when targeted spells fly toward you to reflect them back onto enemies."
    },
    "Arc Warden": {
        "stuns_disables": "Flux crippling single-target movement slow and Magnetic Field evasion",
        "movement": "Tempest Double global clone presence to push lanes and contest runes safely",
        "key_abilities": ["Tempest Double", "Flux", "Spark Wraith", "Magnetic Field"],
        "role_notes": {
            "mid": "dominates 1v1 mid lane pressure with Spark Wraiths, creating double-hero presence across fights with Tempest Double",
            "carry": "pressures high ground safely with Tempest Double clone illusions while slowing isolated targets with Flux"
        },
        "beginner_tip": "Place Spark Wraiths in choke points to scout ganks and deal massive magic burst."
    },
    "Axe": {
        "stuns_disables": "Berserker's Call AoE taunt piercing spell immunity",
        "movement": "Blink Dagger initiation and Culling Blade team movement speed bonus",
        "key_abilities": ["Berserker's Call", "Counter Helix", "Culling Blade", "Battle Hunger"],
        "role_notes": {
            "offlane": "anchors the frontline by blinking into clumped enemies, forcing them to attack with Berserker's Call and spinning them down with Counter Helix"
        },
        "beginner_tip": "Activate Blade Mail immediately as you Blink-Call enemies to turn their own attack damage back on them."
    },
    "Bane": {
        "stuns_disables": "Nightmare sleep disable and Fiend's Grip channeled BKB-piercing suppression stun",
        "movement": "backline positioning and cast range advantage with Enfeeble range reduction",
        "key_abilities": ["Fiend's Grip", "Nightmare", "Brain Sap", "Enfeeble"],
        "role_notes": {
            "support": "neutralizes the strongest enemy core through spell immunity with Fiend's Grip while taking a second enemy out of the fight with Nightmare"
        },
        "beginner_tip": "Channel Fiend's Grip from maximum range or fog so enemy supports cannot easily interrupt you."
    },
    "Batrider": {
        "stuns_disables": "Flaming Lasso BKB-piercing drag disable and Flamebreak knockback",
        "movement": "Firefly unobstructed flying movement over cliffs and trees",
        "key_abilities": ["Flaming Lasso", "Firefly", "Sticky Napalm", "Flamebreak"],
        "role_notes": {
            "offlane": "flies over terrain with Firefly, lassoing priority enemy targets through BKB and dragging them into allied focus fire",
            "mid": "dominates mid lane CS with Sticky Napalm stacks and uses Firefly flight to gank side lanes through unexpected angles",
            "support": "provides flying vision over trees, initiating pickoffs with Blink into Flaming Lasso"
        },
        "beginner_tip": "Stack Sticky Napalm at least 4-5 times before committing Firefly burn damage."
    },
    "Beastmaster": {
        "stuns_disables": "Primal Roar long-duration BKB-piercing single-target stun and Boar poison slows",
        "movement": "Hawk flying map vision and Inner Beast team movement speed aura",
        "key_abilities": ["Primal Roar", "Call of the Wild", "Wild Axes", "Inner Beast"],
        "role_notes": {
            "offlane": "provides unmatched vision control with flying Hawks, initiating pickoffs with unstoppable Primal Roar stuns and pushing with summons"
        },
        "beginner_tip": "Keep your Hawk stationed over high ground or enemy jungle camps to spot incoming rotations."
    },
    "Bloodseeker": {
        "stuns_disables": "Rupture movement-punishing pure damage leash and Blood Rite AoE silence",
        "movement": "Thirst uncapped global movement speed scaling with damaged enemies",
        "key_abilities": ["Rupture", "Blood Rite", "Thirst", "Bloodrage"],
        "role_notes": {
            "carry": "reaches blinding movement speed from Thirst to clean up teamfights, pinning mobile enemy cores in place with Rupture",
            "mid": "sustains mid lane farm with Bloodrage heals, ganking side lanes with Rupture pure damage"
        },
        "beginner_tip": "Cast Rupture on high-mobility heroes (AM, Queen of Pain, Storm) so they kill themselves if they try to escape."
    },
    "Bounty Hunter": {
        "stuns_disables": "Shuriken Toss bouncing ministun and Track movement debuff",
        "movement": "Shadow Walk stealth with bonus speed and Track team movement speed boost",
        "key_abilities": ["Track", "Shadow Walk", "Jinada", "Shuriken Toss"],
        "role_notes": {
            "support": "scouts the map invisibly, siphons enemy gold with Jinada, and boosts allied movement speed toward Tracked targets for bonus team gold",
            "offlane": "bullies the enemy carry in lane with Jinada burst, building early aura items and tracking kills"
        },
        "beginner_tip": "Keep Track active on every visible enemy hero before teamfights to grant true sight and speed buffs to your team."
    },
    "Brewmaster": {
        "stuns_disables": "Primal Split Earth hurl stun, Storm cyclone banish, and Cinder Brew ignition slow",
        "movement": "Drunken Brawler evasion speed stances and elusive multi-unit Primal Split",
        "key_abilities": ["Primal Split", "Cinder Brew", "Thunder Clap", "Drunken Brawler"],
        "role_notes": {
            "offlane": "initiates teamfights and splits into four elemental pandas, banishing the enemy carry with Cyclone and chain-stunning with Earth"
        },
        "beginner_tip": "Use Storm Spirit's Cyclone during Primal Split to take the enemy's main damage dealer out of the fight for 6 seconds."
    },
    "Bristleback": {
        "stuns_disables": "Viscous Nasal Goo stacking movement slow and armor reduction",
        "movement": "Warpath stacking movement speed on every spell cast",
        "key_abilities": ["Bristleback", "Quill Spray", "Viscous Nasal Goo", "Warpath"],
        "role_notes": {
            "offlane": "plows through enemy lines taking 40% reduced damage from behind, building Warpath movement speed to run down backlines",
            "carry": "scales into an unkillable late-game bruiser, constantly stacking Quill Sprays and Nasal Goo slows"
        },
        "beginner_tip": "Always face your back or sides toward incoming burst damage to trigger passive Quill Sprays and reduce damage."
    },
    "Broodmother": {
        "stuns_disables": "Silken Bola heavy movement slow and attack miss chance",
        "movement": "Spin Web unobstructed terrain pathing and extreme web movement speed",
        "key_abilities": ["Spin Web", "Spawn Spiderlings", "Silken Bola", "Insatiable Hunger"],
        "role_notes": {
            "mid": "overwhelms mid lane towers with spiderling swarms, zooming over cliffs to choke out the enemy jungle",
            "offlane": "creates immense lane pressure and map control, eating up enemy towers and hunting squishies across webs"
        },
        "beginner_tip": "Keep webs connected along cliff edges to move across high ground and escape ganks effortlessly."
    },
    "Centaur Warrunner": {
        "stuns_disables": "Hoof Stomp AoE wind-up stun",
        "movement": "Stampede global max-speed haste buff and collision phasing for the entire team",
        "key_abilities": ["Stampede", "Hoof Stomp", "Double Edge", "Retaliate"],
        "role_notes": {
            "offlane": "acts as an immense meat shield who initiates with Hoof Stomp and saves or engages with teamwide Stampede haste"
        },
        "beginner_tip": "Pop Stampede either to save caught teammates across the map or to charge the entire team onto out-of-position enemies."
    },
    "Chaos Knight": {
        "stuns_disables": "Chaos Bolt variable long-duration stun and Reality Rift displacement",
        "movement": "Reality Rift pull gap-closer and high base movement speed",
        "key_abilities": ["Phantasm", "Chaos Bolt", "Reality Rift", "Chaos Strike"],
        "role_notes": {
            "carry": "pulls targets into melee range with Reality Rift, stuns them with Chaos Bolt, and deletes them instantly with Phantasm illusions",
            "offlane": "bullies the safe lane with durable armor, using Chaos Bolt stuns and Reality Rift to set up kills for side laners"
        },
        "beginner_tip": "Cast Reality Rift immediately after casting Chaos Bolt so your Phantasm illusions teleport directly onto the stunned target."
    },
    "Chen": {
        "stuns_disables": "Holy Persuasion creep stuns (Centaur, Troll nets) and Penitence movement slow",
        "movement": "Hand of God global team healing and Penitence attack speed amplification",
        "key_abilities": ["Holy Persuasion", "Hand of God", "Penitence", "Divine Favor"],
        "role_notes": {
            "support": "commands a micro army of jungle creeps providing chain stuns, armor auras, and global saves with Hand of God"
        },
        "beginner_tip": "Persuade a Centaur Conqueror early to give your team a reliable AoE stun for lane ganks."
    },
    "Clinkz": {
        "stuns_disables": "Tar Bomb heavy movement slow and physical damage amplification",
        "movement": "Skeleton Walk high-speed invisibility with bonus movement speed",
        "key_abilities": ["Skeleton Walk", "Tar Bomb", "Strafe", "Burning Army"],
        "role_notes": {
            "carry": "ambushes isolated enemies out of Skeleton Walk, slowing them with Tar Bomb and melting them with rapid Strafe arrows",
            "support": "scouts deep in enemy territory invisibly, applying Tar Bomb slows and vision in teamfights"
        },
        "beginner_tip": "Cast Tar Bomb first from invisibility before activating Strafe to maximize bonus physical damage."
    },
    "Clockwerk": {
        "stuns_disables": "Power Cogs containment and Battery Assault continuous ministuns",
        "movement": "Hookshot screen-wide gap-close stun to latch onto targets",
        "key_abilities": ["Hookshot", "Power Cogs", "Battery Assault", "Rocket Flare"],
        "role_notes": {
            "support": "hooks across the screen to isolate priority targets inside Cogs, interrupting casting with Battery Assault",
            "offlane": "initiates fights and traps fragile enemy backliners in Cogs while disrupting spellcasters"
        },
        "beginner_tip": "Turn on Battery Assault right before your Hookshot lands so the target is ministunned the instant you arrive."
    },
    "Crystal Maiden": {
        "stuns_disables": "Frostbite root disabling movement/blinks and Crystal Nova AoE slow",
        "movement": "global Arcane Aura mana regen enabling allied mobility spells, Freezing Field slow",
        "key_abilities": ["Frostbite", "Crystal Nova", "Arcane Aura", "Freezing Field"],
        "role_notes": {
            "support": "roots mobile enemies in place with Frostbite, slows fights with Crystal Nova, and fuels team spells globally with Arcane Aura"
        },
        "beginner_tip": "Cast Frostbite from safety behind your core, and channel Freezing Field inside trees or with Glimmer Cape active."
    },
    "Dark Seer": {
        "stuns_disables": "Vacuum AoE displacement pull and Wall of Replica illusion wall",
        "movement": "Surge maximum-speed haste buff for self or allies",
        "key_abilities": ["Vacuum", "Surge", "Ion Shell", "Wall of Replica"],
        "role_notes": {
            "offlane": "hastens allied initiators into combat with Surge, grouping the entire enemy team into combos with Vacuum and Wall"
        },
        "beginner_tip": "Surge your melee cores so they can run down enemy heroes without being slowed or kited."
    },
    "Dark Willow": {
        "stuns_disables": "Bramble Maze multiple roots, Cursed Crown AoE stun, and Terrorize fear",
        "movement": "Shadow Realm untargetable evasive mobility and heavy magic burst",
        "key_abilities": ["Shadow Realm", "Bramble Maze", "Cursed Crown", "Terrorize"],
        "role_notes": {
            "support": "controls teamfight choke points with Brambles and Cursed Crown stuns while dishing out safe burst from Shadow Realm"
        },
        "beginner_tip": "Use Terrorize to scatter enemies when they try to initiate on your allied cores."
    },
    "Dawnbreaker": {
        "stuns_disables": "Starbreaker hammer smash stun and Celestial Hammer sweep slows",
        "movement": "Solar Guardian global landing stun/heal and Celestial Hammer pull dash",
        "key_abilities": ["Solar Guardian", "Starbreaker", "Celestial Hammer", "Luminosity"],
        "role_notes": {
            "offlane": "splits the map to farm and lands globally with Solar Guardian to heal allies and stun grouped enemies",
            "support": "turns teamfights from across the map with Solar Guardian saves and Starbreaker stun combos",
            "mid": "pushes waves with Celestial Hammer and rotates globally to counter-gank side lanes with Solar Guardian"
        },
        "beginner_tip": "Target Solar Guardian on whoever is being focused by the enemy to immediately heal them and deter divers."
    },
    "Dazzle": {
        "stuns_disables": "Poison Touch stacking refreshable movement slow",
        "movement": "Shallow Grave invulnerability allowing aggressive dives and Shadow Wave heals",
        "key_abilities": ["Shallow Grave", "Poison Touch", "Shadow Wave", "Bad Juju"],
        "role_notes": {
            "support": "saves dying cores from fatal damage with Shallow Grave and kites enemy heroes indefinitely with Poison Touch slows",
            "mid": "spams low-cooldown spells with Bad Juju, kiting and wearing down opponents in lane"
        },
        "beginner_tip": "Wait until your ally's health is in the red zone before casting Shallow Grave to maximize its duration."
    },
    "Death Prophet": {
        "stuns_disables": "Silence wide AoE spell lock and Spirit Siphon movement slow",
        "movement": "high base movement speed and Witchcraft mobility passive",
        "key_abilities": ["Exorcism", "Silence", "Spirit Siphon", "Crypt Swarm"],
        "role_notes": {
            "mid": "leads tower pushes with Exorcism spirits, silencing spellcasters and draining tank HP with Spirit Siphon",
            "offlane": "frontlines with high armor and siphon sustain, tearing down objectives whenever Exorcism is available"
        },
        "beginner_tip": "Cast Silence on key disablers before popping Exorcism and running through teamfights."
    },
    "Disruptor": {
        "stuns_disables": "Static Storm AoE silence/mute, Kinetic Field barrier trap, and Glimpse recall",
        "movement": "Glimpse to undo enemy mobility spells and drag runners back across the map",
        "key_abilities": ["Static Storm", "Kinetic Field", "Glimpse", "Thunder Strike"],
        "role_notes": {
            "support": "traps enemies inside Kinetic Field, mutes them with Static Storm, and pulls back escaping heroes with Glimpse"
        },
        "beginner_tip": "Track where an enemy hero was 4 seconds ago and cast Glimpse to drag them straight into Kinetic Field."
    },
    "Doom": {
        "stuns_disables": "Doom ultimate BKB-piercing silence and mute, and Infernal Blade stun",
        "movement": "Scorched Earth high bonus movement speed and health regeneration",
        "key_abilities": ["Doom", "Scorched Earth", "Infernal Blade", "Devour"],
        "role_notes": {
            "offlane": "charges into battle with Scorched Earth speed and completely removes the most dangerous enemy core with Doom",
            "mid": "farms rapidly with Devour and roams with Scorched Earth movement to shut down key enemies with Doom"
        },
        "beginner_tip": "Always prioritize casting Doom on heroes who rely entirely on active spells or BKB (Storm, Morphling, Invoker)."
    },
    "Dragon Knight": {
        "stuns_disables": "up to 3-second reliable point-click Dragon Tail stun",
        "movement": "Elder Dragon Form flying movement speed and ranged splash capability",
        "key_abilities": ["Dragon Tail", "Elder Dragon Form", "Breathe Fire", "Dragon Blood"],
        "role_notes": {
            "mid": "secures mid lane stability through Dragon Blood regeneration, rotating with Dragon Tail stuns to take early towers",
            "offlane": "acts as an immovable frontline tank who absorbs enemy spells and initiates fights with reliable point-click stuns",
            "carry": "scales with Dragon Blood armor and Elder Dragon splash damage to siege high ground with his team"
        },
        "beginner_tip": "Pop Elder Dragon Form to initiate ganks on side lanes and immediately melt tier 1 towers with corrosive breath."
    },
    "Drow Ranger": {
        "stuns_disables": "Gust knockback and AoE silence, and Frost Arrows constant movement slow",
        "movement": "Glacier elevation safety and Multishot long-range zone control",
        "key_abilities": ["Marksmanship", "Gust", "Frost Arrows", "Multishot"],
        "role_notes": {
            "carry": "shuts down enemy initiation with Gust silence, kiting attackers with Frost Arrows and piercing base armor from range"
        },
        "beginner_tip": "Use Gust to push away gap-closers like Slark or PA, then deploy Glacier to stand and free-hit."
    },
    "Earth Spirit": {
        "stuns_disables": "Boulder Smash stone stun, Geomagnetic Grip silence, and Magnetize slow",
        "movement": "Rolling Boulder high-speed terrain dash and stone boulder mobility",
        "key_abilities": ["Rolling Boulder", "Boulder Smash", "Geomagnetic Grip", "Magnetize"],
        "role_notes": {
            "support": "rolls across lanes to initiate ganks with stone stuns and silences, spreading Magnetize damage in teamfights",
            "mid": "controls runes with Rolling Boulder mobility and rotates aggressively to side lanes"
        },
        "beginner_tip": "Drop a Stone Remnant along your Rolling Boulder path to double your roll distance and speed."
    },
    "Earthshaker": {
        "stuns_disables": "Fissure long-range path-blocking stun, Enchant Totem / Aftershock stuns, and Echo Slam",
        "movement": "Blink Dagger initiation and Aghanim's Enchant Totem leaping mobility",
        "key_abilities": ["Echo Slam", "Fissure", "Enchant Totem", "Aftershock"],
        "role_notes": {
            "support": "blocks escape paths with Fissure and blinks in to chain-stun teams and wipe illusion armies with Echo Slam",
            "offlane": "initiates teamfights with Blink-Echo Slam and locks down targets with non-stop Aftershock procs"
        },
        "beginner_tip": "Wait for the enemy team or illusion swarm to clump up before dropping Echo Slam for maximum shockwaves."
    },
    "Elder Titan": {
        "stuns_disables": "Echo Stomp sleep disable and Earth Splitter percentage pull and slow",
        "movement": "Astral Spirit scouting and stacking movement speed per unit hit",
        "key_abilities": ["Echo Stomp", "Astral Spirit", "Natural Order", "Earth Splitter"],
        "role_notes": {
            "support": "scouts with Astral Spirit to gain massive movement speed, sleeping groups with Stomp and stripping 100% base armor",
            "offlane": "punishes grouped teams with Natural Order armor strip and crushes teamfights with Earth Splitter"
        },
        "beginner_tip": "Send Astral Spirit through a full creep wave and heroes before recalling it to gain hundreds of attack damage and speed."
    },
    "Ember Spirit": {
        "stuns_disables": "Searing Chains multi-target root disable",
        "movement": "Activate Fire Remnant instant dash across map and Sleight of Fist invulnerability",
        "key_abilities": ["Activate Fire Remnant", "Sleight of Fist", "Searing Chains", "Flame Guard"],
        "role_notes": {
            "mid": "roots mobile targets with Searing Chains while dodging spells and zipping between Remnants in teamfights",
            "carry": "applies on-hit effects across whole teams with Sleight of Fist, remaining virtually uncatchable with Fire Remnants"
        },
        "beginner_tip": "Always leave a defensive Fire Remnant behind in safety before jumping into an aggressive skirmish."
    },
    "Enchantress": {
        "stuns_disables": "Enchant enemy movement slow and creep stuns (Centaur, Ursa)",
        "movement": "Untouchable enemy attack speed slow and high base movement speed",
        "key_abilities": ["Impetus", "Enchant", "Untouchable", "Nature's Attendants"],
        "role_notes": {
            "support": "dominates lanes with jungle creep stuns, heals allies with Nature's Attendants, and fires lethal Impetus pure spears",
            "offlane": "absorbs physical attacks with Untouchable and zones safe lanes with long-range Impetus damage"
        },
        "beginner_tip": "The farther away your target is, the more pure damage Impetus deals—keep maximum distance while attacking."
    },
    "Enigma": {
        "stuns_disables": "Black Hole channeled BKB-piercing gravitational pull and Malefice ministuns",
        "movement": "Blink Dagger initiation and Midnight Pulse percentage terrain zoning",
        "key_abilities": ["Black Hole", "Midnight Pulse", "Malefice", "Demonic Conversion"],
        "role_notes": {
            "offlane": "turns whole teamfights with spell-immunity piercing Black Hole, catching key enemy cores inside Midnight Pulse",
            "support": "farms jungle with Eidolons and controls teamfights with BKB-piercing Black Hole lockdown"
        },
        "beginner_tip": "Lay down Midnight Pulse first before casting Black Hole to shred percentage health from trapped heroes."
    },
    "Faceless Void": {
        "stuns_disables": "Chronosphere universal time-freeze dome and Time Lock bash stuns",
        "movement": "Time Walk short-range dash rewinding damage taken in the last 2 seconds",
        "key_abilities": ["Chronosphere", "Time Walk", "Time Lock", "Time Dilation"],
        "role_notes": {
            "carry": "freezes entire enemy teams inside Chronosphere to safely eliminate priority cores, rewinding burst with Time Walk"
        },
        "beginner_tip": "Time Walk right after taking burst damage to immediately regain all that lost health."
    },
    "Grimstroke": {
        "stuns_disables": "Soulbind leash binding two heroes, Stroke of Fate slow, and Ink Swell stun",
        "movement": "Ink Swell bonus movement speed buff on allied initiators",
        "key_abilities": ["Soulbind", "Ink Swell", "Stroke of Fate", "Phantom's Embrace"],
        "role_notes": {
            "support": "buffs allied frontliners with Ink Swell speed and stuns, binding two enemies with Soulbind to double allied targeted spells"
        },
        "beginner_tip": "Put Ink Swell on your initiator (Axe, Slardar, Centaur) right as they blink into enemy heroes."
    },
    "Gyrocopter": {
        "stuns_disables": "Homing Missile tracking stun and Call Down double missile AoE slows",
        "movement": "Rocket Barrage high-tempo chase and Flak Cannon multi-target clearing",
        "key_abilities": ["Flak Cannon", "Call Down", "Rocket Barrage", "Homing Missile"],
        "role_notes": {
            "carry": "shreds entire enemy teams simultaneously with Flak Cannon while zoning skirmishes with Call Down missiles",
            "support": "launches tracking Homing Missiles to force enemy reactions, dealing huge early magic burst with Rocket Barrage"
        },
        "beginner_tip": "Stand directly on top of isolated single targets to hit them with every single Rocket Barrage rocket."
    },
    "Hoodwink": {
        "stuns_disables": "Bushwhack tree-tether stun and Hunter's Boomerang movement slow",
        "movement": "Scurry tree-walking movement speed buff and physical evasion",
        "key_abilities": ["Bushwhack", "Acorn Shot", "Scurry", "Sharpshooter"],
        "role_notes": {
            "support": "scurries through trees with bonus speed, latching enemies to trees with Bushwhack and sniping with Sharpshooter",
            "mid": "controls lane with Acorn Shot bounces and roams with Scurry speed to land long-range Sharpshooters"
        },
        "beginner_tip": "Plant a tree with Acorn Shot first if no natural trees are nearby to guarantee your Bushwhack stun lands."
    },
    "Huskar": {
        "stuns_disables": "Life Break targeted leap slow and Inner Fire area knockback and disarm",
        "movement": "Life Break targeted gap-closing leap onto enemy heroes",
        "key_abilities": ["Life Break", "Burning Spears", "Inner Fire", "Berserker's Blood"],
        "role_notes": {
            "mid": "dominates mid lane trades with Burning Spears, leaping onto targets with Life Break and disarming physical counters with Inner Fire",
            "carry": "leaps into fights with Life Break, fighting at low HP with massive Berserker's Blood attack speed and magic resist"
        },
        "beginner_tip": "Cast Inner Fire right after landing Life Break to disarm the enemy and prevent them from right-clicking you back."
    },
    "Invoker": {
        "stuns_disables": "Tornado lift, Cold Snap ministuns, Deafening Blast disarm, and Ice Wall slow",
        "movement": "Ghost Walk high-speed invisibility rotation and global Cataclysm strikes",
        "key_abilities": ["Tornado", "Chaos Meteor", "Cold Snap", "Deafening Blast"],
        "role_notes": {
            "mid": "controls mid tempo with 10 versatile spells, lifting enemies with Tornado, chaining Cold Snap stuns, and dropping Cataclysm"
        },
        "beginner_tip": "Cold Snap targets before dropping damage over time (Urn, Meteor, Ice Wall) to trigger non-stop ministuns."
    },
    "Io": {
        "stuns_disables": "Tether movement slow and Spirits slow",
        "movement": "Relocate global team teleportation and Tether high-speed link to allies",
        "key_abilities": ["Tether", "Overcharge", "Relocate", "Spirits"],
        "role_notes": {
            "support": "tethers to allied carries to provide overcharged attack speed and sustain, relocating them globally for coordinated ganks"
        },
        "beginner_tip": "Communicate your Relocate countdown with your core so you both jump onto the target in sync."
    },
    "Jakiro": {
        "stuns_disables": "Ice Path straight-line freezing stun and Dual Breath attack and movement slow",
        "movement": "safe long-range spell artillery and Liquid Fire tower siege pressure",
        "key_abilities": ["Ice Path", "Dual Breath", "Liquid Fire", "Macropyre"],
        "role_notes": {
            "support": "lays down Ice Path walls to freeze enemies in chokepoints, melting lanes with Liquid Fire and burning areas with Macropyre"
        },
        "beginner_tip": "Cast Ice Path along narrow jungle pathways where enemies have nowhere else to run."
    },
    "Juggernaut": {
        "stuns_disables": "Blade Fury spell-immune physical spin damage and Healing Ward sustain",
        "movement": "Blade Fury built-in spell immunity and Omnislash invulnerable slash leaps",
        "key_abilities": ["Omnislash", "Blade Fury", "Healing Ward", "Blade Dance"],
        "role_notes": {
            "carry": "spins through enemy crowd control with Blade Fury spell immunity and tears through teams invulnerably with Omnislash"
        },
        "beginner_tip": "Cast Healing Ward during teamfights and keep it microed behind your team so enemies cannot easily destroy it."
    },
    "Keeper of the Light": {
        "stuns_disables": "Blinding Light knockback and miss chance, Solar Bind slow, and Will-O-Wisp hypnotic stun",
        "movement": "high base movement speed and Chakra Magic cooldown reduction",
        "key_abilities": ["Illuminate", "Blinding Light", "Chakra Magic", "Will-O-Wisp"],
        "role_notes": {
            "support": "blinds enemy right-clickers, hypnotizes teams with Will-O-Wisp, and fuels ally mana with Chakra Magic",
            "mid": "clears waves instantly with Illuminate, using high movement speed to rotate and gank constantly"
        },
        "beginner_tip": "Cast Chakra Magic on allies with high-impact low-cooldown spells to let them double-cast in skirmishes."
    },
    "Kez": {
        "stuns_disables": "Sai stance parry disarm stuns, Katana bleeds, and grapple hook slows",
        "movement": "rapid stance-switching dashes and evasive aerial repositioning",
        "key_abilities": ["Switch Discipline", "Echo Slash", "Grappling Claw", "Ravager's Path"],
        "role_notes": {
            "carry": "swaps between Katana and Sai disciplines, chaining elusive dashes and parry stuns to burst priority targets",
            "mid": "dominates skirmishes with stance agility, parrying enemy attacks and grappling across fights"
        },
        "beginner_tip": "Time your Sai Parry right when the enemy core commits an attack to disarm and stun them."
    },
    "Kunkka": {
        "stuns_disables": "Torrent water eruption stun, Ghostship drunken stun, and X Marks the Spot return",
        "movement": "X Marks the Spot safe scouting recall and Ghostship Rum damage reduction speed buff",
        "key_abilities": ["Ghostship", "Torrent", "X Marks the Spot", "Tidebringer"],
        "role_notes": {
            "mid": "pulls fleeing enemies back with X Marks the Spot, crashing Ghostship down to stun teams and grant Rum defense",
            "offlane": "provides durable frontline control with Tidebringer harass and sets up easy ally kills with X-Torrent combos"
        },
        "beginner_tip": "Cast X Marks the Spot on an enemy, wait 1.6 seconds, cast Torrent underneath them, and recall them immediately."
    },
    "Largo": {
        "stuns_disables": "tactical zone suppression and crowd control",
        "movement": "dynamic repositioning and battlefield pacing",
        "key_abilities": ["Suppression Zone", "Tactical Stun", "Battle Flow"],
        "role_notes": {
            "support": "provides crowd control and defensive utility to protect teammates and coordinate team skirmishes",
            "offlane": "frontlines and controls fight pacing with zoning abilities and durable stats"
        },
        "beginner_tip": "Stay close to your cores and chain your crowd control with ally initiations."
    },
    "Legion Commander": {
        "stuns_disables": "Duel BKB-piercing forced attack lockdown",
        "movement": "Overwhelming Odds burst movement speed buff per unit hit and Press the Attack strong dispel",
        "key_abilities": ["Duel", "Overwhelming Odds", "Press the Attack", "Moment of Courage"],
        "role_notes": {
            "offlane": "purges debuffs with Press the Attack, rushes in with Overwhelming Odds speed, and locks down targets with Duel for permanent damage",
            "carry": "snowballs bonus attack damage with successful Duels, becoming an unstoppable physical assassin"
        },
        "beginner_tip": "Use Press the Attack on yourself before blinking in to Duel so you have max attack speed and health regen."
    },
    "Leshrac": {
        "stuns_disables": "Split Earth AoE ground stun and Lightning Storm movement slow",
        "movement": "high base movement speed and Diabolic Edict tower push tempo",
        "key_abilities": ["Pulse Nova", "Split Earth", "Diabolic Edict", "Lightning Storm"],
        "role_notes": {
            "mid": "storms through fights with high movement speed, landing Split Earth stuns and melting structures with Diabolic Edict",
            "carry": "tanks up with Bloodstone to heal continuously off Pulse Nova damage while running down enemy teams",
            "offlane": "applies immense lane pressure with Diabolic Edict and controls teamfights with Split Earth"
        },
        "beginner_tip": "Cast Lightning Storm first to slow the enemy, making it easy to land your delayed Split Earth stun."
    },
    "Lich": {
        "stuns_disables": "Sinister Gaze hypnotic pull disable and Frost Shield / Chain Frost movement slows",
        "movement": "Frost Shield 60% physical damage reduction armor to protect allies and kite",
        "key_abilities": ["Frost Shield", "Sinister Gaze", "Chain Frost", "Frost Blast"],
        "role_notes": {
            "support": "protects allied cores from physical burst with Frost Shield while pulling targets out of position with Sinister Gaze and bouncing Chain Frost"
        },
        "beginner_tip": "Always cast Frost Shield on whoever is being focused by physical attackers in teamfights."
    },
    "Lifestealer": {
        "stuns_disables": "Ghoul Frenzy attack slow and Open Wounds movement slow",
        "movement": "Rage built-in spell immunity and movement speed buff, and Infest inside mobile allies",
        "key_abilities": ["Rage", "Feast", "Ghoul Frenzy", "Infest"],
        "role_notes": {
            "carry": "infests mobile initiators to deliver surprise ganks, popping Rage for spell immunity and tearing through tanky cores with Feast"
        },
        "beginner_tip": "Infest a friendly initiator (Storm, Slardar, Spirit Breaker) to enter fights right on top of squishy backliners."
    },
    "Lina": {
        "stuns_disables": "Light Strike Array AoE ground stun",
        "movement": "Fiery Soul extreme stacking movement speed and attack speed",
        "key_abilities": ["Laguna Blade", "Light Strike Array", "Dragon Slave", "Fiery Soul"],
        "role_notes": {
            "mid": "stacks blazing movement speed with Fiery Soul to kite across fights, landing Light Strike Array stuns and Laguna Blade burst",
            "carry": "scales with maximum Fiery Soul attack speed to dish out devastating long-range right-click physical damage"
        },
        "beginner_tip": "Keep 3 stacks of Fiery Soul active by casting Dragon Slave on creep waves before entering a teamfight."
    },
    "Lion": {
        "stuns_disables": "instant Hex transformation disable, Earth Spike line stun, and Mana Drain slow",
        "movement": "Blink Dagger initiation and safe backline positioning",
        "key_abilities": ["Hex", "Earth Spike", "Finger of Death", "Mana Drain"],
        "role_notes": {
            "support": "disables priority targets for over 5 seconds with instant Hex and Earth Spike, eliminating squishies with Finger of Death"
        },
        "beginner_tip": "Initiate from fog with Hex first so mobile enemies cannot react with BKB or escapes, then follow up with Earth Spike."
    },
    "Lone Druid": {
        "stuns_disables": "Spirit Bear Entangling Claws root and Savage Roar AoE fear disable",
        "movement": "Spirit Bear Phase Boots chase speed and True Form bonus durability",
        "key_abilities": ["Summon Spirit Bear", "Savage Roar", "Spirit Link", "True Form"],
        "role_notes": {
            "carry": "commands a durable second hero Spirit Bear that roots targets on hit, pushing towers early and fearing divers with Savage Roar",
            "mid": "dominates mid CS with double-unit last hits, taking mid tower early and controlling runes with the Spirit Bear"
        },
        "beginner_tip": "Keep your hero safe behind the creep line while sending the Spirit Bear forward to harass and root enemies."
    },
    "Luna": {
        "stuns_disables": "Lucent Beam ministun and Eclipse night darkness",
        "movement": "high base movement speed and Moon Glaives multi-camp clearing",
        "key_abilities": ["Eclipse", "Moon Glaives", "Lucent Beam", "Lunar Blessing"],
        "role_notes": {
            "carry": "runs at blazing movement speed, clearing camps instantly with Moon Glaives and dropping Eclipse beams on isolated fights"
        },
        "beginner_tip": "Cast Eclipse in skirmishes where there are no enemy creep waves nearby so all beams hit enemy heroes."
    },
    "Lycan": {
        "stuns_disables": "Feral Impulse wolf army body-block and Howl armor and attack reduction",
        "movement": "Shapeshift unslowable maximum haste speed and critical strikes",
        "key_abilities": ["Shapeshift", "Summon Wolves", "Howl", "Feral Impulse"],
        "role_notes": {
            "carry": "transforms into an unslowable wolf with Shapeshift, running down backline supports at max speed with his wolf pack",
            "offlane": "destroys enemy safe lane towers early with summoned wolves and rotates with Shapeshift haste speed"
        },
        "beginner_tip": "Activate Shapeshift before engaging so you cannot be slowed or kited while hunting down squishy backliners."
    },
    "Magnus": {
        "stuns_disables": "Reverse Polarity BKB-piercing vacuum stun, Skewer displacement, and Shockwave slow",
        "movement": "Skewer long-distance charge through terrain and Shockwave pull",
        "key_abilities": ["Reverse Polarity", "Skewer", "Empower", "Shockwave"],
        "role_notes": {
            "offlane": "empowers allied carries with cleave, skewers enemies back into team towers, and turns fights with Reverse Polarity",
            "mid": "farms rapidly with Empower, rotating to side lanes to Skewer enemies into ally setups"
        },
        "beginner_tip": "Keep Empower refreshed on your physical carry at all times to dramatically accelerate their farming speed."
    },
    "Marci": {
        "stuns_disables": "Dispose throw stun and displacement, and Rebound movement slow",
        "movement": "Rebound allied vector leap and Unleash rapid burst speed",
        "key_abilities": ["Unleash", "Dispose", "Rebound", "Sidekick"],
        "role_notes": {
            "support": "leaps across allies with Rebound, throws enemies out of position with Dispose, and buffs allied core damage with Sidekick",
            "carry": "dives backlines with Rebound, pummeling priority targets with rapid Unleash fury punches"
        },
        "beginner_tip": "Use Rebound off your allied frontliner to launch yourself directly behind the target and Dispose them back into your team."
    },
    "Mars": {
        "stuns_disables": "Spear of Mars line wall-pin stun, Arena of Blood containment, and God's Rebuke knockback",
        "movement": "Bulwark directional attack deflection and Arena of Blood battlefield zoning",
        "key_abilities": ["Arena of Blood", "Spear of Mars", "God's Rebuke", "Bulwark"],
        "role_notes": {
            "offlane": "traps enemy squads inside Arena of Blood, pinning priority targets to the wall with Spear of Mars and absorbing hits with Bulwark"
        },
        "beginner_tip": "Cast Arena of Blood first, then immediately Spear an enemy into the arena wall for a guaranteed 3-second pin stun."
    },
    "Medusa": {
        "stuns_disables": "Stone Gaze petrifying gaze stun and physical damage amp, and Mystic Snake slow",
        "movement": "immovable frontline walking tank absorbing damage through Mana Shield",
        "key_abilities": ["Stone Gaze", "Mana Shield", "Split Shot", "Mystic Snake"],
        "role_notes": {
            "carry": "acts as an immovable raid boss whose Stone Gaze forces enemies to turn away or petrify, shredding whole teams with Split Shot"
        },
        "beginner_tip": "Pop Stone Gaze as soon as the enemy team commits on you; enemies who attack you will be forced to turn around or be turned to stone."
    },
    "Meepo": {
        "stuns_disables": "chain Earthbind roots disabling mobility and blinks indefinitely",
        "movement": "Poof teleportation between clones across the map and Dig invulnerability",
        "key_abilities": ["Divided We Stand", "Poof", "Earthbind", "Dig"],
        "role_notes": {
            "mid": "traps enemies indefinitely with chain Earthbind roots, Poofing clone armies to burst targets down and farm every camp",
            "carry": "dominates the map net worth with multiple clones farming simultaneously, ending games before enemy cores come online"
        },
        "beginner_tip": "Throw your next Earthbind just before the previous root expires to keep slippery heroes permanently pinned."
    },
    "Mirana": {
        "stuns_disables": "Sacred Arrow long-range projectile stun (up to 5 seconds)",
        "movement": "Leap forward jump with attack and movement speed buff, and Moonlight Shadow teamwide invisibility",
        "key_abilities": ["Sacred Arrow", "Leap", "Moonlight Shadow", "Starstorm"],
        "role_notes": {
            "support": "snipes enemies with 5-second Sacred Arrows, repositioning with Leap and cloaking the whole team with Moonlight Shadow",
            "mid": "farms lanes with Starstorm waves and uses Leap attack speed to win trades"
        },
        "beginner_tip": "Fire Sacred Arrow from fog or tree lines where enemies have no vision of the incoming projectile."
    },
    "Monkey King": {
        "stuns_disables": "Boundless Strike physical line stun, Primal Spring slow, and Wukong's Command zoning",
        "movement": "Tree Dance treetop leaping, Mischief disguise, and Primal Spring jump",
        "key_abilities": ["Wukong's Command", "Boundless Strike", "Tree Dance", "Jingu Mastery"],
        "role_notes": {
            "carry": "stacks Jingu Mastery to gain lifesteal and damage, initiating with long-range Boundless Strike stuns and Wukong's Command",
            "mid": "leaps between trees with Tree Dance to gank side lanes, dominating 1v1 melee matchups with Jingu Mastery",
            "support": "provides immense scout vision from treetops, initiating with Primal Spring slows and Boundless Strike stuns"
        },
        "beginner_tip": "Get 4 hits for Jingu Mastery before casting Boundless Strike to land a massive critical heal and damage line."
    },
    "Morphling": {
        "stuns_disables": "Adaptive Strike knockback or stun, and Morph spell copying",
        "movement": "Waveform invulnerable repositioning dash through units",
        "key_abilities": ["Waveform", "Adaptive Strike", "Attribute Shift", "Morph"],
        "role_notes": {
            "carry": "shifts attributes between strength and agility, dashing with Waveform and copying enemy spells for surprise plays",
            "mid": "dominates mid lane CS with high base agility damage, surviving ganks by morphing into strength"
        },
        "beginner_tip": "Morph into Strength immediately when you see incoming burst damage to prevent being deleted."
    },
    "Muerta": {
        "stuns_disables": "Dead Shot trickshot fear disable and The Calling circular ghost silence and slow",
        "movement": "Pierce the Veil ethereal transformation becoming immune to physical attacks",
        "key_abilities": ["Pierce the Veil", "Dead Shot", "The Calling", "Gunslinger"],
        "role_notes": {
            "carry": "fears enemies with trickshot Dead Shots, drops The Calling to silence paths, and melts ethereal targets with Pierce the Veil",
            "support": "provides long-range crowd control with Dead Shot fears and zoning with The Calling silences"
        },
        "beginner_tip": "Bounce Dead Shot off trees or creeps so the ricochet bullet passes directly through the target hero to fear them toward your team."
    },
    "Naga Siren": {
        "stuns_disables": "Song of the Siren sleep disable freezing entire screen and Ensnare BKB-piercing root",
        "movement": "Mirror Image illusion scouting and Rip Tide armor shred",
        "key_abilities": ["Song of the Siren", "Ensnare", "Mirror Image", "Rip Tide"],
        "role_notes": {
            "carry": "completely resets or sets up teamfights with Song of the Siren, rooting slippery heroes through BKB with Ensnare",
            "support": "uses Song of the Siren to reset disastrous teamfights or guarantee combos, rooting mobile enemies through BKB"
        },
        "beginner_tip": "Use Song of the Siren to sleep the enemy team, surround the high-priority core with your team, then end the song."
    },
    "Nature's Prophet": {
        "stuns_disables": "Sprout tree ring containment barrier and slow, and Wrath of Nature global bounce",
        "movement": "Teleportation global map presence to anywhere on the map with no range restriction",
        "key_abilities": ["Teleportation", "Sprout", "Nature's Call", "Wrath of Nature"],
        "role_notes": {
            "support": "teleports instantly anywhere on the map to turn ganks, trapping foes in Sprout and providing global Wrath damage",
            "offlane": "pressures enemy towers with Treants and joins any teamfight immediately with Teleportation",
            "carry": "farms the entire map globally, trapping enemies in Sprout and building high physical damage items"
        },
        "beginner_tip": "Keep an eye on side lanes constantly; teleport directly behind overextended enemies to trap them in Sprout."
    },
    "Necrophos": {
        "stuns_disables": "Reaper's Scythe missing-HP execute stun extending enemy death timers",
        "movement": "Ghost Shroud physical attack immunity and slow aura, and Heartstopper sustain",
        "key_abilities": ["Reaper's Scythe", "Death Pulse", "Ghost Shroud", "Heartstopper Aura"],
        "role_notes": {
            "mid": "dominates mid lane sustain with Death Pulse and Heartstopper, executing low-health cores with Reaper's Scythe",
            "offlane": "frontlines as a durable sustain sponge, popping Ghost Shroud against physical carries and securing key scythe executions"
        },
        "beginner_tip": "Wait until an enemy's health bar drops below 40% before casting Reaper's Scythe to guarantee the execution."
    },
    "Night Stalker": {
        "stuns_disables": "Crippling Fear AoE silence aura and Void ministun and movement slow",
        "movement": "Dark Ascension flying vision and flight over terrain, and Hunter in the Night extreme speed",
        "key_abilities": ["Dark Ascension", "Crippling Fear", "Void", "Hunter in the Night"],
        "role_notes": {
            "offlane": "turns day into night with Dark Ascension, flying over trees at max speed to silence backline casters with Crippling Fear"
        },
        "beginner_tip": "Pop Dark Ascension to bypass frontline tanks, flying directly over the trees onto squishy enemy supports."
    },
    "Nyx Assassin": {
        "stuns_disables": "Impale ground line stun, Spiked Carapace damage reflection stun, and Mind Flare burst",
        "movement": "Vendetta stealth with bonus movement speed and armor break",
        "key_abilities": ["Vendetta", "Spiked Carapace", "Impale", "Mind Flare"],
        "role_notes": {
            "support": "stalks invisibly with Vendetta, turning enemy attacks into stuns with Spiked Carapace and bursting casters with Mind Flare",
            "mid": "one-shots enemy intelligence heroes with Vendetta into Mind Flare burst, setting up ganks across the map"
        },
        "beginner_tip": "Activate Spiked Carapace right as an enemy casts an AoE spell (like Meteor, Radiance, or Macropyre) to stun them from across the fight."
    },
    "Ogre Magi": {
        "stuns_disables": "Fireblast single-target stun and lingering Ignite movement slow with Multicast potential",
        "movement": "Bloodlust massive allied movement and attack speed buff",
        "key_abilities": ["Fireblast", "Bloodlust", "Ignite", "Multicast"],
        "role_notes": {
            "support": "dominates lanes with high base armor and HP, stunning runners with Fireblast and supercharging core carries with Bloodlust",
            "offlane": "frontlines as an ultra-durable brawler who absorbs focus fire and locks down priority targets with Multicast stuns"
        },
        "beginner_tip": "Keep Bloodlust active on your main carry 100% of the time and tank skillshots for squishy allies."
    },
    "Omniknight": {
        "stuns_disables": "Hammer of Purity physical slow and Purification burst damage",
        "movement": "Repel magic resistance and debuff immunity, and Guardian Angel physical immunity",
        "key_abilities": ["Guardian Angel", "Repel", "Purification", "Hammer of Purity"],
        "role_notes": {
            "offlane": "frontlines with high sustain, protecting cores with Repel and making the entire team immune to physical attacks with Guardian Angel",
            "support": "babysits allied cores with Purification heals and grants physical damage immunity with Guardian Angel"
        },
        "beginner_tip": "Cast Guardian Angel right when the enemy team commits physical damage ultimates (Omnislash, Chronosphere, Duel)."
    },
    "Oracle": {
        "stuns_disables": "Fortune's End root and dispel, and Fate's Edict 100% magic resistance and disarm",
        "movement": "False Promise ultimate delaying fatal damage and doubling healing",
        "key_abilities": ["False Promise", "Fortune's End", "Fate's Edict", "Purifying Flames"],
        "role_notes": {
            "support": "saves dying allies with False Promise, roots pursuers with Fortune's End, and disarms enemy right-clickers with Fate's Edict"
        },
        "beginner_tip": "Disarm enemy physical carries with Fate's Edict during teamfights, or cast it on an ally right before healing them with Purifying Flames."
    },
    "Outworld Destroyer": {
        "stuns_disables": "Astral Imprisonment banishment disable and save, and Sanity's Eclipse mana drain",
        "movement": "Astral Imprisonment positioning setup and high base movement speed",
        "key_abilities": ["Arcane Orb", "Astral Imprisonment", "Sanity's Eclipse", "Essence Flux"],
        "role_notes": {
            "mid": "banishes enemies to set up ally stuns or save allies from lethal burst, melting high-armor targets with pure Arcane Orb damage"
        },
        "beginner_tip": "Use Astral Imprisonment to save an ally who has been caught by a big disable like Duel or Dismember."
    },
    "Pangolier": {
        "stuns_disables": "Rolling Thunder continuous knock-up stuns and magic immunity, and Lucky Shot disarms",
        "movement": "Swashbuckle directional dash, Shield Crash jump, and Rolling Thunder high-speed bouncing",
        "key_abilities": ["Rolling Thunder", "Swashbuckle", "Shield Crash", "Lucky Shot"],
        "role_notes": {
            "mid": "bounces through teamfights with spell-immune Rolling Thunder, leaping over cliffs with Shield Crash and disarming with Lucky Shot",
            "offlane": "disrupts enemy formations with Rolling Thunder knock-ups and initiates skirmishes with Swashbuckle"
        },
        "beginner_tip": "Bounce off walls and arena barriers during Rolling Thunder to repeatedly knock up the same enemy heroes."
    },
    "Phantom Assassin": {
        "stuns_disables": "Stifling Dagger 50% movement slow and Fan of Knives break",
        "movement": "Phantom Strike targeted blink strike onto allies or enemies, and Blur stealth",
        "key_abilities": ["Coup de Grace", "Phantom Strike", "Stifling Dagger", "Blur"],
        "role_notes": {
            "carry": "jumps onto targets with Phantom Strike, slowing runners with Stifling Dagger and exploding backlines with Coup de Grace crits"
        },
        "beginner_tip": "Use Blur to farm safely near enemy lanes; enemy heroes will not see you on the minimap."
    },
    "Phantom Lancer": {
        "stuns_disables": "Spirit Lance tracking movement slow and Phantom Rush speed boost",
        "movement": "Doppelganger elusive repositioning dispel and Phantom Rush burst sprint",
        "key_abilities": ["Juxtapose", "Doppelganger", "Spirit Lance", "Phantom Rush"],
        "role_notes": {
            "carry": "disjoints spells and dispels debuffs with Doppelganger, rushing down targets with Phantom Rush and exhausting spells with illusion armies"
        },
        "beginner_tip": "Cast Doppelganger right as enemy projectile stuns fly toward you to disjoint the spell and dodge the damage."
    },
    "Phoenix": {
        "stuns_disables": "Fire Spirits massive attack speed slow and Supernova teamwide stun upon hatching",
        "movement": "Icarus Dive looping flight over cliffs and terrain, and Sun Ray beam repositioning",
        "key_abilities": ["Supernova", "Fire Spirits", "Icarus Dive", "Sun Ray"],
        "role_notes": {
            "support": "dives into fights with Icarus Dive, crippling enemy right-clickers with Fire Spirits and stunning teams with Supernova egg",
            "offlane": "zones melee safe lanes with Fire Spirits attack slow and burns tanks with percentage Sun Ray damage"
        },
        "beginner_tip": "Land Fire Spirits on enemy right-clickers before clicking Supernova so they cannot attack fast enough to crack your egg."
    },
    "Primal Beast": {
        "stuns_disables": "Onslaught charging knockback stun and Pulverize BKB-piercing slamming channel stun",
        "movement": "Onslaught charging dash through trees and Uproar movement speed stacks",
        "key_abilities": ["Onslaught", "Pulverize", "Trample", "Uproar"],
        "role_notes": {
            "offlane": "charges through forests with Onslaught, trampling through teamfights and slamming priority targets repeatedly with Pulverize",
            "mid": "controls mid tempo with Onslaught ganks, crushing squishies with Trample and Pulverize"
        },
        "beginner_tip": "Channel Onslaught from behind trees or fog so enemies cannot see where the charging path is aimed."
    },
    "Puck": {
        "stuns_disables": "Dream Coil tether leash and break stun, and Waning Rift AoE silence",
        "movement": "Illusory Orb projectile jaunt, Phase Shift invulnerability, and Waning Rift blink",
        "key_abilities": ["Dream Coil", "Waning Rift", "Phase Shift", "Illusory Orb"],
        "role_notes": {
            "mid": "controls mid lane with supreme elusive mobility, leashing enemies with Dream Coil, silences with Waning Rift, and phase-shifting retaliation"
        },
        "beginner_tip": "Throw Illusory Orb forward, silence with Waning Rift and leash with Dream Coil, then jaunt to your orb to escape safely."
    },
    "Pudge": {
        "stuns_disables": "Meat Hook displacement, Dismember BKB-piercing suppression stun, and Rot slow",
        "movement": "Meat Hook to displace enemies out of safety or pull caught allies to safety",
        "key_abilities": ["Meat Hook", "Dismember", "Rot", "Flesh Heap"],
        "role_notes": {
            "support": "hooks enemies from fog into allied focus fire, locking them down through spell immunity with Dismember",
            "offlane": "tanks frontline damage with Flesh Heap stacks, initiating with Meat Hook and suppressing carries with Dismember",
            "mid": "controls mid lane with Flesh Heap block, rotating to side lanes with Meat Hook from fog"
        },
        "beginner_tip": "Hook targets that are already stunned or slowed by your teammates to guarantee an easy connect."
    },
    "Pugna": {
        "stuns_disables": "Nether Ward magic damage zap and mana flare, and Decrepify ethereal slow",
        "movement": "high base movement speed and Nether Blast tower push tempo",
        "key_abilities": ["Nether Ward", "Life Drain", "Decrepify", "Nether Blast"],
        "role_notes": {
            "support": "places Nether Ward to punish enemy casters, decrepifying physical attackers and siphoning HP to allies with Life Drain",
            "mid": "pushes down mid tower early with Nether Blast and drains enemy cores through magic amplification"
        },
        "beginner_tip": "Place Nether Ward in hidden cliff spots or behind trees before teamfights so enemies cannot easily attack it."
    },
    "Queen of Pain": {
        "stuns_disables": "Shadow Strike heavy movement slow and damage over time, and Sonic Wave knockback",
        "movement": "short-cooldown targeted Blink for instant gap closing and escaping",
        "key_abilities": ["Sonic Wave", "Blink", "Shadow Strike", "Scream of Pain"],
        "role_notes": {
            "mid": "controls runes and lanes with Blink mobility, slowing targets with Shadow Strike and blasting teamfights with pure damage Sonic Wave"
        },
        "beginner_tip": "Blink into the fight at an angle where Sonic Wave hits the maximum number of clumped enemies."
    },
    "Razor": {
        "stuns_disables": "Static Link attack damage drain and Plasma Field movement slow",
        "movement": "Storm Surge constant movement speed passive and Static Link tether speed",
        "key_abilities": ["Static Link", "Plasma Field", "Eye of the Storm", "Storm Surge"],
        "role_notes": {
            "mid": "siphons mid opponent attack damage down to zero with Static Link, pushing lane advantage with Plasma Field",
            "offlane": "runs alongside enemy safe lane carries with Static Link, neutering their physical damage and chasing with high speed",
            "carry": "shreds high-armor carries by stealing their attack damage and building tanky sustain"
        },
        "beginner_tip": "Target the enemy's main physical carry with Static Link and keep running alongside them to steal all their attack power."
    },
    "Riki": {
        "stuns_disables": "Smoke Screen AoE silence, miss chance, and slow, and Sleeping Dart sleep",
        "movement": "Blink Strike dual-charge gap close and Tricks of the Trade invulnerability",
        "key_abilities": ["Tricks of the Trade", "Smoke Screen", "Blink Strike", "Cloak and Dagger"],
        "role_notes": {
            "carry": "silences backlines inside Smoke Screen, jumping with Blink Strike and carving up clumped enemies during Tricks of the Trade",
            "support": "scouts invisibly, drops Smoke Screen silences in fights, and disrupts channeling spells with Sleeping Dart"
        },
        "beginner_tip": "Drop Smoke Screen on spellcasters before attacking so they cannot stun you or blink away."
    },
    "Ringmaster": {
        "stuns_disables": "Wheel of Wonder hypnotic area pull, Tame the Beasts fear whip, and Impalement Arts slow",
        "movement": "Escape Act box save giving bonus movement speed and phasing",
        "key_abilities": ["Wheel of Wonder", "Tame the Beasts", "Escape Act", "Impalement Arts"],
        "role_notes": {
            "support": "saves allies inside Escape Act boxes, whips area fears with Tame the Beasts, and hypnotizes enemy teams with Wheel of Wonder"
        },
        "beginner_tip": "Cast Escape Act on a stunned or focused core to grant them magic resistance and movement speed to reposition."
    },
    "Rubick": {
        "stuns_disables": "Telekinesis air-lift displacement stun and Fade Bolt attack damage reduction",
        "movement": "Telekinesis repositioning of enemies and Arcane Supremacy cast range advantage",
        "key_abilities": ["Spell Steal", "Telekinesis", "Fade Bolt", "Arcane Supremacy"],
        "role_notes": {
            "support": "lifts enemies out of position with Telekinesis, steals the strongest enemy ultimates, and turns their own crowd control back against them"
        },
        "beginner_tip": "Position safely in the backline with your bonus cast range and steal high-impact ultimates (Ravage, Black Hole, Chronosphere)."
    },
    "Sand King": {
        "stuns_disables": "Burrowstrike line stun, Epicenter pulsing slow, and Sand Storm blind and slow",
        "movement": "Burrowstrike underground dash initiation and Sand Storm invisible shroud",
        "key_abilities": ["Epicenter", "Burrowstrike", "Sand Storm", "Caustic Finale"],
        "role_notes": {
            "offlane": "burrows through enemy lines with Burrowstrike stuns, channeling devastating Epicenter earthquake pulses across teamfights",
            "mid": "clears waves instantly with Sand Storm and Caustic Finale, rotating with Blink-Burrowstrike stuns"
        },
        "beginner_tip": "Channel Epicenter from fog or behind a cliff, then immediately shift-queue Blink Dagger and Burrowstrike into the enemy team."
    },
    "Shadow Demon": {
        "stuns_disables": "Disruption banishment save/setup and Demonic Purge continuous slow and passive break",
        "movement": "Disruption to save allies from lethal focus fire and Demonic Purge to slow hasted enemies",
        "key_abilities": ["Disruption", "Demonic Purge", "Shadow Poison", "Disseminate"],
        "role_notes": {
            "support": "saves allies from death with Disruption, breaks enemy passives and strips buffs with Demonic Purge, and amplifies magic damage"
        },
        "beginner_tip": "Use Disruption defensively to banish an ally targeted by lethal spells (Arrow, Scythe, Duel)."
    },
    "Shadow Fiend": {
        "stuns_disables": "Requiem of Souls AoE fear and movement slow, and Shadowraze stacking slows",
        "movement": "Shadowraze triple coil wave clear and high base movement speed",
        "key_abilities": ["Requiem of Souls", "Shadowraze", "Necromastery", "Presence of the Dark Lord"],
        "role_notes": {
            "mid": "dominates mid lane CS with Shadowraze coils, channeling Requiem of Souls from fog to fear and shatter enemy teams",
            "carry": "shreds enemy base armor with Presence of the Dark Lord, building high physical DPS and BKB"
        },
        "beginner_tip": "Cast Shadowraze in sequence (Near, Medium, Far) to stack exponential damage on pursuing enemies."
    },
    "Shadow Shaman": {
        "stuns_disables": "over 7 seconds of lockdown via instant Hex and channeled Shackles",
        "movement": "positioning from fog and Mass Serpent Ward objective zoning",
        "key_abilities": ["Hex", "Shackles", "Mass Serpent Ward", "Ether Shock"],
        "role_notes": {
            "support": "locks down elusive enemy carries with instant Hex and Shackles, enabling guaranteed kills and destroying towers with Serpent Wards"
        },
        "beginner_tip": "Initiate from fog with Hex first so enemies cannot pop BKB or escapes, then chain into Shackles once allies arrive."
    },
    "Silencer": {
        "stuns_disables": "Global Silence map-wide spell lock through BKB and Last Word silence and damage",
        "movement": "safe long-range positioning and Glaives of Wisdom pure damage harass",
        "key_abilities": ["Global Silence", "Arcane Curse", "Glaives of Wisdom", "Last Word"],
        "role_notes": {
            "support": "interrupts big enemy teamfight initiations from anywhere on the map with Global Silence, stealing intelligence on kills",
            "mid": "bullies mid laners with Arcane Curse and Glaives of Wisdom, using Global Silence to counter-initiate"
        },
        "beginner_tip": "Hold Global Silence until the enemy initiator blinks in to cast their key spell (like Enigma, Tidehunter, or Magnus)."
    },
    "Skywrath Mage": {
        "stuns_disables": "Ancient Seal instant target silence and magic damage amp, and Concussive Shot slow",
        "movement": "high base movement speed and long-range spell artillery",
        "key_abilities": ["Mystic Flare", "Ancient Seal", "Arcane Bolt", "Concussive Shot"],
        "role_notes": {
            "support": "silences spellcasters with Ancient Seal, amplifies incoming magic damage, and obliterates locked-down targets with Mystic Flare",
            "mid": "dominates mid trades with Arcane Bolt spam, rotating to delete heroes with Ancient Seal and Mystic Flare"
        },
        "beginner_tip": "Cast Ancient Seal first to amplify magic damage before unleashing Mystic Flare on a stunned target."
    },
    "Slardar": {
        "stuns_disables": "Slithereen Crush AoE stun and slow, and Bash of the Deep repeating physical bashes",
        "movement": "Guardian Sprint unslowable river speed bonus and phased movement",
        "key_abilities": ["Corrosive Haze", "Slithereen Crush", "Guardian Sprint", "Bash of the Deep"],
        "role_notes": {
            "offlane": "sprints down targets through the river with Guardian Sprint, stunning with Slithereen Crush and melting armor with Corrosive Haze"
        },
        "beginner_tip": "Hit creeps three times before blinking on an enemy hero so your very first attack triggers a guaranteed bash."
    },
    "Slark": {
        "stuns_disables": "Pounce leash tether preventing blinks and movement, and Essence Shift stat steal",
        "movement": "Pounce terrain leap and Shadow Dance untargetable invisibility and dark speed",
        "key_abilities": ["Shadow Dance", "Pounce", "Dark Pact", "Essence Shift"],
        "role_notes": {
            "carry": "leashes escaping enemies with Pounce, purging debuffs with Dark Pact and regenerating rapidly out of vision with Shadow Dance"
        },
        "beginner_tip": "Time Dark Pact right before enemy disables land so the dispel pulses immediately break the stun."
    },
    "Snapfire": {
        "stuns_disables": "Firesnap Cookie allied leap stun and Mortimer Kisses long-range slows",
        "movement": "Firesnap Cookie launch leap for allies or self over terrain",
        "key_abilities": ["Mortimer Kisses", "Firesnap Cookie", "Scatterblast", "Lil' Shredder"],
        "role_notes": {
            "support": "launches allies into fight initiation with Firesnap Cookie stuns, raining Mortimer Kisses artillery from extreme range",
            "mid": "bursts squishies with point-blank Scatterblast and shreds armor with Lil' Shredder"
        },
        "beginner_tip": "Cast Firesnap Cookie on your initiator right as they run toward enemy heroes to launch them into a stun."
    },
    "Sniper": {
        "stuns_disables": "Headshot ministun and knockback, Shrapnel area slow, and Assassinate stun",
        "movement": "Take Aim active movement speed and extreme screen-wide attack range safety",
        "key_abilities": ["Assassinate", "Shrapnel", "Headshot", "Take Aim"],
        "role_notes": {
            "mid": "controls high ground and chokepoints with Shrapnel slows, knocking back divers with Headshot from extreme screen range",
            "carry": "dishes out constant long-range physical DPS from maximum safety behind his team"
        },
        "beginner_tip": "Drop Shrapnel on enemy high ground to gain flying vision before attacking towers."
    },
    "Spectre": {
        "stuns_disables": "Spectral Dagger slow and terrain phasing, and Desolate pure damage",
        "movement": "Shadow Step / Haunt global teleportation behind enemy heroes and cliff walking",
        "key_abilities": ["Haunt", "Spectral Dagger", "Desolate", "Dispersion"],
        "role_notes": {
            "carry": "haunts globally onto vulnerable enemy supports in teamfights, walking through cliffs with Spectral Dagger and reflecting damage"
        },
        "beginner_tip": "Farm safely on the opposite side of the map and use Shadow Step to instantly join teamfights when combat breaks out."
    },
    "Spirit Breaker": {
        "stuns_disables": "Charge of Darkness BKB-piercing global stun, Nether Strike bash, and Greater Bash",
        "movement": "Charge of Darkness map-wide high-speed charge ignoring terrain",
        "key_abilities": ["Charge of Darkness", "Nether Strike", "Greater Bash", "Bulldoze"],
        "role_notes": {
            "support": "barrels across the map with Charge of Darkness, bashing enemy carries through spell immunity and disrupting backlines",
            "offlane": "initiates skirmishes globally, soaking up spells with Bulldoze status resistance and bashing priority targets"
        },
        "beginner_tip": "Cast Charge of Darkness on the enemy backline support so you charge through the entire enemy team, bashing multiple units."
    },
    "Storm Spirit": {
        "stuns_disables": "Electric Vortex targeted pull disable and Overload AoE attack slow",
        "movement": "infinite Ball Lightning map-wide invulnerable zip mobility",
        "key_abilities": ["Ball Lightning", "Electric Vortex", "Static Remnant", "Overload"],
        "role_notes": {
            "mid": "dominates mid lane tempo and power runes, zipping across teamfights with Ball Lightning to isolate and assassinate backlines"
        },
        "beginner_tip": "Secure power runes at minutes 6 and 8, and use short zips in fights to constantly trigger Overload damage."
    },
    "Sven": {
        "stuns_disables": "Storm Hammer AoE target stun and Warcry armor and speed buff",
        "movement": "Warcry teamwide bonus movement speed and Storm Hammer transport",
        "key_abilities": ["God's Strength", "Storm Hammer", "Great Cleave", "Warcry"],
        "role_notes": {
            "carry": "cleaves through entire enemy teams during God's Strength, initiating with Storm Hammer stuns and buffing team armor with Warcry",
            "support": "provides reliable AoE stuns with Storm Hammer and protects the team with Warcry armor and speed"
        },
        "beginner_tip": "Pop Warcry before blinking in to grant your entire team bonus movement speed and armor."
    },
    "Techies": {
        "stuns_disables": "Blast Off! area stun and self-damage silence, and Sticky Bomb disarm and slow",
        "movement": "Blast Off! long-range launching leap over cliffs and terrain",
        "key_abilities": ["Blast Off!", "Sticky Bomb", "Reactive Tazer", "Proximity Mines"],
        "role_notes": {
            "support": "leaps into skirmishes with Blast Off! stuns, slowing and disarming enemies with Sticky Bombs and controlling chokepoints",
            "mid": "bursts waves with Sticky Bombs and controls jungle entrances with Proximity Mines"
        },
        "beginner_tip": "Use Blast Off! from fog over trees so enemies have no time to dodge the incoming landing stun."
    },
    "Templar Assassin": {
        "stuns_disables": "Psionic Trap movement slows and vision, and Meld armor shred",
        "movement": "Psionic Projection trap teleportation and Refraction damage block instances",
        "key_abilities": ["Refraction", "Meld", "Psionic Trap", "Psi Blades"],
        "role_notes": {
            "mid": "dominates mid CS with Psi Blades spill, setting up vision traps and melting high-armor targets with Meld",
            "carry": "takes Roshan early with Meld armor reduction and teleports across the map via Psionic Projection"
        },
        "beginner_tip": "Place Psionic Traps at rune spots and Roshan pit to grant flying vision and slow enemy rotations."
    },
    "Terrorblade": {
        "stuns_disables": "Reflection AoE enemy illusion slow and Sunder health swap",
        "movement": "Metamorphosis ranged transformation and Conjure Image split pushing",
        "key_abilities": ["Metamorphosis", "Sunder", "Conjure Image", "Reflection"],
        "role_notes": {
            "carry": "slows entire enemy teams with Reflection, transforming into ranged demonic artillery with Metamorphosis and swapping HP with Sunder"
        },
        "beginner_tip": "Save Sunder for when your HP drops into the red zone, then swap with a full-health enemy hero to turn the fight instantly."
    },
    "Tidehunter": {
        "stuns_disables": "Ravage massive screen-wide tentacle stun and Gush armor reduction slow",
        "movement": "Kraken Shell passive debuff dispel and Blink Dagger initiation",
        "key_abilities": ["Ravage", "Kraken Shell", "Anchor Smash", "Gush"],
        "role_notes": {
            "offlane": "anchors the frontline as an indestructible tank whose Kraken Shell dispels stuns, locking down entire teams with screen-wide Ravage"
        },
        "beginner_tip": "Position aggressively in front of your team; Kraken Shell will automatically remove stuns if the enemy tries to burst you."
    },
    "Timbersaw": {
        "stuns_disables": "Whirling Death attribute reduction slow and Chakram heavy passing slow",
        "movement": "Timber Chain rapid latch and pull to trees across fights",
        "key_abilities": ["Chakram", "Timber Chain", "Whirling Death", "Reactive Armor"],
        "role_notes": {
            "offlane": "zips between trees with Timber Chain, cutting down Strength heroes with Whirling Death and slowing chokepoints with Chakram",
            "mid": "dominates melee mid matchups with Reactive Armor stacks, diving towers with Timber Chain mobility"
        },
        "beginner_tip": "Always fight near tree lines so you can latch Timber Chain every 4 seconds to reposition or escape."
    },
    "Tinker": {
        "stuns_disables": "Laser 100% physical miss blind and Warp Flare banish",
        "movement": "Rearm item refreshing and Defense Matrix status resistance and shield",
        "key_abilities": ["Laser", "Rearm", "Defense Matrix", "Warp Flare"],
        "role_notes": {
            "mid": "blinds enemy right-clickers with Laser, shielding allies with Defense Matrix and continuously rearming utility spells",
            "support": "provides shields with Defense Matrix, blinds cores with Laser, and repositions targets with Warp Flare"
        },
        "beginner_tip": "Cast Laser on enemy physical carries at the start of skirmishes to negate all their right-click damage for 4 seconds."
    },
    "Tiny": {
        "stuns_disables": "Avalanche repeating ground stun and Toss displacement throw",
        "movement": "Toss ally throw gap-close and Tree Grab bonus movement speed",
        "key_abilities": ["Avalanche", "Toss", "Tree Grab", "Grow"],
        "role_notes": {
            "mid": "deletes squishy heroes with Avalanche into Toss burst combos, rotating early to win side lanes",
            "offlane": "initiates fights with Blink-Avalanche, tossing priority targets back into allied towers",
            "carry": "cleaves through teamfights with Tree Grab physical burst and demolishes buildings with Grow damage",
            "support": "roams between lanes to Toss enemies out of position into ally stuns"
        },
        "beginner_tip": "Cast Avalanche first and immediately Toss the target into the air; units take double Avalanche damage while airborne."
    },
    "Treant Protector": {
        "stuns_disables": "Overgrowth BKB-piercing teamwide root and disarm, and Leech Seed slow",
        "movement": "Nature's Guise invisible tree-walking and Living Armor global structure repair",
        "key_abilities": ["Overgrowth", "Living Armor", "Leech Seed", "Nature's Grasp"],
        "role_notes": {
            "support": "roots entire enemy teams through spell immunity with Overgrowth, repairing towers globally and walking through trees invisibly"
        },
        "beginner_tip": "Constantly monitor tower and ally health across the map to keep Living Armor healing active on cooldown."
    },
    "Troll Warlord": {
        "stuns_disables": "Whirling Axes blind and slow, and Berserker's Rage melee net roots",
        "movement": "Battle Trance unslowable frenzy chase and Berserker's Rage bonus movement speed",
        "key_abilities": ["Battle Trance", "Berserker's Rage", "Whirling Axes (Melee)", "Fervor"],
        "role_notes": {
            "carry": "traps targets with melee net roots and bashes, surviving lethal burst with Battle Trance while shredding targets at max attack speed"
        },
        "beginner_tip": "Switch to melee stance when engaging in combat to gain bonus armor, movement speed, and chance to root on hit."
    },
    "Tusk": {
        "stuns_disables": "Walrus PUNCH! BKB-piercing knock-up crit stun, Ice Shards wall, and Snowball stun",
        "movement": "Snowball gathering allies inside an invulnerable rolling sphere",
        "key_abilities": ["Walrus PUNCH!", "Snowball", "Ice Shards", "Tag Team"],
        "role_notes": {
            "support": "gathers allies into Snowball to dodge lethal enemy spells, walling terrain with Ice Shards and punching foes into the air",
            "offlane": "initiates skirmishes with Snowball into Ice Shards, dealing heavy physical crit burst with Walrus PUNCH!",
            "mid": "bursts squishy heroes with Tag Team and Walrus PUNCH!, rotating with Snowball mobility"
        },
        "beginner_tip": "Pull caught or stunned allies into your Snowball to make them completely invulnerable to enemy burst damage."
    },
    "Underlord": {
        "stuns_disables": "Pit of Malice repeating area roots and Firestorm percentage damage slow",
        "movement": "Fiend's Gate global two-way portal teleporting the entire team across the map",
        "key_abilities": ["Fiend's Gate", "Pit of Malice", "Firestorm", "Atrophy Aura"],
        "role_notes": {
            "offlane": "opens Fiend's Gate portals for instant team rotations, trapping enemies in Pit of Malice and reducing enemy attack damage with Atrophy Aura"
        },
        "beginner_tip": "Drop Pit of Malice underneath clumped enemies and immediately cast Firestorm to burn their percentage health while rooted."
    },
    "Undying": {
        "stuns_disables": "Tombstone spawning slowing zombies, Decay Strength steal, and Soul Rip",
        "movement": "Flesh Golem percentage slow and damage amplification aura",
        "key_abilities": ["Tombstone", "Decay", "Soul Rip", "Flesh Golem"],
        "role_notes": {
            "support": "drops Tombstone to overwhelm fights with endless slowing zombies, stealing enemy Strength with Decay to become an unkillable golem",
            "offlane": "steals enemy Strength repeatedly in lane with Decay, zoning the carry and dominating teamfights with Tombstone"
        },
        "beginner_tip": "Place Tombstone on high ground or behind tree lines where enemies cannot easily right-click it down."
    },
    "Ursa": {
        "stuns_disables": "Earthshock leap movement slow and Enrage status resistance",
        "movement": "Earthshock short hop repositioning and Enrage 80% damage reduction",
        "key_abilities": ["Enrage", "Fury Swipes", "Overpower", "Earthshock"],
        "role_notes": {
            "carry": "hops into combat with Earthshock slows, shrugging off disables with Enrage and stacking exponential Fury Swipes to shred Roshan and heroes"
        },
        "beginner_tip": "Pop Enrage the moment you get stunned or jumped to cut all incoming damage by 80% and rapidly reduce debuff durations."
    },
    "Vengeful Spirit": {
        "stuns_disables": "Magic Missile reliable target stun and Nether Swap positional displacement",
        "movement": "Nether Swap instant position swap to isolate enemies or save allies",
        "key_abilities": ["Nether Swap", "Magic Missile", "Wave of Terror", "Vengeance Aura"],
        "role_notes": {
            "support": "swaps positions with Nether Swap to deliver enemy cores to your team or save caught allies, stunning targets with Magic Missile",
            "carry": "scales with Vengeance Aura bonus damage, lowering armor with Wave of Terror and locking down targets"
        },
        "beginner_tip": "Use Nether Swap defensively to pull your carry out of Chronosphere, Black Hole, or Duel to take their place."
    },
    "Venomancer": {
        "stuns_disables": "Venomous Gale 50% movement slow, Poison Nova / Latent Toxicity, and Plague Wards",
        "movement": "Plague Ward vision scouting and continuous lane slow pressure",
        "key_abilities": ["Poison Nova", "Venomous Gale", "Plague Wards", "Poison Sting"],
        "role_notes": {
            "support": "litters combat zones with Plague Wards, crippling enemy movement with Venomous Gale and poisoning entire teams with lethal damage",
            "offlane": "locks down the safe lane with ward vision, denying enemy farm and slowing teamfights to a crawl"
        },
        "beginner_tip": "Plant Plague Wards ahead of your team to cancel enemy Blink Daggers and scout high ground safely."
    },
    "Viper": {
        "stuns_disables": "Nethertoxin passive break and slow, and Viper Strike massive movement and attack slow",
        "movement": "Corrosive Skin passive enemy slow and ranged kiting",
        "key_abilities": ["Viper Strike", "Nethertoxin", "Poison Attack", "Corrosive Skin"],
        "role_notes": {
            "mid": "dominates 1v1 mid lane harass with Poison Attack, breaking passive abilities with Nethertoxin and slowing gank targets with Viper Strike",
            "offlane": "shuts down passive-reliant carries (Bristleback, PA, Specter) with Nethertoxin Break while kiting with Corrosive Skin"
        },
        "beginner_tip": "Drop Nethertoxin directly underneath enemies whose passives keep them alive (like Bristleback, Spectre, or PA) to Break them."
    },
    "Visage": {
        "stuns_disables": "Familiar Stone Form AoE drop stuns and Grave Chill speed steal",
        "movement": "Grave Chill haste speed steal and flying Familiars scouting",
        "key_abilities": ["Summon Familiars", "Grave Chill", "Soul Assumption", "Gravekeeper's Cloak"],
        "role_notes": {
            "support": "steals enemy speed with Grave Chill, dropping Familiar gargoyle stuns to chain-lock targets and burst with Soul Assumption",
            "mid": "accelerates mid lane tower siege with flying Familiars, dropping chain stuns on isolated cores",
            "offlane": "tanks damage with Gravekeeper's Cloak, pushing side lanes and locking down enemies with Stone Form stuns"
        },
        "beginner_tip": "Use Stone Form with one Familiar at a time to chain-stun an enemy for up to 3 seconds."
    },
    "Void Spirit": {
        "stuns_disables": "Aether Remnant vector pull disable, Astral Step movement slow, and Resonant Pulse shield",
        "movement": "Astral Step dual-charge dash and Dissimilate portal phase evasion",
        "key_abilities": ["Astral Step", "Dissimilate", "Aether Remnant", "Resonant Pulse"],
        "role_notes": {
            "mid": "dashes through skirmishes with Astral Step, phasing through spells with Dissimilate and pulling targets with Aether Remnant"
        },
        "beginner_tip": "Vector-aim Aether Remnant toward your allied team so when an enemy triggers it, they are pulled straight into your teammates."
    },
    "Warlock": {
        "stuns_disables": "Chaotic Offering massive BKB-piercing summoning stun and Upheaval 100% slow",
        "movement": "Fatal Bonds damage distribution and Upheaval area denial channel",
        "key_abilities": ["Chaotic Offering", "Fatal Bonds", "Upheaval", "Shadow Word"],
        "role_notes": {
            "support": "links entire enemy teams with Fatal Bonds, dropping stunning Golems with Chaotic Offering and channeling suffocating Upheaval slows"
        },
        "beginner_tip": "Always cast Fatal Bonds on the enemy team first before dropping Chaotic Offering so the golem impact damage is shared across all targets."
    },
    "Weaver": {
        "stuns_disables": "The Swarm armor-shredding beetles with vision, and Geminate Attack physical burst",
        "movement": "Shukuchi maximum-speed invisible sprint with phasing and Time Lapse positional HP rewind",
        "key_abilities": ["Shukuchi", "Time Lapse", "The Swarm", "Geminate Attack"],
        "role_notes": {
            "carry": "sprints invisibly at max speed with Shukuchi, attaching Swarm beetles to strip armor and rewinding fatal damage with Time Lapse",
            "support": "launches Swarm beetles to reveal fog and strip armor, weaving through fights at max speed with Shukuchi"
        },
        "beginner_tip": "Cast Time Lapse immediately after enemy burst spells hit to rewind your position and recover all lost HP."
    },
    "Windranger": {
        "stuns_disables": "Shackleshot dual-target or tree latch stun (up to 3.8s) and Gale Force push",
        "movement": "Windrun 100% physical evasion and maximum movement speed, and moving Focus Fire",
        "key_abilities": ["Focus Fire", "Shackleshot", "Windrun", "Powershot"],
        "role_notes": {
            "mid": "runs at maximum speed with Windrun evasion, pinning targets to trees with 3.8-second Shackleshots and burning them with Focus Fire",
            "support": "lands long Shackleshot stuns in lane and teamfights, scouting with Powershot and diving with Windrun",
            "carry": "scales with Focus Fire attack speed, shredding through enemy cores while moving at max speed with Windrun"
        },
        "beginner_tip": "Position yourself so that an enemy hero is directly between you and a tree or second enemy unit before casting Shackleshot."
    },
    "Winter Wyvern": {
        "stuns_disables": "Winter's Curse BKB-piercing forced attack madness and Splinter Blast slow",
        "movement": "Arctic Burn unobstructed flying movement over trees and Cold Embrace physical save",
        "key_abilities": ["Winter's Curse", "Cold Embrace", "Arctic Burn", "Splinter Blast"],
        "role_notes": {
            "support": "saves allies from physical burst with Cold Embrace, flying over trees with Arctic Burn and forcing enemies to kill their own core with Winter's Curse",
            "mid": "flies over terrain with Arctic Burn to deal heavy percentage damage and clears waves with Splinter Blast"
        },
        "beginner_tip": "Cast Winter's Curse on a squishy support standing right next to their own high-damage physical carry so the carry deletes their own teammate."
    },
    "Witch Doctor": {
        "stuns_disables": "Paralyzing Cask bouncing chain stuns and Maledict percentage burst",
        "movement": "backline positioning and Death Ward channeled physical devastation",
        "key_abilities": ["Death Ward", "Paralyzing Cask", "Maledict", "Voodoo Restoration"],
        "role_notes": {
            "support": "throws bouncing Paralyzing Cask stuns through clustered fights, cursing targets with Maledict and channeling catastrophic Death Ward damage"
        },
        "beginner_tip": "Wait for two enemy units to stand close together before throwing Paralyzing Cask so the cask bounces repeatedly between them."
    },
    "Wraith King": {
        "stuns_disables": "Wraithfire Blast target projectile stun and slow, and Reincarnation death slow",
        "movement": "Reincarnation second life and Vampiric Spirit skeleton push armies",
        "key_abilities": ["Reincarnation", "Wraithfire Blast", "Mortal Strike", "Vampiric Spirit"],
        "role_notes": {
            "carry": "stuns targets with Wraithfire Blast, commands skeleton armies, and reincarnates upon death to slow the entire fight and get a second life",
            "offlane": "acts as an aggressive frontline sponge who initiates with Wraithfire Blast and forces enemies to waste spells killing him twice"
        },
        "beginner_tip": "Keep an eye on your mana pool to ensure you always have enough mana for Reincarnation when taking fatal damage."
    },
    "Zeus": {
        "stuns_disables": "Lightning Bolt ministun interrupting channels and Heavenly Jump movement slow",
        "movement": "Heavenly Jump backward leap and hop, and global Thundergod's Wrath",
        "key_abilities": ["Thundergod's Wrath", "Lightning Bolt", "Arc Lightning", "Heavenly Jump"],
        "role_notes": {
            "mid": "dominates mid lane harass with Arc Lightning, interrupting channels with Lightning Bolt and revealing enemies globally with Thundergod's Wrath",
            "support": "provides dewarding true sight with Lightning Bolt and chips down whole teams globally with percentage magic burst"
        },
        "beginner_tip": "Cast Lightning Bolt on the ground where you suspect enemy invisible wards to instantly reveal and destroy them."
    }
}


def explain_role_fit(hero: str, target_role: str, ally_names: list = None) -> dict:
    """Generate structured beginner-friendly explanation for how a hero fits a role, detailing disables and movement."""
    kit = HERO_TACTICAL_KITS.get(hero)
    norm_role = (target_role or "support").lower().replace(" ", "_")
    if norm_role in ["soft_support", "hard_support"]:
        role_key = "support"
        role_label = "Support" if norm_role == "support" else norm_role.replace("_", " ").title()
    elif norm_role in ["mid", "midlane", "mid_lane"]:
        role_key = "mid"
        role_label = "Mid Lane"
    elif norm_role in ["offlane", "off_lane"]:
        role_key = "offlane"
        role_label = "Offlane"
    elif norm_role in ["carry", "safelane", "safe_lane"]:
        role_key = "carry"
        role_label = "Carry"
    else:
        role_key = "support"
        role_label = target_role.title()

    if kit:
        disables = kit["stuns_disables"]
        movement = kit["movement"]
        notes = kit.get("role_notes", {})
        specific_note = notes.get(role_key) or notes.get("support") or (list(notes.values())[0] if notes else "")
        abilities = kit.get("key_abilities", [])
        tip = kit.get("beginner_tip", "Coordinate spell timings with your team.")
    else:
        disables = "reliable crowd control"
        movement = "active positioning"
        specific_note = f"fills the {role_label} position with solid fundamentals"
        abilities = []
        tip = "Focus on positioning and team communication."

    # Punchy 1-line tactical explanation
    if role_key == "mid":
        one_liner = f"{hero} dominates mid tempo with {movement}, using {disables} to control rotations and set up team kills."
    elif role_key == "offlane":
        one_liner = f"{hero} anchors the frontline with {movement}, using {disables} to initiate teamfights and protect allies."
    elif role_key == "carry":
        one_liner = f"{hero} scales into the primary win condition, utilizing {movement} to farm safely and {disables} to lock down priority targets."
    else:  # support / soft_support / hard_support
        one_liner = f"{hero} provides essential team utility through {disables}, utilizing {movement} to protect allies and coordinate engagements."

    # Detailed tactical paragraph
    ally_phrase = f" Complements {', '.join(ally_names[:3])} with strong teamfight cohesion." if ally_names else ""
    how = (
        f"{hero} fills the team's missing {role_label} role. Specifically, {hero} {specific_note}. "
        f"Their {disables} provides crucial lockdown to interrupt enemy spells and secure kills, while {movement} enables rapid rotations and tactical positioning across fights.{ally_phrase}"
    )

    return {
        "summary": f"Role Fit: {role_label} ({hero})",
        "target_hero": "",
        "reason_type": "role_fit",
        "role": norm_role,
        "one_liner": one_liner,
        "how_and_why": how,
        "key_abilities": abilities,
        "beginner_tip": tip,
        "sample_size": 0,
        "confidence": "high"
    }
