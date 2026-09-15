---
name: rvtools-consolidation
description: Bin-pack a VMware estate from RVTools exports onto a target server spec and show how many servers each consolidation level needs -- cluster-for-cluster, moderate, aggressive -- with N+1 spares, licensing and tenant boundaries kept, memory right-sizing, servers avoided and a hardware-cost range, rendered as a two-page Spectro Cloud branded PDF. Use when someone asks things like can it do bin packing, how many servers or nodes do we need, how few hosts can we land this on, condense or consolidate the clusters, save the N+1 servers, cluster for cluster versus consolidated, size the target hardware from RVTools, turn the host savings into dollars, right-size the VMs for the migration. Pairs with a VMware migration readiness assessment; this skill owns the host-count and consolidation math, not OS readiness.
---

# RVTools consolidation scenarios

Answers "how many target servers does this VMware estate need, and how many fewer if we
consolidate?" from the customer's own RVTools exports. Every powered-on VM is actually
bin-packed; nothing is a ratio estimate.

Two scripts, standard library only (Python 3.9+, no pip install):

- `scripts/consolidate.py` -- reads the exports, packs each scenario, writes `scenarios.json`
  and `cluster_mapping.csv` (every source cluster and the target pool it lands in per scenario).
- `scripts/render_report.py` -- turns `scenarios.json` into a two-page branded HTML report and,
  with headless Chrome/Chromium available, a PDF.

## What you need before running

| Input | Where it comes from |
|---|---|
| One RVTools export per vCenter (`.xlsx`, or a folder of per-sheet CSVs) | Customer. Needs the `vInfo`, `vHost` and `vMemory` sheets. One export = one site; pools never span sites. |
| Target node: RAM, physical cores, threads | Customer's standard build or the proposed server. Ask if not given -- it drives every number. |
| Which clusters are licensing or tenant boundaries | Infer from cluster names, then confirm (see step 3). |
| Server unit prices (optional) | Reseller quote. Without one, give a sensitivity range and say so. |

## Workflow

1. **Run once with defaults** to see the estate and how clusters classify:

   ```bash
   python3 scripts/consolidate.py \
     --site "Chicago=Chicago RVTools_export_all.xlsx" \
     --site "London=London RVTools_export_all.xlsx" \
     --out out/
   ```

   The first printed line is the estate. Check it against the RVTools totals the customer
   quoted (VM count, vCPU, RAM). If they disagree, stop and find out why before going on.

2. **Read `out/cluster_mapping.csv`.** Every cluster name, its hosts, VMs and target pool per
   scenario. This is where misclassification shows up.

3. **Write a config** (start from `assets/example-config.json`). Set the target node, then
   the islands -- clusters whose workloads must never share nodes with anything else:
   - `"kind": "license"` -- the boundary exists for software licensing (Oracle, SQL Server,
     IBM, Windows Datacenter). Kept 1:1 in the moderate scenario; merged by class per site
     only in the aggressive one. **Oracle VMs never go into a general pool** -- Oracle
     licenses every physical core a VM could run on.
   - `"kind": "isolation"` -- tenant-dedicated clusters, firewall A/B pairs, DMZ, PCI.
     Merged per class per site from the moderate scenario on, never mixed with others.

   Islands match the uppercase cluster name as a regex, first match wins, so order specific
   before general (Oracle EE before Oracle SE). Match loosely -- real estates misspell names.

4. **Run with the config** and read the summary: totals per scenario, net-new servers beyond
   the target model already owned, servers avoided versus the first scenario, and which pools
   are CPU-bound.

5. **Verify before it leaves the building.** For customer-facing numbers, have a second agent
   on a different model recompute A/B/C from the CSVs using only the rules in "Scenario
   rules" below -- not this script -- and compare totals per scenario and per site. An agent
   re-running the same script proves nothing.

6. **Render:**

   ```bash
   python3 scripts/render_report.py out/scenarios.json --customer "Acme" \
     --data-date 8/20/26 --html out/Acme_Consolidation.html --pdf out/Acme_Consolidation.pdf
   ```

   It warns if the PDF is not exactly 2 pages. Chrome is found via `$CHROME`, then
   `google-chrome`/`chromium` on PATH, then a puppeteer-cached Chrome, then the macOS app.
   Look at both pages before sending.

## Scenario rules (the defaults)

Common to every scenario:

- Only powered-on, non-template VMs. Clusters with nothing powered on retire with vSphere.
- Pack first-fit decreasing by memory, second dimension allocated vCPU at 4 per hardware thread.
- Measured host CPU (cores x `CPU usage %`) must fit in 70% of the pool's target cores. When
  this binds, the pool is marked CPU-bound.
- +0.25 GiB KubeVirt overhead per VM.
- +1 spare node per target cluster, 3-node minimum per cluster, and no cluster larger than
  the largest cluster in the estate today (split, with a spare each, if exceeded).
- Holding clusters (empty name = standalone hosts, `ESXi_Upgrade`, or 2 or fewer VMs) are not
  workload boundaries: their VMs join the site's largest general-purpose cluster/pool.

| | A -- Cluster-for-cluster | B -- Moderate | C -- Aggressive |
|---|---|---|---|
| General-purpose clusters | each stays its own cluster | merged per site into prod and non-prod | all merged per site |
| License islands | as-is | as-is | merged by class per site |
| Isolation islands | as-is | merged by class per site | merged by class per site |
| VM memory | configured | configured | Consumed x 1.2, never above configured |
| Memory fill per node | 80% | 80% | 90% |

Non-prod is a token match on DEV, NP, NONPROD, TST, TEST, QA, UAT, STG, STAGE, DRTEST, PSR,
PERF, BUILD, SANDBOX, LAB. Everything else general-purpose counts as prod.

The engine also re-runs the last scenario one lever at a time (merging clusters, then
right-sizing, then higher fill) and reports how many servers each lever saves. Lead with the
merging number: it needs no application owner's approval.

## Config reference

Any key you omit keeps its default (see `DEFAULTS` at the top of `consolidate.py`). Lists
(`islands`, `scenarios`) replace the default list entirely.

- `node`: `name` (shown in the report), `ram_gib`, `cores`, `threads`, `model_match` (regex on
  the vHost `Model` column, to count target-model servers already owned).
- `limits`: `vcpu_per_thread`, `cpu_measured_cap`, `vm_overhead_gib`, `min_nodes`,
  `max_nodes` (null = largest cluster today), `spares_per_cluster`, `holding_max_vms`.
- `islands`: list of `{name, match, kind}`.
- `holding`, `nonprod`: regexes on the uppercase cluster name.
- `scenarios`: list of `{key, name, general: cluster|env|site, islands: cluster|merge-isolation|merge, fill, rightsize: null|factor}`.
  The report shows the first three and compares everything to the first.
- `pricing`: `unit_prices` (list, drives the cost rows) and `currency`.

## Gotchas that have bitten

- **RVTools `vInfo` repeats column names** (`Datacenter`, `Environment`). The engine reads the
  last `Cluster` column; if a customer's export differs, check `cluster_mapping.csv`.
- **Misspelled cluster names split islands.** One real estate spelled a tenant's name one way
  at one site and transposed two letters at another; a tight regex silently dropped 1.2 TB
  database VMs into a general pool. Grep the mapping CSV for every island name.
- **Holding clusters inflate cluster-for-cluster.** Without the holding rule, three near-empty
  staging clusters became nine phantom nodes.
- **Maintenance mode means the estate is mid-change.** A whole 28-host cluster can be in
  maintenance with nothing on it. Report hosts-not-in-maintenance alongside hosts.
- **`CPU usage %` is a point-in-time reading.** Firewall and packet-processing VMs pin CPU, so
  their pools are usually CPU-bound -- that is correct, not a bug.
- **`Consumed` is a snapshot too**, and for Windows guests it is close to configured (the OS
  zeroes pages at boot), so right-sizing savings come mostly from Linux. Right-sizing needs VM
  owner sign-off or KubeVirt memory overcommit; say so wherever the aggressive number appears.
- **"1.7 TB" is not a GiB figure.** ESXi may report 1,789 GiB for a server sold as 1.7 TB.
  Pick one planning number, stay consistent with any earlier assessment, and state it.
- **Scope mismatches.** A customer RFP may size "the top 80% of VMs"; this engine sizes every
  powered-on VM. The largest 80% usually holds ~98% of RAM, so the gap is small -- note it
  rather than re-running.
- **Never present the dollar rows as a quote.** They are servers avoided x an assumed price.
  Swap in the reseller's number and re-render; it is one command.

## Delivering it

Send the PDF plus `cluster_mapping.csv` (the reseller and the customer's migration planners
use the mapping). In the covering note: the three totals, the merging-only saving, what still
needs confirming (boundaries, right-sizing, price), and nothing else.
