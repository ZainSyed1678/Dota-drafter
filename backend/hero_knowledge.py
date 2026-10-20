"""
Dota 2 Hero Knowledge Base: Beginner-Friendly Mechanics, Counters & Synergies
Provides deep 'How and Why' explanations for match recommendations.
"""

# ── 1. Hero Complexity / Skill Floor ─────────────────────────────────────────
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
        return {
            "summary": f"Counters {enemy} ({wr_delta:+.1%} WR)",
            "target_hero": enemy,
            "reason_type": "counter",
            "how_and_why": spec["how_and_why"],
            "key_abilities": spec["abilities"],
            "beginner_tip": spec["tip"]
        }

    # Generic intelligent fallback using tags
    h_tags = HERO_TAGS.get(hero, [])
    e_tags = HERO_TAGS.get(enemy, [])

    how = f"{hero} holds a favorable matchup against {enemy} ({wr_delta:+.1%} winrate advantage in high-MMR drafts)."
    abilities = []
    tip = f"Play around your team's initiation and prioritize shutting down {enemy} in skirmishes."

    if "anti_illusions" in h_tags and "illusion_army" in e_tags:
        how = f"{hero}'s AoE abilities clear {enemy}'s illusion swarm instantly, stripping away their main defense and damage."
        tip = f"Hold your key AoE spells until {enemy} summons their full illusion army."
    elif "mana_burn" in h_tags and "mana_reliant_zip" in e_tags:
        how = f"{hero}'s mana draining spells deplete {enemy}'s mana pool, removing their ability to escape or cast spells."
        tip = f"Drain {enemy}'s mana early in the engagement so they are left stranded."
    elif "anti_heal" in h_tags and "low_hp_regen" in e_tags:
        how = f"{hero} disables {enemy}'s ability to heal or lifesteal, cutting off their main survival mechanic."
        tip = f"Land your anti-heal abilities right when {enemy} engages into combat."
    elif "global_gap_close" in h_tags and "squishy_backline" in e_tags:
        how = f"{hero} easily bypasses the frontline to jump straight onto {enemy}, eliminating their long-range safety advantage."
        tip = f"Target {enemy} in the backline before they can free-hit your teammates."
    elif "armor_reduction" in h_tags:
        how = f"{hero} strips {enemy}'s armor, allowing allied physical damage to burst them down much faster."
        tip = "Apply your armor reduction debuffs first before your physical carry commits."
    elif "passive_break" in h_tags:
        how = f"{hero} breaks {enemy}'s strong passive abilities, severely weakening their defensive and offensive stats."
        tip = f"Ensure {enemy} is afflicted with Break before dumping high-damage abilities into them."

    return {
        "summary": f"Counters {enemy} ({wr_delta:+.1%} WR)",
        "target_hero": enemy,
        "reason_type": "counter",
        "how_and_why": how,
        "key_abilities": abilities,
        "beginner_tip": tip
    }

def explain_synergy(hero: str, ally: str, wr_delta: float) -> dict:
    """Generate structured beginner explanation for why hero synergizes with ally."""
    key = (hero, ally)
    if key in SPECIFIC_SYNERGIES:
        spec = SPECIFIC_SYNERGIES[key]
        return {
            "summary": f"Synergizes with {ally} ({wr_delta:+.1%} WR)",
            "target_hero": ally,
            "reason_type": "synergy",
            "how_and_why": spec["how_and_why"],
            "key_abilities": spec["abilities"],
            "beginner_tip": spec["tip"]
        }

    # Generic intelligent fallback
    h_tags = HERO_TAGS.get(hero, [])
    a_tags = HERO_TAGS.get(ally, [])

    how = f"{hero} forms an effective combination with {ally}, boosting team win probability by {wr_delta:+.1%}."
    abilities = []
    tip = f"Coordinate spell timings and target focus together with {ally} during lane and teamfights."

    if ("stationary_bubble" in h_tags or "massive_aoe_stun" in h_tags) and ("channeled_physical_ult" in a_tags or "aoe_burst" in a_tags):
        how = f"{hero} provides heavy AoE crowd control that holds enemies stationary, allowing {ally} to land high-impact spells with 100% accuracy."
        tip = f"Wait for {hero} to initiate and lock targets down before casting your big teamfight spells."
    elif "armor_reduction" in h_tags and "physical_burst" in a_tags:
        how = f"{hero}'s armor shred dramatically amplifies {ally}'s physical right-click burst damage."
        tip = f"Attack whichever target {hero} has debuffed with armor reduction."

    return {
        "summary": f"Synergizes with {ally} ({wr_delta:+.1%} WR)",
        "target_hero": ally,
        "reason_type": "synergy",
        "how_and_why": how,
        "key_abilities": abilities,
        "beginner_tip": tip
    }
