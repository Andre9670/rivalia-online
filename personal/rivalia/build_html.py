import json, os, base64, mimetypes

# INLINE=1 -> embed creature sprites as base64 data URIs (self-contained, works in the
# OneDrive sandbox which blocks relative fetches). Default: external creatures/ folder
# (lighter file, needs the folder alongside — for real hosting).
INLINE = os.environ.get('INLINE') == '1'

mapdata = open('map-data.json').read()
imgs = open('img-b64.json').read()
stats = open('stats-all.json').read()
_spr = json.load(open('creatures/_index.json'))   # slug -> filename (e.g. "amazon":"amazon.gif")
pathgrid = open('pathdata-grid.json').read()       # RLE walkability (block=4, 100% walkable)
pathtrans = open('pathdata-trans.json').read()     # [[gx,gy,floor,typecode]] typecode 0=up 1=down 2=both
insights = open('insights-data.json').read()       # loot-value / quests / farm / hunt areas (from build_insights.py)
pkmap = open('pk-map-data.json').read()             # who-kills-who PK graph, Aeternum (from scrape_pk.py + aggregation)
rels = open('relationships.json').read()             # player relationship graph (build_relationships.py): allies/enemies/co-faction
npcs = open('npcs.json').read() if os.path.exists('npcs.json') else '{"npcs":[],"n_with_coords":0,"n_with_offers":0}'  # NPC directory (build_npcs.py); optional, not in weekly cron

# ---- Merge BOSSES/uniques into the searchable set ----------------------------------
# 174 creatures have fixed spawns on the map (map-data.json / hunt-spots.json). The full
# Bestiary (catalog-stats.json) has ~212 — the extra ~39 are bosses/raid/unique/event
# monsters with NO fixed spawn (Ferumbras, Morgaroth, Orshabaal, Demodras…). They can't be
# "found on the map", but Andrea wants their DETAILS searchable. So we append them to DATA
# (flagged boss=1, no spawns) and to STATS, reusing the existing search + stats panel.
_md = json.loads(mapdata)
_stats = json.loads(stats)
_catalog = json.load(open('catalog-stats.json'))
def _slug(n): return n.lower().replace(',', '').replace("'", '').replace('.', '').replace(' ', '-')
_on_map = set(_md['display'])                       # display names already on the map
_boss_names = sorted(n for n in _catalog if n not in _on_map)
_md.setdefault('boss', {})                          # index -> 1 if boss (no spawn)
_next = len(_md['names'])
for bn in _boss_names:
    sl = _slug(bn)
    _md['names'].append(sl)
    _md['display'].append(bn)
    _md['total'].append(0)                          # no spawns
    _md['crFloors'].append([])                      # no floors
    _md['boss'][_next] = 1
    # feed the stats panel: normalize catalog entry into the STATS shape (keyed by slug)
    c = _catalog[bn]
    _stats[sl] = {k: c.get(k) for k in ('health','experience','speed','race','armor','defense',
                                        'summonable','convinceable','pushable','attacks','summons','loot')}
    _next += 1
mapdata = json.dumps(_md)
stats = json.dumps(_stats)

# route walkthrough images: base64-inline for OneDrive (self-contained), path refs otherwise
ROUTE_IMG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             '..', '..', '.claude', 'skills', 'rivalia', 'references', 'routes', 'images')
ROUTE_IMG_DIR = os.path.normpath(ROUTE_IMG_DIR)
route_imgs = {}
if os.path.isdir(ROUTE_IMG_DIR):
    for fn in os.listdir(ROUTE_IMG_DIR):
        if fn == '_urls.json' or fn.startswith('.'):
            continue
        p = os.path.join(ROUTE_IMG_DIR, fn)
        if not os.path.isfile(p):
            continue
        if INLINE:
            mime = 'image/gif' if fn.lower().endswith('.gif') else (mimetypes.guess_type(fn)[0] or 'image/png')
            route_imgs[fn] = f'data:{mime};base64,' + base64.b64encode(open(p, 'rb').read()).decode()
        else:
            route_imgs[fn] = 'routes-images/' + fn
route_imgs_json = json.dumps(route_imgs)
if INLINE:
    _out = {}
    for slug, fn in _spr.items():
        p = os.path.join('creatures', fn)
        if not os.path.exists(p):
            continue
        mime = 'image/gif' if fn.endswith('.gif') else (mimetypes.guess_type(fn)[0] or 'image/png')
        b64 = base64.b64encode(open(p, 'rb').read()).decode()
        _out[slug] = f'data:{mime};base64,{b64}'
    sprites = json.dumps(_out)
    # Self-contained build → this is what gets published via GitHub Pages at /map/index.html.
    # (Was 'rivalia-reverse-map-onedrive.html' on the old OneDrive-based setup.)
    OUTFILE = os.environ.get('OUTFILE') or os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'map', 'index.html'))
else:
    # store filenames; JS prefixes 'creatures/'
    sprites = json.dumps(_spr)
    OUTFILE = os.environ.get('OUTFILE') or 'rivalia-reverse-map.html'

TEMPLATE = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Rivalia — Reverse Hunt Map</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>
  :root{
    --bg:#0d0f14; --panel:#161a23; --panel2:#1e2430; --line:#2a3140;
    --txt:#e6e9ef; --dim:#8b93a4; --acc:#ffb347; --acc2:#6cc6ff; --danger:#ff5d6c; --ok:#5fd38a;
  }
  *{box-sizing:border-box}
  html,body{margin:0;height:100%;font-family:system-ui,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--txt)}
  #app{display:flex;height:100vh;overflow:hidden}
  /* ---------- sidebar ---------- */
  #side{width:330px;flex:0 0 330px;background:var(--panel);border-right:1px solid var(--line);display:flex;flex-direction:column;overflow-y:auto}
  #side h1{font-size:16px;margin:0;padding:14px 16px;border-bottom:1px solid var(--line);letter-spacing:.5px}
  #side h1 small{display:block;color:var(--dim);font-weight:400;font-size:11px;margin-top:3px}
  .sec{padding:12px 16px;border-bottom:1px solid var(--line)}
  .sec label{font-size:11px;text-transform:uppercase;letter-spacing:.6px;color:var(--dim);display:block;margin-bottom:6px}
  #search{width:100%;padding:8px 10px;background:var(--panel2);border:1px solid var(--line);border-radius:8px;color:var(--txt);font-size:13px}
  #clist{flex:1;min-height:140px;overflow-y:auto;padding:4px 8px}
  /* collapsible sections in the sidebar (Tools, How to use): native <details>,
     styled to match .sec/label so opening them costs one click, not permanent space */
  #side details.sec{padding-top:11px;padding-bottom:11px}
  #side details.sec summary{cursor:pointer;list-style:none;display:flex;align-items:center;gap:6px;
    font-size:11px;text-transform:uppercase;letter-spacing:.6px;color:var(--dim)}
  #side details.sec summary::-webkit-details-marker{display:none}
  #side details.sec summary::before{content:"▸";display:inline-block;font-size:9px;color:var(--dim);
    transition:transform .15s}
  #side details.sec[open] summary::before{transform:rotate(90deg)}
  #side details.sec summary small{text-transform:none;letter-spacing:0;font-weight:400;font-size:10.5px}
  #side details.sec summary b{text-transform:none;letter-spacing:0}
  .toolsGrid{display:flex;flex-wrap:wrap;gap:6px;margin-top:9px}
  .toolsGrid .btn{flex:1 1 108px;min-width:100px}
  .crow{display:flex;align-items:center;gap:8px;padding:6px 8px;border-radius:7px;cursor:pointer;font-size:13px}
  .crow:hover{background:var(--panel2)}
  .crow.on{background:#33405a;outline:1px solid var(--acc2)}
  .bosstag{font-size:10px;color:var(--acc);font-weight:700;margin-left:4px}
  .crow.boss .fl,.crow.boss .ct{opacity:.4}
  .crow .nm{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .crow .ct{font-size:11px;color:var(--dim);background:#0d1018;border-radius:10px;padding:1px 7px}
  .crow .fl{font-size:10px;color:var(--acc2)}
  .legend{font-size:11px;color:var(--dim);line-height:1.6}
  .btnrow{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}
  .btn{flex:1;min-width:0;padding:7px;background:var(--panel2);border:1px solid var(--line);border-radius:7px;color:var(--txt);font-size:12px;cursor:pointer}
  .btn:hover{border-color:var(--acc2)}
  a.btn{display:inline-block;text-align:center;text-decoration:none;line-height:normal}
  .btn.on{background:var(--acc);color:#111;border-color:var(--acc);font-weight:600}
  /* ---------- map ---------- */
  #mapwrap{flex:1;position:relative}
  #map{position:absolute;inset:0;background:#05070b}
  /* floor selector */
  #floors{position:absolute;top:12px;left:12px;z-index:500;background:rgba(22,26,35,.94);border:1px solid var(--line);border-radius:10px;padding:6px;display:flex;flex-direction:column-reverse;gap:3px;max-height:88vh;overflow:auto}
  .fbtn{width:54px;padding:5px 4px;background:var(--panel2);border:1px solid var(--line);border-radius:6px;color:var(--dim);font-size:11px;cursor:pointer;text-align:center;position:relative}
  .fbtn:hover{color:var(--txt);border-color:var(--acc2)}
  .fbtn.on{background:var(--acc2);color:#04121d;font-weight:700;border-color:var(--acc2)}
  .fbtn .b{display:block;font-size:9px;opacity:.8}
  .fbtn.empty{opacity:.35}
  /* hover scanner panel */
  #scan{position:absolute;top:12px;right:12px;z-index:500;width:300px;max-height:90vh;overflow:auto;background:rgba(22,26,35,.97);border:1px solid var(--line);border-radius:12px;padding:0;box-shadow:0 8px 30px rgba(0,0,0,.5)}
  #scan .hd{padding:10px 12px;border-bottom:1px solid var(--line);font-size:12px;text-transform:uppercase;letter-spacing:.6px;color:var(--acc);display:flex;justify-content:space-between;align-items:center}
  #scan .bd{padding:6px 6px 10px}
  #scan .empty{padding:18px 12px;color:var(--dim);font-size:12px;text-align:center}
  .srow{display:flex;align-items:center;gap:8px;padding:6px 8px;border-radius:7px;font-size:13px}
  .srow:hover{background:var(--panel2)}
  .srow .dot{width:10px;height:10px;border-radius:50%;flex:0 0 10px}
  .srow .nm{flex:1}
  .srow .meta{font-size:10px;color:var(--dim)}
  .srow .amt{font-size:11px;background:#0d1018;border-radius:9px;padding:1px 7px;color:var(--acc)}
  #scanhint{font-size:10px;color:var(--dim);padding:0 12px 10px;line-height:1.5}
  /* radius control */
  #rad{display:flex;align-items:center;gap:8px;font-size:11px;color:var(--dim);padding:8px 12px;border-top:1px solid var(--line)}
  #rad input{flex:1}
  /* readout */
  #readout{position:absolute;bottom:12px;left:12px;z-index:500;background:rgba(22,26,35,.94);border:1px solid var(--line);border-radius:9px;padding:7px 12px;font-size:12px;color:var(--dim)}
  #readout b{color:var(--txt)}
  .pin{cursor:crosshair}
  .leaflet-container{background:#05070b}
  .cursor-ring{border:2px solid var(--acc);border-radius:50%;pointer-events:none}
  .crisp-img{image-rendering:pixelated;image-rendering:crisp-edges}
  /* floor BELOW: warm/orange tint, bleeding up through current */
  .ghost-below{filter:sepia(1) saturate(2.2) hue-rotate(-18deg) brightness(.82)}
  /* floor ABOVE: cool/cyan tint, translucent veil on top */
  .ghost-above{filter:sepia(1) saturate(2.4) hue-rotate(160deg) brightness(1.05)}
  /* ghost overlay control */
  #ghostbox{position:absolute;bottom:48px;left:12px;z-index:500;width:230px;background:rgba(22,26,35,.94);border:1px solid var(--line);border-radius:10px;padding:8px}
  #ghostbox .glegend{font-size:10.5px;color:var(--dim);margin-top:7px;display:flex;flex-direction:column;gap:3px}
  #ghostbox .glegend i.gd{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:5px;vertical-align:middle}
  #ghostToggle.off{background:var(--panel2);color:var(--dim)}
  /* ---------- stats panel ---------- */
  #stats{position:absolute;bottom:12px;right:12px;z-index:600;width:300px;max-height:62vh;overflow:auto;
     background:rgba(20,24,33,.985);border:1px solid var(--line);border-radius:12px;box-shadow:0 8px 30px rgba(0,0,0,.6);display:none}
  #stats.show{display:block}
  #stats .shd{position:sticky;top:0;background:linear-gradient(180deg,#222b3a,#1a212c);padding:11px 12px;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:9px}
  #stats .shd .dot{width:14px;height:14px;border-radius:50%;flex:0 0 14px}
  #stats .shd .t{flex:1;font-size:15px;font-weight:700}
  #stats .shd .x{cursor:pointer;color:var(--dim);font-size:18px;line-height:1;padding:2px 4px}
  #stats .shd .x:hover{color:var(--danger)}
  #stats .sb{padding:10px 12px}
  .stat-grid{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:10px}
  .stat{background:var(--panel2);border:1px solid var(--line);border-radius:8px;padding:6px 9px}
  .stat .k{font-size:9.5px;text-transform:uppercase;letter-spacing:.5px;color:var(--dim)}
  .stat .v{font-size:15px;font-weight:700;margin-top:1px}
  .stat.hp .v{color:var(--ok)} .stat.xp .v{color:var(--acc)}
  .sblock{margin:9px 0}
  .sblock .h{font-size:10px;text-transform:uppercase;letter-spacing:.6px;color:var(--acc2);margin-bottom:4px}
  .chip{display:inline-block;background:#0d1018;border:1px solid var(--line);border-radius:20px;padding:2px 9px;font-size:11px;margin:2px 3px 2px 0}
  .chip.imm{border-color:#3a5a7a;color:#9fd0ff}
  .chip.atk{border-color:#7a3a3a;color:#ffb0b0}
  .loot-list{font-size:12px;line-height:1.7;color:var(--txt)}
  .flags{font-size:11px;color:var(--dim);margin-top:6px}
  .flags b{color:var(--txt)}
  .nostat{padding:14px 12px;font-size:12px;color:var(--dim);line-height:1.6}
  /* ---------- creature sprites ---------- */
  .cspr{image-rendering:pixelated;image-rendering:crisp-edges;flex:0 0 auto;object-fit:contain;vertical-align:middle}
  .crow .cspr,.srow .cspr{background:#0d1018;border-radius:6px;padding:1px}
  /* map marker sprite: colored ring encodes the creature (keeps the color legend) */
  .spr-icon{background:none;border:none}
  .spr-wrap{border-radius:50%;box-shadow:0 0 0 2px var(--c),0 1px 4px rgba(0,0,0,.6);
     background:rgba(10,13,20,.55);display:flex;align-items:center;justify-content:center;overflow:hidden}
  .spr-wrap img{image-rendering:pixelated;image-rendering:crisp-edges;width:100%;height:100%;object-fit:contain}
  .spr-wrap.sel{box-shadow:0 0 0 3px var(--c),0 0 10px var(--c)}
  /* stats-header holder can carry a sprite */
  #stats .shd .dot{overflow:hidden;display:flex;align-items:center;justify-content:center}
  #stats .shd .dot img{image-rendering:pixelated;width:28px;height:28px;object-fit:contain}
  /* ---------- character config ---------- */
  .cfg-grid{display:grid;grid-template-columns:1fr 1fr;gap:6px}
  .cfg-grid label{font-size:10px;text-transform:none;letter-spacing:0;color:var(--dim);display:flex;flex-direction:column;gap:2px}
  .cfg-grid input,.cfg-grid select{background:var(--panel2);border:1px solid var(--line);border-radius:6px;color:var(--txt);font-size:13px;padding:5px 6px;width:100%}
  .cfg-note{font-size:10px;color:var(--dim);line-height:1.5;margin-top:8px}
  .party-toggle{display:flex;gap:6px;margin-bottom:10px}
  .ptab{flex:1;padding:6px;background:var(--panel2);border:1px solid var(--line);border-radius:7px;color:var(--dim);font-size:12px;cursor:pointer}
  .ptab.on{background:var(--acc2);color:#04121d;border-color:var(--acc2);font-weight:700}
  .charform{margin-bottom:10px}
  .cf-title{font-size:11px;font-weight:700;color:var(--acc);margin-bottom:6px;text-transform:uppercase;letter-spacing:.4px}
  #pgSec{background:linear-gradient(180deg,rgba(108,198,255,.08),transparent);border-bottom:2px solid var(--acc2)}
  .pg-hd{display:flex;justify-content:space-between;align-items:center;font-size:14px;font-weight:800;color:var(--txt);margin-bottom:8px}
  .pg-hd small{display:block;color:var(--acc2);font-weight:600;font-size:11px;margin-top:2px}
  .pg-hd button{background:var(--panel2);border:1px solid var(--line);color:var(--txt);border-radius:6px;width:26px;height:26px;cursor:pointer;font-size:13px}
  .voc-label{display:flex;flex-direction:column;gap:2px;font-size:10px;color:var(--dim);margin-bottom:6px}
  .voc-sel{background:#33405a;border:1px solid var(--acc2);border-radius:6px;color:var(--txt);font-size:13px;font-weight:600;padding:5px 6px;width:100%}
  /* ---------- verdict / confidence panel ---------- */
  #verdict{position:absolute;top:12px;right:322px;z-index:600;width:280px;max-height:88vh;overflow:auto;
     background:rgba(20,24,33,.985);border:1px solid var(--line);border-radius:12px;box-shadow:0 8px 30px rgba(0,0,0,.6);display:none}
  #verdict.show{display:block}
  #verdict .hd{position:sticky;top:0;background:linear-gradient(180deg,#222b3a,#1a212c);padding:10px 12px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;font-size:12px;text-transform:uppercase;letter-spacing:.6px;color:var(--acc)}
  #verdict .hd button{background:none;border:none;color:var(--dim);cursor:pointer;font-size:15px}
  #verdict .bd{padding:10px 12px}
  #verdict .empty{color:var(--dim);font-size:12px;text-align:center;padding:14px 4px;line-height:1.6}
  .vbadge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:700;letter-spacing:.3px}
  .vbadge.ok{background:rgba(95,211,138,.18);color:var(--ok);border:1px solid #2e6b48}
  .vbadge.warn{background:rgba(255,179,71,.16);color:var(--acc);border:1px solid #7a5a24}
  .vbadge.bad{background:rgba(255,93,108,.16);color:var(--danger);border:1px solid #7a2e36}
  .vhead{display:flex;align-items:center;gap:9px;margin-bottom:8px}
  .vhead img{image-rendering:pixelated;width:30px;height:30px;background:#0d1018;border-radius:7px;flex:0 0 30px;object-fit:contain}
  .vhead .vn{font-size:14px;font-weight:700;flex:1}
  .vbar{height:8px;border-radius:6px;background:#0d1018;overflow:hidden;margin:6px 0 10px}
  .vbar>i{display:block;height:100%}
  .vbar>i.ok{background:var(--ok)} .vbar>i.warn{background:var(--acc)} .vbar>i.bad{background:var(--danger)}
  .vmetrics{display:grid;grid-template-columns:1fr 1fr;gap:5px;margin-bottom:8px}
  .vmetrics .vm{background:var(--panel2);border:1px solid var(--line);border-radius:7px;padding:5px 7px}
  .vmetrics .vm .k{font-size:9px;text-transform:uppercase;letter-spacing:.4px;color:var(--dim)}
  .vmetrics .vm .v{font-size:13px;font-weight:700;margin-top:1px}
  .vnotes{font-size:11px;color:var(--acc2);line-height:1.6}
  .vnotes li{margin-left:-8px}
  .vzrow{display:flex;align-items:center;gap:7px;padding:5px 6px;border-radius:7px;font-size:12px;border-bottom:1px solid #222937}
  .vzrow img{image-rendering:pixelated;width:22px;height:22px;flex:0 0 22px;object-fit:contain;background:#0d1018;border-radius:5px}
  .vzrow .zn{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .vzrow .zs{font-size:10px;font-weight:700;padding:1px 6px;border-radius:10px}
  .vzrow .zs.ok{color:var(--ok)} .vzrow .zs.warn{color:var(--acc)} .vzrow .zs.bad{color:var(--danger)}
  .vsummary{background:var(--panel2);border:1px solid var(--line);border-radius:8px;padding:8px 10px;margin-bottom:10px;text-align:center}
  .vsummary .big{font-size:22px;font-weight:800}
  .pgrow{display:flex;align-items:center;gap:6px;flex-wrap:wrap;padding:4px 0;border-bottom:1px solid #222937;font-size:11px}
  .pgtag{font-weight:700;color:var(--acc2);flex:1;min-width:80px}
  .pgm{background:#0d1018;border-radius:9px;padding:1px 7px;color:var(--dim)}
  .pgm.pg-ok{color:var(--ok)} .pgm.pg-warn{color:var(--acc)} .pgm.pg-bad{color:var(--danger);font-weight:700}
  /* ---------- route / how-to-get-there ---------- */
  .route-pin,.route-tr{background:none;border:none}
  .rpin{width:22px;height:22px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:12px;color:#04121d;box-shadow:0 1px 5px rgba(0,0,0,.6)}
  .rpin.start{background:#5fd38a} .rpin.goal{background:#ffb347}
  .rtr{width:24px;height:24px;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;box-shadow:0 1px 5px rgba(0,0,0,.6)}
  .rtr.up{background:#6cc6ff;color:#04121d} .rtr.down{background:#ff9d3d;color:#04121d}
  .rsteps{margin:8px 0 4px;padding-left:20px;font-size:12px;line-height:1.7;color:var(--txt)}
  .rsteps li{margin-bottom:3px}
  /* ---------- insights modal ---------- */
  .ins-modal{position:fixed;inset:0;background:rgba(4,8,14,.72);z-index:2000;display:none;align-items:center;justify-content:center}
  .ins-modal.show{display:flex}
  .ins-card{width:min(760px,92vw);max-height:86vh;background:var(--panel);border:1px solid var(--line);border-radius:14px;display:flex;flex-direction:column;box-shadow:0 12px 48px rgba(0,0,0,.6)}
  .ins-hd{display:flex;justify-content:space-between;align-items:center;padding:13px 16px;border-bottom:1px solid var(--line);font-size:16px;font-weight:700}
  .ins-hd small{color:var(--dim);font-weight:400;font-size:12px;margin-left:6px}
  .ins-hd button{background:var(--panel2);border:1px solid var(--line);color:var(--txt);border-radius:7px;width:28px;height:28px;cursor:pointer;font-size:14px}
  .ins-tabs{display:flex;gap:6px;padding:10px 16px 0}
  .itab{flex:1;padding:8px;background:var(--panel2);border:1px solid var(--line);border-radius:8px;color:var(--dim);font-size:13px;cursor:pointer;font-weight:600}
  .itab.on{background:var(--acc2);color:#04121d;border-color:var(--acc2)}
  .ins-body{overflow-y:auto;padding:12px 16px;flex:1}
  .ins-search{width:100%;padding:8px 10px;margin-bottom:8px;background:var(--panel2);border:1px solid var(--line);border-radius:8px;color:var(--txt);font-size:13px;position:sticky;top:0}
  .ins-subtabs{display:flex;gap:5px;margin-bottom:10px}
  .isub{flex:1;padding:6px;background:var(--panel2);border:1px solid var(--line);border-radius:7px;color:var(--dim);font-size:11.5px;cursor:pointer;font-weight:600}
  .isub.on{background:#33405a;color:#fff;border-color:var(--acc2)}
  .ins-check{display:flex;align-items:center;gap:7px;font-size:12px;color:var(--dim);margin-bottom:10px;cursor:pointer}
  .ins-check input{width:15px;height:15px;cursor:pointer}
  .qflag{display:inline-block;font-size:10.5px;padding:1px 7px;border-radius:9px;margin-top:3px;font-weight:600}
  .qflag.ok{background:rgba(95,211,138,.18);color:var(--ok);border:1px solid rgba(95,211,138,.4)}
  .qflag.no{background:rgba(139,147,164,.15);color:var(--dim);border:1px solid var(--line)}
  .mobchip{display:inline-block;background:var(--panel2);border:1px solid var(--line);border-radius:12px;padding:2px 9px;margin:2px 3px 2px 0;font-size:11.5px;cursor:pointer;color:var(--txt);white-space:nowrap}
  .mobchip:hover{background:#33405a;border-color:var(--acc2);color:#fff}
  .mobchip small{color:var(--dim)}
  .vdot{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--vc);margin-right:5px;vertical-align:middle;box-shadow:0 0 0 1px rgba(0,0,0,.4)}
  .ins-note{padding:9px 16px;border-top:1px solid var(--line);font-size:10.5px;color:var(--dim);line-height:1.5}
  .pktab{flex:1;padding:8px;background:var(--panel2);border:1px solid var(--line);border-radius:8px;color:var(--dim);font-size:12.5px;cursor:pointer;font-weight:600}
  .pktab.on{background:var(--acc2);color:#04121d;border-color:var(--acc2)}
  .reltab{flex:1;padding:8px;background:var(--panel2);border:1px solid var(--line);border-radius:8px;color:var(--dim);font-size:12.5px;cursor:pointer;font-weight:600;opacity:.45}
  .reltab.on{opacity:1}
  .ptab{flex:1;padding:8px;background:var(--panel2);border:1px solid var(--line);border-radius:8px;color:var(--dim);font-size:13px;cursor:pointer;font-weight:600}
  .ptab.on{background:var(--acc2);color:#04121d;border-color:var(--acc2)}
  .tktab{flex:1;padding:8px;background:var(--panel2);border:1px solid var(--line);border-radius:8px;color:var(--dim);font-size:12.5px;cursor:pointer;font-weight:600}
  .tktab.on{background:var(--acc2);color:#04121d;border-color:var(--acc2)}
  .btn-sec{margin:11px 0 2px;font-size:10.5px;font-weight:700;letter-spacing:.7px;text-transform:uppercase;color:var(--dim)}
  #npcBody .npc-city{margin-bottom:6px} #npcBody .npc-city>summary{cursor:pointer;padding:5px 2px;font-size:13px;position:sticky;top:0;background:var(--panel);z-index:2}
  #npcBody .npc-row{padding:5px 0 6px 10px;border-bottom:1px solid #222937}
  #npcBody .npc-name{color:var(--txt);font-weight:600}
  #npcBody a.npc-web{border-bottom:none;font-size:12px;margin-left:5px;opacity:.7}
  #npcBody .npc-go{background:var(--panel2);border:1px solid var(--line);border-radius:6px;cursor:pointer;font-size:12px;padding:1px 6px;margin-left:4px}
  #npcBody .trd,#pkBody .trd{margin-top:3px} #npcBody .trd summary{cursor:pointer;color:var(--dim);font-size:11.5px}
  #npcBody .trd-tbl{width:100%;border-collapse:collapse;font-size:11.5px;margin-top:3px} #npcBody .trd-tbl th{color:var(--dim);text-align:left;font-weight:600;padding:2px 6px} #npcBody .trd-tbl td{padding:2px 6px;border-top:1px solid #222937} #npcBody .trd-tbl .tn{text-align:right}
  .npc-pin{background:none} .npcpin{font-size:16px;filter:drop-shadow(0 1px 2px #000);cursor:pointer}
  #relBody .relnode text{pointer-events:none}
  #relBody .relnode:hover circle{stroke-width:3}
  #pkBody table{width:100%;border-collapse:collapse;font-size:12.5px}
  #pkBody th,#pkBody td{padding:6px 9px;text-align:left;border-bottom:1px solid var(--line);white-space:nowrap}
  #pkBody th{color:var(--dim);font-size:10px;text-transform:uppercase;letter-spacing:.04em;cursor:pointer;user-select:none;position:sticky;top:0;background:var(--panel)}
  #pkBody th.sorted::after{content:" ▼";color:var(--acc2)} #pkBody th.sorted.asc::after{content:" ▲"}
  #pkBody td.n{text-align:right;font-variant-numeric:tabular-nums;font-family:ui-monospace,Menlo,monospace}
  #pkBody a{color:var(--txt);text-decoration:none;border-bottom:1px dotted var(--dim)} #pkBody a:hover{color:var(--acc2)}
  #relBody a,#relSuggest a,#npcBody a{color:var(--acc2);text-decoration:none;border-bottom:1px dotted var(--dim)} #relBody a:hover,#relSuggest a:hover,#npcBody a:hover{color:var(--txt)}
  #pkBody tr.prow:hover{background:var(--panel2)}
  #pkBody .u{color:#ff5d6c;font-weight:700}
  #pkBody .pkb{display:inline-block;padding:1px 7px;border-radius:11px;font-size:10.5px;font-weight:700}
  #pkBody .pkb.s{background:rgba(255,45,85,.2);color:#ff2d55;border:1px solid rgba(255,45,85,.5)}
  #pkBody .pkb.a{background:rgba(255,93,108,.16);color:#ff5d6c;border:1px solid rgba(255,93,108,.4)}
  #pkBody .pkb.o{background:rgba(255,209,102,.14);color:#ffd166;border:1px solid rgba(255,209,102,.35)}
  #pkBody .pkb.g{background:rgba(139,147,164,.14);color:var(--dim);border:1px solid rgba(139,147,164,.3)}
  #pkBody .exp{cursor:pointer;color:var(--dim);width:16px;display:inline-block;text-align:center}
  #pkBody .det td{background:#10131b;padding:8px 14px}
  #pkBody .vrow{display:flex;gap:10px;font-size:11.5px;color:var(--dim);align-items:center;padding:1px 0}
  #pkBody .vrow .vn{color:var(--txt);min-width:150px} #pkBody .vrow .vu{color:#ff5d6c;font-weight:700;font-size:10px}
  #pkBody .dscore{font-weight:700}
  table.itab-tbl{width:100%;border-collapse:collapse;font-size:12.5px}
  table.itab-tbl th{text-align:left;color:var(--dim);font-weight:600;padding:5px 7px;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--panel)}
  table.itab-tbl td{padding:5px 7px;border-bottom:1px solid #222937}
  table.itab-tbl tr:hover td{background:var(--panel2)}
  .gp{color:var(--acc);font-weight:700;white-space:nowrap}
  .eps{color:var(--ok);font-weight:700}
  /* loot-value trader breakdown (all NPCs per item, with city) */
  details.trd>summary{cursor:pointer;list-style:none;white-space:nowrap}
  details.trd>summary::-webkit-details-marker{display:none}
  .trdn{color:var(--acc2);font-size:11px;margin-left:4px}
  details.trd[open]>summary .trdn{color:var(--dim)}
  table.trd-tbl{width:100%;border-collapse:collapse;margin:6px 0 2px;font-size:11.5px;background:var(--panel2);border-radius:6px;overflow:hidden}
  table.trd-tbl th{text-align:left;color:var(--dim);font-weight:600;padding:3px 8px;border-bottom:1px solid var(--line)}
  table.trd-tbl td{padding:3px 8px;border-bottom:1px solid #222937}
  table.trd-tbl tr:last-child td{border-bottom:none}
  .trd-tbl .tc{color:var(--dim)} .trd-tbl .tn{text-align:right;font-variant-numeric:tabular-nums}
  .trd-tbl .tsell{color:var(--acc);font-weight:600}
  .flyto{cursor:pointer;color:var(--acc2);text-decoration:underline;font-size:11px}
  .qref{color:var(--acc2);text-decoration:none} .qref:hover{text-decoration:underline}
  /* hunt-area zone overlay */
  .area-pin{background:none;border:none}
  .azlabel{padding:2px 8px;border-radius:13px;background:var(--ac);color:#04121d;font-weight:800;font-size:11px;white-space:nowrap;box-shadow:0 1px 6px rgba(0,0,0,.7);border:1.5px solid #04121d;cursor:pointer;transform:translateY(-2px)}
  .area-zone{cursor:pointer}
  .area-popup .leaflet-popup-content-wrapper{background:var(--panel);color:var(--txt);border:1px solid var(--line);border-radius:10px}
  .area-popup .leaflet-popup-tip{background:var(--panel)}
  .area-pop .ap-hd{font-weight:800;font-size:14px;margin-bottom:4px}
  .area-pop .ap-meta{font-size:11.5px;color:var(--dim);margin-bottom:3px}
  .area-pop .ap-crs{margin-top:6px;line-height:1.9}
  .area-pop .ap-note{font-size:10.5px;color:var(--dim);margin-top:6px}
  .area-pop .ap-route{margin-top:7px}
  .ropenpop,.ropen{cursor:pointer;color:var(--acc2);text-decoration:underline;font-weight:600}
  /* routes tab */
  .route-back{cursor:pointer;color:var(--acc2);font-weight:600;margin-bottom:8px;font-size:13px}
  .route-detail h3{margin:0 0 6px;font-size:16px}
  .route-steps{margin:10px 0 4px;padding-left:20px;font-size:13px;line-height:1.6}
  .route-steps li{margin-bottom:10px}
  .rtag{display:inline-block;background:var(--panel2);border:1px solid var(--line);border-radius:6px;padding:0 6px;font-size:10.5px;font-weight:700;color:var(--acc2);margin-right:4px}
  .rtag.dir{color:var(--acc)}
  .rhz{font-size:11px;color:var(--danger);margin-top:2px}
  .rimg{display:block;max-width:100%;margin:6px 0;border:1px solid var(--line);border-radius:6px;image-rendering:pixelated;background:#000}
  .route-ret{background:var(--panel2);border:1px solid var(--line);border-radius:8px;padding:8px 10px;font-size:12px;margin-top:8px}
  /* city landmarks */
  .city-pin{background:none;border:none}
  .citylabel{font-size:13px;font-weight:800;color:#fff;text-shadow:0 0 3px #000,0 0 6px #000,0 1px 2px #000;white-space:nowrap;letter-spacing:.3px;pointer-events:none;opacity:.92}
  .chest-pin{background:none;border:none}
  .chestpin{font-size:15px;cursor:pointer;filter:drop-shadow(0 1px 2px #000);line-height:1}

  /* DESKTOP-neutral: the creature-sheet wrapper is transparent (children float exactly as
     before) and every mobile-only shell element is hidden. */
  #crSheet{display:contents}
  #crSheetHd,#crFab,#crBar,#mnav,#msheet,#mtop,#mfloor{display:none}

  /* =========================================================================
     MOBILE APP SHELL (≤820px) — designed as a native map app, not a squeezed
     desktop sidebar:
       · the MAP is the canvas, full-screen, nothing permanent on top of it
       · a bottom TAB BAR (thumb zone) exposes the whole menu at 1 tap
       · ONE bottom sheet with 4 detents (closed · peek · half · full), real
         drag-to-resize; every tab renders into it
       · map LAYER CHIPS live on the map (top, h-scroll) because they change
         the map — not buried in a menu
       · a FLOOR PILL (right, thumb-reachable) replaces the 16-button column;
         tapping the number opens a compact floor grid
     The desktop DOM/logic is untouched: on boot the shell MOVES the stateful
     panels (search, results, verdict, stats, My Char) into the sheet and
     PROXIES the toggle/modal buttons, so there is no duplicated logic.
     ========================================================================= */
  @media (max-width:820px){
    :root{--navh:56px;--sbi:env(safe-area-inset-bottom);--sti:env(safe-area-inset-top)}
    html,body{height:100%;overflow:hidden;overscroll-behavior:none}
    #app{display:block;height:100dvh;overflow:hidden}
    #mapwrap{position:fixed;inset:0;width:100vw;height:100dvh}
    /* mouse-only chrome + the old mobile chrome this shell replaces */
    #scan,#ghostbox,#crFab,#crBar,#crSheetHd{display:none!important}
    #side{display:none!important}          /* emptied on boot; kept for proxy targets */
    #crSheet{display:contents}
    #readout{font-size:10.5px;padding:5px 9px;left:10px;z-index:900;
      bottom:calc(var(--navh) + var(--sbi) + 10px);background:rgba(22,26,35,.86)}

    /* ---------- map layer chips (top, horizontally scrollable) ---------- */
    #mtop{display:flex;gap:7px;position:fixed;left:0;right:0;z-index:1100;
      top:calc(var(--sti) + 8px);padding:0 10px 2px;overflow-x:auto;
      scrollbar-width:none;-webkit-overflow-scrolling:touch}
    #mtop::-webkit-scrollbar{display:none}
    .mchip{flex:0 0 auto;display:flex;align-items:center;gap:5px;height:36px;padding:0 13px;
      border-radius:18px;background:rgba(22,26,35,.92);border:1px solid var(--line);
      color:var(--txt);font-size:12.5px;font-weight:600;white-space:nowrap;cursor:pointer;
      -webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px);
      box-shadow:0 2px 10px rgba(0,0,0,.4);-webkit-tap-highlight-color:transparent}
    .mchip.on{background:var(--acc);border-color:var(--acc);color:#111}
    .mchip b{font-weight:800;font-size:11px;opacity:.8}

    /* ---------- floor pill + floor grid popover ---------- */
    #mfloor{display:flex;flex-direction:column;align-items:center;gap:2px;position:fixed;
      right:10px;top:50%;transform:translateY(-50%);z-index:1100;padding:4px;
      background:rgba(22,26,35,.92);border:1px solid var(--line);border-radius:22px;
      -webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px);
      box-shadow:0 3px 14px rgba(0,0,0,.45)}
    #mfloor button{background:none;border:none;color:var(--dim);width:42px;height:32px;
      font-size:14px;cursor:pointer;border-radius:16px;padding:0;
      -webkit-tap-highlight-color:transparent}
    #mfNow{height:42px!important;background:var(--panel2)!important;color:var(--acc2)!important;
      font-weight:800;font-size:16px!important;line-height:1.05}
    #mfNow small{display:block;font-size:8.5px;color:var(--dim);font-weight:700;margin-top:1px}
    #floors{display:none;flex-direction:row;flex-wrap:wrap;justify-content:center;gap:6px;
      position:fixed;inset:auto;left:50%;transform:translateX(-50%);
      bottom:calc(var(--navh) + var(--sbi) + 14px);width:min(330px,92vw);max-height:none;
      z-index:1600;padding:11px;border-radius:16px;box-shadow:0 10px 34px rgba(0,0,0,.6)}
    #floors.mopen{display:flex}
    .fbtn{width:66px;height:44px;font-size:13px}

    /* ---------- bottom tab bar: the whole menu, always one tap away ---------- */
    #mnav{display:flex;position:fixed;left:0;right:0;bottom:0;z-index:1500;
      height:calc(var(--navh) + var(--sbi));padding-bottom:var(--sbi);
      background:rgba(18,22,30,.97);border-top:1px solid var(--line);
      -webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px)}
    #mnav button{position:relative;flex:1;background:none;border:none;color:var(--dim);
      display:flex;flex-direction:column;align-items:center;justify-content:center;gap:1px;
      font-size:21px;line-height:1;padding:0;cursor:pointer;
      -webkit-tap-highlight-color:transparent}
    #mnav button i{font-style:normal;font-size:9.5px;font-weight:600;letter-spacing:.2px}
    #mnav button.on{color:var(--acc)}
    #mnav button.on::before{content:"";position:absolute;top:0;width:28px;height:2.5px;
      border-radius:0 0 3px 3px;background:var(--acc)}
    #mnav button .mdot{position:absolute;top:6px;right:calc(50% - 17px);width:7px;height:7px;
      border-radius:50%;background:var(--acc2);display:none}
    #mnav button.act .mdot{display:block}

    /* ---------- THE sheet ---------- */
    #msheet{display:flex;flex-direction:column;position:fixed;left:0;right:0;
      bottom:calc(var(--navh) + var(--sbi));height:78dvh;z-index:1300;
      background:var(--panel);border-top:1px solid var(--line);border-radius:20px 20px 0 0;
      box-shadow:0 -12px 40px rgba(0,0,0,.6);will-change:transform;
      transform:translateY(100%);transition:transform .32s cubic-bezier(.32,.72,0,1)}
    #msheet.dragging{transition:none}
    #mshGrab{flex:0 0 auto;height:24px;display:flex;align-items:center;justify-content:center;
      touch-action:none;cursor:grab}
    #mshGrab::before{content:"";width:44px;height:4.5px;border-radius:3px;background:#3b4457}
    #mshPeek{flex:0 0 auto;padding:0 14px 11px;touch-action:none}
    #mshBody{flex:1;overflow-y:auto;-webkit-overflow-scrolling:touch;overscroll-behavior:contain;
      padding-bottom:calc(var(--sbi) + 20px)}
    .mpane{display:none}
    .mpane.on{display:block}
    /* the moved sidebar title becomes a plain header inside the "Me" pane */
    #msheet h1{position:static;padding:13px 16px;margin:0;font-size:15px;display:block;
      border-radius:0;border-bottom:1px solid var(--line);cursor:default}
    #msheet h1::before,#msheet h1::after{display:none!important}
    #msheet h1 small{display:block}

    /* peek row: creature card when something is selected, else the pane title */
    .mph{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:1px 2px}
    .mph .mpht{font-size:15.5px;font-weight:800}
    .mph .mpht small{display:block;color:var(--dim);font-weight:500;font-size:11.5px;margin-top:2px}
    .mph .mphc{color:var(--dim);font-size:13px}
    .mpk{display:flex;align-items:center;gap:10px;background:var(--panel2);
      border:1px solid var(--line);border-radius:14px;padding:9px 11px;cursor:pointer}
    .mpk>img{width:36px;height:36px;flex:0 0 36px;object-fit:contain;background:#0d1018;
      border-radius:9px;image-rendering:pixelated}
    .mpk .mpn{flex:1;min-width:0}
    .mpk .mpn .mpnt{font-size:14.5px;font-weight:800;display:flex;align-items:center;gap:6px}
    .mpk .mpn .mpns{font-size:11.5px;color:var(--dim);margin-top:3px;white-space:nowrap;
      overflow:hidden;text-overflow:ellipsis}
    .mpk .mpx{flex:0 0 auto;width:36px;height:36px;border-radius:10px;background:var(--panel);
      border:1px solid var(--line);color:var(--txt);font-size:15px;cursor:pointer}
    .mfchip{display:inline-block;background:var(--panel);border:1px solid var(--line);
      border-radius:9px;padding:2px 9px;margin:0 4px 0 0;font-size:11px;font-weight:700;
      color:var(--acc2);cursor:pointer}
    .mfchip.cur{background:var(--acc2);border-color:var(--acc2);color:#04121d}

    /* sticky search inside the Creatures pane */
    .msearch{position:sticky;top:0;z-index:4;background:var(--panel);padding:4px 14px 10px;
      display:flex;align-items:center;gap:9px}
    .msearch::before{content:"🔍";font-size:15px;opacity:.65}
    #search{min-height:46px;font-size:16px;border-radius:12px;padding:10px 12px}
    #clist{flex:none;max-height:none;overflow:visible;padding:0 8px 6px}
    #clist:empty{display:none}
    .crow{padding:11px 8px;gap:10px}
    .crow .nm{font-size:14px}

    /* big list rows for the menu panes (proxy the real sidebar buttons) */
    .msec{padding:14px 16px 6px;font-size:10.5px;font-weight:800;letter-spacing:.7px;
      text-transform:uppercase;color:var(--dim)}
    .mrow{display:flex;align-items:center;gap:12px;width:100%;text-align:left;background:none;
      border:none;border-bottom:1px solid #202634;color:var(--txt);padding:14px 16px;
      font-size:14.5px;cursor:pointer;-webkit-tap-highlight-color:transparent}
    .mrow:active{background:var(--panel2)}
    .mrow .mri{flex:0 0 26px;font-size:20px;text-align:center}
    .mrow .mrt{flex:1;min-width:0;font-weight:600}
    .mrow .mrt small{display:block;color:var(--dim);font-size:11.5px;font-weight:400;
      margin-top:3px;white-space:normal;line-height:1.45}
    .mrow .mrs{flex:0 0 auto;font-size:11px;font-weight:800;padding:4px 10px;border-radius:11px;
      background:var(--panel2);color:var(--dim);border:1px solid var(--line)}
    .mrow .mrs.on{background:var(--acc);color:#111;border-color:var(--acc)}

    /* creature detail inside the pane: the two floating panels become stacked sections */
    #mcrDetail{border-bottom:1px solid var(--line)}
    #mcrDetail #verdict,#mcrDetail #stats{position:static!important;width:auto!important;
      max-width:none!important;max-height:none!important;inset:auto;border:none;border-radius:0;
      box-shadow:none;background:none;overflow:visible;display:none}
    #mcrDetail #verdict.show,#mcrDetail #stats.show{display:block!important}
    #mcrDetail #verdict .hd,#mcrDetail #stats .shd{background:none;border-bottom:none;position:static}
    #mcrDetail #vClose,#mcrDetail #st-close{display:none}

    /* roomier controls everywhere on touch */
    .sec{padding:14px 16px}
    .btnrow{gap:8px;margin-top:10px}
    .btn,.itab,.pktab,.ptab,.reltab{min-height:44px;font-size:13px}
    #pkQ,input[type=text],input[type=search]{min-height:44px;font-size:16px}  /* 16px stops iOS zoom */
    .cfg-note,.ins-note{font-size:11px}
    .vmetrics,.stat-grid{grid-template-columns:1fr 1fr}

    /* ---- modals: full-bleed sheets above the tab bar ---- */
    .ins-modal{align-items:flex-end}
    .ins-card{width:100vw!important;max-width:100vw;max-height:94dvh;border-radius:20px 20px 0 0;
      padding-bottom:var(--sbi)}
    .ins-hd{position:sticky;top:0;z-index:6;padding:16px 16px 13px}
    .ins-hd::before{content:"";position:absolute;top:6px;left:50%;transform:translateX(-50%);
      width:44px;height:4.5px;border-radius:3px;background:#3b4457}
    .ins-hd button{width:36px;height:36px;font-size:16px}
    .ins-tabs{flex-wrap:wrap;position:sticky;top:56px;z-index:5;background:var(--panel);padding:10px 12px 8px}
    .itab,.pktab,.reltab,.tktab{min-height:44px;font-size:12px;flex:1 1 30%}
    .ptab{min-height:44px;font-size:13px;flex:1 1 45%}
    /* PK table: drop the lower-value columns so the rest is readable on a phone
       (Voc, PvP deaths, Avg victim Lv) */
    #pkBody th:nth-child(4),#pkBody td:nth-child(4),
    #pkBody th:nth-child(8),#pkBody td:nth-child(8),
    #pkBody th:nth-child(9),#pkBody td:nth-child(9){display:none}
    #pkBody th,#pkBody td{padding:9px 7px;font-size:12.5px}
    #pkBody .exp{font-size:15px}
  }
</style>
</head>
<body>
<div id="app">
  <aside id="side">
    <h1>🗺️ Rivalia Reverse Hunt Map<small id="sub"></small></h1>
    <div class="sec" id="pgSec">
      <div class="pg-hd">
        <span>⚔️ My Char <small id="pgSummary"></small></span>
        <button id="cfgToggle" title="Show/hide fields">▸</button>
      </div>
      <div id="cfgBox" style="display:none">
        <div class="party-toggle">
          <button class="ptab on" id="ptSolo" data-n="1">👤 Solo</button>
          <button class="ptab" id="ptDuo" data-n="2">👥 Duo</button>
          <button class="ptab" id="ptTrio" data-n="3">👥 Trio</button>
        </div>
        <div id="charForms"></div>
        <div class="cfg-note">Damage formulas are <b>official</b> (Rivalia calculator). Turn-time, averages and mana sustainability are <b>tunable estimates</b> (Exura to verify in-game). Monster damage split: tank 65% / offhand 35% (duo), 50/30/20 (trio). <b>All insights (farmable/risky/lethal) start from here.</b></div>
      </div>
    </div>
    <div class="sec">
      <label>Search creature (highlights where it spawns)</label>
      <input id="search" placeholder="e.g. demon, cyclops, ghoul…" autocomplete="off"/>
      <div class="btnrow">
        <button class="btn on" id="sprMode" title="Auto: icons when you zoom or select a monster · Always: icons everywhere (heavier) · Off: dots only">🖼️ Icons: Auto</button>
        <button class="btn" id="toAll">All monsters</button>
        <button class="btn" id="clearSel">Show all</button>
      </div>
    </div>
    <details class="sec" id="toolsDetails" open>
      <summary>🧰 Tools <small>PK map, hunt areas, NPCs, insights…</small></summary>
      <div class="toolsGrid">
        <button class="btn" id="pkMapBtn" title="PK Map (Aeternum): who kills whom, unjustified flag and threat class, from player death profiles. Shared search with Relations.">☠️ PK Map</button>
        <button class="btn" id="relBtn" title="Relations (Aeternum): a player's allies (same guild or co-kill together), reciprocal enemies and co-faction (shared victims), as a star graph. Shared search with PK Map.">🕸️ Relations</button>
        <button class="btn" id="insBtn" title="Loot-value, doable quests and where to farm items — computed on your data">💎 Insights</button>
        <button class="btn" id="areaBtn" title="Highlight TibiaWiki 7.4 hunting places on the map as zones colored by efficiency (xp/hit). Click a zone for its card + creatures">🎯 Hunt areas: Off</button>
        <button class="btn" id="taskBtn" title="Weekly-task helper: YOU pick a task (a monster) from the full list, one at a time, and it shows the best place & way to do it — densest floor / best hunting area, farmability for your char, with Show-on-map and route.">📋 Task Helper</button>
        <button class="btn" id="npcBtn" title="Rivalia NPC directory (355): by city, with what they buy/sell and at what price (authoritative Rivalia data). 📍 = approximate position from Tibiantis 7.7.">🧙 Directory</button>
        <button class="btn" id="npcPinBtn" title="Show NPCs as pins on the map (APPROXIMATE position, ref Tibiantis 7.7 — verify in-game). Pins on the current floor, popup with offers.">📍 NPC: Off</button>
        <button class="btn" id="routeBtn" title="Find how to reach a point: click the START then the DESTINATION on the map">🧭 How to get there</button>
        <button class="btn on" id="cityBtn" title="Show city names (Thais, Carlin, Venore…) on the map as landmarks">🏰 Cities: On</button>
        <button class="btn" id="chestBtn" title="Show Rivalia's 222 reward chests on the map (pins on the current floor, popup with loot)">🎁 Chest: Off</button>
      </div>
    </details>
    <div id="clist"></div>
    <details class="sec legend" id="legendDetails">
      <summary><b style="color:var(--txt)">❔ How to use</b></summary>
      <div style="margin-top:8px">
      • Move the mouse over the map → the right panel lists <b>ALL</b> monsters within the cursor radius.<br>
      • Click a creature to highlight it on every floor it appears on.<br>
      • Change floor with the numbered column (left). 7 = ground level.<br>
      • <span style="color:var(--danger)">Red</span> in the scanner = the monster is also on a floor other than the one you're viewing.<br>
      • <b>Floors above/below</b>: see <b>the real map</b> of the floor above (<span style="color:#6cc6ff">cyan</span> veil, above) and below (<span style="color:#ff9d3d">orange</span>, showing through the current floor) → understand stairs, holes and corridors to move between levels. Adjust "Floor opacity" to see below better.
      </div>
    </details>
  </aside>
  <div id="insModal" class="ins-modal">
    <div class="ins-card">
      <div class="ins-hd">
        <span>💎 Insights <small id="insSub"></small></span>
        <button id="insClose" title="close">✕</button>
      </div>
      <div class="ins-tabs">
        <button class="itab on" data-t="areas">🎯 Hunt areas</button>
        <button class="itab" data-t="loot">💰 Loot-value</button>
        <button class="itab" data-t="quests">📜 Quest</button>
        <button class="itab" data-t="farm">🔨 Where to farm</button>
        <button class="itab" data-t="routes">🧭 Routes</button>
      </div>
      <div class="ins-body" id="insBody"></div>
      <div class="ins-note">Creature/spawn numbers = <b>real Rivalia data</b>. gp values = <b>real NPC sell price</b> (rivaliaonline.com/items.php). Quests from TibiaWiki 7.4: reward/level <b>to confirm in-game</b>. Click 🎯 on an area to fly there on the map.</div>
    </div>
  </div>
  <div id="playerModal" class="ins-modal">
    <div class="ins-card" style="width:min(1080px,95vw)">
      <div class="ins-hd">
        <span>👥 Player — Aeternum <small id="pkSub"></small><small id="relSub" style="display:none"></small></span>
        <button id="playerClose" title="close">✕</button>
      </div>
      <div class="ins-tabs">
        <button class="ptab on" data-pt="pk">☠️ Threat / PK</button>
        <button class="ptab" data-pt="rel">🕸️ Relations</button>
      </div>
      <div style="padding:8px 16px 0"><input type="search" id="plQ" placeholder="Search killer or victim…" style="width:100%;background:var(--panel2);border:1px solid var(--line);color:var(--txt);border-radius:8px;padding:8px 11px;font-size:13px;outline:none" autocomplete="off"></div>
      <div class="ins-tabs" id="pkChips" style="padding-top:8px">
        <button class="pktab on" data-f="all">All</button>
        <button class="pktab" data-f="PK / Serial">☠️ Serial</button>
        <button class="pktab" data-f="PK / Assassin">🔴 Assassin</button>
        <button class="pktab" data-f="Occasional PK">🟡 Occasional</button>
        <button class="pktab" data-f="Guild-war / justified">⚪ Guild-war</button>
      </div>
      <div class="ins-tabs" id="relChips" style="padding-top:8px;display:none">
        <button class="reltab on" data-e="ally">🟩 Allies</button>
        <button class="reltab on" data-e="enemy">🟥 Enemies</button>
        <button class="reltab on" data-e="cofaction">🟨 Co-faction</button>
      </div>
      <div id="relSuggest" style="padding:6px 16px 0;font-size:12px;color:var(--dim);display:none"></div>
      <div class="ins-body" id="pkBody"></div>
      <div class="ins-body" id="relBody" style="min-height:420px;display:none"></div>
      <div class="ins-note" id="pkNote"><b>Classes:</b> ☠️ <b>Serial</b> = 5+ unjustified · 🔴 <b>Assassin</b> = 2-4 · 🟡 <b>Occasional</b> = 1 · ⚪ <b>Guild-war</b> = 0 unjustified (PvP among peers). <b>Danger</b> weighs unjustified kills + the level advantage over victims. From <b id="pkNprof"></b> profiles (~3-month history, Aeternum). Click ▸ for the victims.</div>
      <div class="ins-note" id="relNote" style="display:none"><b>🟩 Ally</b> = same guild or co-kill together · <b>🟥 Enemy</b> = reciprocal kills · <b>🟨 Co-faction</b> = ≥3 shared victims. Line thickness = bond strength. Click a player in the graph to re-center. <b id="relNplayers"></b> connected players. Renames already merged.</div>
    </div>
  </div>
  <div id="npcModal" class="ins-modal">
    <div class="ins-card" style="width:min(1080px,95vw)">
      <div class="ins-hd">
        <span>🧙 NPC — Rivalia <small id="npcSub"></small></span>
        <button id="npcClose" title="close">✕</button>
      </div>
      <div style="padding:8px 16px 0"><input type="search" id="npcQ" placeholder="Search NPC… (name, city, bought/sold item)" style="width:100%;background:var(--panel2);border:1px solid var(--line);color:var(--txt);border-radius:8px;padding:8px 11px;font-size:13px;outline:none" autocomplete="off"></div>
      <div class="ins-body" id="npcBody"></div>
      <div class="ins-note">Name · city · buy/sell offers = <b>authoritative Rivalia data</b> (npcs.php). 📍 = <b>approximate position</b> (Tibiantis 7.7, geography ≈ 7.4) — <b>verify in-game</b>. <b id="npcNcoord"></b> NPCs with a position.</div>
    </div>
  </div>
  <div id="taskModal" class="ins-modal">
    <div class="ins-card" style="width:min(1080px,95vw)">
      <div class="ins-hd">
        <span>📋 Task Helper <small id="taskSub"></small></span>
        <button id="taskClose" title="close">✕</button>
      </div>
      <div class="ins-tabs" id="taskMode" style="padding-top:10px">
        <button class="tktab on" data-m="mon">⚔️ Kill task</button>
        <button class="tktab" data-m="item">📦 Deliver task</button>
      </div>
      <div style="padding:8px 16px 0"><input type="search" id="taskQ" placeholder="Filter targets… (e.g. cyclops, dragon, minotaur)" style="width:100%;background:var(--panel2);border:1px solid var(--line);color:var(--txt);border-radius:8px;padding:8px 11px;font-size:13px;outline:none" autocomplete="off"></div>
      <div class="ins-body" id="taskBody"></div>
      <div class="ins-note"><b>You</b> pick the weekly task (Rivalia's Task Board is in-game only). Select a target below → for it you get the <b>best spot</b> (densest floor / best hunting area) and a farmability verdict for <b>your char</b> (🟢 farmable · 🟡 risky · 🔴 lethal), plus <b>Show on map</b> and route.</div>
    </div>
  </div>
  <div id="mapwrap">
    <div id="map"></div>
    <button id="crFab" title="Search creature">🐉</button>
    <!-- MOBILE result bar: appears after picking a creature. Map stays visible; tap to expand. -->
    <div id="crBar"><span id="crBarInfo"></span><button id="crBarMore">📊 Stats</button><button id="crBarX" title="deselect">✕</button></div>
    <div id="floors"></div>
    <div id="scan">
      <div class="hd"><span>🎯 Under the cursor</span><span id="scancount">0</span></div>
      <div class="bd" id="scanbody"><div class="empty">Move the mouse over the map…</div></div>
      <div id="rad"><span>Radius</span><input type="range" id="radr" min="5" max="400" value="50"/><span id="radv">50</span></div>
      <div style="padding:0 12px 8px"><button class="btn" id="zoneToggle" style="width:100%" title="On: moving the mouse shows the zone confidence within the radius, updated live">🎯 Zone verdict: Off</button></div>
      <div id="scanhint">The scanner shows every spawn within the radius on the <b>current floor</b>, and flags if the same creature also spawns on nearby floors.</div>
    </div>
    <div id="readout">Floor <b id="ro-floor">7</b> · <b id="ro-spawn">0</b> spawn · coord <b id="ro-xy">–</b></div>
    <div id="ghostbox">
      <div class="btnrow" style="margin-top:0">
        <button class="btn" id="tAbove">▲ Above</button>
        <button class="btn" id="tBelow">▼ Below</button>
      </div>
      <div id="opacityRow" style="display:flex;align-items:center;gap:7px;font-size:10.5px;color:var(--dim);margin-top:7px">
        <span style="width:42px">▼ Below</span><input type="range" id="opac" min="30" max="100" value="78" style="flex:1"><span id="opacv" style="width:32px;text-align:right">78%</span>
      </div>
      <div id="opacityRowUp" style="display:flex;align-items:center;gap:7px;font-size:10.5px;color:var(--dim);margin-top:4px">
        <span style="width:42px">▲ Above</span><input type="range" id="opacUp" min="10" max="100" value="42" style="flex:1"><span id="opacUpv" style="width:32px;text-align:right">42%</span>
      </div>
      <div class="glegend">
        <span><i class="gd" style="background:#6cc6ff"></i> map above (floor ↑, cyan veil)</span>
        <span><i class="gd" style="background:#ff9d3d"></i> map below (floor ↓, shows through)</span>
      </div>
    </div>
    <!-- #crSheet wraps the two creature panels. Desktop: display:contents (children behave
         exactly as before, two floating panels). Mobile: becomes ONE combined bottom sheet. -->
    <div id="crSheet">
      <div id="crSheetHd"><span>🐉 Creature</span><button id="crSheetClose" title="close">✕</button></div>
      <div id="verdict">
        <div class="hd"><span>🛡️ Can I make it?</span><button id="vClose" title="close">✕</button></div>
        <div class="bd" id="verdictbody"><div class="empty">Select a creature or hover over a zone.<br>First set your char's stats (⚔️ My Char).</div></div>
      </div>
      <div id="stats">
        <div class="shd"><span class="dot" id="st-dot"></span><span class="t" id="st-name"></span><span class="x" id="st-close">✕</span></div>
        <div class="sb" id="st-body"></div>
      </div>
    </div>
  </div>
  <!-- ===== MOBILE APP SHELL (hidden on desktop; wired up in the MOBILE SHELL script) =====
       #mtop   = map layer chips  ·  #mfloor = floor stepper pill
       #msheet = the one bottom sheet (peek/half/full)  ·  #mnav = bottom tab bar -->
  <div id="mtop"></div>
  <div id="mfloor">
    <button id="mfUp" title="floor above">▲</button>
    <button id="mfNow" title="pick a floor">7</button>
    <button id="mfDn" title="floor below">▼</button>
  </div>
  <div id="msheet">
    <div id="mshGrab"></div>
    <div id="mshPeek"></div>
    <div id="mshBody">
      <div class="mpane" id="mpCr"></div>
      <div class="mpane" id="mpHunt"></div>
      <div class="mpane" id="mpNpc"></div>
      <div class="mpane" id="mpPl"></div>
      <div class="mpane" id="mpMe"></div>
    </div>
  </div>
  <nav id="mnav">
    <button data-p="cr">🐉<i>Creatures</i><span class="mdot"></span></button>
    <button data-p="hunt">🎯<i>Hunt</i><span class="mdot"></span></button>
    <button data-p="npc">🧙<i>NPC</i><span class="mdot"></span></button>
    <button data-p="pl">👥<i>Players</i><span class="mdot"></span></button>
    <button data-p="me">⚔️<i>My Char</i><span class="mdot"></span></button>
  </nav>
</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const DATA = __MAPDATA__;
const IMGS = __IMGS__;
const STATS = __STATS__;
const SPRITES = __SPRITES__;   // slug -> filename in creatures/
const PATHGRID = __PATHGRID__; // RLE walkability {block,gw,gh,w,h,floors:[[runs]]}
const PATHTRANS = __PATHTRANS__; // [[gx,gy,floor,typecode]] 0=up 1=down 2=both
const INS = __INSIGHTS__;       // insights: {char,avg_hit,max_hit,loot_value,quests,farm,areas,cities,routes}
const PKMAP = __PKMAP__;        // PK graph: {n_profiles_scanned,players:{name->{...,victims}}}
const RELS = __RELS__;          // relationship graph: {players:{name->meta}, edges:[{a,b,type,w,guild?}]}
const NPCS = __NPCS__;          // NPC directory: {npcs:[{name,city,type,sell,buy,px,py,z?}], n_with_coords}
const ROUTE_IMGS = __ROUTEIMGS__;  // {filename -> data-uri (inline) or path}
const OX=31744, OY=30701, IMGW=DATA.imgw, IMGH=DATA.imgh;

// color per creature (stable hash hue)
function hue(i){return (i*47)%360;}
function colorFor(i){return `hsl(${hue(i)},70%,60%)`;}
// sprite url for a creature index (null if none -> caller falls back to a colored dot)
// value is either a bare filename (external mode -> prefix creatures/) or a data: URI (inline)
function spriteFor(i){const v=SPRITES[DATA.names[i]];if(!v)return null;return v.startsWith('data:')?v:('creatures/'+v);}

/* ==========================================================================
   CONFIDENCE ENGINE  — "posso farcela?" per singola creatura e per zona
   Formule combat CONFERMATE dal calculator Rivalia (modello 7.4):
     danno medio = floor((5*skill+50) * atk * stance * 49.5/10000)
     mitigation armor ~ 0.75 * armor
   Parti EURISTICHE (tarabili, marcate nell'UI): turn-time, medie sui max-hit
   dei mostri, sostenibilita mana (valori Exura custom non confermati -> input).
   ========================================================================== */
// Default = le stat reali del Paladin di Andrea (lug 2026): lv30, Distance 64, Shielding 53,
// scudo def 28, armor tot 26 (pari), spear Attack 30. Modificabili nel pannello.
const CHAR_DEF = {voc:'paladin', level:40, weapSkill:71, shield:57, shieldDef:28, hp:615, mana:300,
  weapAtk:30, armor:26, stance:'balanced',            // weapAtk = Attack munizione (pala) o arma (knight)
  mlvl:0, spellDmg:0, spellMana:0,                    // caster: Magic Level, danno medio/cast, mana/cast
  healAmt:120, healMana:40};                           // Exura: HP per cast / mana per cast (INPUT: verifica in-game)
const STANCE_ATK={offensive:1.2, balanced:1.0, defensive:0.6};
const STANCE_DEF={offensive:0.6, balanced:1.0, defensive:1.8};   // stance invertito per il block
// blocco medio dello scudo (formula 7.4 ufficiale, media ≈ metà del max)
function blockOf(c){return Math.floor((5*c.shield+50)*(c.shieldDef||0)*STANCE_DEF[c.stance]*49.5/10000);}
const TURN=2.0;                                        // s per turno (euristico 7.4)
const VOCS={paladin:'Paladin',knight:'Knight',sorcerer:'Sorcerer',druid:'Druid'};
const isCaster=v=>v==='sorcerer'||v==='druid';
// PARTY: 1 o 2 personaggi. CHARS[0] = PG A, CHARS[1] = PG B (usato solo se duo).
let PARTY = loadParty();
function loadParty(){
  try{const s=JSON.parse(localStorage.getItem('rivalia_party'));
    if(s&&s.chars){ const n=s.n||(s.duo?2:1);
      const chars=s.chars.map(c=>Object.assign({},CHAR_DEF,c));
      while(chars.length<3) chars.push(Object.assign({},CHAR_DEF));
      return {n, chars};
    }
  }catch(e){}
  // migrazione dal vecchio single-char se presente → default = le stat paladin di Andrea
  let a=Object.assign({},CHAR_DEF);
  try{const old=JSON.parse(localStorage.getItem('rivalia_char'));if(old)a=Object.assign(a,old);}catch(e){}
  return {n:1, chars:[a, Object.assign({},CHAR_DEF), Object.assign({},CHAR_DEF)]};
}
function saveParty(){localStorage.setItem('rivalia_party',JSON.stringify(PARTY));}
function activeChars(){return PARTY.chars.slice(0,PARTY.n);}

// danno medio per "colpo"/cast di UN personaggio, per vocazione.
// Paladin/Knight: formula arma CONFERMATA (weapon skill + Attack). Caster: danno/cast tarabile (INPUT).
function avgHitOf(c){
  if(isCaster(c.voc)) return c.spellDmg||0;   // danno medio per cast, impostato dall'utente
  return Math.floor((5*c.weapSkill+50)*c.weapAtk*STANCE_ATK[c.stance]*49.5/10000);
}
// quanti "colpi" può sostenere un PG in un fight prima di finire il mana (Infinity se non mana-limited)
function sustainCasts(c){
  if(!isCaster(c.voc)) return Infinity;       // frecce/mischia ~ illimitate nel singolo fight
  return c.spellMana>0 ? Math.floor(c.mana/c.spellMana) : 0;
}

// parse una stringa attacco -> {kind, avg, elem}  (avg = danno atteso per colpo verso di ME)
function parseAtk(a){
  const mMelee=a.match(/Melee\s*\(~(\d+)\)/i);
  if(mMelee) return {kind:'melee', max:+mMelee[1], phys:true};
  const m=a.match(/(Physical|Fire|Energy|Ice|Poison|Life Drain|Mana Drain)\s*\((\d+)-(\d+)\)/i);
  if(m){const hi=+m[2],lo=+m[3];const type=m[1].toLowerCase();
    return {kind:type, max:hi, min:lo, phys:type==='physical'};}
  return null; // condizioni (paralyze, firefield...) -> ignorate nel danno
}
// danno atteso che ricevo da UN colpo di questo attacco, dato l'armor del difensore
function incomingPerHit(atk, defArmor){
  if(!atk) return 0;
  let base = atk.kind==='melee' ? atk.max*0.6 : ((atk.max+ (atk.min||0))/2);
  if(atk.phys) base = Math.max(base - 0.75*defArmor, base*0.15); // armor mitiga il fisico
  return base;
}
// calcolo il verdetto per una lista di PG (1 o 2) contro la creatura s. Ritorna score + dettagli.
// `origIdx` mappa la posizione nella lista → indice reale nel party (per le note "PG1/PG2").
function runAssess(s, group, origIdx){
  const duo=group.length>1;   // "duo" = multi-PG (2 o 3)
  // danno di party per turno: somma del danno effettivo di ogni PG.
  // Fisico (pala/knight) mitigato dall'armor del mostro; magico (caster) NO (elementale).
  const perCharEff=group.map(c=>{const h=avgHitOf(c);
    return isCaster(c.voc)? h : Math.max(h-0.75*(s.armor||0), h*0.15);});
  const partyEff=perCharEff.reduce((a,b)=>a+b,0);
  const hitsToKill=Math.max(1, Math.ceil(s.health/Math.max(1,partyEff)));
  const ttk=hitsToKill*TURN;
  let manaStalled=false;
  group.forEach(c=>{ if(isCaster(c.voc) && sustainCasts(c) < hitsToKill) manaStalled=true; });
  const atks=(s.attacks||[]).map(parseAtk).filter(Boolean);
  const isRanged = atks.some(a=>!(a.kind==='melee'||a.kind==='life drain'||a.kind==='mana drain'));
  function rawPerTurn(c){
    if(!atks.length) return 0;
    const block=blockOf(c);
    return Math.max(...atks.map(a=>{
      let d=incomingPerHit(a,c.armor);
      if(a.kind==='melee'||a.phys) d=Math.max(0,d-block);
      return d;
    }));
  }
  // SPLIT danno mostro sul party ordinato per budget: solo=100%, duo=65/35, trio=50/30/20.
  const split = group.length>=3 ? [0.50,0.30,0.20] : (group.length===2 ? [0.65,0.35] : [1.0]);
  const budgets = group.map(c=>{const casts=c.healMana>0?Math.floor(c.mana/c.healMana):0;return c.hp+casts*c.healAmt;});
  const order = group.map((c,idx)=>idx).sort((a,b)=>budgets[b]-budgets[a]);
  const perChar = group.map((c,idx)=>{
    const shareRank = order.indexOf(idx);
    const share = split[shareRank] ?? split[split.length-1];
    const raw = rawPerTurn(c);
    const dmgTaken = raw*hitsToKill*share;
    const casts=c.healMana>0?Math.floor(c.mana/c.healMana):0;
    const healBudget=casts*c.healAmt;
    const survivable=(c.hp+healBudget)>=dmgTaken;
    const pressure=dmgTaken/Math.max(1,(c.hp+healBudget));
    return {idx:origIdx?origIdx[idx]:idx, voc:c.voc, hp:c.hp,
            raw:Math.round(raw),dmgTaken:Math.round(dmgTaken),healBudget:Math.round(healBudget),
            survivable,pressure,block:Math.round(blockOf(c)),isTank:shareRank===0};
  });
  const worst = perChar.reduce((a,b)=>b.pressure>a.pressure?b:a);
  const hit0=avgHitOf(group[0]);
  let score=100;
  score -= Math.min(60, worst.pressure*60);
  score -= Math.min(25, ttk/8*25);
  const anyDead=perChar.some(p=>!p.survivable);
  if(anyDead) score=Math.min(score,25);
  if(partyEff<=1) score=Math.min(score,10);
  else if(perCharEff[0]<=hit0*0.16 && !isCaster(group[0].voc)) score=Math.min(score,30);
  if(manaStalled) score=Math.min(score,35);
  if(duo) score=Math.min(100,score+6);   // bonus focus-fire / cure incrociate
  score=Math.max(0,Math.round(score));
  return {score,ttk,hitsToKill,partyEff,perCharEff,perChar,worst,atks,isRanged,manaStalled,duo};
}
// verdetto per una singola creatura (s = stats). Usa la PARTY (1 o 2 PG).
function assess(s){
  if(!s || !s.health) return null;
  const chars=activeChars();
  const duo=chars.length>1;
  const r=runAssess(s, chars, chars.map((c,i)=>i));
  let score=r.score;
  // FLOOR duo≥solo: un compagno non può renderti PIÙ debole di quanto saresti da solo.
  // Se PG2 è inutile/fragile, al minimo il duo vale il solo del PG più forte.
  let soloFloor=0;
  if(duo){
    chars.forEach((c,i)=>{ const rs=runAssess(s,[c],[i]); if(rs.score>soloFloor) soloFloor=rs.score; });
    score=Math.max(score, soloFloor);
  }
  const worst=r.worst;
  let label,cls;
  if(score>=70){label='FARMABLE';cls='ok';}
  else if(score>=40){label='RISKY';cls='warn';}
  else {label='LETHAL';cls='bad';}
  const notes=[];
  if(duo){const vs=chars.map(c=>VOCS[c.voc]).join(' + ');notes.push('party ('+vs+'): summed DPS, monster damage split onto the tank');}
  if(duo && score===soloFloor && soloFloor>r.score) notes.push('the teammate does not help here → score = as if playing solo (the better of the two)');
  if(r.isRanged) notes.push('ranged: kiting useless, break LoS or close in');
  else if(r.atks.length) notes.push('melee: kite it (shoot & retreat)');
  if(r.manaStalled) notes.push('⚠️ the caster runs out of mana before the kill — bring mana pots or shorten it');
  r.perChar.forEach(p=>{if(!p.survivable)notes.push(`survival at risk: Char${p.idx+1} (${VOCS[p.voc]}${p.isTank?', tank':''}) takes ~${p.dmgTaken} vs ${p.hp}+${p.healBudget}`);});
  chars.forEach((c,idx)=>{if(isCaster(c.voc)&&(c.spellDmg||0)<=0)notes.push(`Char${idx+1} ${VOCS[c.voc]}: set 'dmg/cast' and 'mana/cast' for the calc`);});
  if(!isCaster(chars[0].voc)&&r.perCharEff[0]<=avgHitOf(chars[0])*0.2) notes.push('high armor: little damage per hit');
  return {ttk:Math.round(r.ttk), effHit:Math.round(r.partyEff), hitsToKill:r.hitsToKill, dmgTaken:worst.dmgTaken,
          healBudget:worst.healBudget, survivable:worst.survivable, isRanged:r.isRanged, duo, perChar:r.perChar,
          block:worst.block||0, worstIdx:worst.idx, score, label, cls, notes};
}
// a small <img> chip for lists/panels (fixed box, pixel-crisp), or a colored dot fallback
function spriteChip(i,px){const s=spriteFor(i);const d=px||20;
  return s?`<img class="cspr" src="${s}" width="${d}" height="${d}" loading="lazy" alt="">`
          :`<span class="dot" style="width:${Math.round(d*.5)}px;height:${Math.round(d*.5)}px;border-radius:50%;background:${colorFor(i)}"></span>`;}

document.getElementById('sub').textContent =
   DATA.creaturesTotal+' creatures · '+DATA.spawnsTotal.toLocaleString()+' spawn · 16 floors';

// ---- Leaflet map in simple pixel CRS ----
const _isMobile = window.matchMedia('(max-width:820px)').matches;
const map = L.map('map',{crs:L.CRS.Simple,minZoom:-3,maxZoom:7,zoomSnap:.25,
   zoomDelta:.5,wheelPxPerZoomLevel:80,attributionControl:false,preferCanvas:true,
   zoomControl:!_isMobile});   // hide +/- buttons on mobile — pinch-to-zoom instead
const bounds=[[0,0],[IMGH,IMGW]];     // [y,x]
// dedicated panes so the ghost floor IMAGES stack below markers (overlayPane = z 400)
map.createPane('belowPane');   map.getPane('belowPane').style.zIndex=205;
map.createPane('currentPane'); map.getPane('currentPane').style.zIndex=215;
map.createPane('abovePane');   map.getPane('abovePane').style.zIndex=225;
['belowPane','currentPane','abovePane'].forEach(p=>map.getPane(p).style.pointerEvents='none');
let imgLayer=null, belowImg=null, aboveImg=null;
let curFloor=7;
let selected=null;          // creature index or null
let ghostLayer=L.layerGroup().addTo(map); // floors above/below spawn dots
let layer=L.layerGroup().addTo(map);      // current-floor markers
let radius=50;
let spriteMode='auto';   // 'auto' (sprite when zoomed/selected) | 'on' (always) | 'off' (dots only)
// Ghost above/below-floor veils default ON on desktop, but OFF on mobile: the toggle box
// (#ghostbox) is hidden on phones, and the translucent veils just clutter a small screen.
let showAbove=false, showBelow=false;   // ghost floor veils default OFF everywhere; user enables them if wanted
const anyGhost=()=>showAbove||showBelow;
let curOpacity=0.78;        // current-floor map opacity when a ghost floor is ON (see-through)
let aboveOpacity=0.42;      // opacity of the floor-above veil

function rm(l){if(l)map.removeLayer(l);return null;}
function setFloorImg(z){
  z=+z;
  belowImg=rm(belowImg); aboveImg=rm(aboveImg); imgLayer=rm(imgLayer);
  // floor BELOW (z+1) — sits under current, warm tint, bleeds through
  if(showBelow && IMGS[z+1])
    belowImg=L.imageOverlay(IMGS[z+1],bounds,{pane:'belowPane',className:'crisp-img ghost-below'}).addTo(map);
  // CURRENT floor — opacity reduced when a ghost floor shows, so the layer below shows through
  imgLayer=L.imageOverlay(IMGS[z]||IMGS['7'],bounds,{pane:'currentPane',className:'crisp-img',opacity:showBelow?curOpacity:1}).addTo(map);
  // floor ABOVE (z-1) — overlaid translucent on top, cool/cyan tint
  if(showAbove && IMGS[z-1])
    aboveImg=L.imageOverlay(IMGS[z-1],bounds,{pane:'abovePane',className:'crisp-img ghost-above',opacity:aboveOpacity}).addTo(map);
  applyCrisp();
}
map.fitBounds(bounds);
// keep the floor image pixel-crisp at every zoom (it's pixel-art); re-apply after tile redraws
function applyCrisp(){document.querySelectorAll('.crisp-img').forEach(im=>{im.style.imageRendering='pixelated';});}
map.on('zoomend moveend',applyCrisp);
// in AUTO mode the dot/sprite threshold depends on zoom → redraw markers on zoom change
let _lastZ=null;
map.on('zoomend',()=>{const z=map.getZoom();if(spriteMode==='auto'&&z!==_lastZ){_lastZ=z;draw();}});
setFloorImg(7);

// ---- marker drawing ----
function pts(z){return DATA.byfloor[String(z)]||[];}

function draw(){
  layer.clearLayers(); ghostLayer.clearLayers();
  // --- GHOST overlay: floor above (z-1, "sopra") cyan, floor below (z+1, "sotto") orange ---
  const above=curFloor-1, below=curFloor+1;
  const drawGhost=(z,col)=>{
    if(z<0||z>15) return;
    for(const p of pts(z)){
      const [ci,px,py]=p;
      if(selected!==null && ci!==selected) continue;
      L.circleMarker([IMGH-py,px],{radius:2,stroke:false,fillColor:col,fillOpacity:.32,interactive:false}).addTo(ghostLayer);
    }
  };
  if(showAbove) drawGhost(above,'#6cc6ff');   // sopra
  if(showBelow) drawGhost(below,'#ff9d3d');   // sotto
  // --- current floor markers ---
  const arr=pts(curFloor);
  let shown=0;
  // Decide sprite vs dot: sprites are DOM <img> (heavy at scale), so only when
  // few markers are on screen — i.e. zoomed in, a single creature selected, or forced.
  const useSprite = spriteMode==='on' ||
      (spriteMode==='auto' && (selected!==null || map.getZoom()>=1));
  const sz = map.getZoom()>=3?32:(map.getZoom()>=1?22:18);
  for(const p of arr){
    const [ci,px,py,amt]=p;
    if(selected!==null && ci!==selected) continue;
    shown++;
    const isSel=(ci===selected);
    const latlng=[IMGH-py,px];
    const spr=useSprite?spriteFor(ci):null;
    let m;
    if(spr){
      const d=isSel?sz+8:sz;
      const html=`<div class="spr-wrap${isSel?' sel':''}" style="--c:${colorFor(ci)};width:${d}px;height:${d}px">`+
                 `<img src="${spr}" width="${d}" height="${d}" alt=""></div>`;
      m=L.marker(latlng,{icon:L.divIcon({className:'spr-icon',html,iconSize:[d,d],iconAnchor:[d/2,d/2]})});
    }else{
      m=L.circleMarker(latlng,{
        radius:isSel?5:3, color:colorFor(ci), weight:isSel?2:1,
        fillColor:colorFor(ci), fillOpacity:isSel?.95:.7, opacity:isSel?1:.6
      });
    }
    m.bindTooltip(DATA.display[ci]+' ×'+amt,{direction:'top',opacity:.9});
    // click sullo sprite/pallino = come cliccare nella lista a sx (stats + confidence)
    m.on('click',()=>selectCreature(ci===selected?null:ci));
    layer.addLayer(m);
  }
  document.getElementById('ro-spawn').textContent=shown;
  document.getElementById('ro-floor').textContent=curFloor;
  applyCrisp();
}

// ---- floor selector ----
const floorsEl=document.getElementById('floors');
function selectFloor(z,keepView){
  if(z<0||z>15) return;
  curFloor=z; setFloorImg(String(z)); draw(); scan(lastLatLng);
  [...floorsEl.children].forEach((c,i)=>c.classList.toggle('on',i===z));
}
for(let z=0;z<=15;z++){
  const b=document.createElement('button');
  const cnt=DATA.floorcount[z]||0;
  b.className='fbtn'+(z===7?' on':'')+(cnt===0?' empty':'');
  b.innerHTML=z+'<span class="b">'+(cnt||'·')+'</span>';
  b.title=`Floor ${z}`+(z<7?' (surface)':z===7?' (ground)':' (underground)')+` — ${cnt} spawn`;
  b.onclick=()=>selectFloor(z);
  floorsEl.appendChild(b);
}

// ---- creature list ----
const clistEl=document.getElementById('clist');
function buildList(filter=''){
  clistEl.innerHTML='';
  const f=filter.trim().toLowerCase();
  const order=[...DATA.names.keys()].sort((a,b)=>DATA.display[a].localeCompare(DATA.display[b]));
  const isBoss=i=>DATA.boss&&DATA.boss[i];
  for(const i of order){
    if(f && !DATA.display[i].toLowerCase().includes(f)) continue;
    const row=document.createElement('div');
    row.className='crow'+(i===selected?' on':'')+(isBoss(i)?' boss':'');
    row.innerHTML=spriteChip(i,22)+
      `<span class="nm">${DATA.display[i]}${isBoss(i)?' <span class="bosstag">👑 boss</span>':''}</span>`+
      `<span class="fl">${isBoss(i)?'—':DATA.crFloors[i].join(',')}</span>`+
      `<span class="ct">${isBoss(i)?'':DATA.total[i]}</span>`;
    row.onclick=()=>selectCreature(i===selected?null:i);
    clistEl.appendChild(row);
  }
}
function renderStats(i){
  const panel=document.getElementById('stats');
  if(i===null){panel.classList.remove('show');return;}
  const slug=DATA.names[i];
  const s=STATS[slug];
  const stdot=document.getElementById('st-dot');
  const spr=spriteFor(i);
  if(spr){stdot.style.cssText='width:32px;height:32px;flex:0 0 32px;border-radius:8px;background:#0d1018;box-shadow:0 0 0 2px '+colorFor(i);
          stdot.innerHTML=`<img src="${spr}" width="30" height="30" alt="">`;}
  else{stdot.style.cssText='width:14px;height:14px;flex:0 0 14px;border-radius:50%;background:'+colorFor(i);stdot.innerHTML='';}
  document.getElementById('st-name').textContent=DATA.display[i];
  const body=document.getElementById('st-body');
  if(!s){
    body.innerHTML=`<div class="nostat">No catalog stats for this creature.<br>`+
      `<span style="color:var(--acc2)">Total spawns: ${DATA.total[i]} · floors: ${DATA.crFloors[i].join(', ')}</span></div>`;
    panel.classList.add('show');return;
  }
  const fl=(b,l)=>`<b>${b?'✔':'✘'}</b> ${l}`;
  let h='';
  h+=`<div class="stat-grid">`+
     `<div class="stat hp"><div class="k">Health</div><div class="v">${(s.health??'?').toLocaleString()}</div></div>`+
     `<div class="stat xp"><div class="k">Experience</div><div class="v">${(s.experience??'?').toLocaleString()}</div></div>`+
     `<div class="stat"><div class="k">Armor</div><div class="v">${s.armor??'?'}</div></div>`+
     `<div class="stat"><div class="k">Defense</div><div class="v">${s.defense??'?'}</div></div>`+
     `<div class="stat"><div class="k">Speed</div><div class="v">${s.speed??'?'}</div></div>`+
     `<div class="stat"><div class="k">Race</div><div class="v" style="font-size:13px">${s.race??'?'}</div></div>`+
     `</div>`;
  if(s.attacks&&s.attacks.length){
    h+=`<div class="sblock"><div class="h">⚔️ Attacks</div>`+
       s.attacks.map(a=>`<span class="chip atk">${a}</span>`).join('')+`</div>`;
  }
  if(s.immunities&&s.immunities.length){
    h+=`<div class="sblock"><div class="h">🛡️ Immunities</div>`+
       s.immunities.map(a=>`<span class="chip imm">${a}</span>`).join('')+`</div>`;
  }else{
    h+=`<div class="sblock"><div class="h">🛡️ Immunities</div><span class="meta" style="color:var(--dim);font-size:12px">None</span></div>`;
  }
  if(s.loot&&s.loot.length){
    h+=`<div class="sblock"><div class="h">💰 Loot</div><div class="loot-list">`+
       s.loot.map(l=>`• ${l}`).join('<br>')+`</div></div>`;
  }
  if(s.summons&&s.summons.length){
    h+=`<div class="sblock"><div class="h">👹 Summon</div>`+
       s.summons.map(a=>`<span class="chip atk">${a}</span>`).join('')+`</div>`;
  }
  h+=`<div class="flags">${fl(s.summonable,'summonable')} &nbsp; ${fl(s.convinceable,'convince')} &nbsp; ${fl(s.pushable,'push')}</div>`;
  if(DATA.boss&&DATA.boss[i]){
    h+=`<div class="flags" style="margin-top:4px;color:var(--acc)">👑 Boss / unique — no fixed spawn (quest, raid or event).</div>`;
  }else{
    h+=`<div class="flags" style="margin-top:4px">Total spawns: <b>${DATA.total[i]}</b> · floors: <b>${DATA.crFloors[i].join(', ')}</b></div>`;
  }
  body.innerHTML=h;
  panel.classList.add('show');
}
// MOBILE ONLY: after picking a creature, the map stays visible with the spawns highlighted,
// and a slim RESULT BAR appears at the bottom (name + verdict + floors). Tapping "Dettagli"
// expands the full combined sheet (verdict + stats). Desktop: no-op (crBar/crSheet hidden).
const _mob=()=>window.matchMedia('(max-width:820px)').matches;
function crSheetShow(i){
  const bar=document.getElementById('crBar'), sh=document.getElementById('crSheet'),
        fab=document.getElementById('crFab');
  if(!bar||!sh) return;
  if(i===null){ bar.classList.remove('show'); sh.classList.remove('show'); if(fab)fab.classList.remove('lifted'); return; }
  if(!_mob()) return;
  // fill the slim bar: name · verdict badge · floors (or boss note)
  const boss = DATA.boss && DATA.boss[i];
  const s = STATS[DATA.names[i]]; const a = (!boss && s) ? assess(s) : null;
  const badge = a ? `<span class="vbadge ${a.cls}">${a.label}</span>` : '';
  const where = boss ? '👑 boss · no fixed spawn'
                     : `floors <b>${DATA.crFloors[i].join(', ')||'?'}</b> · ${DATA.total[i]} spawn`;
  document.getElementById('crBarInfo').innerHTML = `<b>${DATA.display[i]}</b> ${badge}<br><span style="color:var(--dim);font-size:12px">${where} · <span style="color:var(--acc2)">tap for stats ›</span></span>`;
  document.getElementById('crSheetHd').firstElementChild.textContent = '🐉 '+DATA.display[i];
  bar.classList.add('show');
  sh.classList.add('show');                           // open the full stats sheet right away
  if(fab) fab.classList.add('lifted');                // keep the 🐉 clear of the bar
  document.getElementById('side').classList.remove('open');   // tuck the controls sheet away
  const se=document.getElementById('search'); if(se) se.blur();   // drop the keyboard → full map
}
function selectCreature(i){
  selected=i;
  renderStats(i);
  const boss = i!==null && DATA.boss && DATA.boss[i];   // boss = stats only, no spawns
  if(boss){
    // bosses have no map spawn: show stats, no verdict/floor-jump, just refresh the list
    verdictMode=null;document.getElementById('verdict').classList.remove('show');
    buildList(document.getElementById('search').value);
    crSheetShow(i);
    draw();
    return;
  }
  if(i!==null){verdictMode={type:'creature',i};renderCreatureVerdict(i);}
  else if(verdictMode&&verdictMode.type==='creature'){
    // tornato a "nessuna creatura": se il toggle zona è attivo torno in modalità zona, altrimenti chiudo
    if(typeof zoneOn!=='undefined' && zoneOn){verdictMode={type:'zone'};renderZoneVerdict(lastLatLng);}
    else{verdictMode=null;document.getElementById('verdict').classList.remove('show');}
  }
  buildList(document.getElementById('search').value);
  crSheetShow(i);   // mobile: open/close the combined creature bottom sheet
  // if selected creature not on current floor, jump to its busiest floor
  if(i!==null && !DATA.crFloors[i].includes(curFloor)){
    // pick floor with most of this creature
    let best=curFloor,bc=-1;
    for(const z of DATA.crFloors[i]){
      const c=pts(z).filter(p=>p[0]===i).length;
      if(c>bc){bc=c;best=z;}
    }
    selectFloor(best);   // setFloorImg+draw+button sync
  }else{
    draw();
  }
}
document.getElementById('search').oninput=e=>{
  const v=e.target.value;
  buildList(v);
  // If the typed text matches exactly ONE creature (or an exact name), highlight it on the
  // map right away — the whole point of searching. Otherwise just show the filtered list.
  const f=v.trim().toLowerCase();
  if(f.length>=2){
    const hits=[...DATA.names.keys()].filter(i=>DATA.display[i].toLowerCase().includes(f));
    const exact=[...DATA.names.keys()].find(i=>DATA.display[i].toLowerCase()===f);
    // On mobile, don't grab focus/blur mid-typing: auto-pick ONLY on an exact full-name match.
    // On desktop keep the eager single-hit behaviour. Otherwise the user taps a result row.
    const pick = (exact!=null) ? exact : (!_mob() && hits.length===1 ? hits[0] : null);
    if(pick!=null && pick!==selected) selectCreature(pick);
  }
};
// tapping the search field expands the bottom sheet so the results list is visible (mobile)
document.getElementById('search').addEventListener('focus',()=>{
  if(window.matchMedia('(max-width:820px)').matches) document.getElementById('side').classList.add('open');
});
// MOBILE: 🐉 FAB opens controls + focuses search; result-bar "Dettagli" expands the full
// sheet; ✕ clears. The sheet's own close returns to the bar; tap-outside dismisses.
(function(){
  const fab=document.getElementById('crFab'), sh=document.getElementById('crSheet'),
        shClose=document.getElementById('crSheetClose'), side=document.getElementById('side'),
        bar=document.getElementById('crBar'), more=document.getElementById('crBarMore'),
        barX=document.getElementById('crBarX');
  if(fab) fab.onclick=()=>{ side.classList.add('open');
    const s=document.getElementById('search'); s.focus(); s.scrollIntoView({block:'center'}); };
  // tapping the bar (info or 📊 Stats) → expand full verdict+stats sheet
  const openDetails=()=>sh.classList.add('show');
  if(more) more.onclick=openDetails;
  const info=document.getElementById('crBarInfo'); if(info){ info.style.cursor='pointer'; info.onclick=openDetails; }
  if(shClose) shClose.onclick=()=>{ sh.classList.remove('show'); };   // collapse details, keep the bar+map
  if(sh) sh.addEventListener('click',e=>{ if(e.target===sh) sh.classList.remove('show'); });
  if(barX) barX.onclick=()=>selectCreature(null);                      // clear selection entirely
})();
document.getElementById('clearSel').onclick=()=>selectCreature(null);
document.getElementById('toAll').onclick=()=>{selected=null;renderStats(null);buildList();draw();};
document.getElementById('st-close').onclick=()=>selectCreature(null);
document.getElementById('sprMode').onclick=function(){
  spriteMode = spriteMode==='auto'?'on':(spriteMode==='on'?'off':'auto');
  this.textContent='🖼️ Icons: '+(spriteMode==='auto'?'Auto':spriteMode==='on'?'Always':'Off');
  this.classList.toggle('on',spriteMode!=='off');
  draw();
};
document.getElementById('tAbove').onclick=function(){
  showAbove=!showAbove; this.classList.toggle('on',showAbove);
  document.getElementById('opacityRowUp').style.display=showAbove?'flex':'none';
  setFloorImg(curFloor); draw();
};
document.getElementById('tBelow').onclick=function(){
  showBelow=!showBelow; this.classList.toggle('on',showBelow);
  document.getElementById('opacityRow').style.display=showBelow?'flex':'none';
  setFloorImg(curFloor); draw();
};
// sync the toggle buttons + opacity rows to the JS defaults (matters on mobile where these start OFF)
document.getElementById('tAbove').classList.toggle('on',showAbove);
document.getElementById('tBelow').classList.toggle('on',showBelow);
document.getElementById('opacityRowUp').style.display=showAbove?'flex':'none';
document.getElementById('opacityRow').style.display=showBelow?'flex':'none';
document.getElementById('opac').oninput=function(){
  curOpacity=+this.value/100;
  document.getElementById('opacv').textContent=this.value+'%';
  if(imgLayer) imgLayer.setOpacity(showBelow?curOpacity:1);
};
document.getElementById('opacUp').oninput=function(){
  aboveOpacity=+this.value/100;
  document.getElementById('opacUpv').textContent=this.value+'%';
  if(aboveImg) aboveImg.setOpacity(aboveOpacity);
};

// ---- HOVER SCANNER (anti-death) ----
let lastLatLng=null;
let ring=null;
function scan(ll){
  const body=document.getElementById('scanbody');
  if(!ll){body.innerHTML='<div class="empty">Move the mouse over the map…</div>';document.getElementById('scancount').textContent='0';return;}
  const cx=ll.lng, cy=ll.lat;        // lng=x(px), lat=flipped y
  // aggregate by creature within radius on current floor
  const here={};
  for(const p of pts(curFloor)){
    const [ci,px,py,amt]=p;
    const dx=px-cx, dy=(IMGH-py)-cy;
    if(dx*dx+dy*dy<=radius*radius){
      if(!here[ci]) here[ci]={spots:0,amt:0};
      here[ci].spots++; here[ci].amt+=amt;
    }
  }
  const keys=Object.keys(here).map(Number).sort((a,b)=>here[b].amt-here[a].amt);
  document.getElementById('scancount').textContent=keys.length;
  if(!keys.length){body.innerHTML='<div class="empty">No spawn within the radius.<br><span style="color:var(--ok)">Zone appears safe here.</span></div>';return;}
  let html='';
  for(const ci of keys){
    const otherFloors=DATA.crFloors[ci].filter(z=>z!==curFloor);
    const warn=otherFloors.length?`<span class="meta" style="color:var(--danger)">also floor ${otherFloors.join(',')}</span>`:`<span class="meta">only here</span>`;
    html+=`<div class="srow">${spriteChip(ci,24)}`+
      `<span class="nm">${DATA.display[ci]}<br>${warn}</span>`+
      `<span class="amt">${here[ci].amt}</span></div>`;
  }
  body.innerHTML=html;
}
map.on('mousemove',e=>{
  lastLatLng=e.latlng;
  document.getElementById('ro-xy').textContent=Math.round(e.latlng.lng+OX)+', '+Math.round(IMGH-e.latlng.lat+OY);
  if(ring) map.removeLayer(ring);
  ring=L.circle(e.latlng,{radius:radius,color:'#ffb347',weight:1,fill:false,dashArray:'4 4'}).addTo(map);
  scan(e.latlng);
  if(verdictMode&&verdictMode.type==='zone') renderZoneVerdict(e.latlng);
});
map.on('mouseout',()=>{lastLatLng=null;if(ring){map.removeLayer(ring);ring=null;}scan(null);});
document.getElementById('radr').oninput=e=>{radius=+e.target.value;document.getElementById('radv').textContent=radius;if(lastLatLng)scan(lastLatLng);if(ring&&lastLatLng){map.removeLayer(ring);ring=L.circle(lastLatLng,{radius:radius,color:'#ffb347',weight:1,fill:false,dashArray:'4 4'}).addTo(map);}};

// ---- CONFIG panel wiring (solo/duo, vocation-aware) ----
// campi comuni + campi specifici per vocazione
const F_COMMON_TOP=[['level','Level'],['hp','HP max'],['mana','Mana max'],['armor','Armor']];
const F_WEAPON=[['weapSkill','Weapon skill'],['weapAtk','Weapon Attack']];   // pala=Distance, knight=melee
const F_CASTER=[['mlvl','Magic Level'],['spellDmg','Dmg/cast'],['spellMana','Mana/cast']];
const F_DEFENSE=[['shield','Shielding'],['shieldDef','Shield def']];
const F_HEAL=[['healAmt','Exura HP/cast'],['healMana','Exura mana/cast']];
function fieldHtml(idx,k,lab,title){const c=PARTY.chars[idx];
  return `<label>${lab}<input type="number" data-idx="${idx}" data-k="${k}" value="${c[k]}" ${title?`title="${title}"`:''}></label>`;}
function charForm(idx){
  const c=PARTY.chars[idx];
  const caster=isCaster(c.voc);
  const skillLab = c.voc==='paladin'?'Distance':(c.voc==='knight'?'Melee skill':'Weapon skill');
  const atkTitle = c.voc==='paladin'?'Attack of the arrow/bolt':'Attack of the weapon';
  let h=`<div class="charform"><div class="cf-title">${PARTY.n>1?('Char '+(idx+1)):'My character'}</div>`;
  h+=`<label class="voc-label">Vocation<select class="voc-sel" data-idx="${idx}" data-k="voc">`+
     Object.entries(VOCS).map(([v,n])=>`<option value="${v}" ${c.voc===v?'selected':''}>${n}</option>`).join('')+
     `</select></label>`;
  h+=`<div class="cfg-grid">`;
  for(const [k,lab] of F_COMMON_TOP) h+=fieldHtml(idx,k,lab);
  if(caster){ for(const [k,lab] of F_CASTER) h+=fieldHtml(idx,k, k==='spellDmg'?'Dmg/cast*':lab, k==='spellDmg'?'Average damage per cast/rune — verify in-game (custom Rivalia spell)':''); }
  else { h+=fieldHtml(idx,'weapSkill',skillLab); h+=fieldHtml(idx,'weapAtk','Attack',atkTitle); }
  for(const [k,lab] of F_DEFENSE) h+=fieldHtml(idx,k, k==='shieldDef'?'Shield def':lab, k==='shieldDef'?'Defense of the equipped shield':'');
  for(const [k,lab] of F_HEAL) h+=fieldHtml(idx,k,lab, k==='healAmt'?'How many HP a heal restores (verify in-game)':'');
  h+=`<label>Stance<select data-idx="${idx}" data-k="stance">`+
     ['offensive','balanced','defensive'].map(v=>`<option value="${v}" ${c.stance===v?'selected':''}>${v==='offensive'?'Full Atk':v==='balanced'?'Balanced':'Full Def'}</option>`).join('')+
     `</select></label>`;
  h+=`</div>`;
  if(caster) h+=`<div class="cfg-note" style="margin-top:5px">*Rivalia spell damage not on the wiki → tunable input. The formula scales with Magic Level (confirmed mechanic), power set by you.</div>`;
  h+=`</div>`;
  return h;
}
function pgSummary(){
  const c=PARTY.chars[0];
  const extra=PARTY.n>1?` +${PARTY.n-1}`:'';
  return `${VOCS[c.voc]} lv${c.level} · ${c.voc==='paladin'?'dist':'skill'} ${c.weapSkill}${extra}`;
}
function renderCharForms(){
  const wrap=document.getElementById('charForms');
  wrap.innerHTML = PARTY.chars.slice(0,PARTY.n).map((_,i)=>charForm(i)).join('');
  wrap.querySelectorAll('input,select').forEach(el=>{
    el.oninput=()=>{const i=+el.dataset.idx,k=el.dataset.k;
      PARTY.chars[i][k]=(k==='stance'||k==='voc')?el.value:(+el.value||0);
      saveParty();
      if(k==='voc') renderCharForms();   // cambia i campi mostrati
      refreshAll();};
  });
  [['ptSolo',1],['ptDuo',2],['ptTrio',3]].forEach(([id,n])=>
    document.getElementById(id).classList.toggle('on',PARTY.n===n));
  const ps=document.getElementById('pgSummary'); if(ps) ps.textContent=pgSummary();
}
renderCharForms();
function setPartyN(n){PARTY.n=n;saveParty();renderCharForms();refreshAll();}
document.getElementById('ptSolo').onclick=()=>setPartyN(1);
document.getElementById('ptDuo').onclick=()=>setPartyN(2);
document.getElementById('ptTrio').onclick=()=>setPartyN(3);
document.getElementById('cfgToggle').onclick=function(){
  const box=document.getElementById('cfgBox');
  const show=box.style.display==='none';box.style.display=show?'block':'none';
  this.textContent=show?'▾':'▸';
};
// refreshAll: re-run the verdict panel AND re-render any open insights/areas so all
// farmability calls reflect the current PG live.
function refreshAll(){
  refreshVerdict();
  buildDanger();   // PG changed → recompute per-tile danger for the pathfinder
  if(insModal.classList.contains('show')){
    const cur=document.querySelector('.itab.on'); if(cur) showTab(cur.dataset.t);
  }
  if(areaOn) drawAreas();
}

// ---- VERDICT rendering ----
let verdictMode=null;   // {type:'creature',i} | {type:'zone'} | null
function vMetric(k,v){return `<div class="vm"><div class="k">${k}</div><div class="v">${v}</div></div>`;}
function renderCreatureVerdict(i){
  const panel=document.getElementById('verdict'), body=document.getElementById('verdictbody');
  const s=STATS[DATA.names[i]]; const a=assess(s);
  panel.classList.add('show');
  if(!a){body.innerHTML=`<div class="empty">No combat stats for <b>${DATA.display[i]}</b> in the catalog.</div>`;return;}
  const spr=spriteFor(i);
  let h=`<div class="vhead">${spr?`<img src="${spr}">`:''}<div class="vn">${DATA.display[i]}</div><span class="vbadge ${a.cls}">${a.label}</span></div>`;
  h+=`<div class="vbar"><i class="${a.cls}" style="width:${a.score}%"></i></div>`;
  const exposed=activeChars()[a.worstIdx]||activeChars()[0];
  h+=`<div class="vmetrics">`+
     vMetric('Confidence',a.score+'%')+
     vMetric('Kill in',`~${a.ttk}s (${a.hitsToKill} turns)`)+
     vMetric(a.duo?'Party dmg/turn':'My dmg/turn',a.effHit)+
     vMetric('Dmg taken*',a.dmgTaken)+
     vMetric('Shield block/hit',a.block)+
     vMetric((a.duo?('Char'+(a.worstIdx+1)+' HP+heal'):'HP+heal budget'),(exposed.hp)+'+'+a.healBudget)+
     `</div>`;
  // breakdown per-PG in duo: vedi il contributo/rischio di OGNI personaggio
  if(a.duo && a.perChar){
    const chs=activeChars();
    h+=`<div class="sblock" style="margin-top:4px"><div class="h">👥 Per character</div>`;
    a.perChar.forEach(p=>{
      const c=chs[p.idx];const dps=Math.round(isCaster(c.voc)?avgHitOf(c):Math.max(avgHitOf(c)-0.75*(s.armor||0),avgHitOf(c)*0.15));
      const scls=p.survivable?(p.pressure>0.6?'warn':'ok'):'bad';
      h+=`<div class="pgrow"><span class="pgtag">Char${p.idx+1} ${VOCS[c.voc]}${p.isTank?' 🛡️':''}</span>`+
         `<span class="pgm">dmg ${dps}/t</span><span class="pgm">takes ~${p.dmgTaken}</span>`+
         `<span class="pgm pg-${scls}">${p.survivable?'survives':'DIES'}</span></div>`;
    });
    h+=`</div>`;
  }
  if(a.notes.length) h+=`<ul class="vnotes">`+a.notes.map(n=>`<li>${n}</li>`).join('')+`</ul>`;
  h+=`<div class="cfg-note">*worst-case: standing fight. With kiting the real damage is lower. Damage = official formula; sustainability = estimate.</div>`;
  body.innerHTML=h;
}
function renderZoneVerdict(ll){
  const panel=document.getElementById('verdict'), body=document.getElementById('verdictbody');
  if(verdictMode&&verdictMode.type==='creature') return; // creature lock wins
  panel.classList.add('show');
  if(!ll){body.innerHTML='<div class="empty">Move the mouse over a zone…</div>';return;}
  const cx=ll.lng, cy=ll.lat;
  const agg={};
  for(const p of pts(curFloor)){const [ci,px,py,amt]=p;const dx=px-cx,dy=(IMGH-py)-cy;
    if(dx*dx+dy*dy<=radius*radius){if(!agg[ci])agg[ci]={amt:0};agg[ci].amt+=amt;}}
  const keys=Object.keys(agg).map(Number);
  if(!keys.length){body.innerHTML='<div class="empty" style="color:var(--ok)">No spawn within the radius.<br>Safe zone here.</div>';return;}
  // per-creature assessment + weighted zone score (peggiori/più numerosi pesano di più)
  const rows=keys.map(ci=>({ci,amt:agg[ci].amt,a:assess(STATS[DATA.names[ci]])})).filter(r=>r.a);
  const unknown=keys.length-rows.length;
  rows.sort((x,y)=>x.a.score-y.a.score);
  // zone score: media pesata per densità, ma il mostro peggiore tira giù (min ha peso extra)
  let wsum=0,w=0;for(const r of rows){const ww=r.amt;wsum+=r.a.score*ww;w+=ww;}
  let zscore=w?Math.round(wsum/w):0;
  if(rows.length){zscore=Math.round(zscore*0.6 + rows[0].a.score*0.4);} // 40% peso al peggiore
  // se molte creature si sommano nel raggio, penalità pack
  const totMobs=rows.reduce((s,r)=>s+r.amt,0);
  if(totMobs>=6) zscore=Math.max(0,zscore-12);
  const zcls=zscore>=70?'ok':zscore>=40?'warn':'bad';
  const zlab=zscore>=70?'FARMABLE':zscore>=40?'RISKY':'LETHAL';
  let h=`<div class="vsummary"><div class="big" style="color:var(--${zcls==='ok'?'ok':zcls==='warn'?'acc':'danger'})">${zscore}%</div>`+
        `<span class="vbadge ${zcls}">ZONE ${zlab}</span><div class="cfg-note" style="margin-top:6px">${rows.length} creatures · ${totMobs} spawns in radius${unknown?` · ${unknown} without stats`:''}</div></div>`;
  for(const r of rows){const spr=spriteFor(r.ci);
    h+=`<div class="vzrow">${spr?`<img src="${spr}">`:''}<span class="zn">${DATA.display[r.ci]} ×${r.amt}</span>`+
       `<span class="zs ${r.a.cls}">${r.a.score}%</span></div>`;}
  body.innerHTML=h;
}
function refreshVerdict(){
  if(!verdictMode){return;}
  if(verdictMode.type==='creature') renderCreatureVerdict(verdictMode.i);
  else renderZoneVerdict(lastLatLng);
}
let zoneOn=false;
document.getElementById('zoneToggle').onclick=function(){
  zoneOn=!zoneOn;
  this.classList.toggle('on',zoneOn);
  this.textContent='🎯 Zone verdict: '+(zoneOn?'On':'Off');
  if(zoneOn){ if(selected===null){verdictMode={type:'zone'};renderZoneVerdict(lastLatLng);} }
  else { if(verdictMode&&verdictMode.type==='zone'){verdictMode=null;document.getElementById('verdict').classList.remove('show');} }
};
document.getElementById('vClose').onclick=()=>{
  document.getElementById('verdict').classList.remove('show');verdictMode=null;
  zoneOn=false;const zt=document.getElementById('zoneToggle');zt.classList.remove('on');zt.textContent='🎯 Zone verdict: Off';
};

/* ==========================================================================
   HOW TO GET THERE — pathfinding cross-piano (A* su walk-grid rigorosa)
   Walkability: block=4, nodo calpestabile solo se 100% pixel pavimento.
   Diagonali con no-corner-cutting. Transizioni gialle validate cross-piano.
   Verificato avversarialmente: 0 muri/acqua/lava attraversati su 460 rotte.
   ========================================================================== */
const PB=PATHGRID.block, PGW=PATHGRID.gw, PGH=PATHGRID.gh;
// decodifica RLE -> per piano un Uint8Array(PGW*PGH) di 0/1
const PWALK = PATHGRID.floors.map(rows=>{
  const a=new Uint8Array(PGW*PGH);
  for(let gy=0;gy<rows.length;gy++){
    let x=0,bit=0;                       // ogni riga: run che partono da 0
    for(const run of rows[gy]){ if(bit){for(let k=0;k<run;k++)a[gy*PGW+x+k]=1;} x+=run; bit^=1; }
  }
  return a;
});
function pwalk(fl,gx,gy){ if(fl<0||fl>=PWALK.length||gx<0||gy<0||gx>=PGW||gy>=PGH)return false; return PWALK[fl][gy*PGW+gx]===1; }

// ---- DANGER COST GRID (pathfinder lesson: safe route ≠ shortest) ----
// Per (floor,block) extra step-cost = how deadly the mobs spawning there are FOR YOUR PG.
// Rebuilt whenever the PG changes (assess() verdict per creature). LETALE mobs add a lot,
// RISCHIOSO some; the A* then prefers to skirt them, like the hand-drawn routes do.
let DANGER=[];           // DANGER[fl] = Map(blockIndex -> extraCost)
let dangerAvoid=true;    // toggle
function buildDanger(){
  DANGER=PWALK.map(()=>new Map());
  const risk={}; // ci -> cost
  for(let ci=0;ci<DATA.names.length;ci++){
    const s=STATS[DATA.names[ci]]; if(!s){continue;}
    const a=assess(s); if(!a) continue;
    risk[ci]= a.cls==='bad'?14 : a.cls==='warn'?4 : 0;   // LETALE / RISCHIOSO / FARMABILE
  }
  for(let fl=0;fl<PWALK.length;fl++){
    const arr=DATA.byfloor[String(fl)]||[]; const D=DANGER[fl];
    for(const p of arr){ const ci=p[0], px=p[1], py=p[2], amt=p[3]||1;
      const c=risk[ci]; if(!c) continue;
      const gx=Math.floor(px/PB), gy=Math.floor(py/PB);
      // splat over a small radius (mobs wander) — 1-block ring, decaying
      for(let dx=-1;dx<=1;dx++)for(let dy=-1;dy<=1;dy++){
        const x=gx+dx,y=gy+dy; if(x<0||y<0||x>=PGW||y>=PGH)continue;
        const k=y*PGW+x; const add=c*(dx||dy?0.5:1)*Math.min(1,amt/3);
        D.set(k,(D.get(k)||0)+add);
      }
    }
  }
}
function dangerAt(fl,x,y){ if(!dangerAvoid||!DANGER[fl])return 0; return DANGER[fl].get(y*PGW+x)||0; }
// transizioni: mappa "fl,gx,gy" -> array di piani raggiungibili
const PTRANS=new Map();
for(const [gx,gy,fl,tc] of PATHTRANS){
  const k=fl+','+gx+','+gy; let arr=PTRANS.get(k); if(!arr){arr=[];PTRANS.set(k,arr);}
  if(tc===0||tc===2) arr.push(fl-1);   // up
  if(tc===1||tc===2) arr.push(fl+1);   // down
}
// pixel-mappa (Leaflet lat/lng) -> blocco griglia. lng=x(px 0..W), lat=IMGH-py -> py=IMGH-lat
function llToBlock(fl,ll){ const px=Math.round(ll.lng), py=Math.round(IMGH-ll.lat); return [fl, Math.floor(px/PB), Math.floor(py/PB)]; }
function blockToLL(fl,gx,gy){ const px=gx*PB+PB/2, py=gy*PB+PB/2; return [IMGH-py, px]; }  // [lat,lng]
// nodo walkable più vicino (per agganciare click che cade su muro)
function nearestWalk(fl,gx,gy,rad=25){ let best=null,bd=1e9;
  for(let dx=-rad;dx<=rad;dx++)for(let dy=-rad;dy<=rad;dy++){ if(pwalk(fl,gx+dx,gy+dy)){const d=dx*dx+dy*dy;if(d<bd){bd=d;best=[fl,gx+dx,gy+dy];}} }
  return best; }
// binary min-heap (necessario: a block=1 ci sono ~870k nodi/piano, la ricerca lineare non regge)
function Heap(){this.a=[];}
Heap.prototype.push=function(it){const a=this.a;a.push(it);let i=a.length-1;
  while(i>0){const p=(i-1)>>1;if(a[p][0]<=a[i][0])break;[a[p],a[i]]=[a[i],a[p]];i=p;}};
Heap.prototype.pop=function(){const a=this.a;const top=a[0];const last=a.pop();
  if(a.length){a[0]=last;let i=0,n=a.length;for(;;){let l=2*i+1,r=l+1,s=i;
    if(l<n&&a[l][0]<a[s][0])s=l; if(r<n&&a[r][0]<a[s][0])s=r; if(s===i)break;[a[s],a[i]]=[a[i],a[s]];i=s;}}
  return top;};
Heap.prototype.size=function(){return this.a.length;};
// A* 3D — chiave numerica compatta (fl*W*H + y*W + x) per Map veloci
function findPath(start,goal,cap=1500000){
  const NW=PGW, NWH=PGW*PGH;
  const key=(fl,x,y)=>fl*NWH + y*NW + x;
  const h=(fl,x,y)=>Math.abs(x-goal[1])+Math.abs(y-goal[2])+Math.abs(fl-goal[0])*8;  // ≤ costo transizione → euristica ammissibile
  const open=new Heap(); const came=new Map(), g=new Map(); let exp=0;
  const sk=key(start[0],start[1],start[2]); g.set(sk,0); open.push([h(start[0],start[1],start[2]),0,start[0],start[1],start[2]]);
  const gk=key(goal[0],goal[1],goal[2]);
  const moves=[[1,0,1],[-1,0,1],[0,1,1],[0,-1,1],[1,1,1.4142],[1,-1,1.4142],[-1,1,1.4142],[-1,-1,1.4142]];
  while(open.size()){
    const [f,gc,fl,x,y]=open.pop();
    const ck=key(fl,x,y);
    if(gc>(g.get(ck)??Infinity)) continue;   // voce obsoleta nell'heap
    if(ck===gk){ const out=[[fl,x,y]]; let kk=ck;
      while(came.has(kk)){ const pv=came.get(kk); out.push([pv[1],pv[2],pv[3]]); kk=pv[0]; }
      out.reverse(); return {path:out,exp}; }
    if(++exp>cap) return null;
    for(const [dx,dy,cost] of moves){
      const nx=x+dx,ny=y+dy;
      if(!pwalk(fl,nx,ny))continue;
      if(dx&&dy&&!(pwalk(fl,x+dx,y)&&pwalk(fl,x,y+dy)))continue;   // no corner-cutting
      const nk=key(fl,nx,ny),ng=gc+cost+dangerAt(fl,nx,ny);
      if(ng<(g.get(nk)??Infinity)){ g.set(nk,ng); came.set(nk,[ck,fl,x,y]); open.push([ng+h(fl,nx,ny),ng,fl,nx,ny]); }
    }
    const tr=PTRANS.get(fl+','+x+','+y);
    if(tr) for(const toFl of tr){
      // aggancia al tile walkable più vicino sul piano destinazione (il pixel giallo può non essere
      // esattamente allineato al pavimento dell'altro piano — cerca entro ±2)
      let dst=null;
      if(pwalk(toFl,x,y)) dst=[x,y];
      else{ let bd=99; for(let dx=-2;dx<=2;dx++)for(let dy=-2;dy<=2;dy++){ if(pwalk(toFl,x+dx,y+dy)){const d=dx*dx+dy*dy;if(d<bd){bd=d;dst=[x+dx,y+dy];}} } }
      if(dst){ const nk=key(toFl,dst[0],dst[1]),ng=gc+8;   // costo cambio-piano: scoraggia zig-zag inutili
        if(ng<(g.get(nk)??Infinity)){ g.set(nk,ng); came.set(nk,[ck,fl,x,y]); open.push([ng+h(toFl,dst[0],dst[1]),ng,toFl,dst[0],dst[1]]); } } }
  }
  return null;
}
// ---- Route state + UI ----
let routeMode=false, routeStart=null, routeLayers=[];
function clearRoute(){ routeLayers.forEach(l=>map.removeLayer(l)); routeLayers=[]; }
function segmentsByFloor(path){ // spezza il path in tratti per piano + punti transizione
  const segs=[]; let cur=null;
  for(let i=0;i<path.length;i++){ const [fl,gx,gy]=path[i];
    if(!cur||cur.fl!==fl){ if(cur)segs.push(cur); cur={fl,pts:[]}; }
    cur.pts.push(blockToLL(fl,gx,gy)); }
  if(cur)segs.push(cur); return segs;
}
function drawRoute(path){
  clearRoute();
  const segs=segmentsByFloor(path);
  segs.forEach((seg,si)=>{
    const onCur=seg.fl===curFloor;
    const pl=L.polyline(seg.pts,{color:onCur?'#5fd38a':'#5fd38a55',weight:onCur?4:2,opacity:onCur?.95:.4,dashArray:onCur?null:'4 5'}).addTo(map);
    routeLayers.push(pl);
    // marker transizione all'inizio di ogni segmento (tranne il primo)
    if(si>0){ const prev=segs[si-1], up=seg.fl<prev.fl;
      const ll=seg.pts[0];
      const m=L.marker(ll,{icon:L.divIcon({className:'route-tr',html:`<div class="rtr ${up?'up':'down'}">${up?'⬆':'⬇'}</div>`,iconSize:[24,24],iconAnchor:[12,12]})}).addTo(map);
      routeLayers.push(m);
    }
  });
  // start & goal
  const s=path[0], g=path[path.length-1];
  routeLayers.push(L.marker(blockToLL(s[0],s[1],s[2]),{icon:L.divIcon({className:'route-pin',html:'<div class="rpin start">A</div>',iconSize:[22,22],iconAnchor:[11,11]})}).addTo(map));
  routeLayers.push(L.marker(blockToLL(g[0],g[1],g[2]),{icon:L.divIcon({className:'route-pin',html:'<div class="rpin goal">B</div>',iconSize:[22,22],iconAnchor:[11,11]})}).addTo(map));
}
function routeSteps(path){
  const segs=segmentsByFloor(path); const steps=[];
  segs.forEach((seg,si)=>{
    if(si===0) steps.push(`Start from <b>floor ${seg.fl}</b>`);
    else{ const up=seg.fl<segs[si-1].fl; steps.push(`${up?'⬆ Go up (rope/ladder)':'⬇ Go down (hole/ladder)'} to <b>floor ${seg.fl}</b>`); }
  });
  return steps;
}
let lastRouteArgs=null;
function computeRoute(goalFl,goalLL){
  lastRouteArgs=[goalFl,goalLL];
  const gRaw=llToBlock(goalFl,goalLL); let gb=pwalk(...gRaw)?gRaw:nearestWalk(...gRaw);
  const sRaw=routeStart; let sb=pwalk(...sRaw)?sRaw:nearestWalk(...sRaw);
  const box=document.getElementById('verdictbody');
  document.getElementById('verdict').classList.add('show');
  if(!sb||!gb){ box.innerHTML='<div class="empty">Start or destination is not on known walkable ground.</div>'; return; }
  const res=findPath(sb,gb);
  if(!res){ box.innerHTML=`<div class="empty">🚫 No route found.<br><span style="color:var(--dim)">The minimap has sparse coverage in depth: some areas are separated by unmapped void or require passages (boat/teleport) that aren't tracked.</span></div>`; clearRoute(); return; }
  drawRoute(res.path);
  const steps=routeSteps(res.path);
  const floors=[...new Set(res.path.map(p=>p[0]))];
  box.innerHTML=`<div class="vsummary"><div class="big" style="color:var(--ok)">🧭 Route found</div>`+
    `<div class="cfg-note" style="margin-top:6px">${res.path.length} steps · ${floors.length} floors (${floors.join(', ')})</div></div>`+
    `<ol class="rsteps">`+steps.map(s=>`<li>${s}</li>`).join('')+`</ol>`+
    `<label class="ins-check" style="margin-top:6px"><input type="checkbox" id="dangerChk" ${dangerAvoid?'checked':''}/> Avoid mobs lethal for my char (safer route, not the shortest)</label>`+
    `<div class="cfg-note">Green trail on the current floor; faint segments = other floors. ⬆/⬇ = transition points. The route avoids walls/water/lava; with the option on it also weighs mobs 🔴 lethal for you (lesson from the fandom routes). A guide, not a guarantee: the map has unmapped areas, and action-gated passages (dig/lever/parcels) aren't tracked.</div>`;
}

// danger-avoid toggle inside the route result → recompute the same route
document.getElementById('verdictbody').addEventListener('change',e=>{
  if(e.target.id==='dangerChk'){ dangerAvoid=e.target.checked;
    if(lastRouteArgs) computeRoute(lastRouteArgs[0],lastRouteArgs[1]); }
});
// route mode wiring
const routeBtn=document.getElementById('routeBtn');
function setRouteHint(msg){ document.getElementById('verdict').classList.add('show');
  document.getElementById('verdictbody').innerHTML=`<div class="empty">${msg}</div>`; }
routeBtn.onclick=function(){
  routeMode=!routeMode; routeStart=null; clearRoute();
  this.classList.toggle('on',routeMode);
  this.textContent=routeMode?'🧭 Cancel route':'🧭 How to get there';
  if(routeMode){ selected=null; verdictMode=null;
    setRouteHint('🧭 Click the <b>START</b> on the map (current floor).<br><span style="color:var(--dim)">Then click the <b>DESTINATION</b> (even on another floor).</span>'); }
  else { document.getElementById('verdict').classList.remove('show'); }
};
map.on('click',e=>{
  if(!routeMode) return;
  if(!routeStart){ routeStart=llToBlock(curFloor,e.latlng);
    // aggancia al walkable più vicino
    if(!pwalk(...routeStart)){ const n=nearestWalk(...routeStart); if(n) routeStart=n; }
    clearRoute();
    routeLayers.push(L.marker(blockToLL(...routeStart),{icon:L.divIcon({className:'route-pin',html:'<div class="rpin start">A</div>',iconSize:[22,22],iconAnchor:[11,11]})}).addTo(map));
    setRouteHint('✅ Start set (floor '+routeStart[0]+').<br>Now click the <b>DESTINATION</b> (change floor if needed, then click).');
  } else {
    computeRoute(curFloor,e.latlng);
    routeMode=false; routeBtn.classList.remove('on'); routeBtn.textContent='🧭 How to get there';
  }
});

// ================= INSIGHTS MODAL =================
const insModal=document.getElementById('insModal');
const insBody=document.getElementById('insBody');
document.getElementById('insSub').textContent=
  `lvl ${INS.char.level} · dist ${INS.char.distance} · avg hit ${INS.avg_hit} (max ${INS.max_hit})`;

// live farmability verdict for a creature slug, computed from the current PG via assess()
function verdictDot(slug){
  const s=STATS[slug]; if(!s) return '';
  const a=assess(s); if(!a) return '';
  const col=a.cls==='ok'?'#5fd38a':a.cls==='warn'?'#ffb347':'#ff5d6c';
  return `<span class="vdot" style="--vc:${col}" title="${a.label} — kill ~${a.hitsToKill} hits, take ~${a.dmgTaken} (HP+heal ${ (s.health,'')}); from your char"></span>`;
}
function mobChip(m){
  // clickable chip -> selects the creature on the map; dot = FARMABILE/RISCHIOSO/LETALE from your PG
  return `<span class="mobchip" data-slug="${m.slug}" title="Click: highlight ${m.mob} on the map (HP ${m.hp}, ${m.spawns} spawn)">${verdictDot(m.slug)}${m.mob} <small>·${m.spawns}</small></span>`;
}
function lootTraders(r){
  // "Vendi a (NPC)" cell: top sell price headline + expandable full trader table
  // (every NPC with its city, buy and sell), exactly like items.php "Traded by".
  const ts=(r.traders||[]).filter(t=>t.sell!=null||t.buy!=null);
  if(!ts.length) return '<span style="color:var(--dim)">no NPC</span>';
  // sort: highest sell first (that's the "best place to sell" = the loot value)
  const bySell=ts.slice().sort((a,b)=>(b.sell||0)-(a.sell||0));
  const head = r.value>0
    ? `<span class="gp">${r.value.toLocaleString()} gp</span> <small style="color:var(--dim)">@ ${r.sell_npc||''}</small>`
    : '<span style="color:var(--dim)">NPC buy only</span>';
  const rows=bySell.map(t=>{
    const buy = t.buy!=null?`${t.buy.toLocaleString()}`:'—';
    const sell= t.sell!=null?`${t.sell.toLocaleString()}`:'—';
    return `<tr><td>${t.npc}</td><td class="tc">${t.city}</td>`+
           `<td class="tn">${buy}</td><td class="tn tsell">${sell}</td></tr>`;
  }).join('');
  return `<details class="trd"><summary>${head} <span class="trdn">${ts.length} NPC ▾</span></summary>`+
    `<table class="trd-tbl"><tr><th>NPC</th><th>City</th><th class="tn">Buys</th><th class="tn">Sells</th></tr>${rows}</table></details>`;
}
function renderLoot(){
  const priced=INS.loot_value.filter(r=>r.value>0).length;
  let h=`<input class="ins-search" id="lootSearch" placeholder="🔍 filter ${INS.loot_value.length} items… (e.g. ring, armor, gem)"/>`+
    `<label class="ins-check"><input type="checkbox" id="lootOnlyPriced"/> Only with NPC value (${priced}/${INS.loot_value.length})</label>`+
    '<table class="itab-tbl"><tr><th>Item</th><th>Sell to (NPC)*</th><th>Droppers (click to see on map)</th><th>#drop</th></tr><tbody id="lootRows">';
  for(const r of INS.loot_value){
    const gp = lootTraders(r);
    const chips = r.mobs.map(mobChip).join(' ');
    h+=`<tr data-k="${r.item.toLowerCase()}" data-priced="${r.value>0?1:0}"><td>${r.item}</td><td>${gp}</td>`+
       `<td>${chips}</td><td>${r.droppers}</td></tr>`;
  }
  return h+`</tbody></table><div style="color:var(--dim);font-size:11px;margin-top:8px">* <b>Real NPC sell price</b> (max Sell) from rivaliaonline.com/items.php — the NPC that pays most. "no NPC" = player-market only or junk. Up to 5 droppers/item, sorted by farmability (·number = spawns). <b>Click a mob</b> to highlight it on the map.</div>`;
}
let questSub='fandom';    // fandom | questlines | chests
let questlineOpen=null;   // slug of expanded questline
function renderQuests(){
  const sub=`<div class="ins-subtabs">`+
    `<button class="isub ${questSub==='fandom'?'on':''}" data-s="fandom">📜 Fandom Quests (${INS.quests.length})</button>`+
    `<button class="isub ${questSub==='questlines'?'on':''}" data-s="questlines">🗺️ Rivalia Questlines (${(INS.questlines||[]).length})</button>`+
    `<button class="isub ${questSub==='chests'?'on':''}" data-s="chests">🎁 Chest (${(INS.chests||[]).length})</button></div>`;
  if(questSub==='fandom') return sub+renderQuestFandom();
  if(questSub==='questlines') return sub+renderQuestlines();
  return sub+renderChests();
}
function renderQuestFandom(){
  const doable=INS.quests.filter(q=>q.doable).length;
  let h=`<input class="ins-search" id="questSearch" placeholder="🔍 filter ${INS.quests.length} quests… (e.g. armor, ring, demon)"/>`+
    `<label class="ins-check"><input type="checkbox" id="questOnlyDoable"/> Only doable at my level (${doable}/${INS.quests.length})</label>`+
    '<table class="itab-tbl"><tr><th>Quest</th><th>Rec. lvl</th><th>Reward (7.4 — verify)</th></tr><tbody id="questRows">';
  for(const q of INS.quests){
    const flag=q.doable?'<span class="qflag ok">✅ doable</span>':`<span class="qflag no">🔒 lv ${q.rec_level}</span>`;
    h+=`<tr data-k="${q.title.toLowerCase()}" data-doable="${q.doable?1:0}">`+
       `<td><b>${q.title}</b><br>${flag}</td><td>${q.rec_level??'—'}</td>`+
       `<td>${q.reward}</td></tr>`;
  }
  return h+`</tbody></table><div style="color:var(--dim);font-size:11px;margin-top:8px">TibiaWiki 7.4 mainland quests. ✅ = lvl ≤ ${INS.char.level} or unspecified. Reward/level <b>to confirm on Rivalia</b>.</div>`;
}
function renderQuestlines(){
  const qls=INS.questlines||[];
  if(questlineOpen){
    const q=qls.find(x=>x.slug===questlineOpen); if(!q){questlineOpen=null;return renderQuestlines();}
    let h=`<div class="route-back" id="qlBack">← All questlines</div><div class="route-detail"><h3>${q.title}</h3>`+
      `<div class="ap-meta">${q.missions.length} missions</div>`;
    for(const m of q.missions){
      h+=`<div style="margin-top:10px"><b style="color:var(--acc)">${m.no}. ${m.title}</b><ol class="route-steps" style="margin-top:4px">`+
         m.steps.map(s=>`<li>${s}</li>`).join('')+`</ol></div>`;
    }
    return h+`<div class="ins-note" style="border:0;padding:8px 0">Source: rivaliaonline.com (official Rivalia questlines). Step-by-step walkthrough.</div></div>`;
  }
  let h='<table class="itab-tbl"><tr><th>Questline</th><th>Missions</th></tr><tbody>';
  qls.forEach(q=>{ h+=`<tr><td><span class="flyto qlopen" data-slug="${q.slug}">${q.title}</span></td><td>${q.missions.length}</td></tr>`; });
  return h+'</tbody></table><div style="color:var(--dim);font-size:11px;margin-top:8px">Rivalia narrative questlines (multi-step). Click for the full walkthrough.</div>';
}
function renderFarm(){
  const keys=Object.keys(INS.farm);
  let h=`<input class="ins-search" id="farmSearch" placeholder="🔍 search an item among ${keys.length}… (e.g. spear, life ring, plate)"/>`+
    '<div id="farmRows">';
  for(const it of keys){
    const rows=INS.farm[it];
    h+=`<div class="farm-item" data-k="${it.toLowerCase()}"><div style="font-weight:700;color:var(--acc);margin-bottom:3px">🔨 ${it}</div>`+
       '<table class="itab-tbl"><tr><th>Mob</th><th>HP</th><th>#spawn</th><th>Farmability</th></tr>';
    rows.forEach((m,i)=>{
      const cls=i===0?' style="background:var(--panel2)"':'';
      h+=`<tr${cls}><td><span class="mobchip" data-slug="${m.slug}">${verdictDot(m.slug)}${m.mob}</span></td><td>${m.hp}</td><td>${m.mobs}</td><td class="eps">${m.score}</td></tr>`;
    });
    h+='</table></div>';
  }
  return h+'</div><div style="color:var(--dim);font-size:11px">Farmability = spawn density ÷ (HP/100). Higher = more drops/hour. Highlighted row = best dropper.</div>';
}
function renderAreas(){
  let h=`<input class="ins-search" id="areaSearch" placeholder="🔍 filter ${INS.areas.length} areas… (e.g. desert, cyclop, maze)"/>`+
    '<table class="itab-tbl"><tr><th>Area</th><th>xp/hit*</th><th>Rec. lvl</th><th>Creatures (real spawns)</th><th></th></tr><tbody id="areaRows">';
  INS.areas.forEach((a,i)=>{
    const eps = a.exp_per_shot>0 ? `<span class="eps">${a.exp_per_shot}</span>` : '<span style="color:var(--dim)">n/d</span>';
    const rl = (a.rec_level||'—').replace(/Knights?/i,'K').replace(/Paladins?/i,'P').replace(/Mages?/i,'M');
    const crs = a.creatures_present.slice(0,5).join(', ')||'—';
    h+=`<tr data-k="${a.name.toLowerCase()}"><td><b>${a.name}</b><br><span class="qflag ${a.spawn_near>0?'ok':'no'}">${a.spawn_near} Rivalia spawns</span></td>`+
       `<td>${eps}</td><td style="font-size:11px">${rl}</td><td style="font-size:11px">${crs}</td>`+
       `<td><span class="flyto" data-i="${i}">🎯 go</span></td></tr>`;
  });
  h+='</tbody></table><div style="color:var(--dim);font-size:11px;margin-top:8px">Areas = <b>TibiaWiki 7.4 hunting places</b> (references/hunting-places) placed on the map. "Rivalia spawns" = real mobs within 70 tiles of the coord (confirms the area exists on Rivalia). xp/hit computed on mobs kiteable with your damage. "go" opens the area on the map.</div>';
  return h;
}
let routeOpen=null;   // slug of expanded route, or null = list
function routeImg(name){
  const src=ROUTE_IMGS[name]; if(!src) return '';
  return `<img class="rimg" src="${src}" alt="${name}" loading="lazy"/>`;
}
function renderRoutes(){
  const rs=INS.routes||[];
  if(routeOpen){
    const r=rs.find(x=>x.slug===routeOpen); if(!r){routeOpen=null;return renderRoutes();}
    let h=`<div class="route-back" id="routeBack">← All routes</div>`+
      `<div class="route-detail"><h3>${r.route}</h3>`+
      `<div class="ap-meta">${r.from||''} → <b>${r.to||''}</b>${r.gate_level?` · Gate lv ${r.gate_level}`:''}</div>`+
      (r.equipment&&r.equipment.length?`<div class="ap-meta">🎒 ${r.equipment.join(', ')}</div>`:'')+
      (r.floor_transitions?`<div class="ap-meta">Floors: ${r.floor_transitions.join(' → ')}</div>`:'')+
      (r.hazards_all?`<div class="ap-meta">⚠️ ${r.hazards_all.join(', ')}</div>`:'')+
      `<ol class="route-steps">`;
    for(const s of (r.steps||[])){
      const imgs=Array.isArray(s.img)?s.img:(s.img?[s.img]:[]);
      const trans=s.to_floor?` <span class="rtag">→ z${s.to_floor}</span>`:'';
      const fl=s.floor!=null?`<span class="rtag">z${s.floor}</span>`:'';
      const hd=s.heading?`<span class="rtag dir">${s.heading}</span>`:'';
      const hz=(s.hazard&&s.hazard.length)?`<div class="rhz">⚠️ ${s.hazard.join(', ')}</div>`:'';
      h+=`<li>${fl}${hd}${trans} ${s.text||s.action||''}${hz}`+
         imgs.map(routeImg).join('')+`</li>`;
    }
    h+=`</ol>`;
    if(r.return||r.return_shortcut){const rt=r.return_shortcut||{}; h+=`<div class="route-ret"><b>↩ Return:</b> ${r.return||rt.text||''}</div>`;}
    h+=`<div class="ins-note" style="border:0;padding:8px 0">Source: TibiaWiki 7.4 (text + annotated maps). Walking logic reconstructed — verify in-game on Rivalia.</div></div>`;
    return h;
  }
  // list
  let h=`<input class="ins-search" id="routeSearch" placeholder="🔍 filter ${rs.length} routes…"/><table class="itab-tbl"><tr><th>Route</th><th>From → To</th><th>Floors</th></tr><tbody id="routeRows">`;
  for(const r of rs){
    const fl=r.floor_transitions?r.floor_transitions.length:'-';
    h+=`<tr data-k="${(r.route+' '+(r.to||'')).toLowerCase()}"><td><span class="flyto ropen" data-slug="${r.slug}">${r.route}</span></td>`+
       `<td style="font-size:11px">${r.from||'?'} → ${r.to||'?'}</td><td>${fl}</td></tr>`;
  }
  return h+`</tbody></table><div style="color:var(--dim);font-size:11px;margin-top:8px">Step-by-step walkthrough with the fandom's annotated maps. Click a route to open it.</div>`;
}
function renderChests(){
  const cs=INS.chests||[];
  let h=`<input class="ins-search" id="chestSearch" placeholder="🔍 filter ${cs.length} chests… (e.g. ring, armor, gold)"/>`+
    '<table class="itab-tbl"><tr><th>Chest</th><th>Loot</th><th>Floor</th><th></th></tr><tbody id="chestRows">';
  cs.forEach((c,i)=>{
    const loot=(c.items||[]).join(', ');
    const go=(c.px!=null)?`<span class="flyto chestgo" data-i="${i}">🎁 go</span>`:'';
    h+=`<tr data-k="${(c.name+' '+loot).toLowerCase()}"><td><b>${c.name}</b></td>`+
       `<td style="font-size:11px">${loot}</td><td>${c.z!=null?'z'+c.z:'—'}</td><td>${go}</td></tr>`;
  });
  return h+`</tbody></table><div style="color:var(--dim);font-size:11px;margin-top:8px">${cs.length} Rivalia reward chests (rivaliaonline.com), geolocated. "go" opens the chest on the map. Official Rivalia source — not 7.4 vanilla.</div>`;
}
const RENDER={areas:renderAreas,loot:renderLoot,quests:renderQuests,farm:renderFarm,routes:renderRoutes};
function showTab(t){
  if(t!=='routes') routeOpen=null;   // leaving routes resets the detail view
  [...document.querySelectorAll('.itab')].forEach(b=>b.classList.toggle('on',b.dataset.t===t));
  insBody.innerHTML=RENDER[t]();
}
document.querySelectorAll('.itab').forEach(b=>b.onclick=()=>showTab(b.dataset.t));
document.getElementById('insBtn').onclick=()=>{insModal.classList.add('show');showTab('areas');};
// delegated: route open/back + fly-to (areas) + mob-chip click (loot -> select creature on map)
insBody.addEventListener('click',e=>{
  const isub=e.target.closest('.isub');
  if(isub){ questSub=isub.dataset.s; questlineOpen=null; showTab('quests'); return; }
  const qlopen=e.target.closest('.qlopen');
  if(qlopen){ questlineOpen=qlopen.dataset.slug; showTab('quests'); return; }
  if(e.target.id==='qlBack'){ questlineOpen=null; showTab('quests'); return; }
  const ropen=e.target.closest('.ropen');
  if(ropen){ routeOpen=ropen.dataset.slug; showTab('routes'); return; }
  if(e.target.id==='routeBack'){ routeOpen=null; showTab('routes'); return; }
  const cg=e.target.closest('.chestgo');
  if(cg){ flyToChest(INS.chests[+cg.dataset.i]); return; }
  const fly=e.target.closest('.flyto');
  if(fly && fly.dataset.i!==undefined){ const a=INS.areas[+fly.dataset.i]; flyToArea(a.px,a.py,a.z); return; }
  const chip=e.target.closest('.mobchip');
  if(chip){
    const i=DATA.names.indexOf(chip.dataset.slug);
    if(i>=0){ insModal.classList.remove('show'); selectCreature(i); map.setZoom(Math.max(map.getZoom(),1)); }
    return;
  }
});
// quest filter: combines text search + "only doable" checkbox
function applyQuestFilter(){
  const s=document.getElementById('questSearch'); if(!s) return;
  const q=s.value.trim().toLowerCase();
  const onlyDo=document.getElementById('questOnlyDoable').checked;
  insBody.querySelectorAll('#questRows tr').forEach(tr=>{
    const okText=!q||tr.dataset.k.includes(q);
    const okDo=!onlyDo||tr.dataset.doable==='1';
    tr.style.display=(okText&&okDo)?'':'none';
  });
}
function applyLootFilter(){
  const s=document.getElementById('lootSearch'); if(!s) return;
  const q=s.value.trim().toLowerCase();
  const pc=document.getElementById('lootOnlyPriced');
  const onlyPriced=pc&&pc.checked;
  insBody.querySelectorAll('#lootRows tr[data-k]').forEach(tr=>{
    const okText=!q||tr.dataset.k.includes(q);
    const okPrice=!onlyPriced||tr.dataset.priced==='1';
    tr.style.display=(okText&&okPrice)?'':'none';
  });
}
// delegated search filter (loot rows + farm items + quest rows)
insBody.addEventListener('input',e=>{
  if(e.target.id==='questSearch'){ applyQuestFilter(); return; }
  if(e.target.id==='lootSearch'){ applyLootFilter(); return; }
  if(!e.target.classList.contains('ins-search')) return;
  const q=e.target.value.trim().toLowerCase();
  const sel=e.target.id==='farmSearch'?'.farm-item':'tr[data-k]';
  insBody.querySelectorAll(sel).forEach(el=>{
    el.style.display = (!q || el.dataset.k.includes(q)) ? '' : 'none';
  });
});
insBody.addEventListener('change',e=>{
  if(e.target.id==='questOnlyDoable') applyQuestFilter();
  if(e.target.id==='lootOnlyPriced') applyLootFilter();
});
document.getElementById('insClose').onclick=()=>insModal.classList.remove('show');
insModal.onclick=e=>{if(e.target===insModal)insModal.classList.remove('show');};

// ================= PK MAP MODAL =================
const pkModal=document.getElementById('playerModal');
const pkBody=document.getElementById('pkBody'), pkQ=document.getElementById('plQ');
const PK_PLAYERS=Object.values((PKMAP&&PKMAP.players)||{}).sort((a,b)=>b.danger_score-a.danger_score);
let pkFilter='all', pkSortKey='danger_score', pkSortAsc=false;
document.getElementById('pkNprof').textContent=(PKMAP&&PKMAP.n_profiles_scanned)||PK_PLAYERS.length;
document.getElementById('pkSub').textContent=PK_PLAYERS.length+' killer · '+((PKMAP&&PKMAP.total_unjustified)||'?')+' unjustified';
// annotate each filter chip with its count so the classes are self-explanatory
(function(){
  const cnt={};
  for(const p of PK_PLAYERS){cnt[p.class]=(cnt[p.class]||0)+1;}
  document.querySelectorAll('.pktab').forEach(t=>{
    const f=t.dataset.f, n=(f==='all')?PK_PLAYERS.length:(cnt[f]||0);
    t.innerHTML=t.textContent.replace(/\s*\(\d+\)$/,'')+' <span style="opacity:.6">('+n+')</span>';
  });
})();
function pkURL(n){return 'https://rivaliaonline.com/characterprofile.php?name='+encodeURIComponent(n);}
function pkBadge(c){
  if(c==='PK / Serial')return '<span class="pkb s">Serial</span>';
  if(c==='PK / Assassin')return '<span class="pkb a">Assassin</span>';
  if(c==='Occasional PK')return '<span class="pkb o">Occasional</span>';
  return '<span class="pkb g">Guild-war</span>';
}
function pkPass(p){
  const term=pkQ.value.trim().toLowerCase();
  // each chip = exactly one threat class (mutually exclusive); 'all' = no class filter
  if(pkFilter!=='all' && p.class!==pkFilter)return false;
  if(term){
    const inN=p.name.toLowerCase().includes(term);
    const inV=(p.victims||[]).some(v=>(v.victim||'').toLowerCase().includes(term));
    if(!inN&&!inV)return false;
  }
  return true;
}
function pkRender(){
  let rows=PK_PLAYERS.filter(pkPass);
  rows.sort((a,b)=>{let x=a[pkSortKey],y=b[pkSortKey];
    if(typeof x==='string'){x=(x||'').toLowerCase();y=(y||'').toLowerCase();}
    if(x==null)x=-1;if(y==null)y=-1;return (x<y?-1:x>y?1:0)*(pkSortAsc?1:-1);});
  const cols=[['name','Killer'],['level','Lv'],['vocation','Voc'],['class','Type'],['kills','K'],['unjustified','Unj'],['times_died_pvp','Deaths'],['avg_victim_level','Vic. lv'],['danger_score','Danger']];
  let h='<table><thead><tr><th></th>'+cols.map(c=>'<th data-k="'+c[0]+'"'+(c[0]===pkSortKey?' class="sorted'+(pkSortAsc?' asc':'')+'"':'')+'>'+c[1]+'</th>').join('')+'</tr></thead><tbody>';
  for(const p of rows){
    h+='<tr class="prow" data-n="'+encodeURIComponent(p.name)+'">'+
      '<td><span class="exp">▸</span></td>'+
      '<td><a href="'+pkURL(p.name)+'" target="_blank" rel="noopener">'+p.name+'</a></td>'+
      '<td class="n">'+(p.level??'?')+'</td>'+
      '<td>'+(p.vocation||'?')+'</td>'+
      '<td>'+pkBadge(p.class)+'</td>'+
      '<td class="n">'+p.kills+'</td>'+
      '<td class="n '+(p.unjustified?'u':'')+'">'+p.unjustified+'</td>'+
      '<td class="n">'+(p.times_died_pvp??0)+'</td>'+
      '<td class="n">'+(p.avg_victim_level??'?')+'</td>'+
      '<td class="n dscore">'+p.danger_score+'</td></tr>';
    const vl=(p.victims||[]).map(v=>'<div class="vrow"><span class="vn"><a href="'+pkURL(v.victim)+'" target="_blank" rel="noopener" style="color:inherit">'+v.victim+'</a> (Lv'+v.lv+')</span><span>'+v.date+'</span>'+(v.unjustified?'<span class="vu">UNJUSTIFIED</span>':'')+'</div>').join('');
    h+='<tr class="det" style="display:none"><td colspan="10"><b>Victims of '+p.name+'</b> · last login: '+(p.last_login||'?')+' · residence: '+(p.residence||'?')+'<div style="margin-top:5px">'+vl+'</div></td></tr>';
  }
  h+='</tbody></table>';
  pkBody.innerHTML=h;
}
pkBody.addEventListener('click',e=>{
  const th=e.target.closest('th[data-k]');
  if(th){const k=th.dataset.k; if(pkSortKey===k)pkSortAsc=!pkSortAsc; else {pkSortKey=k;pkSortAsc=false;} pkRender(); return;}
  const exp=e.target.closest('.exp');
  if(exp){const tr=exp.closest('tr'); const det=tr.nextElementSibling;
    const open=det.style.display!=='none'; det.style.display=open?'none':'table-row'; exp.textContent=open?'▸':'▾'; return;}
});
/* pkQ.oninput handled by shared player-modal wiring (single input plQ across both tabs) */
document.querySelectorAll('.pktab').forEach(t=>t.onclick=()=>{
  document.querySelectorAll('.pktab').forEach(x=>x.classList.remove('on'));
  t.classList.add('on'); pkFilter=t.dataset.f; pkRender();
});
/* PK open/close now handled by the shared 👥 Player modal wiring below (tab = Minaccia). */

// ===== 🕸️ Relazioni: esploratore ego-network (vista semplice, SVG a stella) =====
(function(){
  const relBody=document.getElementById('relBody'), relQ=document.getElementById('plQ');
  const P=(RELS&&RELS.players)||{}, EDGES=(RELS&&RELS.edges)||[];
  const relTypes={ally:true,enemy:true,cofaction:true};
  const COL={ally:'#4ade80',enemy:'#ef4444',cofaction:'#fbbf24'};
  document.getElementById('relNplayers').textContent=Object.keys(P).length;
  document.getElementById('relSub').textContent=Object.keys(P).length+' player · '+EDGES.length+' legami';
  const EMPTY='<div style="padding:34px;text-align:center;color:var(--dim)">Search a player, or pick one of the most connected above ↑</div>';

  // adjacency: name -> {other -> {ally,enemy,cofaction, guild}}
  const ADJ={}, DEG={};
  const grp=t=>t.indexOf('ally')===0?'ally':(t==='enemy_reciprocal'?'enemy':'cofaction');
  for(const e of EDGES){
    const g=grp(e.type);
    for(const pair of [[e.a,e.b],[e.b,e.a]]){
      const x=pair[0],y=pair[1];
      (ADJ[x]=ADJ[x]||{}); (ADJ[x][y]=ADJ[x][y]||{ally:0,enemy:0,cofaction:0});
      ADJ[x][y][g]+=e.w; if(e.guild)ADJ[x][y].guild=e.guild;
    }
    DEG[e.a]=(DEG[e.a]||0)+1; DEG[e.b]=(DEG[e.b]||0)+1;
  }
  const TOP=Object.keys(DEG).sort((a,b)=>DEG[b]-DEG[a]);
  const relURL=n=>'https://rivaliaonline.com/characterprofile.php?name='+encodeURIComponent(n);
  const meta=n=>P[n]||{};
  let current=null;

  function suggest(){
    document.getElementById('relSuggest').innerHTML='Most connected: '+
      TOP.slice(0,10).map(n=>'<a href="#" class="relseed" data-n="'+encodeURIComponent(n)+'">'+n+'</a>').join(' · ');
  }
  function render(name){
    current=name;
    const m=meta(name), adj=ADJ[name];
    if(!adj){
      const pk=(PKMAP&&PKMAP.players&&PKMAP.players[name]);
      relBody.innerHTML='<div style="padding:34px;text-align:center;color:var(--dim)">'+
        '<div style="font-size:15px;color:var(--txt);margin-bottom:6px">'+name+'</div>'+
        (pk?('lvl '+(pk.level==null?'?':pk.level)+' '+(pk.vocation||'')+' · class '+(pk.class||'?')):'')+
        '<div style="margin-top:10px">No relations recorded — <b>lone player</b>: no guild, no co-kill, no reciprocal enemies.</div>'+
        '<div style="margin-top:8px"><a href="'+relURL(name)+'" target="_blank" rel="noopener">Open profile ↗</a></div></div>';
      return;
    }
    let neigh=[];
    for(const o in adj){
      const r=adj[o];
      const anyActive=(relTypes.enemy&&r.enemy)||(relTypes.ally&&r.ally)||(relTypes.cofaction&&r.cofaction);
      if(!anyActive)continue;
      const prim=(relTypes.enemy&&r.enemy)?'enemy':((relTypes.ally&&r.ally)?'ally':'cofaction');
      neigh.push({o,prim,r,wsum:(r.ally||0)+(r.enemy||0)+(r.cofaction||0),guild:r.guild});
    }
    neigh.sort((a,b)=>b.wsum-a.wsum);
    const CAP=24, extra=Math.max(0,neigh.length-CAP);
    neigh=neigh.slice(0,CAP);
    const groups={enemy:[],ally:[],cofaction:[]};
    for(const nb of neigh)groups[nb.prim].push(nb);
    const W=920,H=600,cx=W/2,cy=H/2,R=Math.min(cx,cy)-104;
    // full-circle layout: each group gets an arc proportional to its size, so a dominant
    // group (e.g. many allies) spreads around most of the ring instead of cramming one side
    const order=['enemy','ally','cofaction'];
    const N=neigh.length||1, GAP=0.22;
    const ng=order.filter(g=>groups[g].length).length;
    const avail=2*Math.PI-GAP*Math.max(1,ng);
    const pos={}; let cur=-Math.PI/2+GAP/2;
    for(const g of order){
      const arr=groups[g], n=arr.length; if(!n)continue;
      const span=avail*(n/N);
      arr.forEach((nb,i)=>{
        const t=(n===1)?cur:(cur+span*i/(n-1));
        const rr=R+((i%2)?28:0);                       // alternate radius to de-collide labels
        pos[nb.o]={x:cx+rr*Math.cos(t),y:cy+rr*Math.sin(t),t:t};
      });
      cur+=span+GAP;
    }
    const trunc=s=>s.length>16?s.slice(0,15)+'…':s;
    let svg='<svg viewBox="0 0 '+W+' '+H+'" style="width:100%;height:auto" font-family="system-ui,sans-serif">';
    for(const nb of neigh){
      const p=pos[nb.o], sw=Math.max(1.3,Math.min(6,0.9+nb.r[nb.prim]*0.6));
      const dash=nb.prim==='cofaction'?' stroke-dasharray="4 3"':'';
      svg+='<line x1="'+cx+'" y1="'+cy+'" x2="'+p.x.toFixed(1)+'" y2="'+p.y.toFixed(1)+'" stroke="'+COL[nb.prim]+'" stroke-width="'+sw.toFixed(1)+'" stroke-opacity="0.6"'+dash+'/>';
    }
    for(const nb of neigh){
      const p=pos[nb.o], mm=meta(nb.o);
      const dsc=(mm.class||'').indexOf('Serial')>=0?'#ef4444':((mm.class||'').indexOf('Assassin')>=0?'#f97316':'#94a3b8');
      const tt=nb.o+' — '+[mm.vocation?(mm.vocation+' '+(mm.level||'')):'',nb.r.enemy?('enemy ×'+nb.r.enemy):'',nb.r.ally?('ally ×'+nb.r.ally+(nb.guild?(' ('+nb.guild+')'):'')):'',nb.r.cofaction?('co-faction ×'+nb.r.cofaction):''].filter(Boolean).join(' · ');
      const right=Math.cos(p.t)>=0, lx=(p.x+(right?10:-10)).toFixed(1), anc=right?'start':'end';
      svg+='<g class="relnode" data-n="'+encodeURIComponent(nb.o)+'" style="cursor:pointer"><title>'+tt+'</title>'+
        '<circle cx="'+p.x.toFixed(1)+'" cy="'+p.y.toFixed(1)+'" r="6.5" fill="'+COL[nb.prim]+'" stroke="'+dsc+'" stroke-width="2"/>'+
        '<text x="'+lx+'" y="'+(p.y+3.5).toFixed(1)+'" fill="var(--txt)" font-size="11" text-anchor="'+anc+'">'+trunc(nb.o)+'</text></g>';
    }
    svg+='<circle cx="'+cx+'" cy="'+cy+'" r="14" fill="#38bdf8" stroke="#fff" stroke-width="2.5"/>'+
      '<text x="'+cx+'" y="'+(cy-20)+'" fill="var(--txt)" font-size="14" font-weight="700" text-anchor="middle">'+name+'</text>'+
      '<text x="'+cx+'" y="'+(cy+30)+'" fill="var(--dim)" font-size="11" text-anchor="middle">'+(m.vocation||'?')+' '+(m.level||'')+(m.guild?(' · '+m.guild):'')+'</text></svg>';
    const counts={ally:0,enemy:0,cofaction:0}; for(const nb of neigh)counts[nb.prim]++;
    relBody.innerHTML='<div style="padding:4px 16px 0;font-size:12px;color:var(--dim)">'+
      '<a href="'+relURL(name)+'" target="_blank" rel="noopener">'+name+'</a> — 🟩 '+counts.ally+' allies · 🟥 '+counts.enemy+' enemies · 🟨 '+counts.cofaction+' co-faction'+
      (extra?(' · <i>+'+extra+' weaker links not shown</i>'):'')+'</div>'+svg;
  }
  function open(name){
    if(!P[name]){const hit=Object.keys(P).find(k=>k.toLowerCase()===name.toLowerCase()); if(hit)name=hit;}
    relQ.value=name; render(name);
  }
  relBody.addEventListener('click',e=>{const g=e.target.closest('.relnode'); if(g)open(decodeURIComponent(g.dataset.n));});
  document.getElementById('relSuggest').addEventListener('click',e=>{const a=e.target.closest('.relseed'); if(a){e.preventDefault();open(decodeURIComponent(a.dataset.n));}});
  function relRun(){
    const q=relQ.value.trim(); if(!q){relBody.innerHTML=EMPTY;return;}
    const exact=Object.keys(P).find(k=>k.toLowerCase()===q.toLowerCase());
    if(exact){render(exact);return;}
    const hits=Object.keys(P).filter(k=>k.toLowerCase().indexOf(q.toLowerCase())>=0).slice(0,12);
    if(hits.length===1){render(hits[0]);return;}
    if(!hits.length){
      // fall back to the full PK roster so a KNOWN but unconnected player (e.g. a pure victim)
      // still resolves to its "player solitario" card instead of a dead end
      const pk=(PKMAP&&PKMAP.players)||{};
      const pkExact=Object.keys(pk).find(k=>k.toLowerCase()===q.toLowerCase());
      if(pkExact){render(pkExact);return;}
      const pkHits=Object.keys(pk).filter(k=>k.toLowerCase().indexOf(q.toLowerCase())>=0).slice(0,12);
      if(pkHits.length===1){render(pkHits[0]);return;}
      if(pkHits.length){relBody.innerHTML='<div style="padding:20px 16px;color:var(--dim)">Maybe: '+pkHits.map(n=>'<a href="#" class="relseed" data-n="'+encodeURIComponent(n)+'">'+n+'</a>').join(' · ')+'</div>';return;}
    }
    relBody.innerHTML='<div style="padding:20px 16px;color:var(--dim)">'+(hits.length?('Maybe: '+hits.map(n=>'<a href="#" class="relseed" data-n="'+encodeURIComponent(n)+'">'+n+'</a>').join(' · ')):'No player found with this name in the crawl.')+'</div>';
  };
  document.querySelectorAll('.reltab').forEach(t=>t.onclick=()=>{const k=t.dataset.e;relTypes[k]=!relTypes[k];t.classList.toggle('on',relTypes[k]);if(current)render(current);else relRun();});
  // exposed for the shared 👥 Player modal wiring (tab = Relazioni)
  window._relSearch=relRun;
  window._relEnter=function(){ suggest(); const q=relQ.value.trim(); if(q) relRun(); else if(current) render(current); else relBody.innerHTML=EMPTY; };
})();

// ===== 👥 Player modal: shared search + tab switch (Minaccia/PK ↔ Relazioni) =====
(function(){
  const pm=document.getElementById('playerModal'), plQ=document.getElementById('plQ');
  const $=id=>document.getElementById(id);
  let ptab='pk';
  function applyTab(){
    document.querySelectorAll('.ptab').forEach(b=>b.classList.toggle('on',b.dataset.pt===ptab));
    const pk=(ptab==='pk');
    $('pkChips').style.display=pk?'':'none';
    $('relChips').style.display=pk?'none':'';
    $('relSuggest').style.display=pk?'none':'';
    $('pkBody').style.display=pk?'':'none';
    $('relBody').style.display=pk?'none':'';
    $('pkNote').style.display=pk?'':'none';
    $('relNote').style.display=pk?'none':'';
    $('pkSub').style.display=pk?'':'none';
    $('relSub').style.display=pk?'none':'';
    plQ.placeholder=pk?'Search killer or victim…':'Search a player… (e.g. Creepy Nuggett, Mala Cudna)';
    if(pk){ pkRender(); } else { window._relEnter&&window._relEnter(); }
  }
  plQ.addEventListener('input',()=>{ ptab==='pk'?pkRender():(window._relSearch&&window._relSearch()); });
  document.querySelectorAll('.ptab').forEach(b=>b.onclick=()=>{ ptab=b.dataset.pt; applyTab(); });
  function openPlayer(t){ ptab=t; pm.classList.add('show'); applyTab(); }
  $('pkMapBtn').onclick=()=>openPlayer('pk');
  $('relBtn').onclick=()=>openPlayer('rel');
  $('playerClose').onclick=()=>pm.classList.remove('show');
  pm.onclick=e=>{ if(e.target===pm) pm.classList.remove('show'); };
})();

// ---- MOBILE: bottom-sheet sidebar (tap handle or swipe to expand/collapse) ----
(function(){
  const side=document.getElementById('side'), h1=side&&side.querySelector('h1');
  if(!h1) return;
  const isMobile=()=>window.matchMedia('(max-width:820px)').matches;
  const setOpen=v=>{ side.classList.toggle('open',v);
    // map is fixed full-screen on mobile → recompute Leaflet size after any layout shift
    setTimeout(()=>{try{map.invalidateSize();}catch(e){}},320); };
  // starts peeking (closed) via CSS transform; tap the handle toggles
  h1.addEventListener('click',()=>{ if(isMobile()) setOpen(!side.classList.contains('open')); });
  // vertical swipe on the handle: up=open, down=close
  let y0=null;
  h1.addEventListener('touchstart',e=>{y0=e.touches[0].clientY;},{passive:true});
  h1.addEventListener('touchend',e=>{
    if(y0==null||!isMobile())return;
    const dy=(e.changedTouches[0].clientY)-y0;
    if(dy<-30)setOpen(true); else if(dy>30)setOpen(false);
    y0=null;
  },{passive:true});
  // tapping a control inside the sheet shouldn't fight the handle; recompute map on rotate
  window.addEventListener('orientationchange',()=>setTimeout(()=>{try{map.invalidateSize();}catch(e){}},350));
  // ensure the full-screen map sizes correctly once on load in mobile layout
  if(isMobile()) setTimeout(()=>{try{map.invalidateSize();}catch(e){}},400);
})();

// ================= HUNT-AREA OVERLAY =================
const areaLayer=L.layerGroup();
let areaOn=false;
function areaColor(eps,hi,lo){
  if(eps<=0) return '#8b93a4';                 // n/d = grey
  const t=(hi>lo)?(eps-lo)/(hi-lo):1;          // 0..1
  // red-ish (low) -> amber -> green (high)
  return t>=0.66?'#5fd38a':t>=0.33?'#ffb347':'#ff8a5d';
}
function drawAreas(){
  areaLayer.clearLayers();
  const epsVals=INS.areas.filter(a=>a.exp_per_shot>0).map(a=>a.exp_per_shot);
  const hi=Math.max(...epsVals), lo=Math.min(...epsVals);
  for(const a of INS.areas){
    if(a.z!==curFloor) continue;               // only areas on the current floor
    const col=areaColor(a.exp_per_shot,hi,lo);
    // 1) translucent zone circle (footprint) — radius is in map px = tiles
    const circle=L.circle([IMGH-a.py,a.px],{radius:a.radius,color:col,weight:2,
      fillColor:col,fillOpacity:.14,opacity:.7,className:'area-zone'});
    circle.on('click',()=>openAreaRef(a));
    areaLayer.addLayer(circle);
    // 2) label chip at the centre
    const eps=a.exp_per_shot>0?` · ${a.exp_per_shot} xp/hit`:'';
    const html=`<div class="azlabel" style="--ac:${col}" title="${a.name} · z${a.z} · ${a.spawn_near} Rivalia spawns · lvl ${a.rec_level||'?'} · ${a.creatures_present.slice(0,4).join(', ')}">🎯 ${a.name}${eps}</div>`;
    const m=L.marker([IMGH-a.py,a.px],{icon:L.divIcon({className:'area-pin',html,iconSize:null}),interactive:true});
    m.on('click',()=>openAreaRef(a));
    areaLayer.addLayer(m);
  }
}
function openAreaRef(a){
  // small popup with the area's key facts + creatures (click a creature to highlight)
  const crs=a.creatures_present.map(c=>{
    const slug=c.toLowerCase().replace(/ /g,'-').replace(/'/g,'');
    return `<span class="mobchip" data-slug="${slug}">${verdictDot(slug)}${c}</span>`;
  }).join(' ');
  const body=`<div class="area-pop"><div class="ap-hd">🎯 ${a.name}</div>`+
    `<div class="ap-meta">Floor z${a.z} · ${a.spawn_near} Rivalia spawns`+
    (a.exp_per_shot>0?` · <b class="eps">${a.exp_per_shot} xp/hit</b>`:'')+`</div>`+
    (a.rec_level?`<div class="ap-meta">Rec. level: ${a.rec_level}</div>`:'')+
    (a.loot?`<div class="ap-meta">Loot: ${a.loot}</div>`:'')+
    `<div class="ap-crs">${crs}</div>`+
    (a.route?`<div class="ap-route"><span class="flyto ropenpop" data-slug="${a.route.slug}">🧭 How to get there: ${a.route.route}</span></div>`:'')+
    `<div class="ap-note">Click a mob to highlight it on the map.</div></div>`;
  L.popup({maxWidth:320,className:'area-popup'}).setLatLng([IMGH-a.py,a.px]).setContent(body).openOn(map);
}
// clicking a mob chip inside an area popup selects that creature on the map
map.on('popupopen',ev=>{
  ev.popup._contentNode.querySelectorAll('.mobchip').forEach(ch=>{
    ch.onclick=()=>{ const i=DATA.names.indexOf(ch.dataset.slug);
      if(i>=0){ map.closePopup(); selectCreature(i); } };
  });
  const rp=ev.popup._contentNode.querySelector('.ropenpop');
  if(rp) rp.onclick=()=>{ map.closePopup(); routeOpen=rp.dataset.slug;
    insModal.classList.add('show'); showTab('routes'); };
});
function flyToArea(px,py,z){
  insModal.classList.remove('show');
  // ensure the area overlay is ON (don't toggle it off if already on)
  if(!areaOn){ areaOn=true; const btn=document.getElementById('areaBtn');
    btn.classList.add('on'); btn.textContent='🎯 Hunt areas: On'; areaLayer.addTo(map); }
  selectFloor(z,true);          // switch to the area's real hunting floor (redraws areas)
  map.setView([IMGH-py,px], 3);
}
document.getElementById('areaBtn').onclick=function(){
  areaOn=!areaOn; this.classList.toggle('on',areaOn);
  this.textContent=areaOn?'🎯 Hunt areas: On':'🎯 Hunt areas: Off';
  if(areaOn){drawAreas();areaLayer.addTo(map);} else {map.removeLayer(areaLayer);}
};
// redraw areas when floor changes
const _selFloor=selectFloor;
selectFloor=function(z,keepView){ _selFloor(z,keepView); if(areaOn) drawAreas(); };

// ================= CITY LANDMARKS =================
// Always-on city name labels on the surface floors, to orient on the map.
const cityLayer=L.layerGroup();
function drawCities(){
  cityLayer.clearLayers();
  for(const c of (INS.cities||[])){
    // show a city on its own floor, and also on the ground floor (z7) as a surface landmark
    if(c.z!==curFloor && !(curFloor===7 && c.z<=7)) continue;
    const html=`<div class="citylabel">🏰 ${c.name}</div>`;
    cityLayer.addLayer(L.marker([IMGH-c.py,c.px],{icon:L.divIcon({className:'city-pin',html,iconSize:null}),interactive:false}));
  }
}
let cityOn=true;
drawCities(); cityLayer.addTo(map);
// keep cities in sync on floor change (wrap selectFloor once more)
const _selFloor2=selectFloor;
selectFloor=function(z,keepView){ _selFloor2(z,keepView); if(cityOn) drawCities(); };
document.getElementById('cityBtn').onclick=function(){
  cityOn=!cityOn; this.classList.toggle('on',cityOn);
  this.textContent=cityOn?'🏰 Cities: On':'🏰 Cities: Off';
  if(cityOn){drawCities();cityLayer.addTo(map);} else {map.removeLayer(cityLayer);}
};

// ================= REWARD CHEST LAYER =================
const chestLayer=L.layerGroup();
let chestOn=false;
function drawChests(){
  chestLayer.clearLayers();
  for(const c of (INS.chests||[])){
    if(c.px==null || c.z!==curFloor) continue;
    const loot=(c.items||[]).slice(0,6).join(', ');
    const html=`<div class="chestpin" title="${c.name} — ${loot}">🎁</div>`;
    const m=L.marker([IMGH-c.py,c.px],{icon:L.divIcon({className:'chest-pin',html,iconSize:null})});
    m.bindTooltip(`🎁 ${c.name}`,{direction:'top',opacity:.9});
    m.on('click',()=>{
      L.popup({maxWidth:280,className:'area-popup'}).setLatLng([IMGH-c.py,c.px])
       .setContent(`<div class="area-pop"><div class="ap-hd">🎁 ${c.name}</div>`+
         `<div class="ap-meta">Floor z${c.z}</div>`+
         `<div class="ap-meta">Loot: ${(c.items||[]).join(', ')||'?'}</div></div>`).openOn(map);
    });
    chestLayer.addLayer(m);
  }
}
document.getElementById('chestBtn').onclick=function(){
  chestOn=!chestOn; this.classList.toggle('on',chestOn);
  this.textContent=chestOn?'🎁 Chest: On':'🎁 Chest: Off';
  if(chestOn){drawChests();chestLayer.addTo(map);} else {map.removeLayer(chestLayer);}
};
const _selFloor3=selectFloor;
selectFloor=function(z,keepView){ _selFloor3(z,keepView); if(chestOn) drawChests(); };
function flyToChest(c){
  insModal.classList.remove('show');
  if(!chestOn){chestOn=true;const btn=document.getElementById('chestBtn');btn.classList.add('on');btn.textContent='🎁 Chest: On';chestLayer.addTo(map);}
  selectFloor(c.z,true); map.setView([IMGH-c.py,c.px],3);
}

// ===== 🧙 NPC: directory modal (Rivalia authoritative) + approximate 7.7 map pins =====
(function(){
  const N=(NPCS&&NPCS.npcs)||[];
  const npcModal=document.getElementById('npcModal'), npcBody=document.getElementById('npcBody'), npcQ=document.getElementById('npcQ');
  document.getElementById('npcSub').textContent=N.length+' NPC · '+(NPCS.n_with_offers||0)+' with offers';
  document.getElementById('npcNcoord').textContent=(NPCS.n_with_coords||0);
  const npcURL=n=>'https://rivaliaonline.com/npcs.php?npc='+encodeURIComponent(n);
  function offers(list,label){
    if(!list||!list.length) return '';
    const rows=list.map(o=>`<tr><td>${o.item}</td><td class="tn">${o.amount==null?'':o.amount}</td><td class="tn">${o.price!=null?o.price.toLocaleString()+' gp':'—'}</td></tr>`).join('');
    return `<details class="trd"><summary>${label} (${list.length})</summary><table class="trd-tbl"><tr><th>Item</th><th class="tn">Qty</th><th class="tn">Price</th></tr>${rows}</table></details>`;
  }
  function renderNpc(){
    const byCity={};
    for(const n of N){ const c=n.city||'Unknown'; (byCity[c]=byCity[c]||[]).push(n); }
    const cities=Object.keys(byCity).sort((a,b)=>{  // named cities by size, 'Unknown' always last
      if(a==='Unknown') return 1; if(b==='Unknown') return -1;
      return byCity[b].length-byCity[a].length; });
    let h='';
    for(const c of cities){
      const arr=byCity[c].slice().sort((a,b)=>a.name.localeCompare(b.name));
      h+=`<details class="npc-city" open><summary><b>${c}</b> <span style="color:var(--dim)">(${arr.length})</span></summary>`;
      for(const n of arr){
        const go=n.px!=null?`<button class="npc-go" data-x="${n.px}" data-y="${n.py}" data-z="${n.z}" title="Go to the map (approximate position, ref 7.7)">📍</button>`:'';
        const kw=(n.name+' '+c+' '+[...(n.sell||[]),...(n.buy||[])].map(o=>o.item).join(' ')).toLowerCase().replace(/"/g,'');
        const hasInfo=(n.sell&&n.sell.length)||(n.buy&&n.buy.length);
        h+=`<div class="npc-row" data-k="${kw}"><div><b class="npc-name">${n.name}</b> <small style="color:var(--dim)">${n.type||''}</small> ${go}`+
           `<a href="${npcURL(n.name)}" target="_blank" rel="noopener" class="npc-web" title="open the card on the Rivalia site">↗</a></div>`+
           (hasInfo?(offers(n.sell,'🛒 Buy here')+offers(n.buy,'💰 Sell here')):'<div style="color:var(--dim);font-size:11.5px;padding:2px 0">no trade offers</div>')+`</div>`;
      }
      h+='</details>';
    }
    npcBody.innerHTML=h;
  }
  npcQ.addEventListener('input',()=>{
    const q=npcQ.value.trim().toLowerCase();
    npcBody.querySelectorAll('.npc-row').forEach(r=>{ r.style.display=(!q||r.dataset.k.indexOf(q)>=0)?'':'none'; });
  });
  npcBody.addEventListener('click',e=>{ const g=e.target.closest('.npc-go'); if(g) flyToNpc(+g.dataset.x,+g.dataset.y,+g.dataset.z); });
  document.getElementById('npcBtn').onclick=()=>{ npcModal.classList.add('show'); if(!npcBody.innerHTML) renderNpc(); };
  document.getElementById('npcClose').onclick=()=>npcModal.classList.remove('show');
  npcModal.onclick=e=>{ if(e.target===npcModal) npcModal.classList.remove('show'); };

  // approximate pin layer (Tibiantis 7.7 coords)
  const npcLayer=L.layerGroup(); let npcOn=false;
  function drawNpcs(){
    npcLayer.clearLayers();
    for(const n of N){
      if(n.px==null || n.z!==curFloor) continue;
      const m=L.marker([IMGH-n.py,n.px],{icon:L.divIcon({className:'npc-pin',html:'<div class="npcpin">🧙</div>',iconSize:null})});
      m.bindTooltip('🧙 '+n.name+(n.city?(' · '+n.city):''),{direction:'top',opacity:.9});
      m.on('click',()=>{
        const sell=(n.sell||[]).slice(0,6).map(o=>o.item+(o.price!=null?' '+o.price+'gp':'')).join(', ');
        const buy=(n.buy||[]).slice(0,6).map(o=>o.item+(o.price!=null?' '+o.price+'gp':'')).join(', ');
        L.popup({maxWidth:300,className:'area-popup'}).setLatLng([IMGH-n.py,n.px])
         .setContent(`<div class="area-pop"><div class="ap-hd">🧙 ${n.name}</div>`+
           `<div class="ap-meta">${n.type||''} · ${n.city||'?'} · <i>approx. position (7.7)</i></div>`+
           (sell?`<div class="ap-meta">🛒 Buy: ${sell}</div>`:'')+
           (buy?`<div class="ap-meta">💰 Sell: ${buy}</div>`:'')+`</div>`).openOn(map);
      });
      npcLayer.addLayer(m);
    }
  }
  document.getElementById('npcPinBtn').onclick=function(){
    npcOn=!npcOn; this.classList.toggle('on',npcOn); this.textContent=npcOn?'📍 NPC: On':'📍 NPC: Off';
    if(npcOn){ drawNpcs(); npcLayer.addTo(map); } else { map.removeLayer(npcLayer); }
  };
  const _selNpc=selectFloor; selectFloor=function(z,keep){ _selNpc(z,keep); if(npcOn) drawNpcs(); };
  window.flyToNpc=function(px,py,z){
    npcModal.classList.remove('show');
    if(!npcOn){ npcOn=true; const b=document.getElementById('npcPinBtn'); b.classList.add('on'); b.textContent='📍 NPC: On'; npcLayer.addTo(map); }
    selectFloor(z,true); map.setView([IMGH-py,px],3);
  };
})();

// ===== 📋 TASK HELPER: user picks a weekly task (a monster) → best spot + how, for their char =====
(function(){
  const $=id=>document.getElementById(id);
  const taskModal=$('taskModal'), taskBody=$('taskBody'), taskQ=$('taskQ');
  // task options = huntable creatures (real spawns, not bosses) — the user picks one at a time
  const OPTS=[...DATA.names.keys()].filter(i=>!(DATA.boss&&DATA.boss[i]) && (DATA.crFloors[i]||[]).length)
     .sort((a,b)=>DATA.display[a].localeCompare(DATA.display[b]));
  const OPTS_ITEM=Object.keys(INS.farm||{}).sort();   // deliver tasks = farmable items (body parts / drops)
  $('taskSub').textContent=OPTS.length+' monsters · '+OPTS_ITEM.length+' items';
  let mode='mon', selMon=null, selItem=null;
  const dotcol=cls=>cls==='ok'?'#5fd38a':cls==='warn'?'#ffb347':'#ff5d6c';
  function areaFor(i){ let best=null; const nm=DATA.display[i].toLowerCase();
    for(const ar of (INS.areas||[])){ if((ar.creatures_present||[]).some(c=>c.toLowerCase()===nm)){ if(!best||(ar.exp_per_shot||0)>(best.exp_per_shot||0)) best=ar; } }
    return best; }
  function densest(i){ let f=null,bc=-1; for(const z of (DATA.crFloors[i]||[])){ const c=pts(z).filter(p=>p[0]===i).length; if(c>bc){bc=c;f=z;} } return {floor:f,count:bc}; }
  function whereShort(i){ const ar=areaFor(i),df=densest(i); return ar?`${ar.name} · z${ar.z}`:(df.floor!=null?`floor z${df.floor}`:'—'); }
  // jump the map to EXACTLY the spot the card recommends (fix: don't stay on the wrong floor)
  function jumpTo(i){
    if(i==null||i<0) return;
    taskModal.classList.remove('show');
    selectCreature(i);                                  // highlight this creature's spawns + verdict
    const ar=areaFor(i), df=densest(i);
    if(ar){ selectFloor(ar.z,true); map.setView([IMGH-ar.py,ar.px],3); }
    else if(df.floor!=null){ selectFloor(df.floor,true); const pt=pts(df.floor).find(p=>p[0]===i); if(pt) map.setView([IMGH-pt[2],pt[1]],2); }
  }
  function card(i){
    const slug=DATA.names[i], s=STATS[slug], a=s?assess(s):null, ar=areaFor(i), df=densest(i), spr=spriteFor(i);
    const badge=a?`<span class="vbadge ${a.cls}">${a.label}</span>`:'<span class="vbadge warn" style="opacity:.6">no stats</span>';
    const where = ar
      ? `Best area: <b>${ar.name}</b> <span style="color:var(--dim)">(floor z${ar.z}${ar.exp_per_shot>0?' · '+ar.exp_per_shot+' xp/hit':''}${ar.rec_level?' · rec lvl '+ar.rec_level:''})</span>`
      : (df.floor!=null?`Densest on <b>floor z${df.floor}</b> <span style="color:var(--dim)">(${df.count} spawn clusters)</span>`:'no fixed spawn (boss/event)');
    const how=[];
    if(a){ how.push(a.isRanged?'ranged mob — break line of sight or close the gap':'melee mob — kite it (shoot & retreat)');
      (a.notes||[]).forEach(n=>{ if(/mana/i.test(n)) how.push(n); }); }
    const metrics=a?`<div class="ap-meta">Kill in ~${a.ttk}s (${a.hitsToKill} turns) · you take ~${a.dmgTaken} (HP+heal budget ${a.healBudget})</div>`:'';
    const h=`<div class="vhead" style="margin-bottom:6px">${spr?`<img src="${spr}">`:''}<div class="vn">${DATA.display[i]}</div>${badge}</div>`+
      `<div class="ap-meta">📍 ${where}</div>`+
      `<div class="ap-meta">Floors: <b>${(DATA.crFloors[i]||[]).join(', ')||'—'}</b> · ${DATA.total[i]} total spawns</div>`+
      metrics+
      (how.length?`<ul class="vnotes" style="margin:6px 0 4px">`+how.map(n=>`<li>${n}</li>`).join('')+`</ul>`:'')+
      `<div style="margin-top:8px"><button class="btn" id="taskGo" style="max-width:220px">🎯 Show on map</button>`+
      (ar&&ar.route?` <span class="flyto taskRoute" data-slug="${ar.route.slug}" style="margin-left:8px">🧭 how to get there</span>`:'')+`</div>`;
    return `<div style="background:var(--panel2);border:1px solid var(--line);border-radius:10px;padding:10px 12px;margin-bottom:10px">${h}</div>`;
  }
  function cardItem(item){
    const drops=(INS.farm[item]||[]).slice().sort((a,b)=>(b.score||0)-(a.score||0)).slice(0,6);
    const rows=drops.map(d=>{
      const i=DATA.names.indexOf(d.slug); const s=(i>=0)?STATS[d.slug]:null, a=s?assess(s):null;
      const badge=a?`<span class="vbadge ${a.cls}" style="padding:1px 8px;font-size:10px">${a.label}</span>`:'';
      const go=(i>=0)?`<button class="btn dropGo" data-i="${i}" style="padding:2px 9px;font-size:11px;max-width:110px">🎯 map</button>`:'';
      return `<div class="pgrow"><span class="pgtag" style="flex:1;min-width:120px">${d.mob} ${badge}</span><span class="pgm">${(i>=0)?whereShort(i):'—'}</span><span class="pgm">×${d.mobs}</span> ${go}</div>`;
    }).join('') || '<div class="ap-meta">No known dropper on the map.</div>';
    return `<div style="background:var(--panel2);border:1px solid var(--line);border-radius:10px;padding:10px 12px;margin-bottom:10px">`+
      `<div class="vhead" style="margin-bottom:4px"><div class="vn">📦 ${item}</div></div>`+
      `<div class="ap-meta">Farm it from — best droppers for your char (🟢 farmable · 🟡 risky · 🔴 lethal):</div>${rows}</div>`;
  }
  const EMPTY_ROW='<div class="empty" style="padding:20px;color:var(--dim);text-align:center">No match.</div>';
  const PROMPT='<div style="padding:14px 4px;color:var(--dim);text-align:center">Select a task below to see the best place &amp; way to do it ↓</div>';
  function monList(){
    const q=taskQ.value.trim().toLowerCase(); let rows='';
    for(const i of OPTS){ if(q && !DATA.display[i].toLowerCase().includes(q)) continue;
      const s=STATS[DATA.names[i]], a=s?assess(s):null;
      const dot=a?`<span class="vdot" style="--vc:${dotcol(a.cls)}"></span>`:'';
      rows+=`<div class="crow taskopt${i===selMon?' on':''}" data-i="${i}">${spriteChip(i,22)}<span class="nm">${dot}${DATA.display[i]}</span><span class="fl">${(DATA.crFloors[i]||[]).join(',')}</span><span class="ct">${DATA.total[i]}</span></div>`;
    }
    return `<div id="taskList">${rows||EMPTY_ROW}</div>`;
  }
  function itemList(){
    const q=taskQ.value.trim().toLowerCase(); let rows='';
    for(const it of OPTS_ITEM){ if(q && !it.toLowerCase().includes(q)) continue;
      const n=(INS.farm[it]||[]).length;
      rows+=`<div class="crow taskitem${it===selItem?' on':''}" data-item="${encodeURIComponent(it)}"><span class="nm">📦 ${it}</span><span class="ct">${n} drop${n===1?'':'s'}</span></div>`;
    }
    return `<div id="taskList">${rows||EMPTY_ROW}</div>`;
  }
  function render(){
    if(mode==='mon') taskBody.innerHTML=(selMon!=null?card(selMon):PROMPT)+monList();
    else taskBody.innerHTML=(selItem!=null?cardItem(selItem):PROMPT)+itemList();
  }
  taskBody.addEventListener('click',e=>{
    const opt=e.target.closest('.taskopt'); if(opt){ selMon=+opt.dataset.i; render(); taskBody.scrollTop=0; return; }
    const it=e.target.closest('.taskitem'); if(it){ selItem=decodeURIComponent(it.dataset.item); render(); taskBody.scrollTop=0; return; }
    if(e.target.id==='taskGo'){ jumpTo(selMon); return; }
    const dg=e.target.closest('.dropGo'); if(dg){ jumpTo(+dg.dataset.i); return; }
    const rt=e.target.closest('.taskRoute'); if(rt){ taskModal.classList.remove('show'); routeOpen=rt.dataset.slug; insModal.classList.add('show'); showTab('routes'); return; }
  });
  taskQ.addEventListener('input',render);
  document.querySelectorAll('#taskMode .tktab').forEach(b=>b.onclick=()=>{
    mode=b.dataset.m; document.querySelectorAll('#taskMode .tktab').forEach(x=>x.classList.toggle('on',x===b));
    taskQ.placeholder = mode==='mon'?'Filter targets… (e.g. cyclops, dragon, minotaur)':'Filter items… (e.g. leather, paw, silk, cheese)';
    render();
  });
  $('taskBtn').onclick=()=>{ taskModal.classList.add('show'); render(); };
  $('taskClose').onclick=()=>taskModal.classList.remove('show');
  taskModal.onclick=e=>{ if(e.target===taskModal) taskModal.classList.remove('show'); };
})();

/* ============================================================================
   MOBILE APP SHELL  (≤820px only — desktop returns immediately)
   Rebuilds the mobile UX as a native-feeling map app. It does NOT duplicate any
   feature logic:
     · stateful panels (#search, #clist, #verdict, #stats, #pgSec, the title)
       are MOVED into the sheet → every listener already bound stays bound;
     · every toggle / modal opener stays in the (hidden) #side and is driven by
       a PROXY chip or list row that .click()s it and mirrors its state through a
       MutationObserver → one source of truth, no drift.
   Layout: map = canvas · #mtop chips = map layers · #mfloor = floor stepper ·
   #msheet = the one sheet (closed/peek/half/full, draggable) · #mnav = tab bar.
   ============================================================================ */
(function(){
  if(!window.matchMedia('(max-width:820px)').matches) return;
  const $=id=>document.getElementById(id);
  const sheet=$('msheet'), grab=$('mshGrab'), peek=$('mshPeek'), sbody=$('mshBody'),
        nav=$('mnav'), chips=$('mtop'), fpop=$('floors');
  const PANES={cr:$('mpCr'),hunt:$('mpHunt'),npc:$('mpNpc'),pl:$('mpPl'),me:$('mpMe')};
  const TITLES={
    cr:['🐉 Creatures','search a monster → every spawn lights up on the map'],
    hunt:['🎯 Hunt','areas, loot value, quests, weekly tasks, routes'],
    npc:['🧙 NPC','355 NPCs — what they buy/sell, and where they stand'],
    pl:['👥 Players','Aeternum threat map + relationship graph'],
    me:['⚔️ My Char','your party drives every farmable / risky / lethal verdict']};
  const mk=(tag,cls,html)=>{const e=document.createElement(tag);
    if(cls)e.className=cls; if(html!=null)e.innerHTML=html; return e;};

  /* ---- 1. move the stateful panels into the sheet ---- */
  const sw=mk('div','msearch'); sw.appendChild($('search'));
  const det=mk('div'); det.id='mcrDetail'; det.style.display='none';
  det.appendChild($('verdict')); det.appendChild($('stats'));
  PANES.cr.append(sw, det, $('clist'));
  PANES.me.append(document.querySelector('#side h1'), $('pgSec'));

  /* ---- 2. proxies: chips (map layers) + list rows (menu) ---- */
  const obs=[];
  function bind(b,fn){ fn(); const o=new MutationObserver(fn);
    o.observe(b,{attributes:true,attributeFilter:['class'],childList:true,
                 characterData:true,subtree:true}); obs.push(o); }
  const isOn=b=>b.classList.contains('on');
  const suffix=b=>{const m=b.textContent.match(/:\s*(.+)$/);return m?m[1].trim():null;};
  function chip(id,icon,label){
    const b=$(id); if(!b) return;
    const c=mk('button','mchip'); c.title=b.title||'';
    c.onclick=()=>b.click();
    bind(b,()=>{ c.classList.toggle('on',isOn(b));
      const s=suffix(b);
      c.innerHTML=icon+' '+label+(s&&/auto|always/i.test(s)?' <b>'+s+'</b>':''); });
    chips.appendChild(c);
  }
  function row(pane,id,icon,label,o){
    const b=$(id); if(!b) return; o=o||{};
    const r=mk('button','mrow');
    r.innerHTML='<span class="mri">'+icon+'</span><span class="mrt">'+label+
      (o.desc===false?'':'<small>'+(b.title||'').replace(/</g,'&lt;')+'</small>')+'</span>'+
      (o.toggle?'<span class="mrs"></span>'
              :'<span class="mrs" style="background:none;border:none;color:var(--dim);font-size:17px;padding:0">›</span>');
    r.onclick=()=>{ b.click(); if(o.close) collapse(); };
    pane.appendChild(r);
    if(o.toggle){ const p=r.querySelector('.mrs');
      bind(b,()=>{ p.textContent=suffix(b)||(isOn(b)?'On':'Off');
                   p.classList.toggle('on',isOn(b)); }); }
  }
  chip('areaBtn','🎯','Areas');   chip('npcPinBtn','📍','NPCs');
  chip('chestBtn','🎁','Chests'); chip('cityBtn','🏰','Cities');
  chip('sprMode','🖼️','Icons');  chip('routeBtn','🧭','Route');

  PANES.hunt.appendChild(mk('div','msec','On the map'));
  row(PANES.hunt,'areaBtn','🎯','Hunt areas',{toggle:1});
  row(PANES.hunt,'routeBtn','🧭','How to get there',{toggle:1,close:1});
  PANES.hunt.appendChild(mk('div','msec','Tools'));
  row(PANES.hunt,'insBtn','💎','Insights');
  row(PANES.hunt,'taskBtn','📋','Task Helper');

  PANES.npc.appendChild(mk('div','msec','Directory'));
  row(PANES.npc,'npcBtn','🧙','NPC directory');
  PANES.npc.appendChild(mk('div','msec','On the map'));
  row(PANES.npc,'npcPinBtn','📍','Show NPC pins',{toggle:1,close:1});

  PANES.pl.appendChild(mk('div','msec','Aeternum'));
  row(PANES.pl,'pkMapBtn','☠️','Threat / PK map');
  row(PANES.pl,'relBtn','🕸️','Relations graph');

  PANES.me.appendChild(mk('div','msec','Map display'));
  row(PANES.me,'sprMode','🖼️','Creature icons',{toggle:1});
  row(PANES.me,'cityBtn','🏰','City names',{toggle:1});
  row(PANES.me,'chestBtn','🎁','Reward chests',{toggle:1});
  PANES.me.appendChild(mk('div','msec','Selection'));
  row(PANES.me,'toAll','🗺️','Show all monsters',{close:1});
  row(PANES.me,'clearSel','✖️','Clear selection',{close:1});
  PANES.me.appendChild(mk('div','msec','How to use it on the phone'));
  PANES.me.appendChild(mk('div','sec legend',
    '• <b>🐉 Creatures</b> → type a name, tap a result: the sheet drops to a card and '+
    'the map lights up every spawn.<br>'+
    '• On the card, tap a <b>z-chip</b> to jump floor, or the card itself for full stats + verdict.<br>'+
    '• <b>Chips on top</b> switch map layers (areas, NPCs, chests, cities, icons, route).<br>'+
    '• <b>Floor pill</b> on the right: ▲▼ steps to the next floor that has spawns, tap the number for the grid. 7 = ground.<br>'+
    '• Drag the sheet handle to resize it; pan the map and it gets out of the way.<br>'+
    '• The hover scanner and the floor-veil overlays are mouse-only — they stay on desktop.'));

  /* ---- 3. sheet: detents + state ---- */
  let H=0,PK=0,state='closed',pane=null,sel=null;
  function measure(){ H=sheet.offsetHeight; PK=grab.offsetHeight+peek.offsetHeight; }
  function pos(s){ if(!H)measure();
    return s==='full'?0:s==='half'?Math.round(H*0.52):s==='peek'?Math.max(0,H-PK):H; }
  function syncNav(){ nav.querySelectorAll('button').forEach(b=>{
      b.classList.toggle('on',(state==='half'||state==='full')&&b.dataset.p===pane);
      if(b.dataset.p==='cr') b.classList.toggle('act',sel!=null); }); }
  function snap(s,silent){ measure(); state=s;
    sheet.style.transform='translateY('+pos(s)+'px)'; syncNav();
    if(!silent) setTimeout(()=>{try{map.invalidateSize();}catch(e){}},340); }
  function showPane(p){ pane=p;
    Object.keys(PANES).forEach(k=>PANES[k].classList.toggle('on',k===p)); }
  function collapse(){ if(sel!=null&&pane!=='cr') showPane('cr');
    renderPeek(); snap(sel!=null?'peek':'closed'); }
  function chev(){ const c=peek.querySelector('.mphc');
    if(c) c.textContent = state==='full'?'▾':'▴'; }

  function renderPeek(){
    if(sel!=null && (pane==='cr'||pane==null)){
      const i=sel, boss=DATA.boss&&DATA.boss[i], s=STATS[DATA.names[i]];
      const a=(!boss&&s)?assess(s):null;
      const badge=a?'<span class="vbadge '+a.cls+'">'+a.label+'</span>':'';
      const spr=spriteFor(i);
      const where= boss ? '👑 boss · no fixed spawn'
        : DATA.crFloors[i].map(z=>'<span class="mfchip'+(z===curFloor?' cur':'')+'" data-z="'+z+'">z'+z+'</span>').join('')
          +'<span style="opacity:.85">'+DATA.total[i]+' spawn</span>';
      peek.innerHTML='<div class="mpk">'+(spr?'<img src="'+spr+'" alt="">':'')+
        '<span class="mpn"><span class="mpnt">'+DATA.display[i]+' '+badge+'</span>'+
        '<span class="mpns">'+where+'</span></span>'+
        '<button class="mpx" title="deselect">✕</button></div>';
      peek.querySelector('.mpx').onclick=e=>{e.stopPropagation();selectCreature(null);};
      peek.querySelectorAll('.mfchip').forEach(c=>c.onclick=e=>{
        e.stopPropagation(); selectFloor(+c.dataset.z); });
      peek.querySelector('.mpk').onclick=()=>snap(state==='full'?'peek':'full');
    }else{
      const t=TITLES[pane||'cr'];
      peek.innerHTML='<div class="mph"><span class="mpht">'+t[0]+'<small>'+t[1]+
        '</small></span><span class="mphc">'+(state==='full'?'▾':'▴')+'</span></div>';
      peek.querySelector('.mph').onclick=()=>{ snap(state==='full'?'half':'full'); chev(); };
    }
  }

  /* ---- 4. tab bar ---- */
  nav.querySelectorAll('button').forEach(b=>b.onclick=()=>{
    const p=b.dataset.p;
    if(pane===p&&(state==='half'||state==='full')){ collapse(); return; }
    showPane(p); sbody.scrollTop=0;
    if(p==='cr') det.style.display = sel!=null?'block':'none';
    renderPeek(); snap('half');
  });

  /* ---- 5. creature selection drives the sheet (replaces the old FAB/bar/sheet trio) ---- */
  crSheetShow=function(i){
    sel=(i==null?null:i);
    if(sel==null){ det.style.display='none';
      if(pane==='cr'&&(state==='half'||state==='full')) renderPeek();
      else { renderPeek(); snap('closed'); }
      syncNav(); return; }
    showPane('cr'); det.style.display='block';
    const s=$('search'); if(s) s.blur();
    fpop.classList.remove('mopen');
    renderPeek(); snap('peek');          // map stays visible → exploration first
  };
  const se=$('search');
  if(se) se.addEventListener('focus',()=>{ showPane('cr'); renderPeek(); snap('full'); });

  /* ---- 6. drag the handle / peek row between detents ---- */
  let y0=0,t0=0,base=0,dragging=false;
  function down(e){ const p=e.touches?e.touches[0]:e;
    y0=p.clientY; t0=Date.now(); base=pos(state); dragging=true;
    sheet.classList.add('dragging'); }
  function move(e){ if(!dragging)return; const p=e.touches?e.touches[0]:e;
    let y=base+(p.clientY-y0); y=Math.max(-24,Math.min(H,y));
    sheet.style.transform='translateY('+y+'px)';
    if(e.cancelable) e.preventDefault(); }
  function up(e){ if(!dragging)return; dragging=false; sheet.classList.remove('dragging');
    const p=e.changedTouches?e.changedTouches[0]:e, dy=p.clientY-y0;
    if(Math.abs(dy)<6){ sheet.style.transform='translateY('+pos(state)+'px)'; return; } // tap → let the click through
    const cur=base+dy, dt=Date.now()-t0, fast=Math.abs(dy)/Math.max(1,dt)>0.6;
    const cands=['full','half'].concat(sel!=null?['peek']:[]).concat(['closed'])
                 .sort((a,b)=>pos(a)-pos(b));
    let best=cands[0],bd=1e9;
    cands.forEach(s=>{const d=Math.abs(pos(s)-cur); if(d<bd){bd=d;best=s;}});
    if(fast){ const i=cands.indexOf(best)+(dy<0?-1:1);
      if(i>=0&&i<cands.length) best=cands[i]; }
    snap(best); chev();
  }
  [grab,peek].forEach(el=>{
    el.addEventListener('touchstart',down,{passive:true});
    el.addEventListener('touchmove',move,{passive:false});
    el.addEventListener('touchend',up,{passive:true});
    el.addEventListener('mousedown',down);
  });
  window.addEventListener('mousemove',move);
  window.addEventListener('mouseup',up);

  /* ---- 7. floor pill + grid popover (replaces the 16-button column) ---- */
  function mfSync(){ $('mfNow').innerHTML=curFloor+
    '<small>'+((DATA.floorcount[curFloor]||0)||'·')+'</small>'; }
  const _sf=selectFloor;
  selectFloor=function(z,keepView){ _sf(z,keepView); mfSync();
    if(sel!=null&&state==='peek') renderPeek(); };
  function step(d){ let z=curFloor+d;
    while(z>=0&&z<=15&&!(DATA.floorcount[z]||0)) z+=d;
    if(z>=0&&z<=15) selectFloor(z); }
  $('mfUp').onclick=()=>step(-1);        // ▲ = one floor up (lower z)
  $('mfDn').onclick=()=>step(1);
  $('mfNow').onclick=e=>{ e.stopPropagation(); fpop.classList.toggle('mopen'); };
  fpop.addEventListener('click',()=>setTimeout(()=>fpop.classList.remove('mopen'),0));
  map.on('movestart',()=>fpop.classList.remove('mopen'));
  map.on('dragstart',()=>{ if(state==='half'||state==='full') collapse(); });
  mfSync();

  /* ---- 8. boot / viewport changes ---- */
  window.addEventListener('resize',()=>{ measure();
    sheet.style.transform='translateY('+pos(state)+'px)'; });
  window.addEventListener('orientationchange',()=>setTimeout(()=>snap(state),350));
  requestAnimationFrame(()=>{ measure(); renderPeek(); snap('closed',true);
    setTimeout(()=>{try{map.invalidateSize();}catch(e){}},300); });
})();

buildDanger();   // initial per-tile danger from the default PG
buildList();
draw();
</script>
</body>
</html>'''

html = (TEMPLATE.replace('__MAPDATA__', mapdata).replace('__IMGS__', imgs)
        .replace('__STATS__', stats).replace('__SPRITES__', sprites)
        .replace('__PATHGRID__', pathgrid).replace('__PATHTRANS__', pathtrans)
        .replace('__INSIGHTS__', insights).replace('__ROUTEIMGS__', route_imgs_json)
        .replace('__PKMAP__', pkmap)
        .replace('__RELS__', rels)
        .replace('__NPCS__', npcs))
open(OUTFILE,'w').write(html)
print("HTML written:", OUTFILE, len(html), "bytes", "(INLINE)" if INLINE else "(external sprites)")
