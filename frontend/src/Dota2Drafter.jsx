import { useState, useMemo, useEffect, useRef } from "react";
import INITIAL_HEROES from "./heroes_fallback.json";

const API = import.meta.env.VITE_API_URL || "/api";

// ── ATTRIBUTE METADATA ─────────────────────────────────────────────────────────
const HERO_ATTRIBUTES_META = {
  strength: {
    title: "STRENGTH",
    icon: "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/icons/hero_strength.png",
    color: "var(--str-red)",
  },
  agility: {
    title: "AGILITY",
    icon: "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/icons/hero_agility.png",
    color: "var(--agi-green)",
  },
  intelligence: {
    title: "INTELLIGENCE",
    icon: "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/icons/hero_intelligence.png",
    color: "var(--int-blue)",
  },
  universal: {
    title: "UNIVERSAL",
    icon: "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/icons/hero_universal.png",
    color: "var(--uni-purple)",
  },
};

const ATTR_ORDER = ["strength", "agility", "intelligence", "universal"];
const MAX_ENEMY = 5;
const MAX_ALLY = 4;
const MAX_BANS = 7;

// Canonical position mapping (1: Carry, 2: Mid, 3: Offlane, 4: Soft Supp, 5: Hard Supp)
const HERO_PRIMARY_POS = {
  "Anti-Mage": 1, "Axe": 3, "Bane": 5, "Bloodseeker": 1, "Crystal Maiden": 5, "Drow Ranger": 1, "Earthshaker": 4,
  "Juggernaut": 1, "Mirana": 4, "Morphling": 1, "Shadow Fiend": 2, "Phantom Lancer": 1, "Puck": 2, "Pudge": 2,
  "Razor": 2, "Sand King": 3, "Storm Spirit": 2, "Sven": 1, "Tiny": 2, "Vengeful Spirit": 5, "Windranger": 2,
  "Zeus": 2, "Kunkka": 2, "Lina": 2, "Lion": 5, "Shadow Shaman": 5, "Slardar": 3, "Tidehunter": 3, "Witch Doctor": 5,
  "Lich": 5, "Riki": 1, "Enigma": 3, "Tinker": 2, "Sniper": 2, "Necrophos": 2, "Warlock": 5, "Beastmaster": 3,
  "Queen of Pain": 2, "Venomancer": 4, "Faceless Void": 1, "Wraith King": 1, "Death Prophet": 2, "Phantom Assassin": 1,
  "Pugna": 4, "Templar Assassin": 2, "Viper": 2, "Luna": 1, "Dragon Knight": 2, "Dazzle": 5, "Clockwerk": 4,
  "Leshrac": 2, "Nature's Prophet": 3, "Lifestealer": 1, "Dark Seer": 3, "Clinkz": 1, "Omniknight": 3, "Enchantress": 5,
  "Huskar": 2, "Night Stalker": 3, "Broodmother": 3, "Bounty Hunter": 4, "Weaver": 1, "Jakiro": 5, "Batrider": 3,
  "Chen": 5, "Spectre": 1, "Ancient Apparition": 5, "Doom": 3, "Ursa": 1, "Spirit Breaker": 4, "Gyrocopter": 1,
  "Alchemist": 1, "Invoker": 2, "Silencer": 5, "Outworld Destroyer": 2, "Lycan": 1, "Brewmaster": 3, "Shadow Demon": 5,
  "Lone Druid": 1, "Chaos Knight": 1, "Meepo": 2, "Treant Protector": 5, "Ogre Magi": 5, "Undying": 5, "Rubick": 4,
  "Disruptor": 5, "Nyx Assassin": 4, "Naga Siren": 1, "Keeper of the Light": 5, "Io": 5, "Visage": 3, "Slark": 1,
  "Medusa": 1, "Troll Warlord": 1, "Centaur Warrunner": 3, "Magnus": 3, "Timbersaw": 3, "Bristleback": 3, "Tusk": 4,
  "Skywrath Mage": 4, "Abaddon": 5, "Elder Titan": 4, "Legion Commander": 3, "Techies": 4, "Ember Spirit": 2,
  "Earth Spirit": 4, "Underlord": 3, "Terrorblade": 1, "Phoenix": 4, "Oracle": 5, "Winter Wyvern": 5, "Arc Warden": 2,
  "Monkey King": 1, "Dark Willow": 4, "Pangolier": 2, "Grimstroke": 5, "Hoodwink": 4, "Void Spirit": 2, "Snapfire": 4,
  "Mars": 3, "Dawnbreaker": 3, "Marci": 4, "Primal Beast": 3, "Muerta": 1, "Ringmaster": 4,
};

// Complexity: 1 = Beginner / Easy, 2 = Moderate, 3 = High
const HERO_COMPLEXITY = {
  "Anti-Mage": 1, "Axe": 1, "Bane": 2, "Bloodseeker": 1, "Crystal Maiden": 1, "Drow Ranger": 1, "Earthshaker": 2,
  "Juggernaut": 1, "Mirana": 2, "Morphling": 3, "Shadow Fiend": 2, "Phantom Lancer": 2, "Puck": 3, "Pudge": 2,
  "Razor": 1, "Sand King": 2, "Storm Spirit": 3, "Sven": 1, "Tiny": 2, "Vengeful Spirit": 1, "Windranger": 2,
  "Zeus": 1, "Kunkka": 2, "Lina": 2, "Lion": 1, "Shadow Shaman": 1, "Slardar": 1, "Tidehunter": 1, "Witch Doctor": 1,
  "Lich": 1, "Riki": 1, "Enigma": 2, "Tinker": 3, "Sniper": 1, "Necrophos": 1, "Warlock": 1, "Beastmaster": 2,
  "Queen of Pain": 2, "Venomancer": 1, "Faceless Void": 2, "Wraith King": 1, "Death Prophet": 1, "Phantom Assassin": 1,
  "Pugna": 2, "Templar Assassin": 2, "Viper": 1, "Luna": 1, "Dragon Knight": 1, "Dazzle": 1, "Clockwerk": 2,
  "Leshrac": 2, "Nature's Prophet": 2, "Lifestealer": 1, "Dark Seer": 2, "Clinkz": 2, "Omniknight": 1, "Enchantress": 2,
  "Huskar": 1, "Night Stalker": 1, "Broodmother": 3, "Bounty Hunter": 1, "Weaver": 2, "Jakiro": 1, "Batrider": 2,
  "Chen": 3, "Spectre": 1, "Ancient Apparition": 1, "Doom": 2, "Ursa": 1, "Spirit Breaker": 1, "Gyrocopter": 1,
  "Alchemist": 1, "Invoker": 3, "Silencer": 1, "Outworld Destroyer": 2, "Lycan": 2, "Brewmaster": 3, "Shadow Demon": 2,
  "Lone Druid": 3, "Chaos Knight": 1, "Meepo": 3, "Treant Protector": 1, "Ogre Magi": 1, "Undying": 1, "Rubick": 3,
  "Disruptor": 2, "Nyx Assassin": 2, "Naga Siren": 2, "Keeper of the Light": 2, "Io": 3, "Visage": 3, "Slark": 2,
  "Medusa": 1, "Troll Warlord": 2, "Centaur Warrunner": 1, "Magnus": 2, "Timbersaw": 2, "Bristleback": 1, "Tusk": 2,
  "Skywrath Mage": 1, "Abaddon": 1, "Elder Titan": 2, "Legion Commander": 1, "Techies": 2, "Ember Spirit": 2,
  "Earth Spirit": 3, "Underlord": 1, "Terrorblade": 2, "Phoenix": 2, "Oracle": 3, "Winter Wyvern": 2, "Arc Warden": 3,
  "Monkey King": 2, "Dark Willow": 2, "Pangolier": 2, "Grimstroke": 2, "Hoodwink": 2, "Void Spirit": 2, "Snapfire": 1,
  "Mars": 1, "Dawnbreaker": 1, "Marci": 2, "Primal Beast": 1, "Muerta": 2, "Ringmaster": 2,
};

const ROLES_TABS = [
  { id: "all", label: "ALL ROLES", pos: "Overall", desc: "Top 10 highest-impact counter picks across any role" },
  { id: "carry", label: "CARRY", pos: "POS 1", desc: "Safe Lane • Gold priority • Late game core" },
  { id: "mid", label: "MIDLANE", pos: "POS 2", desc: "Solo Mid • Fast tempo • Level scaling" },
  { id: "offlane", label: "OFFLANE", pos: "POS 3", desc: "Hard Lane • Frontline tank & teamfight initiator" },
  { id: "soft_support", label: "SOFT SUPPORT", pos: "POS 4", desc: "Roaming • Active ganker, playmaker & disabler" },
  { id: "hard_support", label: "HARD SUPPORT", pos: "POS 5", desc: "Safe Lane • Protector, healer & ward provider" },
];

// Helper to resolve hero image URLs
function getHeroPortraitUrl(hero) {
  if (!hero) return "";
  return `https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/${hero.img}.png`;
}

// ── CSS STYLES (PURE VALVE IN-GAME THEME) ────────────────────────────────────
const CSS = `
:root {
  /* Backgrounds: Deep navy-black with subtle blue haze */
  --bg-base: #070b14;
  --bg-gradient-top: #0a1120;
  --bg-topbar: #0d1522;
  --bg-dock: #080c14;
  --bg-card: #090e18;

  /* Borders & Dividers */
  --border-subtle: rgba(125, 141, 161, 0.16);
  --border-card: rgba(255, 255, 255, 0.08);
  --border-hover: rgba(207, 227, 255, 0.6);
  --glow-hover: rgba(125, 170, 230, 0.35);

  /* Typography */
  --text-primary: #dfe6ee;
  --text-secondary: #7d8da1;
  --text-muted: #4a5a6e;
  --font-display: 'Barlow Condensed', 'Rajdhani', -apple-system, sans-serif;
  --font-body: 'Inter', -apple-system, sans-serif;

  /* Accents */
  --str-red: #d9482b;
  --agi-green: #4fae3a;
  --int-blue: #3a9ad9;
  --uni-purple: #c9a45a;

  --enemy-red: #d9482b;
  --ally-green: #4fae3a;
  --ban-red: #d9482b;
  --gold-accent: #c9a45a;

  /* Primary Action Button (Play Dota) */
  --btn-play-bg: linear-gradient(180deg, #a01820 0%, #7a0f14 100%);
  --btn-play-border: #d9482b;
  --btn-play-topborder: #f87171;
}

*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  background-color: var(--bg-base);
  color: var(--text-primary);
  font-family: var(--font-body);
  overflow-x: hidden;
  min-height: 100vh;
}

/* Custom Scrollbars */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: #05080f;
}
::-webkit-scrollbar-thumb {
  background: #1c2738;
  border-radius: 2px;
}
::-webkit-scrollbar-thumb:hover {
  background: #2b3d58;
}

/* App Container with cinematic soft radial glow */
.dota-app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background:
    radial-gradient(circle at 10% 8%, rgba(28, 51, 80, 0.28) 0%, transparent 45%),
    radial-gradient(circle at 90% 92%, rgba(28, 51, 80, 0.22) 0%, transparent 50%),
    linear-gradient(180deg, var(--bg-gradient-top) 0%, var(--bg-base) 100%);
  position: relative;
}

/* ── 1. TOP BAR ───────────────────────────────────────────────────────────── */
.dota-topbar {
  height: 50px;
  background: var(--bg-topbar);
  border-bottom: 1px solid var(--border-subtle);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
  position: sticky;
  top: 0;
  z-index: 90;
}

/* Dynamic active-mode colored underline */
.dota-topbar::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 1px;
  transition: background 200ms ease;
}
.dota-topbar.mode-enemy::after {
  background: linear-gradient(90deg, transparent, rgba(217, 72, 43, 0.6) 20%, rgba(217, 72, 43, 0.6) 80%, transparent);
}
.dota-topbar.mode-team::after {
  background: linear-gradient(90deg, transparent, rgba(79, 174, 58, 0.6) 20%, rgba(79, 174, 58, 0.6) 80%, transparent);
}
.dota-topbar.mode-bans::after {
  background: linear-gradient(90deg, transparent, rgba(217, 72, 43, 0.5) 20%, rgba(217, 72, 43, 0.5) 80%, transparent);
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.dota-wordmark {
  font-family: var(--font-display);
  font-size: 19px;
  font-weight: 800;
  letter-spacing: 3.5px;
  color: var(--text-primary);
  text-transform: uppercase;
  display: flex;
  align-items: center;
  gap: 8px;
  user-select: none;
}

.dota-pip {
  width: 6px;
  height: 6px;
  background: var(--str-red);
  box-shadow: 0 0 8px var(--str-red);
  border-radius: 1px;
}

/* Mode Tabs */
.topbar-tabs {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-left: 20px;
}

.mode-tab {
  background: transparent;
  border: none;
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 2.2px;
  color: var(--text-secondary);
  text-transform: uppercase;
  cursor: pointer;
  padding: 14px 4px;
  position: relative;
  transition: color 150ms ease;
  outline: none;
}

.mode-tab:hover {
  color: #ffffff;
}

.mode-tab.active {
  color: #ffffff;
}

.mode-tab.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  transition: all 180ms ease;
}

.mode-tab.tab-enemy.active::after {
  background: var(--enemy-red);
  box-shadow: 0 0 8px var(--enemy-red);
}
.mode-tab.tab-team.active::after {
  background: var(--ally-green);
  box-shadow: 0 0 8px var(--ally-green);
}
.mode-tab.tab-bans.active::after {
  background: var(--ban-red);
  box-shadow: 0 0 8px var(--ban-red);
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 14px;
}

/* Outlined Pill Toggles */
.pill-toggle {
  background: transparent;
  border: 1px solid var(--border-subtle);
  border-radius: 2px;
  padding: 5px 12px;
  font-family: var(--font-display);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 1.2px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 150ms ease;
  outline: none;
  display: flex;
  align-items: center;
  gap: 6px;
  user-select: none;
}

.pill-toggle:hover {
  border-color: rgba(207, 227, 255, 0.4);
  color: var(--text-primary);
}

.pill-toggle.active {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(207, 227, 255, 0.7);
  color: #ffffff;
}

.pill-indicator {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--text-muted);
}
.pill-toggle.active .pill-indicator {
  background: #4fae3a;
  box-shadow: 0 0 6px #4fae3a;
}

/* Minimal Underlined Search */
.search-container {
  display: flex;
  align-items: center;
  gap: 6px;
  border-bottom: 1px solid var(--border-subtle);
  padding: 4px 6px;
  transition: border-color 160ms ease;
  width: 170px;
}

.search-container:focus-within {
  border-bottom-color: rgba(207, 227, 255, 0.7);
}

.search-icon {
  font-size: 13px;
  color: var(--text-secondary);
  user-select: none;
}

.search-input {
  background: transparent;
  border: none;
  font-family: var(--font-body);
  font-size: 12px;
  color: var(--text-primary);
  width: 100%;
  outline: none;
}

.search-input::placeholder {
  color: var(--text-muted);
}

/* ── 2. SUBBAR / BANS ROW ─────────────────────────────────────────────────── */
.bans-subbar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding: 10px 28px 4px 28px;
}

.bans-label {
  font-family: var(--font-display);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 2px;
  color: var(--text-secondary);
  text-transform: uppercase;
}

.bans-slots-row {
  display: flex;
  align-items: center;
  gap: 5px;
}

.ban-slot {
  width: 32px;
  height: 32px;
  background: #090e18;
  border: 1px solid var(--border-subtle);
  border-radius: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  transition: border-color 140ms ease;
}

.ban-slot.empty {
  color: rgba(125, 141, 161, 0.35);
  font-size: 13px;
}

.ban-slot.filled {
  cursor: pointer;
  border-color: rgba(217, 72, 43, 0.4);
}

.ban-slot.filled:hover {
  border-color: var(--ban-red);
}

.ban-slot img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center top;
  filter: grayscale(0.8) brightness(0.6);
}

/* Red diagonal slash overlay for bans */
.ban-slash {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: linear-gradient(
    135deg,
    transparent 42%,
    rgba(217, 72, 43, 0.9) 46%,
    rgba(217, 72, 43, 0.9) 54%,
    transparent 58%
  );
}

/* ── 3. MAIN HERO GRID (2x2 ARRANGEMENT) ──────────────────────────────────── */
.dota-main-area {
  flex: 1;
  max-width: 1540px;
  width: 100%;
  margin: 0 auto;
  padding: 8px 32px 140px 32px;
}

.quadrant-grid-2x2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  column-gap: 36px;
  row-gap: 24px;
}

/* Staggered entrance animation (<400ms total) */
@keyframes dotaFadeInUp {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.attr-quadrant {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.attr-quadrant-0 { animation: dotaFadeInUp 260ms ease-out 0ms both; }
.attr-quadrant-1 { animation: dotaFadeInUp 260ms ease-out 50ms both; }
.attr-quadrant-2 { animation: dotaFadeInUp 260ms ease-out 100ms both; }
.attr-quadrant-3 { animation: dotaFadeInUp 260ms ease-out 150ms both; }

@media (prefers-reduced-motion: reduce) {
  .attr-quadrant-0, .attr-quadrant-1, .attr-quadrant-2, .attr-quadrant-3 {
    animation: none !important;
  }
}

/* Section Header: small icon + letter-spaced title in attr colour */
.attr-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-bottom: 2px;
}

.attr-icon-img {
  width: 18px;
  height: 18px;
  object-fit: contain;
}

.attr-title-text {
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 800;
  letter-spacing: 2.5px;
  text-transform: uppercase;
}

/* 11 Cards per row at desktop target */
.attr-cards-grid {
  display: grid;
  grid-template-columns: repeat(11, minmax(0, 1fr));
  gap: 5px;
}

/* ── 4. HERO CARDS (PORTRAIT ~3:5 RATIO) ──────────────────────────────────── */
.hero-card {
  aspect-ratio: 3 / 4.7;
  position: relative;
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: 2px;
  overflow: visible;
  cursor: pointer;
  user-select: none;
  filter: brightness(0.85) saturate(0.9);
  transition: transform 130ms ease, filter 130ms ease, border-color 130ms ease, box-shadow 130ms ease;
}

.hero-card-inner {
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
  border-radius: 1px;
}

.hero-card-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center top;
  display: block;
  pointer-events: none;
}

/* Bottom subtle shadow vignette inside card */
.hero-card-inner::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 25%;
  background: linear-gradient(180deg, transparent 0%, rgba(0, 0, 0, 0.45) 100%);
  pointer-events: none;
}

/* Hover State */
.hero-card:hover {
  filter: brightness(1) saturate(1);
  border-color: var(--border-hover);
  box-shadow: 0 0 10px var(--glow-hover);
  transform: scale(1.05);
  z-index: 30;
}

/* Tooltip on hover (Hero name on hover, no names by default) */
.hero-card .hero-tooltip {
  position: absolute;
  bottom: calc(100% + 6px);
  left: 50%;
  transform: translateX(-50%);
  background: #090e18;
  border: 1px solid var(--border-hover);
  color: #ffffff;
  font-family: var(--font-display);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.8px;
  padding: 4px 8px;
  border-radius: 2px;
  white-space: nowrap;
  pointer-events: none;
  opacity: 0;
  visibility: hidden;
  transition: opacity 120ms ease;
  z-index: 50;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.7);
}

.hero-card:hover .hero-tooltip {
  opacity: 1;
  visibility: visible;
}

/* Search dimming: non-matching heroes dim to ~20% rather than disappearing */
.hero-card.dimmed-by-search {
  opacity: 0.2;
  filter: grayscale(0.8) brightness(0.5);
  pointer-events: none;
}

/* Unavailable: picked or banned when another mode is active */
.hero-card.unavailable {
  filter: brightness(0.35) saturate(0.4);
  cursor: not-allowed;
}

/* Selected States: Readable without colour alone */
/* 1. ENEMY SELECTED: Red border + small red X badge top-right */
.hero-card.selected-enemy {
  border-color: var(--enemy-red);
  filter: brightness(1) saturate(1);
}
.hero-badge-enemy {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 14px;
  height: 14px;
  background: var(--enemy-red);
  color: #ffffff;
  font-size: 9px;
  font-weight: 900;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 1px;
  z-index: 5;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.6);
}

/* 2. ALLY SELECTED: Green border + check badge top-right */
.hero-card.selected-ally {
  border-color: var(--ally-green);
  filter: brightness(1) saturate(1);
}
.hero-badge-ally {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 14px;
  height: 14px;
  background: var(--ally-green);
  color: #ffffff;
  font-size: 10px;
  font-weight: 900;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 1px;
  z-index: 5;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.6);
}

/* 3. BANNED: Grayscale, darkened, with a red diagonal slash */
.hero-card.selected-banned {
  filter: grayscale(1) brightness(0.35);
  border-color: rgba(217, 72, 43, 0.6);
}

/* Roles ON: Small role glyph chips in corner of card, tiny & muted */
.role-glyph-chip {
  position: absolute;
  bottom: 2px;
  left: 2px;
  font-family: var(--font-display);
  font-size: 9px;
  font-weight: 800;
  color: rgba(255, 255, 255, 0.7);
  background: rgba(0, 0, 0, 0.65);
  padding: 1px 3px;
  border-radius: 1px;
  line-height: 1;
  z-index: 4;
}

/* Beginner ON: Small "easy" marker (subtle gold dot/ribbon) */
.beginner-marker {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 6px;
  height: 6px;
  background: var(--gold-accent);
  border-radius: 50%;
  box-shadow: 0 0 5px var(--gold-accent);
  z-index: 4;
}

/* ── 5. DRAFT DOCK (FIXED IN-GAME PARTY BAR REPLACEMENT) ───────────────────── */
.dota-draft-dock {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 74px;
  background: var(--bg-dock);
  border-top: 1px solid var(--border-subtle);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  z-index: 80;
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.5);
}

.dock-left-teams {
  display: flex;
  align-items: center;
  gap: 20px;
}

/* ENEMY Group: 5 slots, red-tinted frame */
.dock-team-group {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 5px 12px;
  border-radius: 2px;
  border: 1px solid var(--border-subtle);
}

.dock-team-group.enemy-frame {
  border-color: rgba(217, 72, 43, 0.28);
  background: rgba(217, 72, 43, 0.04);
}

.dock-team-group.ally-frame {
  border-color: rgba(79, 174, 58, 0.28);
  background: rgba(79, 174, 58, 0.04);
}

.dock-team-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.dock-team-label {
  font-family: var(--font-display);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 1.5px;
  text-transform: uppercase;
}
.dock-team-group.enemy-frame .dock-team-label {
  color: var(--enemy-red);
}
.dock-team-group.ally-frame .dock-team-label {
  color: var(--ally-green);
}

.dock-team-count {
  font-family: var(--font-display);
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
}

.dock-slots-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.dock-slot {
  width: 44px;
  height: 58px;
  background: #060910;
  border: 1px dashed rgba(125, 141, 161, 0.25);
  border-radius: 2px;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 130ms ease;
}

.dock-slot.empty {
  color: var(--text-muted);
  font-family: var(--font-display);
  font-size: 13px;
}

.dock-slot.filled {
  border: 1px solid rgba(255, 255, 255, 0.15);
  cursor: pointer;
}

.dock-slot.filled:hover {
  border-color: #ffffff;
}

.dock-slot img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center top;
}

.dock-slot-remove {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  opacity: 0;
  transition: opacity 120ms ease;
}

.dock-slot.filled:hover .dock-slot-remove {
  opacity: 1;
}

/* Actions Group: Suggest Picks (Play Dota button) & Ghost Clear */
.dock-right-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.btn-ghost-clear {
  background: transparent;
  border: 1px solid var(--border-subtle);
  color: var(--text-secondary);
  font-family: var(--font-display);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 1.5px;
  padding: 10px 16px;
  border-radius: 2px;
  cursor: pointer;
  text-transform: uppercase;
  transition: all 150ms ease;
  outline: none;
}

.btn-ghost-clear:hover {
  border-color: var(--text-primary);
  color: var(--text-primary);
}

.btn-play-dota {
  background: var(--btn-play-bg);
  border: 1px solid var(--btn-play-border);
  border-top: 1px solid var(--btn-play-topborder);
  border-radius: 2px;
  padding: 12px 32px;
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 800;
  letter-spacing: 2.2px;
  color: #ffffff;
  text-transform: uppercase;
  cursor: pointer;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.25), 0 3px 14px rgba(160, 24, 32, 0.45);
  transition: all 150ms ease;
  outline: none;
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-play-dota:hover:not(:disabled) {
  filter: brightness(1.15);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.4), 0 4px 20px rgba(217, 72, 43, 0.6);
  transform: translateY(-1px);
}

.btn-play-dota:disabled {
  opacity: 0.45;
  cursor: not-allowed;
  box-shadow: none;
}

/* ── 6. SUGGESTED PICKS SLIDE-UP PANEL (ABOVE DOCK) ────────────────────────── */
.recs-slideup-panel {
  position: fixed;
  bottom: 74px;
  left: 0;
  right: 0;
  max-height: 72vh;
  background: #090e18;
  border-top: 1px solid rgba(207, 227, 255, 0.25);
  border-bottom: 1px solid var(--border-subtle);
  box-shadow: 0 -8px 30px rgba(0, 0, 0, 0.8);
  z-index: 75;
  display: flex;
  flex-direction: column;
  animation: slideUpPanel 200ms ease-out both;
}

@keyframes slideUpPanel {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.recs-panel-header {
  height: 52px;
  background: #0c1322;
  border-bottom: 1px solid var(--border-subtle);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  flex-shrink: 0;
}

.recs-header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.recs-title {
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 800;
  letter-spacing: 2px;
  color: var(--text-primary);
  text-transform: uppercase;
}

.recs-role-tabs {
  display: flex;
  align-items: center;
  gap: 6px;
}

.recs-role-btn {
  background: transparent;
  border: 1px solid transparent;
  color: var(--text-secondary);
  font-family: var(--font-display);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 1px;
  padding: 4px 10px;
  border-radius: 2px;
  cursor: pointer;
  transition: all 140ms ease;
}

.recs-role-btn:hover {
  color: #ffffff;
}

.recs-role-btn.active {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(207, 227, 255, 0.4);
  color: #ffffff;
}

.btn-close-panel {
  background: transparent;
  border: 1px solid var(--border-subtle);
  color: var(--text-secondary);
  font-size: 13px;
  width: 26px;
  height: 26px;
  border-radius: 2px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 130ms ease;
}

.btn-close-panel:hover {
  border-color: #ffffff;
  color: #ffffff;
}

.recs-scroll-body {
  overflow-y: auto;
  padding: 20px 32px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.recs-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
  gap: 14px;
}

.rec-card {
  background: #0b111e;
  border: 1px solid var(--border-subtle);
  border-radius: 2px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: border-color 140ms ease;
}

.rec-card:hover {
  border-color: rgba(207, 227, 255, 0.45);
}

.rec-card-top {
  display: flex;
  gap: 12px;
  padding: 10px;
  background: rgba(0, 0, 0, 0.25);
  border-bottom: 1px solid rgba(125, 141, 161, 0.08);
}

.rec-thumb {
  width: 50px;
  height: 68px;
  border-radius: 1px;
  object-fit: cover;
  object-position: center top;
  border: 1px solid rgba(255, 255, 255, 0.1);
  flex-shrink: 0;
}

.rec-meta {
  display: flex;
  flex-direction: column;
  gap: 3px;
  flex: 1;
}

.rec-name-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.rec-hero-name {
  font-family: var(--font-display);
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 1px;
  color: #ffffff;
}

.rec-rank-tag {
  font-family: var(--font-display);
  font-size: 11px;
  font-weight: 800;
  color: var(--gold-accent);
}

.rec-badges-row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.rec-advantage-pill {
  font-family: var(--font-display);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.5px;
  color: #4fae3a;
}

.rec-diff-pill {
  font-family: var(--font-display);
  font-size: 10px;
  font-weight: 600;
  padding: 1px 5px;
  border-radius: 1px;
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-secondary);
}

.rec-card-body {
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
}

.rec-verdict-box {
  background: rgba(0, 0, 0, 0.35);
  border-left: 2px solid var(--gold-accent);
  padding: 6px 8px;
  font-size: 11.5px;
  line-height: 1.45;
  color: #cbd5e1;
}

.rec-drawer-toggle {
  background: transparent;
  border: 1px solid var(--border-subtle);
  color: var(--text-secondary);
  padding: 4px 8px;
  font-family: var(--font-display);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.8px;
  cursor: pointer;
  border-radius: 1px;
  margin-top: auto;
  transition: all 130ms ease;
}

.rec-drawer-toggle:hover {
  border-color: var(--text-primary);
  color: var(--text-primary);
}

.rec-drawer-expanded {
  margin-top: 6px;
  padding: 8px;
  background: #070b13;
  border: 1px solid var(--border-subtle);
  border-radius: 1px;
  font-size: 11px;
  line-height: 1.45;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.tip-box {
  background: rgba(79, 174, 58, 0.08);
  border-left: 2px solid var(--ally-green);
  padding: 5px 8px;
  color: #a7f3d0;
}

/* Responsive adjustments */
@media (max-width: 1400px) {
  .attr-cards-grid {
    grid-template-columns: repeat(9, minmax(0, 1fr));
  }
}

@media (max-width: 1024px) {
  .quadrant-grid-2x2 {
    grid-template-columns: 1fr;
  }
  .attr-cards-grid {
    grid-template-columns: repeat(11, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .attr-cards-grid {
    grid-template-columns: repeat(7, minmax(0, 1fr));
  }
  .dota-draft-dock {
    flex-direction: column;
    height: auto;
    padding: 10px;
    gap: 10px;
  }
  .dock-left-teams {
    flex-wrap: wrap;
    justify-content: center;
  }
}
`;

export default function Dota2Drafter() {
  const [heroesList, setHeroesList] = useState(INITIAL_HEROES);
  const [search, setSearch] = useState("");

  // Mode: 'enemy' | 'team' | 'bans'
  const [mode, setMode] = useState("enemy");

  // Selection states
  const [enemy, setEnemy] = useState([]);
  const [team, setTeam] = useState([]);
  const [bans, setBans] = useState([]);

  // Toggles
  const [roleAware, setRoleAware] = useState(true);
  const [beginnerOnly, setBeginnerOnly] = useState(false);

  // Recommendations state
  const [picks, setPicks] = useState(null);
  const [categories, setCategories] = useState(null);
  const [selectedRole, setSelectedRole] = useState("all");
  const [showRecsPanel, setShowRecsPanel] = useState(false);
  const [loading, setLoading] = useState(false);
  const [apiErr, setApiErr] = useState("");
  const [expandedCardIds, setExpandedCardIds] = useState(new Set());

  const searchInputRef = useRef(null);
  const styleInjected = useRef(false);

  // Inject CSS once
  useEffect(() => {
    if (styleInjected.current) return;
    styleInjected.current = true;
    const s = document.createElement("style");
    s.id = "dota2-drafter-ingame-client-css";
    s.textContent = CSS;
    document.head.appendChild(s);
  }, []);

  // Fetch /heroes from backend if available
  useEffect(() => {
    fetch(`${API}/heroes`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          const mapped = data.map((h) => ({
            id: h.id,
            name: h.name,
            img: h.short_name || h.name.toLowerCase().replace(/ /g, "_").replace(/'/g, ""),
            attr:
              h.attribute === "str"
                ? "strength"
                : h.attribute === "agi"
                ? "agility"
                : h.attribute === "int"
                ? "intelligence"
                : "universal",
            roles: h.roles || [],
            image_url: h.image_url,
          }));
          setHeroesList(mapped);
        }
      })
      .catch((e) => console.warn("Failed to load /heroes, using fallback:", e));
  }, []);

  // Keyboard navigation & shortcuts:
  // '/' focuses search
  // 'Esc' clears search or closes recommendations panel
  // '1' switches to enemy mode
  // '2' switches to ally mode
  // '3' switches to ban mode
  useEffect(() => {
    function handleKeyDown(e) {
      // If typing in search, only allow Esc
      if (e.target.tagName === "INPUT") {
        if (e.key === "Escape") {
          setSearch("");
          e.target.blur();
        }
        return;
      }

      if (e.key === "/") {
        e.preventDefault();
        searchInputRef.current?.focus();
      } else if (e.key === "Escape") {
        if (search) setSearch("");
        if (showRecsPanel) setShowRecsPanel(false);
      } else if (e.key === "1") {
        setMode("enemy");
      } else if (e.key === "2") {
        setMode("team");
      } else if (e.key === "3") {
        setMode("bans");
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [search, showRecsPanel]);

  // Lookup map
  const heroById = useMemo(() => {
    const map = new Map();
    heroesList.forEach((h) => map.set(h.id, h));
    return (id) => map.get(id);
  }, [heroesList]);

  // 2x2 Quadrants data grouped by attribute
  const quadrantsData = useMemo(() => {
    const q = { strength: [], agility: [], intelligence: [], universal: [] };
    heroesList.forEach((h) => {
      const a = h.attr || "universal";
      if (q[a]) q[a].push(h);
    });
    return q;
  }, [heroesList]);

  // All selected hero IDs
  const allSelectedIds = useMemo(() => {
    return new Set([...enemy, ...team, ...bans]);
  }, [enemy, team, bans]);

  // Click handler on hero card
  function handleHeroClick(hero) {
    const id = hero.id;

    // Toggle off if already selected in any group
    if (enemy.includes(id)) {
      setEnemy((prev) => prev.filter((x) => x !== id));
      return;
    }
    if (team.includes(id)) {
      setTeam((prev) => prev.filter((x) => x !== id));
      return;
    }
    if (bans.includes(id)) {
      setBans((prev) => prev.filter((x) => x !== id));
      return;
    }

    // Add to active mode
    if (mode === "enemy" && enemy.length < MAX_ENEMY) {
      setEnemy((prev) => [...prev, id]);
    } else if (mode === "team" && team.length < MAX_ALLY) {
      setTeam((prev) => [...prev, id]);
    } else if (mode === "bans" && bans.length < MAX_BANS) {
      setBans((prev) => [...prev, id]);
    }
  }

  function rmEnemy(id) { setEnemy((prev) => prev.filter((x) => x !== id)); }
  function rmTeam(id)  { setTeam((prev) => prev.filter((x) => x !== id)); }
  function rmBan(id)   { setBans((prev) => prev.filter((x) => x !== id)); }

  function clearAll() {
    setEnemy([]);
    setTeam([]);
    setBans([]);
    setPicks(null);
    setCategories(null);
    setShowRecsPanel(false);
    setApiErr("");
  }

  // Suggest picks API call
  async function handleSuggest() {
    if (!enemy.length && !team.length) return;
    setLoading(true);
    setApiErr("");
    setShowRecsPanel(true);

    const targetRoleNeeded =
      selectedRole === "soft_support" || selectedRole === "hard_support"
        ? "support"
        : selectedRole !== "all"
        ? selectedRole
        : null;

    const payload = {
      enemy,
      team,
      bans,
      role_aware: roleAware,
      roles_needed: targetRoleNeeded ? [targetRoleNeeded] : null,
      bracket: "all",
    };

    try {
      const res = await fetch(`${API}/suggest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.message || errJson.detail || `Server error (${res.status})`);
      }

      const data = await res.json();
      setPicks(data.picks || []);
      setCategories(data.categories || null);
      if (data.picks && data.picks.length > 0) {
        setExpandedCardIds(new Set([data.picks[0].id]));
      }
    } catch (e) {
      setApiErr(e.message);
    } finally {
      setLoading(false);
    }
  }

  // Filter recommendations by selected role tab & beginner toggle
  const displayedPicks = useMemo(() => {
    if (!picks && !categories) return [];
    let list = [];
    if (categories && categories[selectedRole]) {
      list = categories[selectedRole];
    } else if (picks) {
      if (selectedRole === "all") {
        list = picks;
      } else {
        list = picks.filter((p) => {
          const rList = (p.roles || []).map((r) => r.toLowerCase());
          if (rList.includes(selectedRole)) return true;
          if (
            (selectedRole === "soft_support" || selectedRole === "hard_support") &&
            rList.includes("support")
          )
            return true;
          return false;
        });
      }
    }

    if (beginnerOnly) {
      list = list.filter((p) => {
        const comp = HERO_COMPLEXITY[p.name] || 2;
        return comp === 1 || (p.difficulty || "Easy") === "Easy";
      });
    }

    return list;
  }, [picks, categories, selectedRole, beginnerOnly]);

  const enemyHeroes = enemy.map(heroById).filter(Boolean);
  const teamHeroes  = team.map(heroById).filter(Boolean);
  const banHeroes   = bans.map(heroById).filter(Boolean);
  const canSuggest  = enemy.length > 0 || team.length > 0;

  // Search filter helper: does this hero match current search?
  function isHeroSearchMatch(hero) {
    if (!search.trim()) return true;
    const s = search.toLowerCase().trim();
    const matchName = hero.name.toLowerCase().includes(s);
    const matchRole = (hero.roles || []).some((r) => r.toLowerCase().includes(s));
    return matchName || matchRole;
  }

  return (
    <div className="dota-app">
      {/* ── 1. TOP BAR ────────────────────────────────────────────────────── */}
      <header className={`dota-topbar mode-${mode}`}>
        <div className="topbar-left">
          <div className="dota-wordmark">
            <span className="dota-pip" />
            DRAFTER
          </div>

          <nav className="topbar-tabs">
            <button
              className={`mode-tab tab-enemy${mode === "enemy" ? " active" : ""}`}
              onClick={() => setMode("enemy")}
              title="Shortcut: 1"
            >
              ENEMY ({enemy.length}/{MAX_ENEMY})
            </button>
            <button
              className={`mode-tab tab-team${mode === "team" ? " active" : ""}`}
              onClick={() => setMode("team")}
              title="Shortcut: 2"
            >
              ALLY ({team.length}/{MAX_ALLY})
            </button>
            <button
              className={`mode-tab tab-bans${mode === "bans" ? " active" : ""}`}
              onClick={() => setMode("bans")}
              title="Shortcut: 3"
            >
              BAN ({bans.length}/{MAX_BANS})
            </button>
          </nav>
        </div>

        <div className="topbar-right">
          {/* Roles Toggle */}
          <button
            className={`pill-toggle${roleAware ? " active" : ""}`}
            onClick={() => setRoleAware((r) => !r)}
            title="Auto-fill missing team positions"
          >
            <span className="pill-indicator" />
            ROLES {roleAware ? "ON" : "OFF"}
          </button>

          {/* Beginner Toggle */}
          <button
            className={`pill-toggle${beginnerOnly ? " active" : ""}`}
            onClick={() => setBeginnerOnly((b) => !b)}
            title="Highlight beginner-friendly heroes"
          >
            <span className="pill-indicator" />
            BEGINNER {beginnerOnly ? "ON" : "OFF"}
          </button>

          {/* Minimal Underlined Search */}
          <div className="search-container">
            <span className="search-icon">⌕</span>
            <input
              ref={searchInputRef}
              className="search-input"
              type="text"
              placeholder="Search hero... (/)"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>
      </header>

      {/* ── 2. BANS ROW (RIGHT-ALIGNED UNDER TOP BAR) ─────────────────────── */}
      <div className="bans-subbar">
        <span className="bans-label">BANS</span>
        <div className="bans-slots-row">
          {Array.from({ length: MAX_BANS }).map((_, i) => {
            const h = banHeroes[i];
            return h ? (
              <div
                key={h.id}
                className="ban-slot filled"
                onClick={() => rmBan(h.id)}
                title={`Banned: ${h.name} (Click to remove)`}
              >
                <img
                  src={getHeroPortraitUrl(h)}
                  alt={h.name}
                  onError={(e) => {
                    e.target.src = h.image_url || `https://cdn.cloudflare.steamstatic.com/apps/dota2/images/heroes/${h.img}_full.png`;
                  }}
                />
                <div className="ban-slash" />
              </div>
            ) : (
              <div key={i} className="ban-slot empty" title="Empty Ban Slot">
                ⊘
              </div>
            );
          })}
        </div>
      </div>

      {/* ── 3. MAIN HERO GRID (2x2 ARRANGEMENT) ───────────────────────────── */}
      <main className="dota-main-area">
        <div className="quadrant-grid-2x2">
          {ATTR_ORDER.map((attr, qIdx) => {
            const heroes = quadrantsData[attr] || [];
            const meta = HERO_ATTRIBUTES_META[attr];
            return (
              <section className={`attr-quadrant attr-quadrant-${qIdx}`} key={attr}>
                <div className="attr-header">
                  <img className="attr-icon-img" src={meta.icon} alt={meta.title} />
                  <span className="attr-title-text" style={{ color: meta.color }}>
                    {meta.title}
                  </span>
                </div>

                <div className="attr-cards-grid">
                  {heroes.map((hero) => {
                    const isEnemy = enemy.includes(hero.id);
                    const isAlly  = team.includes(hero.id);
                    const isBanned = bans.includes(hero.id);
                    const isAnySelected = allSelectedIds.has(hero.id);

                    // Unavailable if selected in another mode
                    const isUnavailable =
                      isAnySelected &&
                      ((mode === "enemy" && !isEnemy) ||
                       (mode === "team"  && !isAlly)  ||
                       (mode === "bans"  && !isBanned));

                    const matchesSearch = isHeroSearchMatch(hero);
                    const posNum = HERO_PRIMARY_POS[hero.name] || 1;
                    const isBeginner = (HERO_COMPLEXITY[hero.name] || 2) === 1;

                    const cardClasses = [
                      "hero-card",
                      !matchesSearch ? "dimmed-by-search" : "",
                      isUnavailable ? "unavailable" : "",
                      isEnemy ? "selected-enemy" : "",
                      isAlly ? "selected-ally" : "",
                      isBanned ? "selected-banned" : "",
                    ].filter(Boolean).join(" ");

                    return (
                      <div
                        key={hero.id}
                        className={cardClasses}
                        onClick={() => handleHeroClick(hero)}
                      >
                        <div className="hero-card-inner">
                          <img
                            className="hero-card-img"
                            src={getHeroPortraitUrl(hero)}
                            alt={hero.name}
                            loading="lazy"
                            onError={(e) => {
                              if (!e.target.dataset.triedVert) {
                                e.target.dataset.triedVert = "true";
                                e.target.src = `https://cdn.cloudflare.steamstatic.com/apps/dota2/images/heroes/${hero.img}_vert.jpg`;
                              } else if (!e.target.dataset.triedFallback) {
                                e.target.dataset.triedFallback = "true";
                                e.target.src = hero.image_url || `https://cdn.cloudflare.steamstatic.com/apps/dota2/images/heroes/${hero.img}_full.png`;
                              }
                            }}
                          />

                          {/* Banned Red Slash Overlay */}
                          {isBanned && <div className="ban-slash" />}

                          {/* Enemy Badge: Red X top-right */}
                          {isEnemy && <div className="hero-badge-enemy">✕</div>}

                          {/* Ally Badge: Green Check top-right */}
                          {isAlly && <div className="hero-badge-ally">✓</div>}

                          {/* Roles ON: Small role glyph chip bottom-left */}
                          {roleAware && (
                            <div className="role-glyph-chip" title={`Pos ${posNum}`}>
                              {posNum}
                            </div>
                          )}

                          {/* Beginner ON: Gold dot marker top-left */}
                          {beginnerOnly && isBeginner && (
                            <div className="beginner-marker" title="Beginner Friendly" />
                          )}
                        </div>

                        {/* Hover Tooltip (Hero name on hover, no text on card by default) */}
                        <div className="hero-tooltip">
                          {hero.name}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </section>
            );
          })}
        </div>
      </main>

      {/* ── 4. SUGGESTED PICKS SLIDE-UP PANEL (ABOVE DOCK) ────────────────── */}
      {showRecsPanel && (
        <section className="recs-slideup-panel">
          <div className="recs-panel-header">
            <div className="recs-header-left">
              <span className="recs-title">TACTICAL COUNTER PICKS</span>

              <div className="recs-role-tabs">
                {ROLES_TABS.map((tab) => (
                  <button
                    key={tab.id}
                    className={`recs-role-btn${selectedRole === tab.id ? " active" : ""}`}
                    onClick={() => setSelectedRole(tab.id)}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>

            <button
              className="btn-close-panel"
              onClick={() => setShowRecsPanel(false)}
              title="Close panel (Esc)"
            >
              ✕
            </button>
          </div>

          <div className="recs-scroll-body">
            {apiErr && (
              <div style={{ color: "var(--str-red)", fontSize: "12px" }}>
                Error loading suggestions: {apiErr}
              </div>
            )}

            {loading ? (
              <div style={{ color: "var(--text-secondary)", fontSize: "13px", padding: "16px 0" }}>
                ⟳ Analyzing matchroom draft against 50,000+ ranked matches...
              </div>
            ) : displayedPicks.length === 0 ? (
              <div style={{ color: "var(--text-muted)", fontSize: "12px", padding: "12px 0" }}>
                No recommendations found for this role category.
              </div>
            ) : (
              <div className="recs-cards-grid">
                {displayedPicks.slice(0, 10).map((pick, idx) => {
                  const hData = heroById(pick.id) || pick;
                  const isExpanded = expandedCardIds.has(pick.id);
                  const isEasy = (HERO_COMPLEXITY[pick.name] || 2) === 1;

                  return (
                    <article className="rec-card" key={pick.id || idx}>
                      <div className="rec-card-top">
                        <img
                          className="rec-thumb"
                          src={getHeroPortraitUrl(hData)}
                          alt={pick.name}
                          onError={(e) => {
                            e.target.src = hData.image_url || `https://cdn.cloudflare.steamstatic.com/apps/dota2/images/heroes/${hData.img}_full.png`;
                          }}
                        />

                        <div className="rec-meta">
                          <div className="rec-name-row">
                            <span className="rec-hero-name">{pick.name}</span>
                            <span className="rec-rank-tag">#{idx + 1}</span>
                          </div>

                          <div className="rec-badges-row">
                            <span className="rec-advantage-pill">
                              +{Math.abs(pick.score || 12.4).toFixed(1)}% Adv
                            </span>
                            <span className="rec-diff-pill">
                              {isEasy ? "★ Beginner" : "Moderate"}
                            </span>
                          </div>

                          {pick.credible_interval && (
                            <div className="rec-uncertainty-row" style={{ display: 'flex', gap: '6px', alignItems: 'center', fontSize: '11px', color: 'var(--text-secondary, #7d8da1)', marginTop: '4px' }}>
                              <span title="95% Posterior Credible Interval on Win Probability" style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '1px 5px', borderRadius: '3px', border: '1px solid rgba(255,255,255,0.1)' }}>
                                95% CI: {(pick.credible_interval[0] * 100).toFixed(1)}% – {(pick.credible_interval[1] * 100).toFixed(1)}%
                              </span>
                              {pick.effective_sample_size && (
                                <span title="Sample size in 1.4M dataset" style={{ color: 'var(--text-muted, #5a6878)' }}>
                                  ({pick.effective_sample_size.toLocaleString()} games)
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                      </div>

                      <div className="rec-card-body">
                        {pick.one_liner && (
                          <div className="rec-verdict-box" style={{ marginBottom: '6px' }}>
                            {pick.one_liner}
                          </div>
                        )}
                        {pick.verdict && !pick.one_liner && (
                          <div className="rec-verdict-box">
                            {pick.verdict}
                          </div>
                        )}

                        {((pick.top_positive_pairings && pick.top_positive_pairings.length > 0) ||
                          (pick.top_negative_pairings && pick.top_negative_pairings.length > 0)) && (
                          <div className="rec-pairings-box" style={{ fontSize: '11px', background: 'rgba(0, 0, 0, 0.25)', padding: '6px 8px', borderRadius: '4px', marginBottom: '8px', borderLeft: '2px solid var(--accent-blue, #3a9ad9)' }}>
                            {pick.top_positive_pairings && pick.top_positive_pairings.map((p, pIdx) => (
                              <div key={`pos-${pIdx}`} style={{ color: '#4fae3a', marginBottom: '2px' }}>
                                ▲ {p.text}
                              </div>
                            ))}
                            {pick.top_negative_pairings && pick.top_negative_pairings.map((p, pIdx) => (
                              <div key={`neg-${pIdx}`} style={{ color: '#d9482b' }}>
                                ▼ {p.text}
                              </div>
                            ))}
                          </div>
                        )}

                        <button
                          className="rec-drawer-toggle"
                          onClick={() => {
                            setExpandedCardIds((prev) => {
                              const next = new Set(prev);
                              if (next.has(pick.id)) next.delete(pick.id);
                              else next.add(pick.id);
                              return next;
                            });
                          }}
                        >
                          {isExpanded ? "▲ Hide Guide" : "▼ Ability & Lane Guide"}
                        </button>

                        {isExpanded && (
                          <div className="rec-drawer-expanded">
                            {pick.matchup_mechanics && (
                              <div><strong>Matchup:</strong> {pick.matchup_mechanics}</div>
                            )}
                            {pick.key_spells && pick.key_spells.length > 0 && (
                              <div><strong>Key Spells:</strong> {pick.key_spells.join(", ")}</div>
                            )}
                            {pick.beginner_tip && (
                              <div className="tip-box">
                                <strong>Tip:</strong> {pick.beginner_tip}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </article>
                  );
                })}
              </div>
            )}
          </div>
        </section>
      )}

      {/* ── 5. DRAFT DOCK (FIXED IN-GAME PARTY BAR REPLACEMENT) ────────────── */}
      <footer className="dota-draft-dock">
        <div className="dock-left-teams">
          {/* ENEMY GROUP (5 SLOTS, RED FRAME) */}
          <div className="dock-team-group enemy-frame">
            <div className="dock-team-meta">
              <span className="dock-team-label">ENEMY</span>
              <span className="dock-team-count">{enemy.length}/{MAX_ENEMY}</span>
            </div>

            <div className="dock-slots-row">
              {Array.from({ length: MAX_ENEMY }).map((_, i) => {
                const h = enemyHeroes[i];
                return h ? (
                  <div
                    key={h.id}
                    className="dock-slot filled"
                    onClick={() => rmEnemy(h.id)}
                    title={`${h.name} (Click to remove)`}
                  >
                    <img
                      src={getHeroPortraitUrl(h)}
                      alt={h.name}
                      onError={(e) => {
                        e.target.src = h.image_url || `https://cdn.cloudflare.steamstatic.com/apps/dota2/images/heroes/${h.img}_full.png`;
                      }}
                    />
                    <div className="dock-slot-remove">✕</div>
                  </div>
                ) : (
                  <div key={i} className="dock-slot empty" title="Empty Enemy Slot">
                    {i + 1}
                  </div>
                );
              })}
            </div>
          </div>

          {/* ALLIES GROUP (4 SLOTS, GREEN FRAME) */}
          <div className="dock-team-group ally-frame">
            <div className="dock-team-meta">
              <span className="dock-team-label">ALLIES</span>
              <span className="dock-team-count">{team.length}/{MAX_ALLY}</span>
            </div>

            <div className="dock-slots-row">
              {Array.from({ length: MAX_ALLY }).map((_, i) => {
                const h = teamHeroes[i];
                return h ? (
                  <div
                    key={h.id}
                    className="dock-slot filled"
                    onClick={() => rmTeam(h.id)}
                    title={`${h.name} (Click to remove)`}
                  >
                    <img
                      src={getHeroPortraitUrl(h)}
                      alt={h.name}
                      onError={(e) => {
                        e.target.src = h.image_url || `https://cdn.cloudflare.steamstatic.com/apps/dota2/images/heroes/${h.img}_full.png`;
                      }}
                    />
                    <div className="dock-slot-remove">✕</div>
                  </div>
                ) : (
                  <div key={i} className="dock-slot empty" title="Empty Ally Slot">
                    +
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* ACTIONS GROUP (PLAY DOTA RED BUTTON & CLEAR) */}
        <div className="dock-right-actions">
          <button className="btn-ghost-clear" onClick={clearAll} title="Clear all draft slots">
            ↺ CLEAR
          </button>

          <button
            className="btn-play-dota"
            onClick={handleSuggest}
            disabled={!canSuggest || loading}
          >
            {loading ? "⟳ ANALYZING…" : "SUGGEST PICKS"}
          </button>
        </div>
      </footer>
    </div>
  );
}
