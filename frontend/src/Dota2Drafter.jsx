import { useState, useMemo, useEffect, useRef } from "react";

// ── Hero roster (name must match hero_map.pkl exactly) ───────────────────────
const HEROES = [
  // AGILITY
  { id:1,   name:"Anti-Mage",          img:"antimage",            attr:"agility" },
  { id:2,   name:"Arc Warden",          img:"arc_warden",          attr:"agility" },
  { id:3,   name:"Bloodseeker",         img:"bloodseeker",         attr:"agility" },
  { id:4,   name:"Bounty Hunter",       img:"bounty_hunter",       attr:"agility" },
  { id:5,   name:"Clinkz",              img:"clinkz",              attr:"agility" },
  { id:6,   name:"Drow Ranger",         img:"drow_ranger",         attr:"agility" },
  { id:7,   name:"Ember Spirit",        img:"ember_spirit",        attr:"agility" },
  { id:8,   name:"Faceless Void",       img:"faceless_void",       attr:"agility" },
  { id:9,   name:"Gyrocopter",          img:"gyrocopter",          attr:"agility" },
  { id:10,  name:"Hoodwink",            img:"hoodwink",            attr:"agility" },
  { id:11,  name:"Juggernaut",          img:"juggernaut",          attr:"agility" },
  { id:12,  name:"Luna",                img:"luna",                attr:"agility" },
  { id:13,  name:"Medusa",              img:"medusa",              attr:"agility" },
  { id:14,  name:"Meepo",               img:"meepo",               attr:"agility" },
  { id:15,  name:"Monkey King",         img:"monkey_king",         attr:"agility" },
  { id:16,  name:"Morphling",           img:"morphling",           attr:"agility" },
  { id:17,  name:"Naga Siren",          img:"naga_siren",          attr:"agility" },
  { id:18,  name:"Phantom Assassin",    img:"phantom_assassin",    attr:"agility" },
  { id:19,  name:"Phantom Lancer",      img:"phantom_lancer",      attr:"agility" },
  { id:20,  name:"Razor",               img:"razor",               attr:"agility" },
  { id:21,  name:"Riki",                img:"riki",                attr:"agility" },
  { id:22,  name:"Shadow Fiend",        img:"nevermore",           attr:"agility" },
  { id:23,  name:"Slark",               img:"slark",               attr:"agility" },
  { id:24,  name:"Sniper",              img:"sniper",              attr:"agility" },
  { id:25,  name:"Spectre",             img:"spectre",             attr:"agility" },
  { id:26,  name:"Templar Assassin",    img:"templar_assassin",    attr:"agility" },
  { id:27,  name:"Terrorblade",         img:"terrorblade",         attr:"agility" },
  { id:28,  name:"Troll Warlord",       img:"troll_warlord",       attr:"agility" },
  { id:29,  name:"Ursa",                img:"ursa",                attr:"agility" },
  { id:30,  name:"Viper",               img:"viper",               attr:"agility" },
  { id:31,  name:"Weaver",              img:"weaver",              attr:"agility" },
  // STRENGTH
  { id:32,  name:"Alchemist",           img:"alchemist",           attr:"strength" },
  { id:33,  name:"Axe",                 img:"axe",                 attr:"strength" },
  { id:34,  name:"Bristleback",         img:"bristleback",         attr:"strength" },
  { id:35,  name:"Centaur Warrunner",   img:"centaur",             attr:"strength" },
  { id:36,  name:"Chaos Knight",        img:"chaos_knight",        attr:"strength" },
  { id:37,  name:"Dawnbreaker",         img:"dawnbreaker",         attr:"strength" },
  { id:38,  name:"Doom",                img:"doom_bringer",        attr:"strength" },
  { id:39,  name:"Dragon Knight",       img:"dragon_knight",       attr:"strength" },
  { id:40,  name:"Earth Spirit",        img:"earth_spirit",        attr:"strength" },
  { id:41,  name:"Earthshaker",         img:"earthshaker",         attr:"strength" },
  { id:42,  name:"Elder Titan",         img:"elder_titan",         attr:"strength" },
  { id:43,  name:"Huskar",              img:"huskar",              attr:"strength" },
  { id:44,  name:"Kunkka",              img:"kunkka",              attr:"strength" },
  { id:45,  name:"Legion Commander",    img:"legion_commander",    attr:"strength" },
  { id:46,  name:"Lifestealer",         img:"life_stealer",        attr:"strength" },
  { id:47,  name:"Mars",                img:"mars",                attr:"strength" },
  { id:48,  name:"Night Stalker",       img:"night_stalker",       attr:"strength" },
  { id:49,  name:"Ogre Magi",           img:"ogre_magi",           attr:"strength" },
  { id:50,  name:"Omniknight",          img:"omniknight",          attr:"strength" },
  { id:51,  name:"Primal Beast",        img:"primal_beast",        attr:"strength" },
  { id:52,  name:"Pudge",               img:"pudge",               attr:"strength" },
  { id:53,  name:"Slardar",             img:"slardar",             attr:"strength" },
  { id:54,  name:"Sven",                img:"sven",                attr:"strength" },
  { id:55,  name:"Tidehunter",          img:"tidehunter",          attr:"strength" },
  { id:56,  name:"Timbersaw",           img:"shredder",            attr:"strength" },
  { id:57,  name:"Tiny",                img:"tiny",                attr:"strength" },
  { id:58,  name:"Underlord",           img:"abyssal_underlord",   attr:"strength" },
  { id:59,  name:"Undying",             img:"undying",             attr:"strength" },
  { id:60,  name:"Wraith King",         img:"skeleton_king",       attr:"strength" },
  // INTELLIGENCE
  { id:61,  name:"Ancient Apparition",  img:"ancient_apparition",  attr:"intelligence" },
  { id:62,  name:"Crystal Maiden",      img:"crystal_maiden",      attr:"intelligence" },
  { id:63,  name:"Death Prophet",       img:"death_prophet",       attr:"intelligence" },
  { id:64,  name:"Disruptor",           img:"disruptor",           attr:"intelligence" },
  { id:65,  name:"Enchantress",         img:"enchantress",         attr:"intelligence" },
  { id:66,  name:"Grimstroke",          img:"grimstroke",          attr:"intelligence" },
  { id:67,  name:"Jakiro",              img:"jakiro",              attr:"intelligence" },
  { id:68,  name:"Keeper of the Light", img:"keeper_of_the_light", attr:"intelligence" },
  { id:69,  name:"Leshrac",             img:"leshrac",             attr:"intelligence" },
  { id:70,  name:"Lich",                img:"lich",                attr:"intelligence" },
  { id:71,  name:"Lina",                img:"lina",                attr:"intelligence" },
  { id:72,  name:"Lion",                img:"lion",                attr:"intelligence" },
  { id:73,  name:"Muerta",              img:"muerta",              attr:"intelligence" },
  { id:74,  name:"Nature's Prophet",    img:"furion",              attr:"intelligence" },
  { id:75,  name:"Necrophos",           img:"necrolyte",           attr:"intelligence" },
  { id:76,  name:"Oracle",              img:"oracle",              attr:"intelligence" },
  { id:77,  name:"Outworld Destroyer",  img:"obsidian_destroyer",  attr:"intelligence" },
  { id:78,  name:"Puck",                img:"puck",                attr:"intelligence" },
  { id:79,  name:"Pugna",               img:"pugna",               attr:"intelligence" },
  { id:80,  name:"Queen of Pain",       img:"queenofpain",         attr:"intelligence" },
  { id:81,  name:"Rubick",              img:"rubick",              attr:"intelligence" },
  { id:82,  name:"Shadow Demon",        img:"shadow_demon",        attr:"intelligence" },
  { id:83,  name:"Shadow Shaman",       img:"shadow_shaman",       attr:"intelligence" },
  { id:84,  name:"Silencer",            img:"silencer",            attr:"intelligence" },
  { id:85,  name:"Skywrath Mage",       img:"skywrath_mage",       attr:"intelligence" },
  { id:86,  name:"Techies",             img:"techies",             attr:"intelligence" },
  { id:87,  name:"Tinker",              img:"tinker",              attr:"intelligence" },
  { id:88,  name:"Treant Protector",    img:"treant",              attr:"intelligence" },
  { id:89,  name:"Vengeful Spirit",     img:"vengefulspirit",      attr:"intelligence" },
  { id:90,  name:"Visage",              img:"visage",              attr:"intelligence" },
  { id:91,  name:"Warlock",             img:"warlock",             attr:"intelligence" },
  { id:92,  name:"Winter Wyvern",       img:"winter_wyvern",       attr:"intelligence" },
  { id:93,  name:"Witch Doctor",        img:"witch_doctor",        attr:"intelligence" },
  { id:94,  name:"Zeus",                img:"zuus",                attr:"intelligence" },
  // UNIVERSAL
  { id:95,  name:"Abaddon",             img:"abaddon",             attr:"universal" },
  { id:96,  name:"Bane",                img:"bane",                attr:"universal" },
  { id:97,  name:"Batrider",            img:"batrider",            attr:"universal" },
  { id:98,  name:"Beastmaster",         img:"beastmaster",         attr:"universal" },
  { id:99,  name:"Brewmaster",          img:"brewmaster",          attr:"universal" },
  { id:100, name:"Broodmother",         img:"broodmother",         attr:"universal" },
  { id:101, name:"Chen",                img:"chen",                attr:"universal" },
  { id:102, name:"Clockwerk",           img:"rattletrap",          attr:"universal" },
  { id:103, name:"Dark Seer",           img:"dark_seer",           attr:"universal" },
  { id:104, name:"Dark Willow",         img:"dark_willow",         attr:"universal" },
  { id:105, name:"Dazzle",              img:"dazzle",              attr:"universal" },
  { id:106, name:"Enigma",              img:"enigma",              attr:"universal" },
  { id:107, name:"Invoker",             img:"invoker",             attr:"universal" },
  { id:108, name:"Io",                  img:"wisp",                attr:"universal" },
  { id:109, name:"Lone Druid",          img:"lone_druid",          attr:"universal" },
  { id:110, name:"Lycan",               img:"lycan",               attr:"universal" },
  { id:111, name:"Magnus",              img:"magnataur",           attr:"universal" },
  { id:112, name:"Marci",               img:"marci",               attr:"universal" },
  { id:113, name:"Mirana",              img:"mirana",              attr:"universal" },
  { id:114, name:"Nyx Assassin",        img:"nyx_assassin",        attr:"universal" },
  { id:115, name:"Pangolier",           img:"pangolier",           attr:"universal" },
  { id:116, name:"Phoenix",             img:"phoenix",             attr:"universal" },
  { id:117, name:"Sand King",           img:"sand_king",           attr:"universal" },
  { id:118, name:"Spirit Breaker",      img:"spirit_breaker",      attr:"universal" },
  { id:119, name:"Storm Spirit",        img:"storm_spirit",        attr:"universal" },
  { id:120, name:"Venomancer",          img:"venomancer",          attr:"universal" },
  { id:121, name:"Windranger",          img:"windrunner",          attr:"universal" },
];

const IMG = img =>
  `https://cdn.cloudflare.steamstatic.com/apps/dota2/images/heroes/${img}_full.png`;

const ATTR_META = {
  agility:      { color:"#4bc87a", icon:"⚡" },
  strength:     { color:"#c84b4b", icon:"🛡"  },
  intelligence: { color:"#5b9bd5", icon:"✦"   },
  universal:    { color:"#c8a84b", icon:"◈"   },
};

const ROLE_COLORS = {
  carry:   "#c8a84b",
  mid:     "#5b9bd5",
  offlane: "#c84b4b",
  support: "#4bc87a",
};

const ATTR_ORDER = ["agility","strength","intelligence","universal"];
const MAX_PICKS  = 5;
const API = import.meta.env.VITE_API_URL || "/api";

const NAME_TO_IMG = {};
HEROES.forEach(h => { NAME_TO_IMG[h.name] = h.img; });

// ── CSS ───────────────────────────────────────────────────────────────────────
const CSS = `
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700;900&family=Rajdhani:wght@400;600;700&display=swap');

*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}

:root{
  --bg:#06080d;--panel:#0b0f16;--border:#1a2436;
  --gold:#c8a84b;--gold-dim:#7a6228;
  --red:#c84b4b;--green:#4bc87a;--blue:#3a8fd4;
  --text:#d4c5a0;--dim:#4a5568;
}

body{background:var(--bg);color:var(--text);overflow-x:hidden}

.app{
  font-family:'Rajdhani',sans-serif;
  min-height:100vh;
  display:grid;
  grid-template-rows:56px 1fr auto;
  grid-template-columns:1fr 280px;
  grid-template-areas:"hdr hdr" "grid panel" "results results";
  background:
    radial-gradient(ellipse 60% 40% at 15% 5%,rgba(58,143,212,.06) 0,transparent 100%),
    radial-gradient(ellipse 50% 30% at 85% 95%,rgba(200,168,75,.05) 0,transparent 100%),
    var(--bg);
}

/* ── HEADER ── */
.hdr{
  grid-area:hdr;
  display:flex;align-items:center;gap:12px;
  padding:0 20px;
  border-bottom:1px solid var(--border);
  background:rgba(6,8,13,.97);
  position:sticky;top:0;z-index:100;
}
.logo{
  font-family:'Cinzel',serif;font-size:18px;font-weight:900;
  letter-spacing:4px;color:var(--gold);
  text-shadow:0 0 18px rgba(200,168,75,.4);
  white-space:nowrap;margin-right:4px;
}
.logo span{color:#fff}
.search-wrap{position:relative;flex:1;max-width:260px}
.search{
  width:100%;background:rgba(255,255,255,.04);
  border:1px solid var(--border);border-radius:2px;
  padding:6px 12px 6px 30px;color:var(--text);
  font-family:'Rajdhani',sans-serif;font-size:13px;font-weight:600;
  letter-spacing:.8px;outline:none;transition:border-color .18s;
}
.search:focus{border-color:var(--gold-dim)}
.search::placeholder{color:var(--dim)}
.search-ico{position:absolute;left:9px;top:50%;transform:translateY(-50%);color:var(--dim);font-size:13px;pointer-events:none}

.hdr-btns{display:flex;gap:6px;margin-left:auto}
.btn{
  font-family:'Rajdhani',sans-serif;font-size:11px;font-weight:700;
  letter-spacing:2px;text-transform:uppercase;
  padding:6px 14px;border:1px solid;border-radius:2px;
  cursor:pointer;background:transparent;transition:all .18s;
  white-space:nowrap;
}
.btn-enemy{color:var(--red);border-color:var(--red)}
.btn-enemy.on{background:rgba(200,75,75,.18);box-shadow:0 0 12px rgba(200,75,75,.35)}
.btn-ally{color:var(--green);border-color:var(--green)}
.btn-ally.on{background:rgba(75,200,122,.14);box-shadow:0 0 12px rgba(75,200,122,.28)}
.btn-suggest{
  color:#fff;border-color:var(--gold);
  background:linear-gradient(135deg,rgba(200,168,75,.22),rgba(200,168,75,.06));
  box-shadow:0 0 10px rgba(200,168,75,.18);
}
.btn-suggest:hover:not(:disabled){background:linear-gradient(135deg,rgba(200,168,75,.38),rgba(200,168,75,.14));box-shadow:0 0 20px rgba(200,168,75,.42)}
.btn-suggest:disabled{opacity:.38;cursor:not-allowed}
.btn-suggest.spinning{animation:pulse-g .9s infinite}
@keyframes pulse-g{0%,100%{box-shadow:0 0 10px rgba(200,168,75,.18)}50%{box-shadow:0 0 24px rgba(200,168,75,.55)}}
.btn-clear{color:var(--gold);border-color:var(--gold-dim)}
.btn-clear:hover{border-color:var(--gold)}

/* ── GRID ── */
.grid-area{
  grid-area:grid;
  padding:16px 18px;
  overflow-y:auto;
}
.attr-sec{margin-bottom:18px}
.attr-lbl{
  font-family:'Cinzel',serif;font-size:9px;letter-spacing:3px;font-weight:700;
  margin-bottom:8px;display:flex;align-items:center;gap:6px;text-transform:uppercase;
}
.attr-line{flex:1;height:1px;opacity:.2}

.hero-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(78px,1fr));gap:6px}

.hcard{
  position:relative;cursor:pointer;border-radius:3px;overflow:hidden;
  border:1px solid transparent;
  transition:transform .13s,box-shadow .13s,border-color .13s;
  aspect-ratio:16/9;background:#0b0f16;
}
.hcard:hover{transform:translateY(-2px) scale(1.05);z-index:3}
.hcard img{width:100%;height:100%;object-fit:cover;display:block;transition:filter .18s}
.hcard.gray img{filter:grayscale(1) brightness(.25)}
.hcard.enemy{border-color:var(--red);box-shadow:0 0 8px rgba(200,75,75,.5)}
.hcard.ally{border-color:var(--green);box-shadow:0 0 8px rgba(75,200,122,.5)}
.hname{
  position:absolute;bottom:0;left:0;right:0;
  background:linear-gradient(transparent,rgba(0,0,0,.88));
  padding:8px 3px 2px;font-size:9px;font-weight:700;
  letter-spacing:.3px;text-align:center;color:#e0d5bf;line-height:1.2;
}
.hcard.gray .hname{color:#222}
.hbadge{
  position:absolute;top:2px;right:2px;width:14px;height:14px;
  border-radius:50%;display:flex;align-items:center;justify-content:center;
  font-size:7px;font-weight:900;z-index:4;
}
.hbadge.e{background:var(--red);color:#fff}
.hbadge.a{background:var(--green);color:#000}

/* ── PANEL ── */
.panel{
  grid-area:panel;
  border-left:1px solid var(--border);
  background:rgba(11,15,22,.97);
  display:flex;flex-direction:column;
  padding:14px 12px;overflow-y:auto;gap:0;
}
.ptitle{
  font-family:'Cinzel',serif;font-size:9px;letter-spacing:3px;font-weight:700;
  padding-bottom:6px;border-bottom:1px solid;
  display:flex;align-items:center;gap:6px;margin-bottom:4px;
}
.ptitle.e{color:var(--red);border-color:rgba(200,75,75,.3)}
.ptitle.a{color:var(--green);border-color:rgba(75,200,122,.3)}
.pcount{font-size:9px;color:var(--dim);letter-spacing:1px;font-weight:600;margin-bottom:4px}
.psec{display:flex;flex-direction:column;gap:5px;margin-bottom:14px}

/* ── SLOT ── */
.slot{
  display:flex;align-items:center;gap:7px;
  padding:4px 5px;border-radius:2px;
  border:1px solid var(--border);background:rgba(255,255,255,.02);
  min-height:38px;position:relative;
}
.slot.fe{border-color:rgba(200,75,75,.38)}
.slot.fa{border-color:rgba(75,200,122,.3)}
.slot img{width:42px;height:24px;object-fit:cover;border-radius:2px;flex-shrink:0}
.slot-info{flex:1;min-width:0}
.slot-name{font-size:11px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.slot-attr{font-size:8px;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-top:1px}
.slot-empty{font-size:9px;color:var(--dim);letter-spacing:1px;font-style:italic}
/* FIX: remove button is now a proper clickable element with enough padding */
.slot-rm{
  flex-shrink:0;
  width:22px;height:22px;
  display:flex;align-items:center;justify-content:center;
  background:rgba(255,255,255,.06);
  border:1px solid rgba(255,255,255,.1);
  border-radius:3px;cursor:pointer;
  color:var(--dim);font-size:12px;
  transition:color .14s,background .14s;
  /* Important: must not have pointer-events:none */
  pointer-events:all;
  user-select:none;
}
.slot-rm:hover{color:#fff;background:rgba(200,75,75,.25);border-color:var(--red)}

.divider{height:1px;background:linear-gradient(90deg,transparent,var(--border),transparent);margin:2px 0 12px}

/* ── RESULTS ── */
.results{
  grid-area:results;
  border-top:1px solid var(--border);
  padding:20px 22px 28px;
  background:rgba(6,8,13,.98);
}
.res-title{
  font-family:'Cinzel',serif;font-size:12px;letter-spacing:4px;font-weight:700;
  color:var(--gold);text-shadow:0 0 14px rgba(200,168,75,.35);
  margin-bottom:16px;display:flex;align-items:center;gap:10px;
}
.res-title::before,.res-title::after{content:'';flex:1;height:1px}
.res-title::before{background:linear-gradient(90deg,transparent,rgba(200,168,75,.3))}
.res-title::after{background:linear-gradient(270deg,transparent,rgba(200,168,75,.3))}

/* 3-column grid of pick cards */
.picks-grid{
  display:grid;
  grid-template-columns:repeat(3,1fr);
  gap:12px;
}

.pick-card{
  background:rgba(255,255,255,.03);
  border:1px solid var(--border);
  border-radius:5px;overflow:hidden;
  transition:border-color .18s,transform .18s,box-shadow .18s;
  animation:fadeIn .3s ease both;
}
.pick-card:hover{
  border-color:rgba(200,168,75,.4);
  transform:translateY(-3px);
  box-shadow:0 8px 24px rgba(0,0,0,.4);
}
@keyframes fadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}

.pick-card:nth-child(1){animation-delay:.00s}
.pick-card:nth-child(2){animation-delay:.04s}
.pick-card:nth-child(3){animation-delay:.08s}
.pick-card:nth-child(4){animation-delay:.12s}
.pick-card:nth-child(5){animation-delay:.16s}
.pick-card:nth-child(6){animation-delay:.20s}
.pick-card:nth-child(7){animation-delay:.24s}
.pick-card:nth-child(8){animation-delay:.28s}
.pick-card:nth-child(9){animation-delay:.32s}

.pick-img-wrap{position:relative;aspect-ratio:16/7;overflow:hidden}
.pick-img-wrap img{width:100%;height:100%;object-fit:cover;display:block;
  transition:transform .3s}
.pick-card:hover .pick-img-wrap img{transform:scale(1.05)}

/* Score badge top-right */
.pick-score{
  position:absolute;top:6px;right:6px;
  background:rgba(0,0,0,.78);border:1px solid var(--gold-dim);
  border-radius:2px;padding:2px 6px;
  font-size:10px;font-weight:700;color:var(--gold);letter-spacing:.5px;
  font-family:'Rajdhani',sans-serif;
}
.pick-score.neg{color:#c84b4b;border-color:rgba(200,75,75,.4)}

/* Rank badge top-left */
.pick-rank{
  position:absolute;top:6px;left:6px;
  width:20px;height:20px;border-radius:50%;
  background:rgba(0,0,0,.8);border:1px solid rgba(200,168,75,.5);
  display:flex;align-items:center;justify-content:center;
  font-family:'Cinzel',serif;font-size:9px;font-weight:700;color:var(--gold);
}

/* Role badges */
.role-badges{
  position:absolute;bottom:6px;left:6px;
  display:flex;gap:3px;
}
.rbadge{
  padding:1px 5px;border-radius:2px;
  font-size:8px;font-weight:700;letter-spacing:.8px;text-transform:uppercase;
  font-family:'Rajdhani',sans-serif;
  background:rgba(0,0,0,.75);
}

.pick-body{padding:8px 10px 10px}
.pick-name{font-size:14px;font-weight:700;color:#e8dcc4;margin-bottom:6px;letter-spacing:.5px}
.pick-reasons{display:flex;flex-direction:column;gap:3px}
.preason{
  font-size:10px;color:var(--dim);
  display:flex;align-items:flex-start;gap:4px;line-height:1.35;
}
.preason::before{content:'▸';color:var(--gold-dim);flex-shrink:0;font-size:9px;margin-top:1px}
.preason.counter{color:#8bc4a8}
.preason.synergy{color:#7aabcc}
.preason.meta{color:#c8a84b}

/* No results */
.no-picks{
  display:flex;align-items:center;justify-content:center;
  padding:24px;color:var(--dim);font-size:11px;
  letter-spacing:1.5px;text-transform:uppercase;
  border:1px dashed var(--border);border-radius:3px;font-style:italic;
}

.err-msg{color:var(--red);font-size:11px;letter-spacing:1px;padding:10px 0;text-align:center}
.no-res{color:var(--dim);font-size:12px;letter-spacing:1px;padding:20px;text-align:center;font-style:italic}

::-webkit-scrollbar{width:4px;height:4px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px}
::-webkit-scrollbar-thumb:hover{background:var(--gold-dim)}
`;

export default function Dota2Drafter() {
  const [mode,    setMode]    = useState("enemy");
  const [enemy,   setEnemy]   = useState([]);  // frontend hero IDs
  const [team,    setTeam]    = useState([]);
  const [search,  setSearch]  = useState("");
  const [picks,   setPicks]   = useState(null);
  const [loading, setLoading] = useState(false);
  const [apiErr,  setApiErr]  = useState("");
  const styleRef = useRef(false);

  useEffect(() => {
    if (styleRef.current) return;
    styleRef.current = true;
    const s = document.createElement("style");
    s.id = "d2-css"; s.textContent = CSS;
    document.head.appendChild(s);
  }, []);

  const allSel = useMemo(() => new Set([...enemy, ...team]), [enemy, team]);

  const filtered = useMemo(() => {
    const q = search.toLowerCase().trim();
    return q ? HEROES.filter(h => h.name.toLowerCase().includes(q)) : HEROES;
  }, [search]);

  const grouped = useMemo(() => {
    const g = {};
    ATTR_ORDER.forEach(a => { g[a] = []; });
    filtered.forEach(h => { if (g[h.attr]) g[h.attr].push(h); });
    return g;
  }, [filtered]);

  function heroById(id) { return HEROES.find(h => h.id === id); }

  function handleHero(hero) {
    const id = hero.id;
    // If already selected in either team → deselect
    if (enemy.includes(id)) { setEnemy(e => e.filter(x => x !== id)); return; }
    if (team.includes(id))  { setTeam(t  => t.filter(x => x !== id)); return; }
    // Add to current mode
    if (mode === "enemy" && enemy.length < MAX_PICKS) setEnemy(e => [...e, id]);
    if (mode === "team"  && team.length  < MAX_PICKS) setTeam(t  => [...t, id]);
    setPicks(null); setApiErr("");
  }

  // These functions are used by the ✕ buttons in the side panel
  function rmEnemy(id) {
    setEnemy(prev => prev.filter(x => x !== id));
    setPicks(null);
  }
  function rmTeam(id) {
    setTeam(prev => prev.filter(x => x !== id));
    setPicks(null);
  }
  function clearAll() {
    setEnemy([]); setTeam([]); setPicks(null); setApiErr("");
  }

  async function handleSuggest() {
    if (!enemy.length && !team.length) return;
    setLoading(true); setApiErr(""); setPicks(null);
    const en = enemy.map(id => heroById(id)?.name).filter(Boolean);
    const al = team.map(id  => heroById(id)?.name).filter(Boolean);
    try {
      const res = await fetch(`${API}/suggest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enemy: en, team: al }),
      });
      if (!res.ok) throw new Error(`${res.status}`);
      const data = await res.json();
      setPicks(data.picks || []);
    } catch(e) {
      setApiErr(`Backend error: ${e.message}. Is uvicorn running on port 8000?`);
    } finally {
      setLoading(false);
    }
  }

  const enemyHeroes = enemy.map(heroById).filter(Boolean);
  const teamHeroes  = team.map(heroById).filter(Boolean);
  const canSuggest  = enemy.length > 0 || team.length > 0;

  function scoreColor(s) { return s >= 0 ? "" : "neg"; }

  function reasonClass(r) {
    if (r.startsWith("Counters") || r.startsWith("Even")) return "counter";
    if (r.startsWith("Synergy"))  return "synergy";
    if (r.startsWith("Meta"))     return "meta";
    return "";
  }

  return (
    <div className="app">
      {/* HEADER */}
      <header className="hdr">
        <div className="logo">DOTA<span>2</span> DRAFTER</div>

        <div className="search-wrap">
          <span className="search-ico">⌕</span>
          <input
            className="search"
            placeholder="Search hero..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>

        <div className="hdr-btns">
          <button
            className={`btn btn-enemy${mode==="enemy" ? " on" : ""}`}
            onClick={() => setMode("enemy")}
          >✕ Enemy</button>
          <button
            className={`btn btn-ally${mode==="team" ? " on" : ""}`}
            onClick={() => setMode("team")}
          >✓ Ally</button>
          <button
            className={`btn btn-suggest${loading ? " spinning" : ""}`}
            onClick={handleSuggest}
            disabled={!canSuggest || loading}
          >{loading ? "⟳ Analyzing…" : "🔥 Suggest Picks"}</button>
          <button className="btn btn-clear" onClick={clearAll}>↺ Clear</button>
        </div>
      </header>

      {/* HERO GRID */}
      <main className="grid-area">
        {filtered.length === 0 && (
          <div className="no-res">No heroes match "{search}"</div>
        )}
        {ATTR_ORDER.map(attr => {
          const heroes = grouped[attr];
          if (!heroes.length) return null;
          const m = ATTR_META[attr];
          return (
            <div className="attr-sec" key={attr}>
              <div className="attr-lbl" style={{ color: m.color }}>
                <span>{m.icon} {attr.toUpperCase()}</span>
                <span className="attr-line" style={{
                  background: `linear-gradient(90deg,${m.color},transparent)`
                }}/>
              </div>
              <div className="hero-grid">
                {heroes.map(hero => {
                  const isE  = enemy.includes(hero.id);
                  const isA  = team.includes(hero.id);
                  const gray = allSel.has(hero.id);
                  return (
                    <div
                      key={hero.id}
                      className={["hcard", gray?"gray":"", isE?"enemy":"", isA?"ally":""].filter(Boolean).join(" ")}
                      onClick={() => handleHero(hero)}
                      title={hero.name}
                    >
                      <img
                        src={IMG(hero.img)} alt={hero.name} loading="lazy"
                        onError={e => { e.target.src="https://via.placeholder.com/78x44/0b0f16/333?text=?"; }}
                      />
                      <div className="hname">{hero.name}</div>
                      {isE && <div className="hbadge e">✕</div>}
                      {isA && <div className="hbadge a">✓</div>}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </main>

      {/* SIDE PANEL */}
      <aside className="panel">
        {/* Enemy */}
        <div className="psec">
          <div className="ptitle e">✕ ENEMY TEAM</div>
          <div className="pcount">{enemyHeroes.length} / {MAX_PICKS} selected</div>
          {Array.from({length: MAX_PICKS}).map((_, i) => {
            const h = enemyHeroes[i];
            return h ? (
              <div key={h.id} className="slot fe">
                <img src={IMG(h.img)} alt={h.name}
                     onError={e => e.target.style.display="none"} />
                <div className="slot-info">
                  <div className="slot-name">{h.name}</div>
                  <div className="slot-attr" style={{color:ATTR_META[h.attr]?.color}}>
                    {h.attr}
                  </div>
                </div>
                {/* FIX: onClick uses arrow function capturing h.id to prevent stale closure */}
                <div
                  className="slot-rm"
                  onClick={(e) => { e.stopPropagation(); rmEnemy(h.id); }}
                  title="Remove"
                >✕</div>
              </div>
            ) : (
              <div key={i} className="slot">
                <span className="slot-empty">— Empty slot —</span>
              </div>
            );
          })}
        </div>

        <div className="divider"/>

        {/* Ally */}
        <div className="psec">
          <div className="ptitle a">✓ YOUR TEAM</div>
          <div className="pcount">{teamHeroes.length} / {MAX_PICKS} selected</div>
          {Array.from({length: MAX_PICKS}).map((_, i) => {
            const h = teamHeroes[i];
            return h ? (
              <div key={h.id} className="slot fa">
                <img src={IMG(h.img)} alt={h.name}
                     onError={e => e.target.style.display="none"} />
                <div className="slot-info">
                  <div className="slot-name">{h.name}</div>
                  <div className="slot-attr" style={{color:ATTR_META[h.attr]?.color}}>
                    {h.attr}
                  </div>
                </div>
                <div
                  className="slot-rm"
                  onClick={(e) => { e.stopPropagation(); rmTeam(h.id); }}
                  title="Remove"
                >✕</div>
              </div>
            ) : (
              <div key={i} className="slot">
                <span className="slot-empty">— Empty slot —</span>
              </div>
            );
          })}
        </div>
      </aside>

      {/* RESULTS — flat 3×3 grid */}
      {(picks !== null || apiErr) && (
        <section className="results">
          <div className="res-title">🎯 RECOMMENDED PICKS</div>
          {apiErr && <div className="err-msg">⚠ {apiErr}</div>}
          {picks && picks.length === 0 && (
            <div className="no-picks">
              No counter picks found — check /debug for name alignment
            </div>
          )}
          {picks && picks.length > 0 && (
            <div className="picks-grid">
              {picks.map((p, idx) => {
                const imgKey = NAME_TO_IMG[p.name] ||
                  p.name.toLowerCase().replace(/ /g,"_").replace(/'/g,"");
                return (
                  <div className="pick-card" key={p.id}>
                    <div className="pick-img-wrap">
                      <img
                        src={IMG(imgKey)} alt={p.name}
                        onError={e => {
                          e.target.src="https://via.placeholder.com/300x100/0b0f16/333?text=?";
                        }}
                      />
                      <div className="pick-rank">{idx + 1}</div>
                      <div className={`pick-score ${scoreColor(p.score)}`}>
                        {p.score > 0 ? "+" : ""}{p.score.toFixed(3)}
                      </div>
                      <div className="role-badges">
                        {(p.roles || []).map(r => (
                          <span
                            key={r}
                            className="rbadge"
                            style={{ color: ROLE_COLORS[r] || "#999",
                                     borderLeft: `2px solid ${ROLE_COLORS[r] || "#999"}` }}
                          >{r}</span>
                        ))}
                      </div>
                    </div>
                    <div className="pick-body">
                      <div className="pick-name">{p.name}</div>
                      <div className="pick-reasons">
                        {p.reasons.map((r, i) => (
                          <div className={`preason ${reasonClass(r)}`} key={i}>{r}</div>
                        ))}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
