---
name: spectrocloud-common
description: "READ THIS FIRST for any Spectro Cloud Palette API work -- getting the Palette API key out of 1Password, resolving the ProjectUid (always ask which project), pack and registry lookups, and the end-to-end order of operations for demo or meeting prep. Use whenever a task touches api.spectrocloud.com, a Palette tenant (prod, custeng-prod, a customer tenant, an EU tenant), or Craig says: use the spectrocloud skills that make sense, check palette, look at prod, I just added an API token for this tenant, get the key from op. Other spectrocloud-* skills assume this one has already been read; read it before them rather than guessing at auth, project scoping, or pagination."
---

# Spectro Cloud Common Utilities

Shared utilities for all Palette API operations. Reference this skill for project/pack lookups.

## End-to-End Workflow

**For meeting prep / demo setup, follow this order:**

1. **Get credentials** → Retrieve `palette-api-key` from your secret store, set `PALETTE_API_KEY`
2. **Get project** → **ALWAYS ASK** user for project name, then look up `PROJECT_UID`. Never assume or infer.
3. **Discover existing resources** → List profiles, clusters, edge hosts
4. **Decide what to create/update** → Present findings to user
5. **Create/update profiles** → Use `spectrocloud-cluster-profiles` skill
6. **Create cluster** → Use `spectrocloud-clusters` skill (if edge hosts available)
7. **Verify deployment** → Check cluster state, get kubeconfig

**API vs Terraform decision:**
- **API**: Quick one-off demos, testing, exploration
- **Terraform**: Repeatable deployments, production, GitOps workflows

## Authentication

All API calls require `PALETTE_API_KEY` and `PROJECT_UID` environment variables.

### Get Credentials

```bash
export PALETTE_API_KEY="<your-api-key>"
```

**Before any Palette API operations**, verify credentials are set:
```bash
# Test API connectivity
curl -s "https://api.spectrocloud.com/v1/projects" \
  -H "ApiKey: $PALETTE_API_KEY" | jq 'if .items then "OK: Found \(.items | length) projects" else "ERROR: \(.)" end'
```

---

## Project Lookup

**ALWAYS ASK the user which project to use.** Never assume or infer from context.

API calls require a Project UID. Ask for the project **name**, then look it up:

```bash
# List all projects
curl -s "https://api.spectrocloud.com/v1/projects" \
  -H "ApiKey: $PALETTE_API_KEY" | \
  jq '[.items[] | {name: .metadata.name, uid: .metadata.uid}]'
```

**If name isn't an exact match**, search case-insensitively:
```bash
PROJECT_NAME="demo"
curl -s "https://api.spectrocloud.com/v1/projects" \
  -H "ApiKey: $PALETTE_API_KEY" | \
  jq --arg name "$PROJECT_NAME" '[.items[] |
    select(.metadata.name | ascii_downcase | contains($name | ascii_downcase)) |
    {name: .metadata.name, uid: .metadata.uid}]'
```

**If multiple matches**, present options to user and confirm before proceeding.

---

## Pack Discovery

**Ask user for the pack name.** If unknown, suggest browsing Palette UI or searching.

**CRITICAL**: Always query for the LATEST version of every pack before use. Never assume or use remembered versions - they change frequently. See "Get Latest Pack Version" section below.

### Find Pack by Exact Name (All Versions, Newest First)

**Important**: Pack API paginates at 50 results. Newer versions may require offset parameter.

```bash
# Get ALL versions of a pack (handles pagination)
PACK_NAME="edge-k3s"
(for OFFSET in 0 50 100 150; do
  curl -s "https://api.spectrocloud.com/v1/packs?filters=metadata.name=$PACK_NAME&limit=50&offset=$OFFSET" \
    -H "ApiKey: $PALETTE_API_KEY" | \
    jq '[.items[] | select(.status.disabled != true) |
      {name: .metadata.name, version: .spec.version, uid: .metadata.uid,
       registryUid: .spec.registryUid, layer: .spec.layer}]'
done) | jq -s 'add | sort_by(.version | split(".") | map(tonumber? // 0)) | reverse'
```

### Get Pack Default Values (Critical!)
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

### Search Packs by Keyword
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

Before creating resources, check what already exists:

### List Cluster Profiles
```bash
curl -s "https://api.spectrocloud.com/v1/clusterprofiles" \
  -H "ApiKey: $PALETTE_API_KEY" \
  -H "ProjectUid: $PROJECT_UID" | \
  jq '[.items[] | {name: .metadata.name, uid: .metadata.uid, version: .spec.version, type: .spec.published.type}]'
```

### List Edge Clusters
```bash
curl -s "https://api.spectrocloud.com/v1/spectroclusters?filters=spec.cloudType=edge-native" \
  -H "ApiKey: $PALETTE_API_KEY" \
  -H "ProjectUid: $PROJECT_UID" | \
  jq '[.items[] | {name: .metadata.name, uid: .metadata.uid, state: .status.state}]'
```

### List Edge Hosts (with status)
```bash
curl -s "https://api.spectrocloud.com/v1/edgehosts" \
  -H "ApiKey: $PALETTE_API_KEY" \
  -H "ProjectUid: $PROJECT_UID" | \
  jq '[.items[] | {name: .metadata.name, uid: .metadata.uid, state: .status.state,
      health: .status.health.state, clusterUid: .status.clusterUid}]'
```

### Get Latest Pack Version (MANDATORY)

**ALWAYS run this query for EVERY pack** you intend to use. Never skip this step or use cached/remembered versions.

**CRITICAL**: API paginates at 50 results. Popular packs (Calico, K8s, etc.) have many versions - you MUST use pagination to find the true latest:

```bash
# Get LATEST version of a pack (handles pagination properly)
PACK_NAME="cni-calico"  # Replace with actual pack name
LATEST=$((for OFFSET in 0 50 100 150; do
  curl -s "https://api.spectrocloud.com/v1/packs?filters=metadata.name=$PACK_NAME&limit=50&offset=$OFFSET" \
    -H "ApiKey: $PALETTE_API_KEY" | jq '.items[]'
done) | jq -s '[.[] | select(.status.disabled != true)] |
  sort_by(.spec.version | split(".") | map(tonumber? // 0)) |
  reverse | .[0] | {name: .metadata.name, version: .spec.version, uid: .metadata.uid}')
echo "$LATEST"
```

**Example**: Calico 3.30.1 vs 3.31.2 - without pagination you may get an older version that appears "latest" in the first 50 results.

### Get Latest BYOOS Version (edge-native-byoi)

BYOOS exists in TWO registries; filter on Public Repo (`5eecc89d0b150045ae661cef`, `type = "spectro"`, recommended). Never hardcode the version:

```bash
curl -s "https://api.spectrocloud.com/v1/packs?filters=metadata.name=edge-native-byoi&limit=50" \
  -H "ApiKey: $PALETTE_API_KEY" | jq -r '[.items[] | select(.spec.registryUid == "5eecc89d0b150045ae661cef")] |
  sort_by(.spec.version | split(".") | map(tonumber)) | reverse | .[0] | {version: .spec.version, uid: .metadata.uid}'
```

---

## K8s Version Discovery

**Default to n-1 minor version** (one behind latest) for stability. Example: if 1.33.6 is latest, use 1.32.x.

### Get n-1 Minor K8s Version (Palette API)

For cluster profiles, query Palette API for edge K8s pack versions:

```bash
# Get n-1 minor version for edge-k3s (recommended default)
PACK_NAME="edge-k3s"
K8S_VERSION=$((for OFFSET in 0 50 100 150; do
  curl -s "https://api.spectrocloud.com/v1/packs?filters=metadata.name=$PACK_NAME&limit=50&offset=$OFFSET" \
    -H "ApiKey: $PALETTE_API_KEY" | jq '.items[]'
done) | jq -s '[.[] | select(.status.disabled != true) | .spec.version] | unique |
  sort_by(split(".") | map(tonumber)) | reverse |
  group_by(split(".")[0:2] | join(".")) |
  sort_by(.[0] | split(".") | map(tonumber)) | reverse | .[1][0] // .[0][0]')
echo "Recommended K8s version: $K8S_VERSION"
```

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
| Can't find latest K8s version | API paginates at 50 - use offset parameter (0, 50, 100, 150) |
| API returns empty for recent versions | Pagination issue - newer versions beyond first 50 results |

---

## Quick Reference

| Item | Endpoint |
|------|----------|
| List Projects | `GET /v1/projects` |
| Find Pack | `GET /v1/packs?filters=metadata.name=<name>` |
| Get Pack Values | `GET /v1/packs/{uid}?includePackValues=true` |
| List Pack Registries | `GET /v1/registries/pack` |
| List Helm Registries | `GET /v1/registries/helm` |
| Required Headers | `ApiKey`, `ProjectUid` (for pack calls) |

## Links

- [API Introduction](https://docs.spectrocloud.com/api/introduction/)
- [Palette API Reference](https://docs.spectrocloud.com/api/category/palette-api-v1/)
