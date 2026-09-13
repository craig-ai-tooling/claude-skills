---
name: spectrocloud-cluster-profiles
description: "Create, version, clone and repair Palette cluster profiles via API or Terraform -- pack discovery, layer CRUD, profile variables, import/export, cross-tenant copying. Use when Craig says: use the profiles skill, create a new version of the profile, iterate the profile, update the profile so the change persists on rebuild, make those values profile variables, is anything glaringly wrong with this profile, mirror the profiles from one tenant to another (US to EU), export and import these profiles, build me an infra and an add-on profile, add this pack as a layer. Remember he usually wants a NEW profile version rather than an edit in place, and wants fixes pushed into the profile so a rebuilt cluster keeps them. Pair with spectrocloud-packs for the values that go in each layer."
---

# Spectro Cloud Cluster Profiles

Cluster profiles define the software stack deployed on clusters.

## Profile Types

| Type | API Value | Use Case |
|------|-----------|----------|
| Infrastructure | `cluster` | OS, K8s, CNI, CSI layers |
| Add-on | `add-on` | Application packs only |

**Best Practice**: Create separate infrastructure and add-on profiles rather than one combined profile.

## Application Deployment Priority

When adding applications, search in this order:
1. **Pack** (preferred) - Search `Public Repo` registry first
2. **Helm** - Search `Bitnami` or other helm registries
3. **Manifest** - Use only when no pack/helm exists

## Before Creating Profiles

**Ask the user:**
1. Project name? (use `spectrocloud-common` skill for UID lookup)
2. Cloud type? (edge-native, maas, eks, etc.)
3. Profile type? (cluster or add-on)
4. What packs? (use `spectrocloud-common` skill for discovery)

**For edge-native profiles, determine K8s version FIRST:**
- Run the "Get n-1 Minor K8s Version" query from the `spectrocloud-common` skill (`edge-k3s`, or `edge-k8s` for kubeadm)
- Default to **n-1 minor** (e.g., 1.32.x when 1.33 is latest) for stability
- Query before asking user - present the recommended version

**ALWAYS get the latest version of each pack** unless the user specifies a version. Use the Version Selection query below for EVERY pack.

## MANDATORY: Pack Values Workflow

**Partial pack values WILL fail validation.** Before creating ANY profile:

### Step 1: Fetch Complete Values for EVERY Pack

Get the pack's latest UID via the "Get Latest Pack Version" query in the `spectrocloud-common` skill (pagination-safe), then:

```bash
# Fetch COMPLETE values - save to file
curl -s "https://api.spectrocloud.com/v1/packs/$PACK_UID?includePackValues=true" \
  -H "ApiKey: $PALETTE_API_KEY" | jq -r '.packValues[0].values' > pack-values.yaml
```

### Step 2: Modify Only What's Needed
Keep ALL other values intact. Only change specific fields.

### Step 3: Include ENTIRE Values File
```hcl
# NEVER DO THIS - partial values cause failures
values = <<-EOT
  options:
    system.uri: "my-image:tag"
EOT

# ALWAYS DO THIS - complete values with modification
values = file("pack-values-modified.yaml")
```

### Step 4: Update CIDRs in K8s Packs
- `cluster-cidr` → `100.64.0.0/18`
- `service-cidr` → `100.64.64.0/18`

## Pack Types (Registry Determines Type!)

| Registry Name | Pack `type` Value |
|---------------|-------------------|
| Public Repo | `spectro` |
| Bitnami | `helm` |
| Palette Community Registry | `oci` |

**BYOOS Pack (edge-native-byoi)**: Exists in TWO registries with different types:
- **Public Repo** (5eecc89d0b150045ae661cef) → `type = "spectro"` (recommended)
- **Palette Community Registry** (64eaff453040297344bcad5d) → `type = "oci"`

**Always use the latest BYOOS version** - never hardcode it. Query it with the "Get Latest BYOOS Version" query in the `spectrocloud-common` skill.

Profile creation fails with "PackType 'X' is not matching with registry type 'Y'" if type doesn't match registry.

Mismatch causes: `PackType 'pack' is not matching with registry type 'oci'`

**Discover registries:**
```bash
curl -s "https://api.spectrocloud.com/v1/registries/metadata" -H "ApiKey: $PALETTE_API_KEY" | \
  jq '[.items[] | {name: .metadata.name, uid: .metadata.uid, kind: .kind}]'
```

## Common Pack Names

| Search Term | Pack Name | Registry | Type |
|-------------|-----------|----------|------|
| metallb | `lb-metallb-helm` | Public Repo | `spectro` |
| nginx/ingress | `nginx` | Public Repo | `spectro` |
| hello-universe | `hello-universe` | Palette Community Registry | `oci` |
| calico | `cni-calico` | Public Repo | `spectro` |
| cilium | `cni-cilium-oss` | Public Repo | `spectro` |
| harbor | `harbor` | Bitnami | `helm` |

## Version Selection (MANDATORY)

**ALWAYS query for the latest version of EVERY pack** before creating profiles. Never assume or hardcode versions - they change frequently.

**CRITICAL**: API paginates at 50 results. Popular packs like Calico have many versions - you MUST use pagination to find the true latest. Run the "Get Latest Pack Version" query from the `spectrocloud-common` skill for EACH pack you're adding to the profile. Do not skip this step or use cached/remembered versions.

## CRUD Operations

### Create (API)
```bash
curl -s -X POST "https://api.spectrocloud.com/v1/clusterprofiles?publish=true" \
  -H "ApiKey: $PALETTE_API_KEY" \
  -H "ProjectUid: $PROJECT_UID" \
  -H "Content-Type: application/json" \
  -d '{"metadata": {"name": "my-profile"}, "spec": {...}}'
```

### Read
```bash
curl -s "https://api.spectrocloud.com/v1/clusterprofiles/$PROFILE_UID" \
  -H "ApiKey: $PALETTE_API_KEY" -H "ProjectUid: $PROJECT_UID"
```

### Update (Create New Version)
**To update a profile deployed to a cluster:**
1. Create new version (same name, bumped version number)
2. Update cluster to use new version (see `spectrocloud-clusters` skill)

```bash
# Create new version of existing profile
curl -s -X POST "https://api.spectrocloud.com/v1/clusterprofiles?publish=true" \
  -H "ApiKey: $PALETTE_API_KEY" \
  -H "ProjectUid: $PROJECT_UID" \
  -H "Content-Type: application/json" \
  -d '{
    "metadata": {"name": "my-existing-profile"},
    "spec": {
      "version": "1.1.0",
      ...
    }
  }'
# This creates version 1.1.0 alongside existing 1.0.0
```

### List Profile Versions

**Note**: Profile listing also paginates at 50 results. Use offset parameter for projects with many profiles.

```bash
# List all profiles (with pagination)
(for OFFSET in 0 50 100; do
  curl -s "https://api.spectrocloud.com/v1/clusterprofiles?limit=50&offset=$OFFSET" \
    -H "ApiKey: $PALETTE_API_KEY" \
    -H "ProjectUid: $PROJECT_UID" | jq '.items[]'
done) | jq -s '[.[] | {name: .metadata.name, uid: .metadata.uid, version: .spec.version}]'

# Filter by name (still use pagination if many versions)
curl -s "https://api.spectrocloud.com/v1/clusterprofiles?filters=metadata.name=PROFILE_NAME&limit=50" \
  -H "ApiKey: $PALETTE_API_KEY" \
  -H "ProjectUid: $PROJECT_UID" | \
  jq '[.items[] | {name: .metadata.name, uid: .metadata.uid, version: .spec.version}]'
```

### Delete
```bash
curl -s -X DELETE "https://api.spectrocloud.com/v1/clusterprofiles/$PROFILE_UID" \
  -H "ApiKey: $PALETTE_API_KEY" -H "ProjectUid: $PROJECT_UID"
```

## Cross-Tenant Profile Cloning

Clone profiles between different Palette tenants. Pack UIDs and registry UIDs differ between tenants, so a simple export/import won't work - you must resolve every pack reference in the destination tenant before importing.

**See `references/cross-tenant-cloning.md`** for the full 5-step procedure: export from source, extract pack references, resolve pack UIDs in the destination, transform the profile JSON with jq, and import. Includes the validation checklist (packs exist in destination, versions match, BYOOS `system.uri` updated for the destination registry).

## Pack Install Priority (CRITICAL for Multi-Profile Deployments)

Palette deploys packs in parallel by default. When packs have dependencies (e.g., VMO CRDs must exist before VM templates), you MUST set install priority to enforce ordering.

### How It Works

Install priority is set via the `pack.spectrocloud.com/install-priority` annotation in pack values YAML. Lower numbers install first. Packs with the same priority install in parallel.

```yaml
pack:
  namespace: my-namespace
  spectrocloud.com/install-priority: "10"
charts:
  ...
```

### Manifest Packs Too

Manifest-type packs (no helm chart, just raw YAML) also support install-priority via the `values` field. This is easy to miss when exporting profiles — the API returns values separately from manifest content.

**Terraform example for manifest pack with install-priority:**
```hcl
pack {
  name   = "vmo-storage"
  type   = "manifest"
  values = "pack:\n  spectrocloud.com/install-priority: \"40\""

  manifest {
    name    = "storageprofile-cdi"
    content = file("${path.module}/manifests/storageprofile-cdi.yaml")
  }
}
```

### Common Priority Scheme (VMO Reference Architecture)

| Priority | Packs | Why |
|----------|-------|-----|
| (none) | Infra packs (BYOOS, K8s, CNI, CSI) | Installed by infrastructure layer, not addon ordering |
| 10 | MetalLB, nginx | Base networking — no dependencies |
| 20 | Prometheus/Grafana | Needs MetalLB for LoadBalancer IPs |
| 30 | VMO (KubeVirt, CDI, Multus) | Installs CRDs needed by templates |
| 40 | Template manifests (storage profiles, NADs, golden images, VM templates) | Depends on VMO CRDs |
| 50 | VMA (VM Migration Assistant) | Depends on VMO being fully operational |

### Export/Clone Gotcha

**When exporting or cloning profiles, ALWAYS check for install-priority in pack values.** The API returns it in the `values` field of each pack, but it's easy to overlook — especially for manifest packs where you might only extract the manifest content and skip the values entirely.

**Verification query:**
```bash
curl -s "https://api.spectrocloud.com/v1/clusterprofiles/$PROFILE_UID" \
  -H "ApiKey: $PALETTE_API_KEY" -H "ProjectUid: $PROJECT_UID" | \
  jq '[.spec.published.packs[] | {name: .name, priority: ((.values // "") | capture("install-priority: \"(?<v>[^\"]+)\"") | .v // "none")}]'
```

### Creating New Profiles

When building new profiles (not cloning), think about pack dependencies:
- Does this pack install CRDs that other packs consume? → Give it a lower priority number
- Does this pack create resources using CRDs from another pack? → Give it a higher priority number
- Are packs independent? → Same priority (parallel install) or no priority needed

**If you skip install-priority:** Packs deploy in parallel and manifests referencing CRDs that don't exist yet will fail with "no matches for kind" errors. The Palette reconciler will retry, but it's slow and unreliable compared to proper ordering.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Parameter X value is required" | You used partial pack values - fetch and include complete defaults |
| "PackType 'pack' is not matching with registry type 'oci'" | Wrong pack type - check registry (Public Repo=spectro, Community=oci, Bitnami=helm) |
| Can't find latest pack version | API paginates at 50 - use offset parameter |
| Profile validation fails | Ensure ALL pack default values are included, not just modified sections |
| Profiles created but don't exist | Missing `project_name` in Terraform provider - profiles are orphaned |
| Terraform shows ID but API returns null | Add `project_name` to provider, `terraform state rm`, re-apply |
| Cross-tenant: Pack not found in destination | Pack may not exist or version differs - check available versions in destination tenant |
| Cross-tenant: Import fails with UID error | Pack/registry UIDs weren't resolved - run Step 3 for all packs |
| Cross-tenant: Profile imports but cluster fails | BYOOS `system.uri` still points to source tenant's registry - update for destination |

## API Gotchas

- **Pagination**: API paginates at 50 results. Always use offset for pack discovery.
- **Filtering**: Often fails. Fetch all and filter with jq.

## BYOOS Pack Values: Agent vs Edge Mode

The BYOOS (edge-native-byoi) pack is the **ONLY mode-specific pack** in a Palette Edge infrastructure profile. All other packs (K8s, CNI, storage) and all add-on profiles are mode-agnostic. Three things differ between the modes:

| Config Area | Agent Mode | Edge/Appliance Mode |
|-------------|-----------|-------------------|
| `options.system.uri` | `"NA"` | Go template with sub-options |
| Containerd config | Spectro-specific paths | System defaults (no root/state/grpc/BinaryName) |
| Initramfs commands | `spectro.slice` + `system.slice` | `system.slice` only |

**See `references/byoos-agent-vs-edge.md`** for the full values blocks (options YAML, containerd TOML diffs, spectro.slice lines), why the modes differ, and what NOT to conflate when cloning RA templates.

### CRITICAL: Provider Image / K8s Version Alignment

For appliance/edge mode, **three components MUST align**:
1. **Provider image K8s version** - Built into image during CanvOS build
2. **BYOOS pack system.uri** - Must reference exact image tag from registry
3. **K8s layer version** - The edge-k8s/edge-k3s pack version must match

**Workflow:**
1. After CanvOS build, check actual tag: `docker images | grep $IMAGE_REPO`
2. Use that EXACT tag in BYOOS `system.uri`
3. Set K8s pack version to match what was built (e.g., if you built with `K8S_VERSION=1.33.6`, use edge-k8s version 1.33.6)

**Failure mode**: Mismatched versions cause cluster provisioning to hang or fail.

## Terraform: Critical Configuration

### CRITICAL: Provider project_name Required

**The `spectrocloud` provider MUST have `project_name` set for project-scoped resources:**

```hcl
provider "spectrocloud" {
  host         = "api.spectrocloud.com"
  api_key      = var.palette_api_key
  project_name = "My-Project"  # REQUIRED!
}
```

**Failure mode**: Without `project_name`, profiles appear to create successfully (Terraform shows IDs) but are orphaned and inaccessible in the project. The API returns null when querying.

**Detection**: Query the API to verify profiles exist:
```bash
curl -s "https://api.spectrocloud.com/v1/clusterprofiles/$PROFILE_UID" \
  -H "ApiKey: $PALETTE_API_KEY" -H "ProjectUid: $PROJECT_UID" | jq '.metadata.name'
# Returns null if profile doesn't exist in project
```

**Fix**: Add `project_name` to provider, remove stale state (`terraform state rm`), re-apply.

### Registry UID Required

When packs exist in multiple registries, `spectrocloud_pack` data source returns error:
```
Error: Multiple packs returned. Restrict packs criteria to a single match.
```

**Solution**: Always specify `registry_uid`:
```hcl
locals {
  palette_registry_uid = "5eecc89d0b150045ae661cef"  # Public Palette registry
}

data "spectrocloud_pack" "edge_k3s" {
  name         = "edge-k3s"
  version      = "1.32.9"
  registry_uid = local.palette_registry_uid  # Required!
}
```

Get registry UID:
```bash
curl -s "https://api.spectrocloud.com/v1/registries/metadata" -H "ApiKey: $PALETTE_API_KEY" | \
  jq '[.items[] | {name: .metadata.name, uid: .metadata.uid}]'
```

## Profile Variables

Use for cluster-specific values: `{{ .spectro.var.K8sPodCIDR }}`, `{{ .spectro.var.K8sServiceCIDR }}`

## Additional Resources

- `references/api-examples.md` - Full API examples
- `references/terraform-examples.md` - Terraform patterns
- `references/cross-tenant-cloning.md` - Clone profiles between tenants (UID resolution workflow)
- `references/byoos-agent-vs-edge.md` - Full BYOOS values diffs for agent vs edge mode

## Quick Reference

| Operation | Endpoint |
|-----------|----------|
| Create & Publish | `POST /v1/clusterprofiles?publish=true` |
| Read | `GET /v1/clusterprofiles/{uid}` |
| Delete | `DELETE /v1/clusterprofiles/{uid}` |
| Get Pack Values | `GET /v1/packs/{uid}?includePackValues=true` |

## Links

- [API Docs](https://docs.spectrocloud.com/api/v1/clusterprofiles/)
- [Cluster Profiles](https://docs.spectrocloud.com/profiles/cluster-profiles/)
