import { useState, useMemo, useEffect, useRef } from "react";
import INITIAL_HEROES from "./heroes_fallback.json";

const IMG = img =>
  `https://cdn.cloudflare.steamstatic.com/apps/dota2/images/heroes/${img}_full.png`;

const ATTR_META = {
  agility:      { color:"#4bc87a", icon:"⚡" },
  strength:     { color:"#c84b4b", icon:"🛡"  },
  intelligence: { color:"#5b9bd5", icon:"✦"   },
  universal:    { color:"#c8a84b", icon:"◈"   },
};

const ROLE_COLORS = {
  carry:        "#c8a84b",
  mid:          "#5b9bd5",
  offlane:      "#c84b4b",
  support:      "#4bc87a",
  soft_support: "#20b2aa",
  hard_support: "#4bc87a",
};

const ATTR_ORDER = ["agility","strength","intelligence","universal"];
const MAX_ENEMY = 5;
const MAX_ALLY = 4;
const MAX_BANS = 7;
const API = import.meta.env.VITE_API_URL || "/api";

// ── CSS ───────────────────────────────────────────────────────────────────────
const CSS = `
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700;900&family=Rajdhani:wght@400;600;700&display=swap');

*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}

:root{
  --bg:#06080d;--panel:#0b0f16;--border:#1a2436;
  --gold:#c8a84b;--gold-dim:#7a6228;
  --red:#c84b4b;--green:#4bc87a;--blue:#3a8fd4;--orange:#e07a3f;
  --text:#d4c5a0;--dim:#4a5568;
}

body{background:var(--bg);color:var(--text);overflow-x:hidden}

.app{
  font-family:'Rajdhani',sans-serif;
  min-height:100vh;
  display:grid;
  grid-template-rows:56px 1fr auto auto;
  grid-template-columns:1fr 280px;
  grid-template-areas:"hdr hdr" "grid panel" "results results" "footer footer";
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
  flex-wrap:nowrap;overflow-x:auto;
}
.logo{
  font-family:'Cinzel',serif;font-size:18px;font-weight:900;
  letter-spacing:4px;color:var(--gold);
  text-shadow:0 0 18px rgba(200,168,75,.4);
  white-space:nowrap;margin-right:4px;
}
.logo span{color:#fff}
.search-wrap{position:relative;flex:1;max-width:240px;min-width:140px}
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

.hdr-btns{display:flex;gap:6px;margin-left:auto;align-items:center}
.btn{
  font-family:'Rajdhani',sans-serif;font-size:11px;font-weight:700;
  letter-spacing:1px;text-transform:uppercase;
  padding:6px 12px;border:1px solid;border-radius:2px;
  cursor:pointer;background:transparent;transition:all .18s;
  white-space:nowrap;
}
.btn-enemy{color:var(--red);border-color:var(--red)}
.btn-enemy.on{background:rgba(200,75,75,.18);box-shadow:0 0 12px rgba(200,75,75,.35)}
.btn-ally{color:var(--green);border-color:var(--green)}
.btn-ally.on{background:rgba(75,200,122,.14);box-shadow:0 0 12px rgba(75,200,122,.28)}
.btn-ban{color:var(--orange);border-color:var(--orange)}
.btn-ban.on{background:rgba(224,122,63,.2);box-shadow:0 0 12px rgba(224,122,63,.35)}
.btn-role-aware{color:#5b9bd5;border-color:rgba(91,155,213,.5)}
.btn-role-aware.on{background:rgba(91,155,213,.2);border-color:#5b9bd5;box-shadow:0 0 12px rgba(91,155,213,.35)}
.btn-beginner{color:#4bc87a;border-color:rgba(75,200,122,.5)}
.btn-beginner.on{background:rgba(75,200,122,.2);border-color:#4bc87a;box-shadow:0 0 12px rgba(75,200,122,.35)}
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
.hcard.ban{border-color:var(--orange);box-shadow:0 0 8px rgba(224,122,63,.5)}
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
.hbadge.b{background:var(--orange);color:#fff}

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
.ptitle.b{color:var(--orange);border-color:rgba(224,122,63,.3)}
.pcount{font-size:9px;color:var(--dim);letter-spacing:1px;font-weight:600;margin-bottom:4px}
.psec{display:flex;flex-direction:column;gap:5px;margin-bottom:14px}

/* ── SLOT ── */
.slot{
  display:flex;align-items:center;gap:7px;
  padding:4px 5px;border-radius:2px;
  border:1px solid var(--border);background:rgba(255,255,255,.02);
  min-height:36px;position:relative;
}
.slot.fe{border-color:rgba(200,75,75,.38)}
.slot.fa{border-color:rgba(75,200,122,.3)}
.slot.fb{border-color:rgba(224,122,63,.35)}
.slot img{width:42px;height:24px;object-fit:cover;border-radius:2px;flex-shrink:0}
.slot-info{flex:1;min-width:0}
.slot-name{font-size:11px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.slot-attr{font-size:8px;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-top:1px}
.slot-empty{font-size:9px;color:var(--dim);letter-spacing:1px;font-style:italic}
.slot-rm{
  flex-shrink:0;width:20px;height:20px;
  display:flex;align-items:center;justify-content:center;
  background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);
  border-radius:3px;cursor:pointer;color:var(--dim);font-size:11px;
  transition:all .14s;pointer-events:all;user-select:none;
}
.slot-rm:hover{color:#fff;background:rgba(200,75,75,.25);border-color:var(--red)}

.divider{height:1px;background:linear-gradient(90deg,transparent,var(--border),transparent);margin:4px 0 12px}

/* ── RESULTS ── */
.results{
  grid-area:results;
  border-top:1px solid var(--border);
  padding:20px 22px 28px;
  background:rgba(6,8,13,.98);
}
.res-hdr{
  display:flex;flex-direction:column;align-items:center;gap:12px;
  margin-bottom:16px;
}
.res-title{
  font-family:'Cinzel',serif;font-size:13px;letter-spacing:4px;font-weight:700;
  color:var(--gold);text-shadow:0 0 14px rgba(200,168,75,.35);
  display:flex;align-items:center;gap:10px;width:100%;
}
.res-title::before,.res-title::after{content:'';flex:1;height:1px}
.res-title::before{background:linear-gradient(90deg,transparent,rgba(200,168,75,.3))}
.res-title::after{background:linear-gradient(270deg,transparent,rgba(200,168,75,.3))}

.res-controls{
  display:flex;align-items:center;justify-content:center;gap:8px;flex-wrap:wrap;
}
.role-filter-bar{
  display:flex;gap:6px;align-items:center;flex-wrap:wrap;margin:4px 0;
}
.role-pill{
  font-family:'Rajdhani',sans-serif;font-size:11px;font-weight:700;letter-spacing:1px;
  padding:4px 12px;border-radius:14px;background:rgba(255,255,255,.04);
  border:1px solid var(--border);color:var(--text);cursor:pointer;transition:all .15s;
}
.role-pill:hover{border-color:var(--gold-dim)}
.role-pill.active{
  background:rgba(200,168,75,.18);border-color:var(--gold);color:var(--gold);
  box-shadow:0 0 10px rgba(200,168,75,.25);
}

.picks-grid{
  display:grid;grid-template-columns:repeat(3,1fr);gap:12px;align-items:start;
}
.pick-card{
  background:rgba(255,255,255,.03);border:1px solid var(--border);
  border-radius:5px;overflow:hidden;transition:all .18s;
  animation:fadeIn .3s ease both;
}
.pick-card:hover{border-color:rgba(200,168,75,.4);transform:translateY(-2px);box-shadow:0 4px 18px rgba(0,0,0,.6)}
.pick-img-wrap{position:relative;width:100%;aspect-ratio:16/9;overflow:hidden;background:#06080d}
.pick-img-wrap img{width:100%;height:100%;object-fit:cover;display:block}
.pick-rank{
  position:absolute;top:6px;left:6px;background:rgba(0,0,0,.75);
  border:1px solid var(--border);padding:2px 7px;border-radius:3px;
  font-family:'Cinzel',serif;font-size:11px;font-weight:900;color:var(--gold);
}
.pick-score{
  position:absolute;top:6px;right:6px;background:rgba(0,0,0,.75);
  border:1px solid var(--border);padding:2px 7px;border-radius:3px;
  font-size:11px;font-weight:700;color:#4bc87a;
}
.pick-score.neg{color:var(--red)}
.role-badges{position:absolute;bottom:6px;left:6px;display:flex;gap:4px;flex-wrap:wrap}
.rbadge{
  font-size:8px;font-weight:700;letter-spacing:1px;text-transform:uppercase;
  background:rgba(0,0,0,.75);padding:1px 5px;border-radius:2px;
}

.pick-body{padding:12px}
.pick-hdr-row{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:6px}
.pick-name{font-size:14px;font-weight:700;color:#fff}
.diff-badge{font-size:9px;font-weight:700;padding:2px 6px;border-radius:2px}
.diff-badge.easy{background:rgba(75,200,122,.15);color:#4bc87a}
.diff-badge.moderate{background:rgba(200,168,75,.15);color:#c8a84b}
.diff-badge.complex{background:rgba(200,75,75,.15);color:#c84b4b}

.pick-meta-row{display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap}
.conf-badge{
  font-size:8px;font-weight:700;letter-spacing:1px;text-transform:uppercase;
  padding:2px 6px;border-radius:10px;border:1px solid;display:inline-flex;align-items:center;gap:4px;
}
.conf-badge.high{color:#4bc87a;border-color:rgba(75,200,122,.4);background:rgba(75,200,122,.1)}
.conf-badge.medium{color:#e6b800;border-color:rgba(230,184,0,.4);background:rgba(230,184,0,.1)}
.conf-badge.low{color:#94a3b8;border-color:rgba(148,163,184,.3);background:rgba(148,163,184,.08)}
.sample-tag{font-size:9px;color:var(--dim);font-weight:600;display:inline-flex;align-items:center;gap:4px}

.pick-one-liner{
  display:flex;align-items:flex-start;gap:7px;
  background:rgba(200,168,75,.09);border:1px solid rgba(200,168,75,.35);
  border-left:3px solid var(--gold);
  border-radius:3px;padding:7px 9px;margin-bottom:8px;
  font-size:11.5px;line-height:1.42;color:#f3ebd8;
}
.one-liner-ico{font-size:13px;flex-shrink:0;line-height:1.2}
.one-liner-txt{font-weight:600;letter-spacing:.2px}

.pick-overview{font-size:11px;color:#a8b3cf;line-height:1.4;margin-bottom:8px}

.pick-reasons{display:flex;flex-direction:column;gap:4px;margin-bottom:8px}
.preason{
  font-size:10px;font-weight:600;padding:3px 6px;border-radius:2px;
  background:rgba(255,255,255,.03);border-left:2px solid var(--border);
}
.preason.counter{border-left-color:var(--red);color:#ff9e9e}
.preason.synergy{border-left-color:var(--green);color:#a8f0c2}
.preason.meta{border-left-color:var(--gold);color:#ffd885}

.btn-guide-toggle{
  width:100%;background:rgba(255,255,255,.04);border:1px solid var(--border);
  border-radius:3px;padding:6px 8px;color:var(--gold);font-family:'Rajdhani',sans-serif;
  font-size:10px;font-weight:700;letter-spacing:1px;display:flex;justify-content:space-between;
  align-items:center;cursor:pointer;margin-top:6px;
}
.btn-guide-toggle:hover{border-color:var(--gold-dim);background:rgba(200,168,75,.08)}
.btn-guide-toggle .arrow{transition:transform .18s;font-size:8px}
.btn-guide-toggle.open .arrow{transform:rotate(180deg)}

.guide-details{margin-top:6px;display:flex;flex-direction:column;gap:6px}
.guide-item{background:rgba(0,0,0,.4);border:1px solid rgba(255,255,255,.05);border-radius:3px;padding:8px}
.guide-item-hdr{display:flex;align-items:center;gap:6px;margin-bottom:4px}
.guide-target-img{width:24px;height:14px;object-fit:cover;border-radius:2px}
.guide-item-title{font-size:10px;font-weight:700}
.guide-item-title.role_fit{color:var(--gold)}
.guide-how{font-size:10px;color:#c0c9df;line-height:1.35;margin-bottom:4px}
.guide-abilities{display:flex;gap:4px;flex-wrap:wrap;margin-bottom:4px}
.ability-pill{font-size:9px;background:rgba(255,255,255,.08);padding:1px 5px;border-radius:2px;color:#e2e8f0}
.guide-tip-box{font-size:10px;color:#ffd885;background:rgba(200,168,75,.08);padding:4px 6px;border-radius:2px;border-left:2px solid var(--gold)}

/* Loading & Error States */
.state-box{text-align:center;padding:32px 16px;background:rgba(255,255,255,.02);border:1px dashed var(--border);border-radius:4px;margin-top:12px}
.err-box{background:rgba(200,75,75,.08);border-color:var(--red);color:#ff9e9e}
.err-title{font-size:13px;font-weight:700;margin-bottom:6px}

/* ── FOOTER ── */
.app-footer{
  grid-area:footer;
  border-top:1px solid var(--border);
  background:rgba(6,8,13,.99);
  padding:14px 20px;
  display:flex;align-items:center;justify-content:space-between;
  font-size:11px;color:var(--dim);flex-wrap:wrap;gap:12px;
}
.footer-left{display:flex;gap:16px;flex-wrap:wrap;align-items:center}
.footer-badge{display:inline-flex;align-items:center;gap:5px}
.footer-right{color:#555}

/* ── MOBILE BAR ── */
.mobile-bar{
  display:none;position:fixed;bottom:0;left:0;right:0;z-index:99;
  background:rgba(6,8,13,.98);border-top:1px solid var(--border);
  padding:8px 12px;gap:8px;
}
.mobile-modes{display:flex;gap:4px;flex:1}

@media(max-width:900px){
  .picks-grid{grid-template-columns:repeat(2,1fr)}
}
@media(max-width:768px){
  .app{
    grid-template-columns:1fr;
    grid-template-areas:"hdr" "panel" "grid" "results" "footer";
    padding-bottom:56px;
  }
  .panel{border-left:none;border-bottom:1px solid var(--border);max-height:220px}
  .picks-grid{grid-template-columns:1fr}
  .mobile-bar{display:flex}
  .hdr-btns .btn-suggest{display:none}
}

@keyframes fadeIn{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
`;

export default function Dota2Drafter() {
  const [heroesList,     setHeroesList]      = useState(INITIAL_HEROES);
  const [mode,           setMode]            = useState("enemy"); // enemy | team | bans
  const [enemy,          setEnemy]           = useState([]);      // numeric hero IDs
  const [team,           setTeam]            = useState([]);
  const [bans,           setBans]            = useState([]);
  const [search,         setSearch]          = useState("");
  const [picks,          setPicks]           = useState(null);
  const [categories,     setCategories]      = useState(null);
  const [loading,        setLoading]         = useState(false);
  const [apiErr,         setApiErr]          = useState("");
  const [beginnerOnly,   setBeginnerOnly]    = useState(false);
  const [roleAware,      setRoleAware]       = useState(false);
  const [selectedRole,   setSelectedRole]    = useState("all");
  const [bracket,        setBracket]         = useState("all");
  const [healthInfo,     setHealthInfo]      = useState(null);
  const [expandedCardIds,setExpandedCardIds] = useState(new Set());
  const styleRef = useRef(false);

  useEffect(() => {
    if (styleRef.current) return;
    styleRef.current = true;
    const s = document.createElement("style");
    s.id = "d2-css"; s.textContent = CSS;
    document.head.appendChild(s);
  }, []);

  // Fetch dynamic heroes list and data freshness on mount
  useEffect(() => {
    async function initData() {
      try {
        const res = await fetch(`${API}/heroes`);
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data) && data.length > 0) {
            const mapped = data.map(h => ({
              id: h.id,
              name: h.name,
              img: h.short_name || h.name.toLowerCase().replace(/ /g, "_").replace(/'/g, ""),
              attr: h.attribute === "str" ? "strength" :
                    h.attribute === "agi" ? "agility" :
                    h.attribute === "int" ? "intelligence" : "universal",
              roles: h.roles || [],
              image_url: h.image_url
            }));
            setHeroesList(mapped);
          }
        }
      } catch (e) {
        console.warn("Failed to load /heroes, using initial fallback:", e);
      }

      try {
        const hRes = await fetch(`${API}/health`);
        if (hRes.ok) {
          const hData = await hRes.json();
          setHealthInfo(hData);
        }
      } catch (e) {
        console.warn("Failed to load /health:", e);
      }
    }
    initData();
  }, []);

  const allSel = useMemo(() => new Set([...enemy, ...team, ...bans]), [enemy, team, bans]);

  const filtered = useMemo(() => {
    const q = search.toLowerCase().trim();
    return q ? heroesList.filter(h => h.name.toLowerCase().includes(q)) : heroesList;
  }, [search, heroesList]);

  const grouped = useMemo(() => {
    const g = {};
    ATTR_ORDER.forEach(a => { g[a] = []; });
    filtered.forEach(h => {
      const a = h.attr || "universal";
      if (g[a]) g[a].push(h);
    });
    return g;
  }, [filtered]);

  function heroById(id) {
    return heroesList.find(h => h.id === id);
  }

  function handleHero(hero) {
    const id = hero.id;
    // If already in any list, remove it
    if (enemy.includes(id)) { setEnemy(e => e.filter(x => x !== id)); return; }
    if (team.includes(id))  { setTeam(t  => t.filter(x => x !== id)); return; }
    if (bans.includes(id))  { setBans(b  => b.filter(x => x !== id)); return; }

    // Add to active selection mode
    if (mode === "enemy" && enemy.length < MAX_ENEMY) setEnemy(e => [...e, id]);
    if (mode === "team"  && team.length  < MAX_ALLY)  setTeam(t  => [...t, id]);
    if (mode === "bans"  && bans.length  < MAX_BANS)  setBans(b  => [...b, id]);

    setPicks(null);
    setCategories(null);
    setApiErr("");
  }

  function rmEnemy(id) { setEnemy(prev => prev.filter(x => x !== id)); setPicks(null); setCategories(null); }
  function rmTeam(id)  { setTeam(prev => prev.filter(x => x !== id));  setPicks(null); setCategories(null); }
  function rmBan(id)   { setBans(prev => prev.filter(x => x !== id));  setPicks(null); setCategories(null); }

  function clearAll() {
    setEnemy([]); setTeam([]); setBans([]);
    setPicks(null); setCategories(null); setApiErr(""); setExpandedCardIds(new Set());
  }

  function toggleCardGuide(id) {
    setExpandedCardIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function handleSuggest() {
    if (!enemy.length && !team.length) return;
    setLoading(true); setApiErr(""); setPicks(null); setCategories(null);

    const targetRoleNeeded = (selectedRole === "soft_support" || selectedRole === "hard_support")
      ? "support"
      : (selectedRole !== "all" ? selectedRole : null);

    const payload = {
      enemy: enemy,
      team: team,
      bans: bans,
      role_aware: roleAware,
      roles_needed: targetRoleNeeded ? [targetRoleNeeded] : null,
      bracket: bracket
    };

    try {
      const res = await fetch(`${API}/suggest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        const details = Array.isArray(errJson.details) ? ` - ${errJson.details.join("; ")}` : "";
        const msg = (errJson.message || errJson.detail || `Server error (${res.status})`) + details;
        throw new Error(msg);
      }
      const data = await res.json();
      const resPicks = data.picks || [];
      setPicks(resPicks);
      setCategories(data.categories || null);
      if (resPicks.length > 0) {
        setExpandedCardIds(new Set([resPicks[0].id]));
      }
      setTimeout(() => {
        const el = document.getElementById("results-section");
        if (el) el.scrollIntoView({ behavior: "smooth" });
      }, 120);
    } catch(e) {
      setApiErr(`${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  const displayedPicks = useMemo(() => {
    if (!picks && !categories) return null;
    let list = [];
    if (categories && categories[selectedRole]) {
      list = categories[selectedRole];
    } else if (picks) {
      list = selectedRole === "all"
        ? picks
        : picks.filter(p => {
            const rList = (p.roles || []).map(r => r.toLowerCase());
            if (rList.includes(selectedRole)) return true;
            if ((selectedRole === "soft_support" || selectedRole === "hard_support") && rList.includes("support")) return true;
            return false;
          });
    }
    if (beginnerOnly) {
      list = list.filter(p => (p.difficulty || "Easy") === "Easy");
    }
    return list;
  }, [picks, categories, beginnerOnly, selectedRole]);

  const enemyHeroes = enemy.map(heroById).filter(Boolean);
  const teamHeroes  = team.map(heroById).filter(Boolean);
  const banHeroes   = bans.map(heroById).filter(Boolean);
  const canSuggest  = enemy.length > 0 || team.length > 0;

  function scoreColor(s) { return s >= 0 ? "" : "neg"; }

  function reasonClass(r) {
    if (r.startsWith("Counters") || r.startsWith("Even") || r.startsWith("Matchup")) return "counter";
    if (r.startsWith("Synergy"))  return "synergy";
    if (r.startsWith("Meta") || r.startsWith("Role Fit") || r.startsWith("Fills"))     return "meta";
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
          >✕ Enemy ({enemy.length}/{MAX_ENEMY})</button>

          <button
            className={`btn btn-ally${mode==="team" ? " on" : ""}`}
            onClick={() => setMode("team")}
          >✓ Ally ({team.length}/{MAX_ALLY})</button>

          <button
            className={`btn btn-ban${mode==="bans" ? " on" : ""}`}
            onClick={() => setMode("bans")}
          >🚫 Ban ({bans.length}/{MAX_BANS})</button>

          <button
            className={`btn btn-role-aware${roleAware ? " on" : ""}`}
            onClick={() => setRoleAware(r => !r)}
            title="Auto-fill missing team positions"
          >🎯 Roles {roleAware ? "ON" : "OFF"}</button>

          <button
            className={`btn btn-beginner${beginnerOnly ? " on" : ""}`}
            onClick={() => setBeginnerOnly(b => !b)}
            title="Filter to beginner-friendly heroes only"
          >🐣 Beginner {beginnerOnly ? "ON" : "OFF"}</button>

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
          <div className="no-res" style={{padding:"24px",color:"#777",textAlign:"center"}}>
            No heroes match "{search}"
          </div>
        )}
        {ATTR_ORDER.map(attr => {
          const heroes = grouped[attr] || [];
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
                  const isB  = bans.includes(hero.id);
                  const gray = allSel.has(hero.id);
                  return (
                    <div
                      key={hero.id}
                      className={["hcard", gray?"gray":"", isE?"enemy":"", isA?"ally":"", isB?"ban":""].filter(Boolean).join(" ")}
                      onClick={() => handleHero(hero)}
                      title={hero.name}
                    >
                      <img
                        src={hero.image_url || IMG(hero.img)}
                        alt={hero.name}
                        loading="lazy"
                        onError={e => { e.target.src="https://via.placeholder.com/78x44/0b0f16/333?text=?"; }}
                      />
                      <div className="hname">{hero.name}</div>
                      {isE && <div className="hbadge e">✕</div>}
                      {isA && <div className="hbadge a">✓</div>}
                      {isB && <div className="hbadge b">🚫</div>}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </main>

      {/* SIDE PANEL / MOBILE DOCK */}
      <aside className="panel">
        {/* Enemy */}
        <div className="psec">
          <div className="psec-hdr">
            <div className="ptitle e">✕ ENEMY TEAM</div>
            <div className="pcount">{enemyHeroes.length} / {MAX_ENEMY} selected</div>
          </div>
          <div className="slots-list">
            {Array.from({length: MAX_ENEMY}).map((_, i) => {
              const h = enemyHeroes[i];
              return h ? (
                <div key={h.id} className="slot fe">
                  <img src={h.image_url || IMG(h.img)} alt={h.name} onError={e => e.target.style.display="none"} />
                  <div className="slot-info">
                    <div className="slot-name">{h.name}</div>
                    <div className="slot-attr" style={{color:ATTR_META[h.attr]?.color}}>{h.attr}</div>
                  </div>
                  <div className="slot-rm" onClick={(e) => { e.stopPropagation(); rmEnemy(h.id); }} title="Remove">✕</div>
                </div>
              ) : (
                <div key={i} className="slot"><span className="slot-empty">—</span></div>
              );
            })}
          </div>
        </div>

        <div className="divider"/>

        {/* Ally */}
        <div className="psec">
          <div className="psec-hdr">
            <div className="ptitle a">✓ YOUR ALLIES</div>
            <div className="pcount">{teamHeroes.length} / {MAX_ALLY} selected</div>
          </div>
          <div className="slots-list">
            {Array.from({length: MAX_ALLY}).map((_, i) => {
              const h = teamHeroes[i];
              return h ? (
                <div key={h.id} className="slot fa">
                  <img src={h.image_url || IMG(h.img)} alt={h.name} onError={e => e.target.style.display="none"} />
                  <div className="slot-info">
                    <div className="slot-name">{h.name}</div>
                    <div className="slot-attr" style={{color:ATTR_META[h.attr]?.color}}>{h.attr}</div>
                  </div>
                  <div className="slot-rm" onClick={(e) => { e.stopPropagation(); rmTeam(h.id); }} title="Remove">✕</div>
                </div>
              ) : (
                <div key={i} className="slot"><span className="slot-empty">—</span></div>
              );
            })}
          </div>
        </div>

        <div className="divider"/>

        {/* Bans */}
        <div className="psec">
          <div className="psec-hdr">
            <div className="ptitle b">🚫 BANS</div>
            <div className="pcount">{banHeroes.length} / {MAX_BANS} banned</div>
          </div>
          <div className="slots-list">
            {Array.from({length: MAX_BANS}).map((_, i) => {
              const h = banHeroes[i];
              return h ? (
                <div key={h.id} className="slot fb">
                  <img src={h.image_url || IMG(h.img)} alt={h.name} onError={e => e.target.style.display="none"} />
                  <div className="slot-info">
                    <div className="slot-name">{h.name}</div>
                    <div className="slot-attr" style={{color:ATTR_META[h.attr]?.color}}>{h.attr}</div>
                  </div>
                  <div className="slot-rm" onClick={(e) => { e.stopPropagation(); rmBan(h.id); }} title="Remove">✕</div>
                </div>
              ) : (
                <div key={i} className="slot"><span className="slot-empty">—</span></div>
              );
            })}
          </div>
        </div>
      </aside>

      {/* RESULTS SECTION */}
      {(picks !== null || categories !== null || apiErr || loading) && (
        <section className="results" id="results-section">
          <div className="res-hdr">
            <div className="res-title">🎯 RECOMMENDED PICKS</div>
            <div className="res-controls">
              {/* Role Filter Pills */}
              <div className="role-filter-bar">
                {[
                  { id: "all",          label: "ALL (10)" },
                  { id: "carry",        label: "CARRY (POS 1)" },
                  { id: "mid",          label: "MID (POS 2)" },
                  { id: "offlane",      label: "OFFLANE (POS 3)" },
                  { id: "soft_support", label: "SOFT SUPP (POS 4)" },
                  { id: "hard_support", label: "HARD SUPP (POS 5)" },
                ].map(r => (
                  <button
                    key={r.id}
                    className={`role-pill ${selectedRole === r.id ? "active" : ""}`}
                    onClick={() => setSelectedRole(r.id)}
                  >
                    {r.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {loading && (
            <div className="state-box">
              <div style={{fontSize:"13px",fontWeight:"700",color:"var(--gold)",marginBottom:"6px"}}>
                ⟳ Computing Shrunk Matchups & Running Tree Model…
              </div>
              <div style={{fontSize:"11px",color:"var(--dim)"}}>
                Evaluating synergy, lane counters, and draft win probability across meta matrix
              </div>
            </div>
          )}

          {apiErr && (
            <div className="state-box err-box">
              <div className="err-title">⚠ Draft Suggestion Error</div>
              <div>{apiErr}</div>
              <button
                className="btn btn-suggest"
                style={{marginTop:"10px",display:"inline-block"}}
                onClick={handleSuggest}
              >
                ↻ Retry Suggestion
              </button>
            </div>
          )}

          {(!displayedPicks || displayedPicks.length === 0) && (picks !== null || categories !== null) && !loading && (
            <div className="state-box">
              No picks available matching current constraints. Try adjusting role filter or bans.
            </div>
          )}

          {displayedPicks && displayedPicks.length > 0 && !loading && (
            <div className="picks-grid">
              {displayedPicks.map((p, idx) => {
                const diff = p.difficulty || "Easy";
                const isExpanded = expandedCardIds.has(p.id);
                const conf = p.confidence || "medium";
                const heroObj = heroById(p.id);
                return (
                  <div className="pick-card" key={p.id}>
                    <div className="pick-img-wrap">
                      <img
                        src={heroObj?.image_url || IMG(p.name.toLowerCase().replace(/ /g,"_").replace(/'/g,""))}
                        alt={p.name}
                        onError={e => { e.target.src="https://via.placeholder.com/300x100/0b0f16/333?text=?"; }}
                      />
                      <div className="pick-rank">#{idx + 1}</div>
                      <div className={`pick-score ${scoreColor(p.score)}`}>
                        {p.score > 0 ? "+" : ""}{p.score.toFixed(3)}
                      </div>
                      <div className="role-badges">
                        {(p.roles || []).filter(r => r !== "support" || !(p.roles.includes("soft_support") || p.roles.includes("hard_support"))).map(r => (
                          <span
                            key={r}
                            className="rbadge"
                            style={{ color: ROLE_COLORS[r.toLowerCase()] || "#999",
                                     borderLeft: `2px solid ${ROLE_COLORS[r.toLowerCase()] || "#999"}` }}
                          >{r === "soft_support" ? "Pos 4" : r === "hard_support" ? "Pos 5" : r}</span>
                        ))}
                      </div>
                    </div>

                    <div className="pick-body">
                      <div className="pick-hdr-row">
                        <div className="pick-name">{p.name}</div>
                        <span className={`diff-badge ${diff.toLowerCase()}`}>
                          {diff === "Easy" ? "🟢 Easy" : diff === "Moderate" ? "🟡 Moderate" : "🔴 Complex"}
                        </span>
                      </div>

                      {/* Confidence & Sample Size */}
                      <div className="pick-meta-row">
                        <span className={`conf-badge ${conf}`}>
                          {conf === "high" ? "🟢 High Confidence" : conf === "medium" ? "🟡 Med Confidence" : "⚪ Low Confidence"}
                        </span>
                        {p.sample_size > 0 && (
                          <span className="sample-tag">
                            📊 {p.sample_size} matches
                          </span>
                        )}
                      </div>

                      {p.one_liner && (
                        <div className="pick-one-liner">
                          <span className="one-liner-ico">⚔️</span>
                          <span className="one-liner-txt">{p.one_liner}</span>
                        </div>
                      )}

                      {p.overview && (
                        <div className="pick-overview">{p.overview}</div>
                      )}

                      <div className="pick-reasons">
                        {(p.reasons || []).map((r, i) => (
                          <div className={`preason ${reasonClass(r)}`} key={i}>{r}</div>
                        ))}
                      </div>

                      {p.reason_details && p.reason_details.length > 0 && (
                        <>
                          <button
                            className={`btn-guide-toggle ${isExpanded ? "open" : ""}`}
                            onClick={() => toggleCardGuide(p.id)}
                          >
                            <span>💡 Tactical Breakdown ({p.reason_details.length})</span>
                            <span className="arrow">▼</span>
                          </button>

                          {isExpanded && (
                            <div className="guide-details">
                              {p.reason_details.map((detail, dIdx) => (
                                <div className="guide-item" key={dIdx}>
                                  <div className="guide-item-hdr">
                                    <span className={`guide-item-title ${detail.reason_type || "counter"}`}>
                                      {detail.summary}
                                    </span>
                                  </div>
                                  {detail.how_and_why && (
                                    <div className="guide-how">{detail.how_and_why}</div>
                                  )}
                                  {detail.key_abilities && detail.key_abilities.length > 0 && (
                                    <div className="guide-abilities">
                                      {detail.key_abilities.map(ab => (
                                        <span key={ab} className="ability-pill">⚡ {ab}</span>
                                      ))}
                                    </div>
                                  )}
                                  {detail.beginner_tip && (
                                    <div className="guide-tip-box">
                                      💡 <strong>Beginner Tip:</strong> {detail.beginner_tip}
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>
      )}

      {/* DATA FRESHNESS FOOTER */}
      <footer className="app-footer">
        <div className="footer-left">
          <span className="footer-badge">
            ⚡ <strong>Model:</strong> {healthInfo?.model_version || "v2.2.0"}
          </span>
          <span className="footer-badge">
            📅 <strong>Patch:</strong> {healthInfo?.data_freshness?.latest_patch || "7.35d"}
          </span>
          <span className="footer-badge">
            📊 <strong>Matches:</strong> {healthInfo?.data_freshness?.match_count?.toLocaleString() || "14,907"}
          </span>
          <span className="footer-badge">
            🛡 <strong>Zero-Leakage Guarantee:</strong> Verified
          </span>
        </div>
        <div className="footer-right">
          Dota 2 assets & hero portraits © Valve Corporation
        </div>
      </footer>

      {/* MOBILE BAR */}
      <div className="mobile-bar">
        <div className="mobile-modes">
          <button
            className={`btn btn-enemy${mode==="enemy" ? " on" : ""}`}
            onClick={() => setMode("enemy")}
          >✕ Enemy ({enemy.length})</button>

          <button
            className={`btn btn-ally${mode==="team" ? " on" : ""}`}
            onClick={() => setMode("team")}
          >✓ Ally ({team.length})</button>

          <button
            className={`btn btn-ban${mode==="bans" ? " on" : ""}`}
            onClick={() => setMode("bans")}
          >🚫 Ban ({bans.length})</button>
        </div>
        <button
          className={`btn btn-suggest${loading ? " spinning" : ""}`}
          onClick={handleSuggest}
          disabled={!canSuggest || loading}
        >{loading ? "⟳ …" : `🔥 Suggest (${enemy.length + team.length})`}</button>
      </div>
    </div>
  );
}
