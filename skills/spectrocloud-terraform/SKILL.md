---
name: spectrocloud-terraform
description: "The spectrocloud/spectrocloud Terraform provider -- provider block and auth, which resource maps to which Palette object, pinning the provider version against the Palette release train, importing existing clusters/profiles into state, what the provider cannot do (the API has to take over), and the failure modes that actually bite (version-mutation gotcha, scope race condition, orphaned profiles). Use when Craig says: write this as Terraform, give me the HCL for this cluster/profile, import this into state, pin the provider version, why did terraform silently overwrite the profile, why do I get perpetual diffs, terraform shows an id but the API returns null, should this be Terraform or the API. Pair with spectrocloud-common for auth/project lookup, spectrocloud-clusters and spectrocloud-cluster-profiles for the resources being declared, and spectrocloud-troubleshooting when an apply produced a cluster that will not come up."
---

# Spectro Cloud Terraform Provider

`spectrocloud/spectrocloud` on the Terraform Registry. Read `spectrocloud-common` first for
credential retrieval and project lookup — this skill assumes `PALETTE_API_KEY` and the target
project are already sorted. Source: `github.com/spectrocloud/terraform-provider-spectrocloud`
(public repo; provider docs live in `docs/resources` and `docs/data-sources` there and are the
ground truth for any field this skill doesn't quote in full).

## Provider Block and Auth

```hcl
terraform {
  required_providers {
    spectrocloud = {
      source  = "spectrocloud/spectrocloud"
      version = "~> 0.30"   # pin a minor series -- see Version Pinning below
    }
  }
}

provider "spectrocloud" {
  host         = var.sc_host         # defaults to api.spectrocloud.com; set for on-prem/VerteX
  api_key      = var.sc_api_key      # or SPECTROCLOUD_APIKEY env var -- prefer the env var
  project_name = var.sc_project_name # defaults to "Default" if omitted -- always set it explicitly
}
```

Env vars the provider reads directly (no HCL needed): `SPECTROCLOUD_HOST`,
`SPECTROCLOUD_APIKEY`, `SPECTROCLOUD_TRACE`, `SPECTROCLOUD_RETRY_ATTEMPTS`. `retry_attempts`
defaults to 10 — raise it for flaky on-prem tenants rather than wrapping applies in retry loops.

**`ignore_insecure_tls_error`** skips TLS verification. Only for self-signed on-prem/appliance
management endpoints on a trusted network during a POC — never for anything reachable from the
internet, and never as a fix for an unrelated cert error.

### Feature flags vs feature previews (different maps, different purpose)

```hcl
provider "spectrocloud" {
  feature_flag = {
    disable_addon_deployment_resource = true   # blocks spectrocloud_addon_deployment entirely
  }
  feature_preview = {
    "immutable-clusterprofiles" = true         # opt-in replacement-based profile versioning
  }
}
```

- `feature_flag` gates whether a resource is *allowed* (currently just
  `disable_addon_deployment_resource` — set it to stop `cluster_profile`/`cluster_template` and
  `addon_deployment` from fighting over the same attached profiles; see the provider's own
  `disable_addon_deployment_resource` doc for the read-refresh behavior difference between
  `cluster_profile`-only and `cluster_template`-only configs).
- `feature_preview` changes *how* a resource behaves. Today there's exactly one:
  `immutable-clusterprofiles` — see **Cluster Profile Versioning** under Failure Modes, it is the
  single most consequential knob in this provider for anyone doing repeatable profile work.

Multiple scopes (tenant + several projects) in one apply: give each scope its own **provider
alias** rather than one provider block switching `project_name` between resources — see the
Concurrency Race Condition entry under Failure Modes for why.

## Resource → Palette Object Map

The provider covers roughly 90% of what the Palette API/UI can do; new Palette features land in
the API first and get a Terraform resource later, sometimes much later. Full lists:
`docs/resources/` (53 resources) and `docs/data-sources/` (35) in the provider repo. The
groupings that matter day to day:

| Palette object | Resource(s) | Data source(s) |
|---|---|---|
| Project | `spectrocloud_project` | `spectrocloud_project` |
| Cluster profile | `spectrocloud_cluster_profile` (add-on/infra/full) | `spectrocloud_cluster_profile` |
| Cluster profile from exported JSON | `spectrocloud_cluster_profile_import` | — |
| Cluster template (multi-profile bundles) | `spectrocloud_cluster_config_template` | `spectrocloud_cluster_config_template` |
| Cluster config policy | `spectrocloud_cluster_config_policy` | `spectrocloud_cluster_config_policy` |
| Edge-native cluster | `spectrocloud_cluster_edge_native`, `spectrocloud_cluster_edge_vsphere` | `spectrocloud_cluster` (generic read) |
| Cloud clusters | `spectrocloud_cluster_{aws,azure,gcp,eks,aks,gke,vsphere,maas,apache_cloudstack,custom_cloud}` | `spectrocloud_cluster` |
| Existing (brownfield) k8s cluster | `spectrocloud_cluster_brownfield` | — |
| Cluster group (multi-cluster pooling) | `spectrocloud_cluster_group` | `spectrocloud_cluster_group` |
| Cloud account (credentials) | `spectrocloud_cloudaccount_{aws,azure,gcp,vsphere,maas,custom,apache_cloudstack}` | matching `data.spectrocloud_cloudaccount_*` |
| Appliance (edge device object) | `spectrocloud_appliance` | `spectrocloud_appliance`, `spectrocloud_appliances` |
| Registration token (pairing edge hosts / attaching brownfield) | `spectrocloud_registration_token` | `spectrocloud_registration_token` |
| Pack / pack registry | — (packs are data only) | `spectrocloud_pack`, `spectrocloud_pack_simple`, `spectrocloud_registry_pack` |
| Registry (generic/Helm/OCI) | `spectrocloud_registry_helm`, `spectrocloud_registry_oci` | `spectrocloud_registry`, `spectrocloud_registry_helm`, `spectrocloud_registry_oci` |
| Add-on deployment (attach profile post-create) | `spectrocloud_addon_deployment` | — |
| Backup storage *target* (not executions) | `spectrocloud_backup_storage_location` | `spectrocloud_backup_storage_location` |
| Workspace | `spectrocloud_workspace` | `spectrocloud_workspace` |
| Palette Apps (App Mode) | `spectrocloud_application`, `spectrocloud_application_profile` | `spectrocloud_application_profile` |
| Virtual clusters / VMs (Palette Virtual) | `spectrocloud_virtual_cluster`, `spectrocloud_virtual_machine`, `spectrocloud_datavolume` | — |
| IAM | `spectrocloud_user`, `spectrocloud_team`, `spectrocloud_role`, `spectrocloud_sso`, `spectrocloud_password_policy` | matching data sources + `spectrocloud_permission` |
| SSH key, filter, macro, resource limit, alert, audit trail, dev/platform settings, PCG DNS map & IP pool | one resource each, mostly small config objects | matching data sources where listed above |

Pack discovery is **data-source only** — there is no `resource "spectrocloud_pack"`. Look packs
up with `data.spectrocloud_pack` (advanced filters) or `data.spectrocloud_pack_simple`, then feed
`.id`/`.values` into a `pack {}` block inside `spectrocloud_cluster_profile`. See
`spectrocloud-packs` for pack version discovery and `spectrocloud-cluster-profiles` for the full
pack-block HCL patterns (manifest packs, values, install-priority).

## Version Pinning Against the Palette Release Train

The provider's **minor** version tracks Palette releases; **patch** releases ship roughly weekly
independent of Palette. Each minor series is tested against its Palette release and the one
before it (N‑1) — pin a minor series (`~> 0.30`), not an exact patch, and don't assume a patch
bump is safe against an arbitrarily old Palette tenant.

Known mapping points, oldest to current as of this skill (verify current with
`gh api repos/spectrocloud/terraform-provider-spectrocloud/releases` — provider release notes are
the source of truth, not this table, since both trains move):

| Palette | Provider |
|---|---|
| 4.4.x and later | `>= v0.20.6` |
| 4.10.x | `v0.30.0` (SDK refresh for 4.10.0 API changes) |
| latest at time of writing | `v0.30.1`, published 2026-09-11 |

**LTS window**: engineering targets N‑2 major-version forward/backward compatibility for
Palette/VerteX LTS trains — don't assume a provider release from two majors back still talks to a
current LTS tenant without checking the release matrix.

**Before bumping the provider version on an existing config**, read that release's CHANGELOG
entry for `BACKWARDS INCOMPATIBILITIES` — the provider does ship breaking field removals (e.g. a
deprecated `cloud_config.ssh_key` field dropped in favor of `ssh_keys`). `terraform plan`
immediately after a version bump, before touching HCL, to see what the new provider version
alone changes.

## Importing Existing Clusters and Profiles

Terraform ≥ 1.5 `import` blocks are preferred over `terraform import` on the CLI; both use the
same ID format. **Most resources need `<id>:<context>`**, context being `project` or `tenant`
(some, like `cluster_profile_import`, also take a version suffix). Tenant-scope imports need
tenant admin access.

```hcl
# Cluster (any cloud type) -- id is <cluster_uid>/<cluster_name>, colon then context
import {
  to = spectrocloud_cluster_edge_native.example
  id = "abc123/my-cluster:project"
}

# Cluster profile -- id:context
import {
  to = spectrocloud_cluster_profile.example
  id = "def456:project"
}

# Appliance -- id is <appliance_uid>/<appliance_name>, no context suffix; project-scoped
import {
  to = spectrocloud_appliance.example
  id = "ghi789/my-appliance"
}
```

- **`spectrocloud_cluster_profile` import** pulls in the profile as it exists *today*. It does
  **not** retroactively give you `immutable-clusterprofiles` history for versions that existed
  before you turned that preview flag on — versioning behavior only applies going forward.
- **Importing a profile from an exported JSON file** (cross-tenant copy, DR, "make this US profile
  exist in the EU tenant") is a different resource: `spectrocloud_cluster_profile_import`, which
  takes `import_file` (a local path) rather than pulling from an existing Palette object by ID.
  Use `palette-axi profile <ref>` / the Palette export UI to produce that file first — this skill
  doesn't cover profile export, `spectrocloud-cluster-profiles` does.
  It can also be imported after the fact via `terraform import
  spectrocloud_cluster_profile_import.{uid}/{name}:context:version`.
- **Registering a cluster Palette didn't create** (an existing EKS/AKS/on-prem k8s cluster you
  want under Palette management) is not a Terraform *import* at all — it's the
  `spectrocloud_cluster_brownfield` resource, which calls Palette's brownfield-registration API to
  attach an existing cluster. `import_mode = "read_only"` vs `"full"` controls whether Palette
  actually manages the cluster afterward or just observes it. Don't confuse this with `import
  {}` blocks, which only reattach Terraform state to something Palette already fully owns.

After any import, run `terraform plan` before touching HCL — a nonempty diff means your
configuration doesn't yet match the imported object's actual field values, not that the import
failed.

## What the Provider Cannot Do — Where the API Takes Over

The provider is declarative desired-state provisioning for Day‑0/Day‑1. It has no concept of
imperative, one-shot, or streaming operations. These always need `palette-axi` / raw curl (see
`spectrocloud-common`), never a Terraform resource, no matter what version you're on:

| Category | Provider gives you | API-only |
|---|---|---|
| Backup/restore | `spectrocloud_backup_storage_location` (target config only) | Triggering on-demand backup/restore, inspecting run history, deleting a specific snapshot, resetting a schedule |
| Edge host lifecycle | `spectrocloud_appliance`, `spectrocloud_registration_token`, `cluster_edge_native` | Generating/rotating pairing keys, associate/de-associate a host to a cluster, updating host metadata, resetting a host |
| Cluster observability | `data.spectrocloud_cluster` (point-in-time metadata) | Event streams, audit trails, live node/component health, support-bundle export |
| Node remediation | Profile changes that trigger a rolling repave on `apply` | Manual out-of-band repave, cordon/drain/reboot a specific node, tracking live repave progress, pausing/resuming machine health-check remediation |
| Credentials | Static `kubeconfig`/`admin_kube_config` as computed outputs at create/read time | Short-lived scoped kubeconfig tokens, credential rotation without mutating TF state |
| Registry sync | Registry resource definitions | Forcing an immediate "sync now" on a Helm/OCI registry |
| Identity/API keys | `spectrocloud_user`, `spectrocloud_role`, `spectrocloud_team` | Service-account creation, API key generation/rotation |
| Misc | — | Pausing cluster reconciliation, forcing a state re-import, emergency hard teardown outside `destroy` |

Rule of thumb from SE guidance: default to Terraform for anything repeatable — profiles, cloud
accounts, cluster lifecycle, GitOps/CI pipelines. Reach for the API directly for anything
time-boxed, imperative, or not yet mapped to a resource — this is the same split
`spectrocloud-common` describes as "API vs Terraform" but the table above is the actual boundary,
not a rule of thumb.

## Failure Modes That Actually Bite

**Cluster profile version mutation (the big one).** Changing `version` on a plain
`spectrocloud_cluster_profile` does **not** create a new version in Palette — it calls
`UpdateClusterProfile` and mutates/renames the existing version in place, orphaning any cluster
still referencing the old version by UID. If Craig wants a new profile version to persist
alongside old ones (the usual ask — see `spectrocloud-cluster-profiles`), either declare a
separate Terraform resource per version, or turn on `feature_preview =
{ "immutable-clusterprofiles" = true }` **and** `skip_destroy = true` on the resource **and**
`lifecycle { create_before_destroy = true }`. All three are required together — missing
`skip_destroy` fails the plan outright; missing `create_before_destroy` risks the old version
being destroyed before the new one exists.

**Missing `project_name` → silently orphaned resources.** Without `project_name` set on the
provider block, `terraform apply` reports success and shows an id, but the resource (commonly
profiles) isn't attached to any project the UI or API will show you — `GET` on it returns null.
Fix: set `project_name` explicitly, `terraform state rm` the orphaned resource, re-apply. This is
also documented in `spectrocloud-cluster-profiles`; it is not profile-specific, it applies to
anything scoped to a project.

**Concurrent tenant/project scope race (PLT‑2438).** The provider mutates a shared internal HTTP
client in place when switching between tenant and project scope. Under Terraform's default
parallelism, concurrent creates across scopes can cross-contaminate — a tenant-scope request
picks up a stray `ProjectUid` header, or a project-scope request drops its project context
entirely. Workaround: one provider alias per scope, not one provider block juggling
`project_name` across resources in the same apply.

**Perpetual diffs from schema quirks.** Older provider versions show phantom
`false → null` drift on `profile_variables` (`hidden`, `immutable`, `is_sensitive`) and re-drift
`spectrocloud_registry_helm` credentials on every refresh because the API returns masked
secret values the provider can't diff against cleanly (fixed with `is_synchronization` /
masked-value handling in v0.30.0). If you see a diff that never resolves no matter how many times
you apply, check the provider version before assuming your HCL is wrong.

**Day‑2 immutability silently ignored.** Fields like `update_worker_pools_in_parallel` only take
effect at cluster creation. Changing them on an existing cluster used to fail silently (drift
forever); current releases reject the change at plan time instead — if you hit a hard plan-time
error on a field you're sure you set correctly, check whether it's create-only.

**Debugging a provider failure Palette diagnostics won't show you.** The provider's client-side
errors (auth failures, malformed requests before they even hit the API) don't show up in Palette
support bundles. Set `SPECTROCLOUD_TRACE=true` (or `trace = true` in the provider block) plus
`TF_LOG=DEBUG` to see the raw HTTP request/response.

## Links

- Provider docs: https://registry.terraform.io/providers/spectrocloud/spectrocloud/latest/docs
- Source + resource/data-source markdown: https://github.com/spectrocloud/terraform-provider-spectrocloud
- E2E examples: https://github.com/spectrocloud/terraform-provider-spectrocloud/tree/main/examples/e2e
- Releases (check current provider/Palette pairing before pinning): https://github.com/spectrocloud/terraform-provider-spectrocloud/releases
