---
name: spectrocloud-clusters
description: "Create, inspect, tear down and re-create Palette clusters -- edge-native (agent mode, appliance mode, 2-node HA) plus imported and cloud clusters, via API or Terraform. Use when Craig says: create that cluster, deploy a 3 node palette cluster, spin up a cluster to demo, destroy and recreate the cluster, destroy all the Palette resources we created for this, delete the cluster and remove the import, import this EKS cluster, did you deploy the cluster yet, check on the cluster it seems like it is finishing up, add or replace a node. Ask for project, cluster name, profiles, and edge host UIDs before creating. Pair with spectrocloud-cluster-profiles for the profile layers and spectrocloud-troubleshooting when the cluster does not come up."
---

# Spectro Cloud Edge Clusters

Deploy and manage Kubernetes clusters on edge infrastructure using Palette.

## Before Creating Clusters

**Ask the user:**
1. Project name? (use `spectrocloud-common` skill for UID)
2. Cluster name?
3. Infrastructure profile? (use `spectrocloud-cluster-profiles` skill)
4. Add-on profile(s)? (optional)
5. Edge host UIDs? (must be registered)
6. Deployment mode? (agent, appliance, or 2-node HA)
7. Network mode? VIP (needs IP) or Overlay
8. SSH public key(s)?
9. NTP server(s)?

**Best Practice**: Use separate infrastructure + add-on profiles.

## Edge Deployment Modes

| Mode | Nodes | BYOOS | Use Case |
|------|-------|-------|----------|
| Agent | 1 or 3+ | `system.uri: "NA"` | Existing OS |
| Appliance | 1 or 3+ | Provider image URL | Immutable |
| 2-Node HA | Exactly 2 | Provider + K3s | HA edge |

**2-Node**: K3s only, appliance mode only, `TWO_NODE=true` in CanvOS.

## API: Create Cluster

```bash
curl -s -X POST "https://api.spectrocloud.com/v1/spectroclusters/edge-native" \
  -H "ApiKey: $PALETTE_API_KEY" \
  -H "ProjectUid: $PROJECT_UID" \
  -H "Content-Type: application/json" \
  -d '{
    "metadata": {"name": "my-cluster"},
    "spec": {
      "cloudType": "edge-native",
      "profiles": [{"uid": "<infra-uid>"}, {"uid": "<addon-uid>"}],
      "cloudConfig": {
        "sshKeys": ["ssh-rsa AAAA..."],
        "vip": "192.168.1.100",
        "ntpServers": ["time.google.com"]
      },
      "machinePools": [{
        "name": "control-plane-pool",
        "size": 1,
        "controlPlane": true,
        "controlPlaneAsWorker": true,
        "edgeHosts": [{"hostUid": "<edge-host-uid>"}]
      }]
    }
  }'
```

### Overlay Network (instead of VIP)
```json
"cloudConfig": {
  "sshKeys": ["..."],
  "ntpServers": ["time.google.com"],
  "overlayNetworkConfiguration": {"enable": true}
}
```

### 2-Node HA Configuration

**Correct API structure** (differs from standard cluster):
```json
{
  "spec": {
    "cloudConfig": {
      "isTwoNodeCluster": true,
      "sshKeys": ["ssh-rsa ..."],
      "vip": "192.168.1.100",
      "ntpServers": ["time.google.com"]
    },
    "machinePoolConfig": [{
      "cloudConfig": {
        "edgeHosts": [
          {"hostUid": "<node1-uid>", "twoNodeCandidatePriority": "primary"},
          {"hostUid": "<node2-uid>", "twoNodeCandidatePriority": "secondary"}
        ]
      },
      "poolConfig": {
        "name": "control-plane-pool",
        "size": 2,
        "isControlPlane": true,
        "useControlPlaneAsWorker": true
      }
    }]
  }
}
```

**Key 2-node fields:**
- `isTwoNodeCluster: true` in `cloudConfig` (not at spec level)
- `twoNodeCandidatePriority`: `"primary"` or `"secondary"` per host
- `useControlPlaneAsWorker: true` to run workloads on both nodes
- Uses `machinePoolConfig` (not `machinePools`) with nested `cloudConfig`/`poolConfig`

## API: Other Operations

### Get Cluster
```bash
curl -s "https://api.spectrocloud.com/v1/spectroclusters/$CLUSTER_UID" \
  -H "ApiKey: $PALETTE_API_KEY" -H "ProjectUid: $PROJECT_UID"
```

### Get Kubeconfig
```bash
curl -s "https://api.spectrocloud.com/v1/spectroclusters/$CLUSTER_UID/assets/kubeconfig" \
  -H "ApiKey: $PALETTE_API_KEY" -H "ProjectUid: $PROJECT_UID" > kubeconfig.yaml
```

### Delete Cluster
```bash
curl -s -X DELETE "https://api.spectrocloud.com/v1/spectroclusters/$CLUSTER_UID" \
  -H "ApiKey: $PALETTE_API_KEY" -H "ProjectUid: $PROJECT_UID"
```

### List Edge Hosts
```bash
curl -s "https://api.spectrocloud.com/v1/edgehosts" \
  -H "ApiKey: $PALETTE_API_KEY" -H "ProjectUid: $PROJECT_UID" | \
  jq '[.items[] | {name: .metadata.name, uid: .metadata.uid, state: .status.state}]'
```

## Cluster Lifecycle

### Update Profile
Create new profile version first (see `spectrocloud-cluster-profiles`), then:
```bash
curl -s -X PUT "https://api.spectrocloud.com/v1/spectroclusters/$CLUSTER_UID/profiles" \
  -H "ApiKey: $PALETTE_API_KEY" -H "ProjectUid: $PROJECT_UID" \
  -H "Content-Type: application/json" \
  -d '{"profiles": [{"uid": "<new-version-uid>"}]}'
```

**IMPORTANT**: PUT replaces the cluster's entire attached-profile set. Any attached profile whose uid is left out of the body gets detached — including add-ons. On a cluster with more than one profile, read the complete current list from `spec.clusterProfileTemplates` (Get Cluster, below) and send all of it, or use PATCH instead (see "Attach an Additional Profile" below). Also remember: a new profile version resets that profile's variable overrides.

### Attach an Additional Profile to a Running Cluster (Additive)
To attach a profile (e.g. an add-on) without touching what's already attached, PATCH instead of PUT:
```bash
curl -s -X PATCH "https://api.spectrocloud.com/v1/spectroclusters/$CLUSTER_UID/profiles?resolveNotification=false" \
  -H "ApiKey: $PALETTE_API_KEY" -H "ProjectUid: $PROJECT_UID" \
  -H "Content-Type: application/json" \
  -d '{"profiles": [{"uid": "<addon-profile-uid>"}]}'
```

Verify — re-GET the cluster and confirm `spec.clusterProfileTemplates` grew from N to N+1 with the original uids unchanged:
```bash
curl -s "https://api.spectrocloud.com/v1/spectroclusters/$CLUSTER_UID" \
  -H "ApiKey: $PALETTE_API_KEY" -H "ProjectUid: $PROJECT_UID" | \
  jq '.spec.clusterProfileTemplates[] | {name, uid, type}'
```

Source (re-verify against these if this ever needs re-checking): `spectrocloud/palette-sdk-go` `client/cluster.go` (`PatchClusterProfileValues`, `UpdateClusterProfileValues`) and `client/addon_deployment_update.go` (`CreateAddonDeployment`).

### Add Edge Host
```bash
curl -s -X PATCH "https://api.spectrocloud.com/v1/spectroclusters/$CLUSTER_UID/machinePools/worker-pool" \
  -H "ApiKey: $PALETTE_API_KEY" -H "ProjectUid: $PROJECT_UID" \
  -H "Content-Type: application/json" \
  -d '{"edgeHosts": [{"hostUid": "<new-host-uid>"}]}'
```

## Profile Variables

Override profile variables at cluster creation:
```json
"profiles": [{"uid": "<uid>", "variables": [
  {"name": "K8sPodCIDR", "value": "100.64.0.0/18"},
  {"name": "K8sServiceCIDR", "value": "100.64.64.0/18"}
]}]
```

## Additional Resources

- `references/api-examples.md` - Full API examples (multi-node, 2-node)
- `references/terraform-examples.md` - Full Terraform patterns

## Edge Host Token Creation

**IMPORTANT**: Edge host tokens are TENANT-scoped, not project-scoped. Do NOT include ProjectUid header.

```bash
# Create edge host token (NO ProjectUid header!)
curl -s -X POST "https://api.spectrocloud.com/v1/edgehosts/tokens" \
  -H "ApiKey: $PALETTE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"metadata": {"name": "my-token"}}'

# Token value is in spec.token (NOT status.token)
TOKEN=$(echo $RESPONSE | jq -r '.spec.token')
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Enable two-node cluster to configure candidate priority" | Set `is_two_node_cluster = true` in Terraform cloud_config block |
| "Two-node candidate priority demands one primary and one secondary" | Add `two_node_role = "primary"` and `"secondary"` to each edge_host block (Terraform) |
| Terraform attribute not found | API vs Terraform naming differs - check with `terraform providers schema -json` |
| Cluster stuck provisioning | Check edge host logs: `journalctl -u spectro-stylus-agent.service -f` |
| Cluster stuck Provisioning, no nodes appearing | VMs likely in install loop - check boot order is disk-first (`scsi0;ide2`), power cycle VMs |
| 2-node cluster needs VIP | 2-node clusters cannot use overlay-only networking - must specify a VIP |
| Can't find latest K8s version | API paginates at 50 - use offset parameter to get all versions |
| "ProjectUidIsNotEmpty" on token creation | Edge host tokens are tenant-scoped - remove ProjectUid header |
| Profiles created but cluster creation fails | Check Terraform provider has `project_name` set (see `spectrocloud-cluster-profiles` skill) |

## Quick Reference

| Operation | Endpoint |
|-----------|----------|
| Create | `POST /v1/spectroclusters/edge-native` |
| Get | `GET /v1/spectroclusters/{uid}` |
| Delete | `DELETE /v1/spectroclusters/{uid}` |
| Kubeconfig | `GET /v1/spectroclusters/{uid}/assets/kubeconfig` |
| Edge Hosts | `GET /v1/edgehosts` |
| Update Profile (replaces set) | `PUT /v1/spectroclusters/{uid}/profiles` |
| Attach profile (additive) | `PATCH /v1/spectroclusters/{uid}/profiles` |

## Links

- [Edge Clusters](https://docs.spectrocloud.com/clusters/edge/)
- [Terraform Provider](https://registry.terraform.io/providers/spectrocloud/spectrocloud/latest/docs)
