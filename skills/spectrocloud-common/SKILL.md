---
name: spectrocloud-common
description: "READ THIS FIRST for any Spectro Cloud Palette API work -- getting the Palette API key out of 1Password, resolving the ProjectUid (always ask which project), pack and registry lookups, and the end-to-end order of operations for demo or meeting prep. Use whenever a task touches api.spectrocloud.com, a Palette tenant (prod, custeng-prod, a customer tenant, an EU tenant), or Craig says: use the spectrocloud skills that make sense, check palette, look at prod, I just added an API token for this tenant, get the key from op. Other spectrocloud-* skills assume this one has already been read; read it before them rather than guessing at auth, project scoping, or pagination."
---

# Spectro Cloud Common Utilities

Shared utilities for all Palette API operations. **Try the matching `palette-axi`
verb before raw curl** — it routes around dead/degraded endpoints and paginates
`/v1/packs` for you (see Quick Reference). Curl is still required for writes, pack
full-values, and registries/cloudconfigs (no verb yet).

## End-to-End Workflow

**For meeting prep / demo setup, follow this order:**

1. **Get credentials** → Retrieve `palette-api-key` from your secret store, set `PALETTE_API_KEY`
2. **Get project** → **ALWAYS ASK** user for project name, then look up `PROJECT_UID` (`palette-axi projects`). Never assume or infer.
3. **Discover existing resources** → `palette-axi profiles`, `palette-axi clusters --edge`, `palette-axi edgehosts` (all take `--project`)
4. **Decide what to create/update** → Present findings to user
5. **Create/update profiles** → Use `spectrocloud-cluster-profiles` skill
6. **Create cluster** → Use `spectrocloud-clusters` skill (if edge hosts available)
7. **Verify deployment** → Check cluster state, get kubeconfig

**API vs Terraform decision:**
- **API**: Quick one-off demos, testing, exploration
- **Terraform**: Repeatable deployments, production, GitOps workflows

## Authentication

All API calls require `PALETTE_API_KEY`. Writes and anything palette-axi doesn't cover
(pack full-values, registries) also need `PROJECT_UID` as a `ProjectUid:` header.

### Get Credentials

```bash
export PALETTE_API_KEY="<your-api-key>"
```

**Before any Palette API operations**, verify credentials and connectivity:
```bash
palette-axi doctor
```
Checks 1Password and the Palette API in one call (`--json` for machine-readable output).

---

## Project Lookup

**ALWAYS ASK the user which project to use.** Never assume or infer from context.

```bash
palette-axi projects
```
Lists every project's `name`, `uid`, and `clusters` count — use the `uid` as
`PROJECT_UID` for writes and for the fallback curl recipes below. This replaces the
old `GET /v1/projects` recipe: that endpoint now 405s on GET for some tenants and
caps at 50 rows for others; `palette-axi projects` calls the working
`/v1/dashboard/projects` endpoint instead.

**If the name isn't an exact match**, filter the output yourself
(`palette-axi projects | grep -i <name>`) and confirm with the user before proceeding.

---

## Pack Discovery

**Ask user for the pack name.** If unknown, search by keyword below.

**CRITICAL**: Always query for the LATEST version of every pack before use. Never assume or use remembered versions - they change frequently.

### Find Pack by Exact Name (All Versions, Newest First)

```bash
palette-axi packs <name>          # e.g. palette-axi packs edge-k3s
palette-axi packs <name> --full   # every version, not just the newest 12
```
Handles the `/v1/packs` 50-row pagination for you, drops disabled versions, sorts
newest-first, and flags the top row `latest:true` — no manual offset loop or jq
version-sort needed.

### Get Pack Default Values (no palette-axi verb yet)

Once you have the pack `uid` from `palette-axi packs <name>`, fetch its full values:
```bash
# Fetch the COMPLETE default values for a pack
curl -s "https://api.spectrocloud.com/v1/packs/$PACK_UID?includePackValues=true" \
  -H "ApiKey: $PALETTE_API_KEY" \
  -H "ProjectUid: $PROJECT_UID" | jq -r '.packValues[0].values'
```

**Important workflow for pack values:**
1. **Fetch the entire default values file** - don't summarize or truncate
2. **Keep ALL default values intact** - include the complete file in your profile
3. **Only modify specific sections** you need to change
4. Never strip out sections - missing values cause validation failures

### Search Packs by Keyword (exact name unknown)

`palette-axi packs` needs an exact `metadata.name`; for a keyword scan across a
whole layer, curl is still the way:
```bash
KEYWORD="hello"
curl -s "https://api.spectrocloud.com/v1/packs?filters=spec.layer=addon&limit=100" \
  -H "ApiKey: $PALETTE_API_KEY" \
  -H "ProjectUid: $PROJECT_UID" | \
  jq --arg kw "$KEYWORD" '[.items[] | select(.metadata.name | ascii_downcase | contains($kw | ascii_downcase)) |
      {name: .metadata.name, version: .spec.version}] | unique_by(.name)'
```

---

## Registry Types

| Registry Type | Example Name | Notes |
|---------------|--------------|-------|
| Pack | "Public Repo" | Standard packs (metallb, cni, etc.) |
| Helm | "Bitnami" | Helm charts indexed as packs |
| OCI | (various) | Some packs use OCI registries |

**Important**: If a pack isn't found with a specific registry, omit `registry_uid` to let Terraform auto-discover.

`palette-axi` has no `registries` verb yet — a read-only one is filed
(`lm-palette-axi-registries`) but not built, and no version is promised. Curl is the
only way to list registries today:

### List Available Registries
```bash
# Pack registries
curl -s "https://api.spectrocloud.com/v1/registries/pack?limit=50" \
  -H "ApiKey: $PALETTE_API_KEY" | \
  jq '[.items[] | {name: .metadata.name, uid: .metadata.uid}]'

# Helm registries
curl -s "https://api.spectrocloud.com/v1/registries/helm?limit=50" \
  -H "ApiKey: $PALETTE_API_KEY" | \
  jq '[.items[] | {name: .metadata.name, uid: .metadata.uid, endpoint: .spec.endpoint}]'
```

---

## Discovery: What Exists?

Before creating resources, check what already exists — all three take `--project`:

```bash
palette-axi profiles          # cluster profiles: name, uid, version, type, cloudType
palette-axi clusters --edge   # edge-native clusters: name, uid, state, health
palette-axi edgehosts         # edge hosts: name, uid, state, health, attached cluster
```

### Get Latest Pack Version (MANDATORY)

**ALWAYS check the latest version for EVERY pack** you intend to use. Never skip this step or use cached/remembered versions — `palette-axi packs cni-calico --full` (see Pack Discovery above).

### Get Latest BYOOS Version (edge-native-byoi)

BYOOS exists in TWO registries; filter on Public Repo (`5eecc89d0b150045ae661cef`, `type = "spectro"`, recommended). Never hardcode the version:

```bash
palette-axi packs edge-native-byoi --full
```
Pick the newest row whose `registryUid` is `5eecc89d0b150045ae661cef`.

---

## K8s Version Discovery

**Default to n-1 minor version** (one behind latest) for stability. Example: if 1.33.6 is latest, use 1.32.x.

### Get n-1 Minor K8s Version (Palette API)

```bash
palette-axi packs edge-k3s --full   # recommended default; or edge-k8s for kubeadm
```
Versions come back deduped, disabled-filtered, and sorted newest-first — the n-1
minor is the newest row whose `major.minor` differs from the top row's.

**Query for other distributions:**
- `edge-k3s` - K3s (required for 2-node clusters)
- `edge-k8s` - Kubeadm

### Get Supported K8s Versions from CanvOS

For appliance mode builds, query CanvOS `k8s_version.json` from latest release:

```bash
# Get latest CanvOS tag
CANVOS_TAG=$(gh api repos/spectrocloud/CanvOS/tags --jq '.[0].name')
echo "Latest CanvOS: $CANVOS_TAG"

# Fetch k8s_version.json
curl -s "https://raw.githubusercontent.com/spectrocloud/CanvOS/$CANVOS_TAG/k8s_version.json" > k8s_versions.json

# Get n-1 minor for a distribution (default: k3s)
DISTRO="k3s"
K8S_VERSION=$(jq -r --arg d "$DISTRO" '.[$d] |
  sort_by(split(".") | map(tonumber)) | reverse |
  group_by(split(".")[0:2] | join(".")) |
  sort_by(.[0] | split(".") | map(tonumber)) | reverse | .[1][0] // .[0][0]' k8s_versions.json)
echo "Recommended $DISTRO version: $K8S_VERSION"
```

**Supported distributions in CanvOS:**
- `k3s` - K3s (lightweight, required for 2-node)
- `rke2` - RKE2 (Rancher)
- `kubeadm` - Standard kubeadm
- `kubeadm-fips` - FIPS-compliant kubeadm
- `nodeadm` - Amazon EKS nodeadm
- `canonical` - Canonical K8s

### List All Available Versions

```bash
# From CanvOS - all distributions and their versions
curl -s "https://raw.githubusercontent.com/spectrocloud/CanvOS/$CANVOS_TAG/k8s_version.json" | \
  jq 'to_entries | .[] | "\(.key): \(.value | length) versions, latest: \(.value | sort_by(split(".") | map(tonumber)) | reverse | .[0])"'
```

### n-1 Minor Logic Explained

The jq filter:
1. `sort_by(split(".") | map(tonumber)) | reverse` - Sort versions descending
2. `group_by(split(".")[0:2] | join("."))` - Group by major.minor
3. `sort_by(.[0] | split(".") | map(tonumber)) | reverse` - Re-sort groups by version (group_by doesn't preserve order)
4. `.[1][0]` - Take first version from second group (n-1 minor)
5. `// .[0][0]` - Fallback to latest if only one minor exists

---

## Terraform Setup

### Provider Configuration
```hcl
terraform {
  required_providers {
    spectrocloud = {
      source  = "spectrocloud/spectrocloud"
      version = ">= 0.26.0"  # 2-node (two_node_role) needs 0.26+
    }
  }
}

provider "spectrocloud" {
  host    = var.palette_host      # "api.spectrocloud.com" for SaaS
  api_key = var.palette_api_key   # From env var or secret store

  # Optional: project_name to scope all resources
  # project_name = "my-project"
}

variable "palette_host" {
  default = "api.spectrocloud.com"
}

variable "palette_api_key" {
  sensitive = true
}
```

### tfvars Pattern
```hcl
# terraform.tfvars (do NOT commit to git)
palette_api_key = "your-api-key"

# Or use environment variable:
# export TF_VAR_palette_api_key="your-api-key"
```

### Modular Structure (Recommended)

**Separate profiles from clusters** for independent lifecycle management:

```
palette-demo/
├── shared/
│   └── providers.tf      # Shared provider config (symlinked)
├── profiles/
│   ├── providers.tf -> ../shared/providers.tf
│   ├── main.tf           # Cluster profiles only
│   ├── variables.tf
│   └── terraform.tfvars
└── clusters/
    ├── providers.tf -> ../shared/providers.tf
    ├── main.tf           # Clusters only (uses data sources for profiles)
    ├── variables.tf
    └── terraform.tfvars
```

**Benefits:**
- Delete cluster without affecting profiles: `cd clusters && terraform destroy`
- Update profiles independently: `cd profiles && terraform apply`
- Demo profile versioning without cluster changes
- Cleaner state management

**Workflow:**
```bash
# 1. Create profiles first
cd profiles && terraform init && terraform apply

# 2. Create clusters (references profiles via data sources)
cd ../clusters && terraform init && terraform apply

# 3. Demo: Delete just the cluster
cd clusters && terraform destroy

# 4. Demo: Update profile, then update cluster
cd profiles && terraform apply  # Creates new version
cd ../clusters && terraform apply  # Updates to new version
```

### Project Lookup
```hcl
data "spectrocloud_project" "this" {
  name = "my-project"
}
# Use: data.spectrocloud_project.this.id
```

### Pack Lookup (with auto-discovery)
```hcl
# Omit registry_uid to auto-discover the correct registry
data "spectrocloud_pack" "hello_universe" {
  name    = "hello-universe"
  version = "1.2.0"
}

# With explicit registry (if you know it)
data "spectrocloud_pack" "metallb" {
  name         = "lb-metallb-helm"
  version      = "0.14.9"
  registry_uid = data.spectrocloud_registry.public.id
}

data "spectrocloud_registry" "public" {
  name = "Public Repo"
}
```

### Helm Chart as Pack
```hcl
# Helm charts are indexed as packs - versions differ from source repos
data "spectrocloud_pack" "harbor" {
  name         = "harbor"
  version      = "16.3.3"  # Palette's version, not Bitnami's
  registry_uid = data.spectrocloud_registry.bitnami.id
}

data "spectrocloud_registry" "bitnami" {
  name = "Bitnami"
}
```

---

## Common Edge-Native Packs

| Layer | Pack Name | Notes |
|-------|-----------|-------|
| os | `edge-native-byoi` | Agent or appliance mode |
| k8s | `edge-k3s` | K3s (required for 2-node) |
| k8s | `edge-k8s` | Kubeadm |
| cni | `cni-calico` | Calico |
| cni | `cni-cilium-oss` | Cilium |
| addon | `hello-universe` | Demo app |

---

## Common Gotchas

| Issue | Solution |
|-------|----------|
| "no matching packs" | Omit `registry_uid` to auto-discover |
| "pack not found with tag X" | Check versions via API, not source repo |
| "Parameter X value is required" | Fetch and include pack default values |
| Pack in wrong registry | Some packs exist in multiple registries |
| Project not found | Use project name lookup, not hardcoded UID |
| Can't find latest K8s/pack version by hand | Use `palette-axi packs <name> --full` — it paginates for you |
| Raw `/v1/packs` returns empty for recent versions | Pagination issue beyond first 50 rows; not a problem for `palette-axi packs` |

---

## Quick Reference

**`palette-axi` verbs — try these first:**

| Verb | Replaces |
|------|----------|
| `palette-axi doctor` | credential + API connectivity check |
| `palette-axi projects` | `GET /v1/projects` (retired: 405s on GET / caps at 50 rows for some accounts) |
| `palette-axi packs <name> [--full]` | paginated `GET /v1/packs?filters=metadata.name=...` |
| `palette-axi profiles` / `profile <ref>` | `GET /v1/clusterprofiles[/{uid}]` |
| `palette-axi clusters --edge` / `cluster <ref>` | `GET /v1/spectroclusters[/{uid}]` |
| `palette-axi edgehosts` | `GET /v1/edgehosts` (also 405s on some accounts) |
| `palette-axi events <ref>` | `GET /v1/spectroclusters/{uid}/events` (404s ~75% of the time — see `spectrocloud-troubleshooting`) |

**Raw curl — fallback only, no verb yet:**

| Item | Endpoint |
|------|----------|
| Get Pack Values | `GET /v1/packs/{uid}?includePackValues=true` |
| List Pack Registries | `GET /v1/registries/pack` |
| List Helm Registries | `GET /v1/registries/helm` |
| Required Headers | `ApiKey`, `ProjectUid` (for pack/registry calls) |

## Links

- [API Introduction](https://docs.spectrocloud.com/api/introduction/)
- [Palette API Reference](https://docs.spectrocloud.com/api/category/palette-api-v1/)
