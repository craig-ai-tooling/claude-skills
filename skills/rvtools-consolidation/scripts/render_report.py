#!/usr/bin/env python3
"""Render consolidate.py output as a two-page Spectro Cloud branded report (HTML, optionally PDF).

usage:
  render_report.py OUT/scenarios.json --customer "Acme" --data-date 8/20/26 \
                   --html report.html [--pdf report.pdf]

PDF printing uses headless Chrome/Chromium: $CHROME, then google-chrome / chromium on PATH,
then a puppeteer-cached Chrome under ~/.cache/puppeteer, then the macOS app bundle.
"""
import argparse, datetime, glob, html, json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(HERE, "..", "assets"))


def esc(s):
    return html.escape(str(s))


def n(x):
    return f"{x:,.0f}"


def money(x, cur):
    return f"{cur}{x / 1e6:.1f}M" if abs(x) >= 1e6 else f"{cur}{x / 1e3:,.0f}K"


def svg(name, style):
    raw = open(os.path.join(ASSETS, name)).read()
    raw = re.sub(r"<\?xml[^>]*\?>", "", raw)
    return re.sub(r"<svg\b", f'<svg style="{style}"', raw, count=1)


def join(items):
    items = list(items)
    return ", ".join(items[:-1]) + (" and " if len(items) > 1 else "") + (items[-1] if items else "")


def describe(s, cfg):
    lic = [i["name"] for i in cfg["islands"] if i.get("kind", "isolation") == "license"]
    iso = [i["name"] for i in cfg["islands"] if i.get("kind", "isolation") == "isolation"]
    L = cfg["limits"]
    general = {"cluster": "Every source cluster becomes its own target cluster",
               "env": "General-purpose clusters merge per site into one prod and one non-prod pool",
               "site": "All general-purpose clusters at a site merge into one pool (prod + non-prod)"}[s["general"]]
    if s["islands"] == "cluster":
        islands = "Licensing and isolation clusters stay exactly as they are"
    elif s["islands"] == "merge-isolation":
        islands = (f"{join(iso)} merge per site" if iso else "") + \
                  (f"; {join(lic)} clusters stay as-is" if lic else "")
    else:
        islands = f"{join(lic + iso)} each merge into one pool per site"
    memory = (f"VM memory right-sized to consumed &times; {s['rightsize']}" if s.get("rightsize")
              else "VMs keep their configured memory")
    return [general, islands.lstrip("; "), f"{memory}; nodes packed to {s['fill']:.0%} memory",
            f"+{L['spares_per_cluster']} spare node per target cluster, {L['min_nodes']}-node minimum"]


def find_chrome():
    cands = [os.environ.get("CHROME")] + [shutil.which(b) for b in
                                          ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome")]
    cands += sorted(glob.glob(os.path.expanduser("~/.cache/puppeteer/chrome/*/chrome-*/chrome")), reverse=True)
    cands += ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
    return next((c for c in cands if c and os.path.exists(c)), None)


CSS = """
@page { size: letter; margin: 12px 22px; }
:root { --primary:#043736; --primary-mid:#005B5B; --primary-light:#1F7A78; --accent:#F0BE65; --accent-light:#F5D48A;
  --accent-dim:#DE8D2A; --ink:#012121; --paper:#F7F1ED; --surface:#FFFFFF; --border:#D0D5DD; --text-dim:#4A5568;
  --teal:#1F7A78; --green:#1A7A4C; --radius:10px; }
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:'Plus Jakarta Sans','Trebuchet MS',-apple-system,sans-serif; background:var(--paper); color:var(--ink);
  line-height:1.45; -webkit-print-color-adjust:exact; print-color-adjust:exact; }
.page { min-height:calc(100vh - 24px); display:flex; flex-direction:column; }
.page-break { break-before:page; }
.container { max-width:1040px; margin:0 auto; padding:6px 34px; width:100%; }
.header { background:linear-gradient(135deg,var(--primary) 0%,var(--primary-mid) 45%,var(--primary-light) 100%); color:#fff; padding:13px 36px 11px; }
.header-inner { max-width:1040px; margin:0 auto; }
.logo-row { display:flex; align-items:center; gap:14px; margin-bottom:10px; }
.logo-text { font-size:14px; font-weight:700; color:rgba(255,255,255,.9); }
.logo-divider { width:1px; height:22px; background:rgba(255,255,255,.25); }
.badge { display:inline-flex; background:rgba(240,190,101,.2); border:1px solid rgba(240,190,101,.4); color:var(--accent-light);
  font-size:9px; font-weight:700; letter-spacing:.1em; text-transform:uppercase; padding:3px 12px; border-radius:100px; margin-bottom:8px; }
.header h1 { font-size:23px; font-weight:800; letter-spacing:-.025em; line-height:1.14; margin-bottom:5px; }
.header h1 span { color:var(--accent); }
.header p { color:rgba(255,255,255,.7); font-size:10.5px; max-width:720px; line-height:1.4; }
.section-title { font-size:10px; font-weight:700; letter-spacing:.1em; text-transform:uppercase; color:var(--primary-mid);
  margin:8px 0 4px; display:flex; align-items:center; gap:7px; }
.section-title::before { content:''; width:3px; height:12px; background:var(--accent); border-radius:2px; }
.stat-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:8px; }
.stat-card { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); padding:7px 10px 8px;
  text-align:center; position:relative; overflow:hidden; }
.stat-card::before { content:''; position:absolute; top:0; left:0; right:0; height:3px; background:linear-gradient(90deg,var(--primary-mid),var(--accent)); }
.stat-card.today::before { background:var(--border); }
.stat-number { font-size:22px; font-weight:800; color:var(--primary-mid); letter-spacing:-.03em; line-height:1.1; }
.today .stat-number { color:var(--text-dim); }
.stat-label { font-size:9px; font-weight:700; color:var(--ink); text-transform:uppercase; letter-spacing:.05em; margin-top:2px; }
.stat-detail { font-size:8.5px; color:var(--accent-dim); margin-top:2px; line-height:1.3; font-weight:600; }
table.t { width:100%; border-collapse:collapse; font-size:9.5px; border:1px solid var(--border); }
table.t th { background:var(--primary); color:rgba(255,255,255,.9); font-weight:700; font-size:8.5px; text-transform:uppercase;
  letter-spacing:.06em; padding:4px 10px; text-align:right; }
table.t th:first-child, table.t td:first-child { text-align:left; }
table.t td { padding:2px 10px; border-bottom:1px solid var(--border); color:var(--text-dim); background:var(--surface); text-align:right; }
table.t td:first-child { font-weight:600; color:var(--ink); }
table.t tr.strong td { font-weight:800; color:var(--primary-mid); background:rgba(240,190,101,.10); }
table.t tr.site td { background:var(--paper); color:var(--primary-mid); font-weight:800; font-size:8.5px; text-transform:uppercase; letter-spacing:.06em; }
table.t.small { font-size:8.3px; } table.t.small td { padding:1px 7px; } table.t.small th { padding:3px 7px; font-size:7.8px; }
.cards { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; }
.card { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); overflow:hidden; }
.card h4 { font-size:10.5px; font-weight:800; color:var(--ink); padding:6px 11px; border-bottom:1px solid var(--border); }
.card h4 span { color:var(--accent-dim); font-weight:800; margin-right:5px; }
.card ul { list-style:none; padding:5px 11px 7px; }
.card li { font-size:8.5px; color:var(--text-dim); padding:1.5px 0 1.5px 10px; position:relative; line-height:1.35; }
.card li::before { content:''; position:absolute; left:0; top:6px; width:4px; height:4px; border-radius:50%; background:var(--primary-mid); }
.callout { font-size:9px; color:var(--text-dim); padding:7px 12px; background:var(--surface); border-left:3px solid var(--accent);
  border-radius:0 8px 8px 0; line-height:1.45; margin-top:8px; }
.callout strong { color:var(--ink); }
.two { display:grid; grid-template-columns:1fr 1fr; gap:10px; align-items:start; }
.fine { font-size:8px; color:var(--text-dim); line-height:1.4; }
.fine li { margin:0 0 2px 12px; }
.next { display:grid; grid-template-columns:1fr 1fr; gap:4px 16px; list-style:none; }
.next li { font-size:8.7px; color:var(--text-dim); line-height:1.35; padding-left:16px; position:relative; }
.next li b { color:var(--ink); }
.next li::before { content:counter(step); counter-increment:step; position:absolute; left:0; top:0; font-weight:800; color:var(--accent-dim); }
.next { counter-reset:step; }
.page-footer { display:flex; align-items:center; justify-content:space-between; padding:4px 34px 0; border-top:2px solid var(--teal); margin-top:auto; }
.footer-left { font-size:9px; color:var(--text-dim); }
.footer-right { display:flex; align-items:center; gap:10px; font-size:8px; font-weight:700; color:var(--primary-mid); text-transform:uppercase; letter-spacing:.05em; }
@media print { .card, .stat-card, table.t tr { break-inside:avoid; } }
"""


def render(d, customer, data_date, month):
    cfg, e, S = d["config"], d["estate"], d["scenarios"]
    first = S[0]
    cur = cfg["pricing"].get("currency", "$")
    prices = cfg["pricing"].get("unit_prices") or []
    node = cfg["node"]
    model = node.get("model_match")
    logo_white = svg("spectrocloud-logo-horizontal-knockout-white.svg", "height:18px;width:auto")
    logo_foot = svg("spectrocloud-logo-horizontal-currentcolor.svg", "height:14px;width:auto;opacity:.6;color:#012121")
    sites = e["sites"]

    def footer(page):
        return (f'<div class="page-footer"><div class="footer-left">Confidential &mdash; Prepared for {esc(customer)}</div>'
                f'<div class="footer-right">Page {page} of 2 {logo_foot}</div></div>')

    # ---- page 1
    cards = [f'<div class="stat-card today"><div class="stat-number">{n(e["hosts"])}</div><div class="stat-label">Hosts today</div>'
             f'<div class="stat-detail">{n(e["hosts_active"])} in service &middot; {n(e["clusters"])} clusters</div></div>']
    for s in S:
        t = s["totals"]
        detail = (f'{n(t["working"])} working + {n(t["spares"])} spare' if s is first
                  else f'{n(t["avoided_vs_first"])} fewer than {esc(first["key"])} &middot; {n(t["spares"])} spare')
        cards.append(f'<div class="stat-card"><div class="stat-number">{n(t["total"])}</div>'
                     f'<div class="stat-label">{esc(s["key"])} &middot; {esc(s["name"])}</div><div class="stat-detail">{detail}</div></div>')
    head = "".join(f'<th>{esc(s["key"])} &middot; {esc(s["name"])}</th>' for s in S)

    def row(label, vals, cls=""):
        return f'<tr class="{cls}"><td>{label}</td>' + "".join(f"<td>{v}</td>" for v in vals) + "</tr>"

    rows = [row("Target clusters", [n(s["totals"]["clusters"]) for s in S]),
            row("Working nodes", [n(s["totals"]["working"]) for s in S]),
            row("Spare nodes (N+1 and 3-node minimum)", [n(s["totals"]["spares"]) for s in S]),
            row(f"Total nodes", [n(s["totals"]["total"]) for s in S], "strong")]
    if model and e["owned_target_model"]:
        rows.append(row(f"Net-new to buy beyond the {n(e['owned_target_model'])} {esc(model)}s already owned",
                        [n(s["totals"]["net_new"]) for s in S]))
    rows.append(row(f"Servers avoided vs {esc(first['key'])}", ["&mdash;"] + [n(s["totals"]["avoided_vs_first"]) for s in S[1:]], "strong"))
    for p in prices:
        rows.append(row(f"Hardware avoided at {money(p, cur)} per server",
                        ["&mdash;"] + [money(s["totals"]["avoided_vs_first"] * p, cur) for s in S[1:]]))
    site_rows = "".join(
        row(esc(site), [n(e["by_site"][site]["hosts"]), n(e["by_site"][site]["clusters"])] +
            [n(s["totals"]["by_site"][site]) for s in S]) for site in sites)
    site_rows += row("Total", [n(e["hosts"]), n(e["clusters"])] + [n(s["totals"]["total"]) for s in S], "strong")
    assume = "".join(
        f'<div class="card"><h4><span>{esc(s["key"])}</span>{esc(s["name"])}</h4><ul>'
        + "".join(f"<li>{x}</li>" for x in describe(s, cfg)) + "</ul></div>" for s in S[:3])
    decomp = ""
    if d.get("decomposition"):
        dc = d["decomposition"]
        last = next(s for s in S if s["key"] == dc["scenario"])
        parts = " &middot; ".join(f'<strong>{n(st["nodes_avoided"])}</strong> from {esc(st["lever"])}' for st in dc["steps"])
        decomp = (f'<div class="callout"><strong>Where {esc(last["key"])}&rsquo;s {n(last["totals"]["avoided_vs_first"])} '
                  f'servers come from:</strong> {parts}. Merging is the part no application owner has to approve &mdash; '
                  f'it removes spare nodes and part-filled nodes that exist only because of cluster boundaries.</div>')
    price_note = (f" Dollar rows are a sensitivity range at {join(money(p, cur) for p in prices)} per server, not a quote."
                  if prices else "")
    p1 = f"""
<div class="page">
<div class="header"><div class="header-inner">
  <div class="logo-row"><div class="logo-text">{esc(customer)}</div><div class="logo-divider"></div>{logo_white}</div>
  <div class="badge">Consolidation Scenarios &mdash; {esc(month)}</div>
  <h1>Land the VMware estate on <span>fewer servers</span></h1>
  <p>Every one of {n(e["vms"])} powered-on VMs across {join(esc(s) for s in sites)} bin-packed onto
  {esc(node["name"])} from RVTools exports dated {esc(data_date)}. Three ways to land it: keep every cluster,
  consolidate moderately, or consolidate aggressively.{price_note}</p>
</div></div>
<div class="container">
  <div class="section-title">Servers needed by scenario</div>
  <div class="stat-grid">{''.join(cards[:4])}</div>
  <div class="section-title">Scenario comparison</div>
  <table class="t"><tr><th></th>{head}</tr>{''.join(rows)}</table>
  {decomp}
  <div class="section-title">What each scenario assumes</div>
  <div class="cards">{assume}</div>
  <div class="section-title">By site</div>
  <table class="t"><tr><th>Site</th><th>Hosts today</th><th>Clusters today</th>{"".join(f'<th>{esc(s["key"])}</th>' for s in S)}</tr>{site_rows}</table>
</div>
{footer(1)}
</div>"""

    # ---- page 2
    def pool_table(s):
        body = ""
        for site in sites:
            rs = [r for r in s["pools"] if r["site"] == site]
            body += f'<tr class="site"><td colspan="4">{esc(site)} &middot; {n(s["totals"]["by_site"][site])} nodes</td></tr>'
            for r in sorted(rs, key=lambda r: (-r["total"], r["pool"])):
                k = len(r["sources"])
                src = ("as-is" if r["sources"] == [r["pool"]]
                       else f'{k} cluster{"s" if k != 1 else ""} &middot; {n(r["source_hosts"])} hosts')
                cpu = " *" if r["binding"] == "cpu" else ""
                body += (f'<tr><td>{esc(r["pool"])}</td><td>{src}</td><td>{n(r["vms"])}</td>'
                         f'<td>{r["working"]} + {r["spares"]}{cpu}</td></tr>')
        return (f'<div><div class="section-title">{esc(s["key"])} &middot; {esc(s["name"])} &mdash; target clusters</div>'
                f'<table class="t small"><tr><th>Target</th><th>From</th><th>VMs</th><th>Working + spare</th></tr>{body}</table></div>')

    shown = S[1:3] if len(S) > 1 else S
    L = cfg["limits"]
    lic = [i["name"] for i in cfg["islands"] if i.get("kind", "isolation") == "license"]
    iso = [i["name"] for i in cfg["islands"] if i.get("kind", "isolation") == "isolation"]
    cpu_bound = sorted({r["pool"] for s in shown for r in s["pools"] if r["binding"] == "cpu"})
    method = [
        f"Packing: first-fit decreasing by memory, with allocated vCPU capped at {L['vcpu_per_thread']} per hardware thread "
        f"({node['threads']} threads per node). Node memory planned at {n(node['ram_gib'])} GiB.",
        f"Measured CPU: each pool keeps its measured host CPU below {L['cpu_measured_cap']:.0%} of target cores. "
        + (f"CPU, not memory, sets the size of the pools marked * ({join(esc(p) for p in cpu_bound)})."
           if cpu_bound else "Memory is the binding constraint everywhere."),
        f"Resilience: +{L['spares_per_cluster']} spare node per target cluster, {L['min_nodes']}-node minimum, no cluster larger than "
        f"{d['max_nodes_applied']} nodes (the largest cluster in the estate today). {L['vm_overhead_gib']} GiB KubeVirt overhead per VM.",
        "Scope: powered-on, non-template VMs. Clusters with nothing powered on retire with vSphere. Pools never span sites.",
        "Boundaries: " + (f"{join(lic)} are licensing boundaries, merged only in the aggressive scenario. " if lic else "")
        + (f"{join(iso)} are tenant or failure-domain boundaries, never mixed with other workloads." if iso else ""),
        "Right-sizing uses RVTools <em>Consumed</em> memory, a point-in-time reading. It needs VM-owner sign-off, or KubeVirt memory overcommit, before it is real.",
    ]
    nxt = [
        "<b>Price the build.</b> Replace the sensitivity range with the reseller&rsquo;s quote for the target node.",
        "<b>Confirm the boundaries.</b> Licensing and tenant islands above are inferred from cluster names.",
        "<b>Validate right-sizing</b> against 30+ days of utilization before counting on the aggressive number.",
        "<b>Pick a level per site.</b> Scenarios can be mixed: aggressive where teams agree, moderate elsewhere.",
    ]
    p2 = f"""
<div class="page page-break">
<div class="container">
  <div class="two">{''.join(pool_table(s) for s in shown)}</div>
  <div class="section-title">Method &amp; assumptions</div>
  <ul class="fine">{''.join(f'<li>{m}</li>' for m in method)}</ul>
  <div class="section-title">Before this becomes a design</div>
  <ul class="next">{''.join(f'<li>{x}</li>' for x in nxt)}</ul>
</div>
{footer(2)}
</div>"""
    return (f'<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>{esc(customer)} &mdash; Consolidation Scenarios</title>'
            f'<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">'
            f'<style>{CSS}</style></head><body>{p1}{p2}</body></html>')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scenarios")
    ap.add_argument("--customer", required=True)
    ap.add_argument("--data-date", required=True, help="RVTools export date, e.g. 8/20/26")
    ap.add_argument("--month", default=datetime.date.today().strftime("%B %Y"))
    ap.add_argument("--html", required=True)
    ap.add_argument("--pdf")
    a = ap.parse_args()
    d = json.load(open(a.scenarios))
    open(a.html, "w").write(render(d, a.customer, a.data_date, a.month))
    print("wrote", a.html)
    if a.pdf:
        chrome = find_chrome()
        if not chrome:
            sys.exit("no Chrome/Chromium found -- set $CHROME, or print the HTML to PDF from a browser")
        subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={os.path.abspath(a.pdf)}", "file://" + os.path.abspath(a.html)],
                       check=True, capture_output=True, timeout=120)
        pages = len(re.findall(rb"/Type\s*/Page[^s]", open(a.pdf, "rb").read()))
        print(f"wrote {a.pdf} ({pages} pages)")
        if pages != 2:
            print("WARNING: expected 2 pages -- trim content or tighten CSS", file=sys.stderr)


if __name__ == "__main__":
    main()
