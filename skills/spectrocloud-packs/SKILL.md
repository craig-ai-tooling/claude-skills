---
name: spectrocloud-packs
description: "Known-good pack values and the gotchas that bite, for Palette pack layers -- Piraeus/LINSTOR, Longhorn, MetalLB, Cilium, Calico, external-secrets, MongoDB, nginx, hello-universe -- plus how to page through the packs API for every version and pull the FULL default values. Use when Craig says: check the pack values, what should this pack's values look like, why is this pack failing (ChartInstallFailed, PackServiceNotReady, ManifestInstallFailed), get longhorn or piraeus RWX working, fix the pod/service CIDRs, set install-priority, what versions of this pack exist, turn these values into profile variables, is anything glaringly wrong with this profile's layers. Also use before adding or bumping a pack layer in a cluster profile, so the values go in complete rather than partial."
---

# Spectro Cloud Pack Learnings

Pack-specific configuration patterns, gotchas, and known issues.

## Pack Discovery

Use the `spectrocloud-common` skill for all discovery queries — pagination-safe find-by-name ("Find Pack by Exact Name"), latest-version + UID lookup ("Get Latest Pack Version"), and full default values ("Get Pack Default Values"). Two rules that skill enforces:

- The pack API **paginates at 50 results** — always loop offsets 0/50/100/150
- **Never use partial pack values** — fetch the COMPLETE file via `GET /v1/packs/$PACK_UID?includePackValues=true`

---

## Storage Packs

### Piraeus (LINSTOR)

Distributed storage for edge using LINSTOR/DRBD.

**Pack name**: `piraeus-operator`
**Registry**: Check with discovery (often Palette Community Registry)
**Type**: `oci`

**Critical configuration** (all of these are needed):

```yaml
charts:
  piraeus:
    # 1. Service name length limit (63 chars) - pack name creates resources too long
    fullnameOverride: "piraeus"
  linstor-gui:
    fullnameOverride: "linstor-gui"

  # 2. DRBD module loader fails on HWE kernels (Ubuntu 22.04 with 6.8.x kernel)
  linstorSatelliteConfigurations:
    - name: disable-drbd-loader
      spec:
        podTemplate:
          spec:
            initContainers:
              - name: drbd-module-loader
                $patch: delete
    # 3. File-based storage pool (default path works, don't override unless needed)
    - name: file-thin-storage-pool
      spec:
        storagePools:
          - name: file-pool
            fileThinPool:
              directory: /var/lib/piraeus-pools

  # 4. Storage without DRBD - must use STORAGE layer only (no replication)
  storageClasses:
    - name: piraeus-storage
      parameters:
        placementCount: "1"
        storagePool: "file-pool"
        layerList: "STORAGE"  # Critical when DRBD disabled
```

**Gotchas:**
- **Name too long**: Without `fullnameOverride`, resources exceed 63-char K8s limit
- **HWE kernel**: Ubuntu 22.04 HWE kernel (6.8.x) has no pre-built DRBD modules - must disable loader
- **No DRBD = no replication**: When DRBD disabled, use `layerList: "STORAGE"` only
- **File pool sizing**: Uses root partition space - 100GB VM disk leaves only ~2.5GB after OS install
- On nodes with a separate data disk: put the storage pool on the data disk, not the OS drive

**Post-deploy verification:**
```bash
kubectl get pods -n piraeus
kubectl get storageclasses
kubectl get linstorsatellites  # Check nodes joined
```

---

### Longhorn

Cloud-native distributed storage.

**Pack name**: `longhorn`
**Registry**: Public Repo
**Type**: `spectro`

**Key configuration:**
```yaml
defaultSettings:
  defaultDataPath: /var/lib/longhorn  # Ensure disk space here
  replicaCount: 1  # For single-node edge, 3 for HA
```

**Gotchas:**
- Needs open-iscsi on nodes
- High resource usage for small edge deployments
- Replica count must match available nodes

---

## Networking Packs

### MetalLB

Bare-metal load balancer for on-prem/edge.

**Pack name**: `lb-metallb-helm`
**Registry**: Public Repo
**Type**: `spectro`

**Key configuration:**
```yaml
# L2 mode (most common for edge)
configInline:
  address-pools:
    - name: default
      protocol: layer2
      addresses:
        - 192.168.1.200-192.168.1.250  # MUST be in same subnet as nodes

# For newer MetalLB versions (0.13+), use IPAddressPool + L2Advertisement
# Check pack version to determine config format
```

**Gotchas:**
- IP range must be routable from clients
- L2 mode requires nodes on same L2 network
- BGP mode needs router configuration
- **Version matters**: Config format changed significantly in 0.13.x

**Post-deploy verification:**
```bash
kubectl get pods -n metallb-system
kubectl get ipaddresspools  # For newer versions
kubectl get svc -A | grep LoadBalancer  # Check for EXTERNAL-IP
```

---

### Calico (CNI)

**Pack name**: `cni-calico`
**Registry**: Public Repo
**Type**: `spectro`

**Key configuration:**
```yaml
# Update CIDRs to avoid conflicts
installation:
  calicoNetwork:
    ipPools:
      - cidr: 100.64.0.0/18  # Pod CIDR - change from default!
```

---

### Cilium (CNI)

**Pack name**: `cni-cilium-oss`
**Registry**: Public Repo
**Type**: `spectro`

**Gotchas:**
- Requires kernel 4.9+ (5.4+ recommended)
- May conflict with existing iptables rules
- Hubble UI needs additional config for observability

---

## Security Packs

### External Secrets Operator

Syncs secrets from external stores (1Password, AWS, Vault, etc.).

**Pack name**: `external-secrets-operator`
**Registry**: Public Repo
**Type**: `spectro`

**Usage:**

1. Deploy operator with this config:
```yaml
# Pack values
installCRDs: true
```

2. After operator deploys, create a `ClusterSecretStore` for your backend (AWS Secrets Manager, HashiCorp Vault, 1Password, etc.) — see [ESO provider docs](https://external-secrets.io/latest/provider/aws-secrets-manager/).

3. Create ExternalSecret to sync:
```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: my-secret
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: my-secret-store
    kind: ClusterSecretStore
  target:
    name: my-k8s-secret
  data:
    - secretKey: password
      remoteRef:
        key: my-secret-item
        property: password
```

**Gotchas:**
- Backend-specific credentials must be configured before SecretStore works
- Secret key names and paths are case-sensitive

---

## Database Packs

### MongoDB (Bitnami)

**Pack name**: `mongodb`
**Registry**: Bitnami
**Type**: `helm`

**Gotchas:**

1. **Image tags expire**: Bitnami removes old image tags (e.g., `4.4.24-debian-11-r9`). Options:
   - Use official `mongo:4.4` image (requires changing volumeMount from `/bitnami/mongodb` to `/data/db`)
   - Check current available tags before deployment: `docker pull bitnami/mongodb:<tag>`

2. **Standalone vs ReplicaSet**: For single-node MongoDB:
```yaml
architecture: standalone  # Creates Deployment, not StatefulSet
persistence:
  enabled: true
  size: 8Gi
```

3. **Volume mount path differs by image**:
   - Bitnami image: `/bitnami/mongodb`
   - Official mongo image: `/data/db`

---

## Application Packs

### Hello Universe

Demo application for testing deployments.

**Pack name**: `hello-universe`
**Registry**: Palette Community Registry
**Type**: `oci`

**Key configuration:**
```yaml
# Minimal config - usually works with defaults
pack:
  namespace: hello-universe
```

**Gotchas:**
- Needs LoadBalancer or Ingress to access
- If using NodePort, find port: `kubectl get svc -n hello-universe`

---

### Nginx Ingress

**Pack name**: `nginx`
**Registry**: Public Repo
**Type**: `spectro`

**Key configuration:**
```yaml
controller:
  service:
    type: LoadBalancer  # Needs MetalLB on bare-metal
    # Or use NodePort for simple edge:
    # type: NodePort
```

---

## Pack Type Quick Reference

| Pack | Registry | Type | Layer |
|------|----------|------|-------|
| `edge-native-byoi` | Public Repo | `spectro` | os |
| `edge-k3s` | Public Repo | `spectro` | k8s |
| `edge-k8s` | Public Repo | `spectro` | k8s |
| `cni-calico` | Public Repo | `spectro` | cni |
| `cni-cilium-oss` | Public Repo | `spectro` | cni |
| `lb-metallb-helm` | Public Repo | `spectro` | addon |
| `external-secrets-operator` | Public Repo | `spectro` | addon |
| `hello-universe` | Palette Community | `oci` | addon |
| `piraeus-operator` | (discover) | `oci` | addon |
| `longhorn` | Public Repo | `spectro` | addon |
| `nginx` | Public Repo | `spectro` | addon |
| `harbor` | Bitnami | `helm` | addon |
| `mongodb` | Bitnami | `helm` | addon |

## Adding New Pack Learnings

When you discover a pack-specific issue or pattern:
1. Note the exact pack name and version
2. Document what config was needed
3. Document what failed and why
4. Add verification commands

## Links

- [Palette Pack Registry](https://docs.spectrocloud.com/integrations/)
- [Community Packs](https://github.com/spectrocloud/pack-central)
