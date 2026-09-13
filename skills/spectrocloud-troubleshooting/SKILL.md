---
name: spectrocloud-troubleshooting
description: "Figure out why a Palette cluster, edge host, or pack is not healthy -- cluster event stream and conditions via the API, log bundles, stylus and palette-agent logs over SSH, plus a list of which errors are real versus normal deploy noise. Use when Craig says: why is this cluster stuck, it is in Provisioning and not provisioning, take a look and see if you can figure out why, why are nodes going NotReady, why is it cordoned, everything is still failing yes, this pack will not install, the registry is syncing forever, gather the logs / grab a support bundle / pull a log bundle, deep dive on what is going on, do not fix it just diagnose it, watch the deploy and tell me what breaks. Also use while watching any deploy, since it says which errors to ignore and when impatience is the real problem."
---

# Spectro Cloud Troubleshooting

Debug cluster provisioning, upgrades, and operational issues using Palette's event streams and logs.

For the `$PALETTE_API_KEY` / `$PROJECT_UID` env vars used below, see the `spectrocloud-common` skill (auth + project UID lookup).

## Key Concepts

- **Event Stream**: Live cluster events showing orchestration progress and errors
- **Cluster Conditions**: Milestones like "Creating Infrastructure", "Adding Control Plane Node"
- **Log Bundle**: Downloadable archive with Spectro logs, system logs, and manifests
- **Reconciliation**: Palette retries failed operations - intermittent errors may resolve automatically

## Cluster Event Stream (API)

Events stream live and show orchestration progress. Watch these during provisioning.

### Get Cluster Events
```bash
# Get recent events for a cluster
curl -s "https://api.spectrocloud.com/v1/spectroclusters/$CLUSTER_UID/events?limit=50" \
  -H "ApiKey: $PALETTE_API_KEY" \
  -H "ProjectUid: $PROJECT_UID" | \
  jq '[.items[] | {time: .metadata.creationTimestamp, type: .involvedObject.kind,
      reason: .reason, message: .message}]'
```

### Get Cluster Status & Conditions
```bash
# Overview with conditions and upgrade history
curl -s "https://api.spectrocloud.com/v1/dashboard/spectroclusters/$CLUSTER_UID/overview" \
  -H "ApiKey: $PALETTE_API_KEY" \
  -H "ProjectUid: $PROJECT_UID" | \
  jq '{state: .status.state, conditions: .status.conditions, upgrades: .status.upgrades}'
```

### Watch Events (Poll)
```bash
# Poll events every 10 seconds during provisioning
while true; do
  echo "=== $(date) ==="
  curl -s "https://api.spectrocloud.com/v1/spectroclusters/$CLUSTER_UID/events?limit=10" \
    -H "ApiKey: $PALETTE_API_KEY" \
    -H "ProjectUid: $PROJECT_UID" | \
    jq -r '.items[] | "\(.metadata.creationTimestamp) [\(.reason)] \(.message)"' | head -10
  sleep 10
done
```

## Log Bundle Download

Download comprehensive logs for deep debugging or support requests.

### Download via API
```bash
# Download log bundle (returns zip file)
curl -s "https://api.spectrocloud.com/v1/spectroclusters/$CLUSTER_UID/features/logFetcher/logs" \
  -H "ApiKey: $PALETTE_API_KEY" \
  -H "ProjectUid: $PROJECT_UID" \
  -o spectro_logs.zip

# Extract and examine
unzip spectro_logs.zip -d cluster-logs/
ls cluster-logs/
```

### Log Bundle Contents
| File/Folder | Contents |
|-------------|----------|
| `Manifest.yaml` | CRDs, Deployments, Pods, ConfigMaps, Events, Nodes |
| `spectro-*.log` | Palette agent logs (last 10k lines) |
| `system.log` | System logs |
| `cloud-init.log` | Cloud-init output |

## Edge Host Logs (SSH)

For edge deployments, SSH to the host for live debugging.

```bash
# SSH to edge host (default creds: kairos/kairos)
ssh kairos@<edge-host-ip>

# Watch Palette agent logs (most useful)
sudo journalctl -u spectro-stylus-agent.service -f

# Check all Spectro services
sudo systemctl list-units 'spectro*'

# Key log files
cat /var/log/stylus-upgrade.log
cat /var/log/kube-init.log
cat /var/log/kube-join.log

# Check kubelet if K8s is initializing
sudo journalctl -u kubelet -f
```

## Cluster State Reference

| State | Meaning |
|-------|---------|
| `Pending` | Waiting for resources |
| `Provisioning` | Creating infrastructure/nodes |
| `Running` | Healthy and operational |
| `Updating` | Profile or config change in progress |
| `Deleting` | Teardown in progress |
| `Failed` | Unrecoverable error (check events) |

## Known Errors: Noise vs. Actionable

Palette's reconciliation pattern means some errors are transient and resolve automatically.

### Normal/Transient (Usually Safe to Ignore)

These often appear during provisioning but resolve:

| Error Pattern | Why It's OK |
|---------------|-------------|
| `context deadline exceeded` | Temporary timeout, will retry |
| `connection refused` to API server | Node not ready yet, will retry |
| `unable to retrieve node` | Node registering, will resolve |
| `waiting for control plane` | Normal during bootstrap |
| `etcd cluster is not healthy` | Etcd initializing, give it time |

### Actionable Errors (Investigate)

These indicate real problems:

| Error Pattern | Likely Cause | Action |
|---------------|--------------|--------|
| `failed to pull image` | Registry auth or network | Check registry creds, network |
| `node not found` (persistent) | Edge host not registered | Check edge host in Palette UI |
| `insufficient resources` | Node too small | Increase CPU/RAM |
| `pack validation failed` | Profile misconfigured | Check pack values |
| `version mismatch` | K8s/image version conflict | Align provider image with K8s pack |
| `duplicate edge host ID` | Re-imaging without cleanup | Delete old edge host from Palette |
| `certificate has expired` | Stale certs | Re-register edge host |

### 2-Node Specific Errors

| Error Pattern | Likely Cause | Action |
|---------------|--------------|--------|
| `leader election failed` | Both nodes competing | Check network between nodes |
| `kine connection refused` | Postgres/Kine not ready | Wait, check node logs |
| `split brain` | Network partition | Restore network, may need recovery |

## Debugging Workflow

### 1. Check Cluster State
```bash
curl -s "https://api.spectrocloud.com/v1/spectroclusters/$CLUSTER_UID" \
  -H "ApiKey: $PALETTE_API_KEY" \
  -H "ProjectUid: $PROJECT_UID" | \
  jq '{name: .metadata.name, state: .status.state, health: .status.clusterHealth}'
```

### 2. Check Active Condition
```bash
curl -s "https://api.spectrocloud.com/v1/dashboard/spectroclusters/$CLUSTER_UID/overview" \
  -H "ApiKey: $PALETTE_API_KEY" \
  -H "ProjectUid: $PROJECT_UID" | \
  jq '.status.conditions[] | select(.status != "True") | {type, message, reason}'
```

### 3. Recent Events
```bash
curl -s "https://api.spectrocloud.com/v1/spectroclusters/$CLUSTER_UID/events?limit=20" \
  -H "ApiKey: $PALETTE_API_KEY" \
  -H "ProjectUid: $PROJECT_UID" | \
  jq -r '.items[] | "\(.metadata.creationTimestamp) [\(.reason)] \(.message)"'
```

### 4. SSH to Edge Host (if applicable)
```bash
ssh kairos@<edge-host-ip>
sudo journalctl -u spectro-stylus-agent.service -n 100 --no-pager
```

### 5. Download Full Logs (for support)
```bash
curl -s "https://api.spectrocloud.com/v1/spectroclusters/$CLUSTER_UID/features/logFetcher/logs" \
  -H "ApiKey: $PALETTE_API_KEY" \
  -H "ProjectUid: $PROJECT_UID" \
  -o spectro_logs_$(date +%Y%m%d_%H%M).zip
```

## Edge Host Registration Issues

```bash
# List edge hosts and their state
curl -s "https://api.spectrocloud.com/v1/edgehosts" \
  -H "ApiKey: $PALETTE_API_KEY" \
  -H "ProjectUid: $PROJECT_UID" | \
  jq '[.items[] | {name: .metadata.name, uid: .metadata.uid, state: .status.state,
      health: .status.health.state, cluster: .status.clusterUid}]'

# Check specific edge host
curl -s "https://api.spectrocloud.com/v1/edgehosts/$EDGEHOST_UID" \
  -H "ApiKey: $PALETTE_API_KEY" \
  -H "ProjectUid: $PROJECT_UID" | \
  jq '{name: .metadata.name, state: .status.state, health: .status.health,
      lastHeartbeat: .status.lastHeartbeat}'
```

## Pack Deployment Issues

```bash
# Check pack status on cluster
curl -s "https://api.spectrocloud.com/v1/spectroclusters/$CLUSTER_UID/packs/status" \
  -H "ApiKey: $PALETTE_API_KEY" \
  -H "ProjectUid: $PROJECT_UID" | \
  jq '[.items[] | {name: .name, status: .status, message: .message}]'
```

## Adding New Learnings

**This skill is a living document.** When you encounter new errors:

1. Determine if it's noise (transient, resolved by retry) or actionable
2. Add to the appropriate table above
3. Include the error pattern, cause, and recommended action
4. Commit with descriptive message

## Quick Reference

| Operation | Endpoint |
|-----------|----------|
| Cluster events | `GET /v1/spectroclusters/{uid}/events` |
| Cluster overview | `GET /v1/dashboard/spectroclusters/{uid}/overview` |
| Download logs | `GET /v1/spectroclusters/{uid}/features/logFetcher/logs` |
| Edge hosts | `GET /v1/edgehosts` |
| Pack status | `GET /v1/spectroclusters/{uid}/packs/status` |

## Links

- [Nodes and Clusters Troubleshooting](https://docs.spectrocloud.com/troubleshooting/nodes/)
- [Edge Troubleshooting](https://docs.spectrocloud.com/troubleshooting/edge/)
- [Common Issues](https://docs.spectrocloud.com/troubleshooting/)
