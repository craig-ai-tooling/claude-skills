#!/usr/bin/env python3
"""Bin-pack powered-on VMs from RVTools exports onto a target node spec, per scenario.

usage:
  consolidate.py --site "Chicago=Chicago RVTools_export_all.xlsx" --site "London=London.xlsx" \
                 [--config customer.json] --out DIR

A --site path may be an RVTools .xlsx or a directory of CSVs whose names contain the sheet
name (vInfo, vHost, vMemory). One site = one vCenter export; pools never cross sites.
Standard library only -- no pandas/openpyxl needed.

Writes DIR/scenarios.json and DIR/cluster_mapping.csv, prints a summary.
Config keys you omit fall back to DEFAULTS below; see SKILL.md for what each one means.
"""
import argparse, collections, copy, csv, glob, json, math, os, re, sys, zipfile
import xml.etree.ElementTree as ET

DEFAULTS = {
    "node": {"name": "Target node", "ram_gib": 1024, "cores": 64, "threads": 128, "model_match": None},
    "limits": {
        "vcpu_per_thread": 4,        # allocated vCPU ceiling per hardware thread
        "cpu_measured_cap": 0.70,    # measured host CPU may use at most this share of target cores
        "vm_overhead_gib": 0.25,     # KubeVirt virt-launcher overhead per VM
        "min_nodes": 3,              # per target cluster (control-plane quorum)
        "max_nodes": None,           # per target cluster; None = largest source cluster today
        "spares_per_cluster": 1,     # N+1
        "holding_max_vms": 2,        # clusters this small are staging, not workload boundaries
    },
    # kind "license": boundary exists for software licensing -- only merged in "merge" mode
    # kind "isolation": tenant / appliance / anti-affinity boundary -- merged per class from "merge-isolation"
    "islands": [
        {"name": "Oracle EE", "match": r"ORACLE.*(^|[-_ ])EE([-_ 0-9]|$)|(^|[-_ ])EE([-_ ]).*ORACLE", "kind": "license"},
        {"name": "Oracle SE", "match": r"ORACLE", "kind": "license"},
        {"name": "IBM", "match": r"IBM", "kind": "license"},
    ],
    "holding": r"^$|ESXI.?UPGRADE",
    "nonprod": r"(^|[-_ .])(DEV|NP|NONPROD|TST|TEST|QA|UAT|STG|STAGE|DRTEST|PSR|PERF|BUILD|SANDBOX|LAB)([-_ .0-9]|$)",
    "scenarios": [
        {"key": "A", "name": "Cluster-for-cluster", "general": "cluster", "islands": "cluster",
         "fill": 0.80, "rightsize": None},
        {"key": "B", "name": "Moderate consolidation", "general": "env", "islands": "merge-isolation",
         "fill": 0.80, "rightsize": None},
        {"key": "C", "name": "Aggressive consolidation", "general": "site", "islands": "merge",
         "fill": 0.90, "rightsize": 1.2},
    ],
    "pricing": {"unit_prices": [], "currency": "$"},
}

# ---------------------------------------------------------------- xlsx / csv reading
M = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


def _col(ref):
    n = 0
    for ch in ref:
        if ch.isalpha():
            n = n * 26 + ord(ch.upper()) - 64
        else:
            break
    return n - 1


def read_xlsx(path, wanted):
    z = zipfile.ZipFile(path)
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        for _, el in ET.iterparse(z.open("xl/sharedStrings.xml")):
            if el.tag == M + "si":
                shared.append("".join(t.text or "" for t in el.iter(M + "t")))
                el.clear()
    rels = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
    out = {}
    for s in ET.fromstring(z.read("xl/workbook.xml")).find(M + "sheets"):
        name = s.get("name")
        if name not in wanted:
            continue
        target = rels[s.get(R + "id")].lstrip("/")
        part = target if target.startswith("xl/") else "xl/" + target
        rows = []
        for _, el in ET.iterparse(z.open(part)):
            if el.tag != M + "row":
                continue
            cells, nxt = {}, 0
            for c in el.iter(M + "c"):
                i = _col(c.get("r")) if c.get("r") else nxt
                nxt = i + 1
                t, v = c.get("t"), c.find(M + "v")
                if t == "s":
                    val = shared[int(v.text)] if v is not None else ""
                elif t == "inlineStr":
                    val = "".join(x.text or "" for x in c.iter(M + "t"))
                elif t == "b":
                    val = "True" if v is not None and v.text == "1" else "False"
                else:
                    val = v.text if v is not None and v.text is not None else ""
                cells[i] = val
            rows.append([cells.get(i, "") for i in range(max(cells) + 1)] if cells else [])
            el.clear()
        out[name] = rows
    missing = set(wanted) - set(out)
    if missing:
        sys.exit(f"{path}: missing sheets {sorted(missing)}")
    return out


def read_csv_dir(path, wanted):
    out = {}
    for name in wanted:
        hits = [f for f in glob.glob(os.path.join(path, "*.csv")) if re.search(rf"(^|[_ .-]){name}\.csv$", os.path.basename(f))]
        if len(hits) != 1:
            sys.exit(f"{path}: expected one CSV for sheet {name}, found {hits}")
        out[name] = list(csv.reader(open(hits[0], newline="", encoding="utf-8-sig")))
    return out


class Sheet:
    def __init__(self, rows, label):
        self.header, self.rows, self.label = rows[0], rows[1:], label

    def col(self, name, last=False):
        ids = [i for i, h in enumerate(self.header) if h == name]
        if not ids:
            sys.exit(f"{self.label}: no column {name!r}")
        return ids[-1] if last else ids[0]

    def __iter__(self):
        w = len(self.header)
        for r in self.rows:
            yield r + [""] * (w - len(r))


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0

# ---------------------------------------------------------------- model


def load_site(site, path):
    wanted = ("vInfo", "vHost", "vMemory")
    raw = read_csv_dir(path, wanted) if os.path.isdir(path) else read_xlsx(path, wanted)
    info, host, mem = (Sheet(raw[s], f"{site}/{s}") for s in wanted)
    clusters = {}
    hc = dict(cl=host.col("Cluster"), cores=host.col("# Cores"), cpu=host.col("CPU usage %"),
              maint=host.col("in Maintenance Mode"), model=host.col("Model"), ram=host.col("# Memory"))
    for r in host:
        c = clusters.setdefault(r[hc["cl"]], dict(site=site, cluster=r[hc["cl"]], hosts=0, hosts_active=0,
                                                 models=collections.Counter(), cores=0, ram_gib=0.0,
                                                 cpu_used_cores=0.0, vms=[]))
        cores = num(r[hc["cores"]])
        c["hosts"] += 1
        c["hosts_active"] += r[hc["maint"]] != "True"
        c["models"][r[hc["model"]]] += 1
        c["cores"] += cores
        c["ram_gib"] += num(r[hc["ram"]]) / 1024
        c["cpu_used_cores"] += cores * num(r[hc["cpu"]]) / 100
    consumed = {r[mem.col("VM ID")]: num(r[mem.col("Consumed")]) / 1024 for r in mem}
    ic = dict(power=info.col("Powerstate"), tmpl=info.col("Template"), cl=info.col("Cluster", last=True),
              ram=info.col("Memory"), cpu=info.col("CPUs"), id=info.col("VM ID"))
    for r in info:
        if r[ic["power"]] != "poweredOn" or r[ic["tmpl"]] == "True":
            continue
        c = clusters.get(r[ic["cl"]])
        if c is None:
            c = clusters.setdefault(r[ic["cl"]], dict(site=site, cluster=r[ic["cl"]], hosts=0, hosts_active=0,
                                                     models=collections.Counter(), cores=0, ram_gib=0.0,
                                                     cpu_used_cores=0.0, vms=[]))
        c["vms"].append(dict(ram=num(r[ic["ram"]]) / 1024, cpu=num(r[ic["cpu"]]), cons=consumed.get(r[ic["id"]], 0.0)))
    return list(clusters.values())


def merge_config(user):
    cfg = copy.deepcopy(DEFAULTS)
    for k, v in (user or {}).items():
        if isinstance(v, dict) and isinstance(cfg.get(k), dict):
            cfg[k].update(v)
        else:
            cfg[k] = v
    return cfg


def classify(cfg, c):
    u = c["cluster"].upper()
    for isl in cfg["islands"]:
        if re.search(isl["match"], u, re.I):
            return dict(island=isl["name"], kind=isl.get("kind", "isolation"))
    hold = bool(re.search(cfg["holding"], u, re.I)) or len(c["vms"]) <= cfg["limits"]["holding_max_vms"]
    env = "non-prod" if re.search(cfg["nonprod"], u, re.I) else "prod"
    return dict(island=None, holding=hold, env=env)


def pool_name(scen, cls, c, hold_target):
    label = c["cluster"] or "(standalone hosts)"
    if cls["island"]:
        mode = scen["islands"]
        if mode == "merge" or (mode == "merge-isolation" and cls["kind"] == "isolation"):
            return cls["island"]
        return label
    g = scen["general"]
    if g == "cluster":
        return hold_target if cls["holding"] else label
    if g == "env":
        return "General prod" if cls["holding"] or cls["env"] == "prod" else "General non-prod"
    return "General (prod + non-prod)"


def pack(items, cap_ram, cap_cpu):
    """First-fit decreasing on RAM with vCPU as a second dimension."""
    nodes = []
    for ram, cpu in sorted(items, reverse=True):
        if ram > cap_ram:
            sys.exit(f"a {ram:.0f} GiB VM exceeds per-node capacity {cap_ram:.0f} GiB -- raise node ram_gib or fill")
        for n in nodes:
            if n[0] + ram <= cap_ram and n[1] + cpu <= cap_cpu:
                n[0] += ram
                n[1] += cpu
                break
        else:
            nodes.append([ram, cpu])
    return len(nodes)


def size(cfg, ffd_nodes, cpu_used, max_nodes):
    L, N = cfg["limits"], cfg["node"]
    cpu_nodes = math.ceil(cpu_used / (N["cores"] * L["cpu_measured_cap"])) if cpu_used else 0
    working = max(ffd_nodes, cpu_nodes, 1)
    clusters = math.ceil(working / (max_nodes - L["spares_per_cluster"]))
    total = max(working + clusters * L["spares_per_cluster"], L["min_nodes"] * clusters)
    return dict(ffd_nodes=ffd_nodes, cpu_nodes=cpu_nodes, working=working, clusters=clusters, total=total,
                spares=total - working, binding="cpu" if cpu_nodes > ffd_nodes else "ram")


def run(cfg, clusters):
    L, N = cfg["limits"], cfg["node"]
    max_nodes = L["max_nodes"] or max(c["hosts"] for c in clusters)
    cls = {(c["site"], c["cluster"]): classify(cfg, c) for c in clusters}
    sites = list(dict.fromkeys(c["site"] for c in clusters))
    hold_target = {}
    for site in sites:
        general = [c for c in clusters if c["site"] == site and not cls[(site, c["cluster"])]["island"]
                   and not cls[(site, c["cluster"])]["holding"]]
        hold_target[site] = max(general, key=lambda c: len(c["vms"]))["cluster"] if general else "General"
    owned = sum(n for c in clusters for m, n in c["models"].items()
                if N.get("model_match") and re.search(N["model_match"], m, re.I))
    allv = [v for c in clusters for v in c["vms"]]
    out = dict(config=cfg, max_nodes_applied=max_nodes,
               estate=dict(sites=sites, hosts=sum(c["hosts"] for c in clusters),
                           hosts_active=sum(c["hosts_active"] for c in clusters),
                           clusters=sum(1 for c in clusters if c["hosts"] and c["cluster"]),
                           clusters_with_vms=sum(1 for c in clusters if c["vms"]),
                           owned_target_model=owned, vms=len(allv), vcpu=sum(v["cpu"] for v in allv),
                           vram_gib=round(sum(v["ram"] for v in allv), 1),
                           consumed_gib=round(sum(v["cons"] for v in allv), 1),
                           cpu_used_cores=round(sum(c["cpu_used_cores"] for c in clusters), 1),
                           physical_cores=sum(c["cores"] for c in clusters),
                           by_site={s: dict(hosts=sum(c["hosts"] for c in clusters if c["site"] == s),
                                            clusters=sum(1 for c in clusters if c["site"] == s and c["hosts"] and c["cluster"]),
                                            vms=sum(len(c["vms"]) for c in clusters if c["site"] == s))
                                    for s in sites}),
               scenarios=[], mapping=[])
    mapping = {(c["site"], c["cluster"]): {} for c in clusters}

    def evaluate(scen, record=True):
        pools = collections.OrderedDict()
        for c in clusters:
            if not c["vms"]:
                continue  # clusters with nothing powered on retire with vSphere
            k = cls[(c["site"], c["cluster"])]
            name = pool_name(scen, k, c, hold_target[c["site"]])
            p = pools.setdefault((c["site"], name), dict(site=c["site"], pool=name, sources=[], source_hosts=0,
                                                         items=[], cpu_used=0.0,
                                                         kind=k.get("kind") or ("general")))
            p["sources"].append(c["cluster"] or "(standalone hosts)")
            p["source_hosts"] += c["hosts"]
            p["cpu_used"] += c["cpu_used_cores"]
            for v in c["vms"]:
                ram = v["ram"]
                if scen.get("rightsize") and v["cons"] > 0:
                    ram = min(ram, v["cons"] * scen["rightsize"])
                p["items"].append((ram + L["vm_overhead_gib"], v["cpu"]))
            if record:
                mapping[(c["site"], c["cluster"])][scen["key"]] = name
        rows = []
        for p in pools.values():
            ffd = pack(p["items"], N["ram_gib"] * scen["fill"], N["threads"] * L["vcpu_per_thread"])
            rows.append(dict(site=p["site"], pool=p["pool"], kind=p["kind"], sources=p["sources"],
                             source_hosts=p["source_hosts"], vms=len(p["items"]),
                             packed_ram_gib=round(sum(i[0] for i in p["items"])),
                             vcpu=int(sum(i[1] for i in p["items"])), cpu_used_cores=round(p["cpu_used"]),
                             **size(cfg, ffd, p["cpu_used"], max_nodes)))
        t = dict(total=sum(r["total"] for r in rows), working=sum(r["working"] for r in rows),
                 spares=sum(r["spares"] for r in rows), clusters=sum(r["clusters"] for r in rows),
                 by_site={s: sum(r["total"] for r in rows if r["site"] == s) for s in sites},
                 spares_by_site={s: sum(r["spares"] for r in rows if r["site"] == s) for s in sites},
                 clusters_by_site={s: sum(r["clusters"] for r in rows if r["site"] == s) for s in sites},
                 cpu_bound=[f'{r["site"]}/{r["pool"]}' for r in rows if r["binding"] == "cpu"])
        t["net_new"] = max(t["total"] - owned, 0)
        return dict(scen, totals=t, pools=rows)

    for scen in cfg["scenarios"]:
        out["scenarios"].append(evaluate(scen))
    # where the last scenario's saving comes from: re-run it adding one lever at a time
    if len(cfg["scenarios"]) > 1:
        first, last = cfg["scenarios"][0], cfg["scenarios"][-1]
        steps = [("merging clusters", dict(last, rightsize=None, fill=first["fill"]))]
        if last.get("rightsize"):
            steps.append(("right-sizing VM memory", dict(last, fill=first["fill"])))
        if last["fill"] != first["fill"]:
            steps.append(("higher memory fill", last))
        prev, decomp = out["scenarios"][0]["totals"]["total"], []
        for lever, scen in steps:
            total = evaluate(scen, record=False)["totals"]["total"]
            decomp.append(dict(lever=lever, nodes_avoided=prev - total, total_after=total))
            prev = total
        out["decomposition"] = dict(scenario=last["key"], steps=decomp)
    base = out["scenarios"][0]["totals"]["total"] if out["scenarios"] else 0
    for s in out["scenarios"]:
        s["totals"]["avoided_vs_first"] = base - s["totals"]["total"]
        s["totals"]["cost_at"] = {str(p): s["totals"]["avoided_vs_first"] * p for p in cfg["pricing"]["unit_prices"]}
    for c in clusters:
        m = mapping[(c["site"], c["cluster"])]
        out["mapping"].append(dict(site=c["site"], cluster=c["cluster"] or "(standalone hosts)", hosts=c["hosts"],
                                   hosts_not_in_maintenance=c["hosts_active"], vms=len(c["vms"]),
                                   vcpu=int(sum(v["cpu"] for v in c["vms"])),
                                   vram_gib=round(sum(v["ram"] for v in c["vms"])),
                                   consumed_gib=round(sum(v["cons"] for v in c["vms"])),
                                   **{f'pool_{s["key"]}': m.get(s["key"], "retire (nothing powered on)")
                                      for s in cfg["scenarios"]}))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--site", action="append", required=True, help='"Name=path" (xlsx or CSV dir); repeat per vCenter')
    ap.add_argument("--config", help="JSON overrides for DEFAULTS")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    cfg = merge_config(json.load(open(a.config)) if a.config else None)
    clusters = []
    for spec in a.site:
        name, _, path = spec.partition("=")
        if not path:
            sys.exit(f"--site needs Name=path, got {spec!r}")
        clusters += load_site(name.strip(), path.strip())
    out = run(cfg, clusters)
    os.makedirs(a.out, exist_ok=True)
    json.dump(out, open(os.path.join(a.out, "scenarios.json"), "w"), indent=1, default=dict)
    with open(os.path.join(a.out, "cluster_mapping.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out["mapping"][0]))
        w.writeheader()
        w.writerows(out["mapping"])
    e = out["estate"]
    print(f'estate: {e["hosts"]} hosts ({e["hosts_active"]} not in maintenance) in {e["clusters"]} clusters | '
          f'{e["vms"]} powered-on VMs | {e["vcpu"]:.0f} vCPU | {e["vram_gib"]:.0f} GiB configured | '
          f'{e["consumed_gib"]:.0f} GiB consumed | owned target-model hosts: {e["owned_target_model"]} | '
          f'max nodes/cluster: {out["max_nodes_applied"]}')
    for s in out["scenarios"]:
        t = s["totals"]
        print(f'{s["key"]} {s["name"]}: {t["total"]} nodes = {t["working"]} working + {t["spares"]} spare, '
              f'{t["clusters"]} clusters | {t["by_site"]} | net-new {t["net_new"]} | '
              f'avoided vs {out["scenarios"][0]["key"]}: {t["avoided_vs_first"]} | cpu-bound: {t["cpu_bound"]}')
    print(f'wrote {a.out}/scenarios.json and cluster_mapping.csv')


if __name__ == "__main__":
    main()
