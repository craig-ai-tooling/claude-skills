---
name: spectrocloud-appliance-mode
description: "Build the Palette Edge ISO and everything that goes into it -- CanvOS checkout and .arg file, earthly builds, provider images, user-data and site-user-data, content bundles, air-gap installs, 2-node HA. Use when Craig says: build an ISO, rebuild the ISO with X, which CanvOS tag or K8s version should we use, does appliance mode accept Site User Data, set the hostname and static IP in user-data, build the content bundle, do the airgap / offline / disconnected build, boot it on Proxmox and install, what will the provider image tag be, stylus or Kairos on the node, two-node with a witness, secure boot. Also for a node stuck in an install loop or a /oem user-data that did not take. Use spectrocloud-agent-mode instead when Palette manages an existing OS rather than shipping an ISO."
---

# Spectro Cloud Appliance Mode

Appliance Mode creates immutable edge deployments using Kairos-based images built with CanvOS.

## When to Use

| Use Case | Mode |
|----------|------|
| Immutable, locked-down edge | Appliance |
| 2-node HA clusters | Appliance (only option) |
| Existing OS/golden images | Agent |
| Quick testing on VMs | Agent |

## Key Concepts

- **CanvOS**: Earthly-based build system for edge artifacts
- **Provider Image**: Container image with OS + specific K8s version
- **Installer ISO**: Bootable image with Palette agent + user-data
- **Content Bundle**: Pre-cached images for offline deployments

## Prerequisites

- Linux AMD64 build machine (4+ CPU, 8GB+ RAM, 150GB+ storage)
- Git, Docker, Earthly

```bash
# Install Earthly
curl -fsSL https://releases.earthly.dev/earthly-linux-amd64 -o earthly
sudo mv earthly /usr/local/bin/ && sudo chmod +x /usr/local/bin/earthly
earthly bootstrap
```

## Build Process

**Ask the user:**
1. Registry for provider images? (ttl.sh for testing, or specify)
2. K8s distribution? (k3s, rke2, kubeadm, kubeadm-fips)
3. 2-node deployment? (requires K3s + TWO_NODE=true)
4. Need content bundles for offline?

### Step 0: Determine K8s Version

**Query CanvOS for supported versions before building.** Default to n-1 minor for stability.

Run the "Get Supported K8s Versions from CanvOS" query from the `spectrocloud-common` skill (fetches `k8s_version.json` from the latest CanvOS tag and computes the n-1 minor for your distribution — k3s, rke2, kubeadm, kubeadm-fips).

**Use the resulting K8S_VERSION in Step 1's .arg file.**

### Step 1: Clone and Configure

```bash
# Clone fresh or update existing repo
if [ -d "CanvOS" ]; then
  cd CanvOS && git fetch --tags && git pull
else
  git clone https://github.com/spectrocloud/CanvOS.git && cd CanvOS
fi
LATEST_TAG=$(git describe --tags --abbrev=0)
echo "Using CanvOS $LATEST_TAG"
git checkout "$LATEST_TAG"

# Use K8S_VERSION from Step 0, or set manually
cat << EOF > .arg
OS_DISTRIBUTION=ubuntu
OS_VERSION=24.04
K8S_DISTRIBUTION=${DISTRO:-k3s}
K8S_VERSION=${K8S_VERSION:-1.32.9}
IMAGE_REGISTRY=ttl.sh
IMAGE_REPO=my-edge-images
CUSTOM_TAG=demo
ARCH=amd64
FIPS_ENABLED=false
TWO_NODE=false
EOF
```

### Step 2: Create user-data

**Bridge networking is recommended** for VM-based edge deployments (allows containers to get IPs on host network).

```bash
cat << 'EOF' > user-data
#cloud-config
install:
  reboot: true

users:
  - name: kairos
    passwd: kairos
    groups: [sudo, admin]
    sudo: ALL=(ALL) NOPASSWD:ALL

stages:
  initramfs:
    - name: "Setup bridge networking"
      files:
        - path: /etc/systemd/network/20-dhcp.network
          content: |
            [Match]
            Name=en*
            [Network]
            Bridge=br0
            LinkLocalAddressing=no
          permissions: 0644
          owner: 0
          group: 0
        - path: /etc/systemd/network/bridge0.netdev
          content: |
            [NetDev]
            Name=br0
            Kind=bridge
          permissions: 0644
          owner: 0
          group: 0
        - path: /etc/systemd/network/bridge0.network
          content: |
            [Match]
            Name=br0
            [Network]
            DHCP=yes
          permissions: 0644
          owner: 0
          group: 0

stylus:
  site:
    paletteEndpoint: api.spectrocloud.com
    edgeHostToken: <registration-token>
    projectName: <project-name>
EOF
```

**For proxy, static IP, bonds**: See `references/user-data-examples.yaml`

### Step 3: Build

```bash
docker login <registry>  # Skip for ttl.sh
earthly +iso  # Build ISO first - start imaging nodes while provider images push
earthly --push +build-provider-images
# Output: build/palette-edge-installer.iso
```

### Step 4: Version the ISO

**Critical**: The default ISO name has no version info. Rename it before uploading:

```bash
# Create versioned ISO name with date and K8s version
ISO_NAME="palette-edge-$(grep K8S_VERSION .arg | cut -d= -f2)-$(date +%Y%m%d-%H%M).iso"
mv build/palette-edge-installer.iso "build/$ISO_NAME"
echo "Built: $ISO_NAME"
```

**Before imaging any VM**, verify you're using the correct ISO:
```bash
# Check ISO build date (should match your recent build)
ls -la build/*.iso

# When uploading to hypervisor, include version in the storage name
# e.g., "palette-edge-k3s-1.30.5-20241222-1430.iso"
```

## 2-Node Deployment

2-node HA uses Postgres + Kine backend. **Appliance-mode only.**

### Requirements
- **K3s only** (not kubeadm/rke2)
- Ubuntu 22.04 recommended
- Cannot expand to 3+ nodes later

### 2-Node .arg

```bash
cat << 'EOF' > .arg
OS_DISTRIBUTION=ubuntu
OS_VERSION=22.04
K8S_DISTRIBUTION=k3s
K8S_VERSION=1.33.3
IMAGE_REGISTRY=ttl.sh
IMAGE_REPO=my-edge-2node
CUSTOM_TAG=two-node-demo
ARCH=amd64
TWO_NODE=true
EOF
```

### Build & Deploy
```bash
earthly +iso  # Build ISO first - start imaging nodes while provider images push
earthly --push +provider-image
```

When creating cluster: toggle "Two-Node Mode", select exactly 2 edge hosts.

### 2-Node Failover Behavior
- One node is leader (writes), other is follower
- Follower detects leader failure and self-promotes (~30s failover)
- On recovery, nodes compare timestamps; most recent becomes leader

## Content Bundles

Pre-cache images for offline deployments:

```bash
# Install Palette CLI
curl -LO https://github.com/spectrocloud/palette-cli/releases/latest/download/palette-linux-amd64
chmod +x palette-linux-amd64 && sudo mv palette-linux-amd64 /usr/local/bin/palette

# Build bundle
palette content build --arch amd64 --project-id <uid> \
  --cluster-profile-ids <id1>,<id2> --output ./content-bundle.tar.zst

# Include in ISO
mkdir -p content && cp content-bundle.tar.zst content/
earthly +iso
```

## Deploy

### Pre-Deploy Checklist
- [ ] ISO name includes version/date (not generic `palette-edge-installer.iso`)
- [ ] Provider image tag matches ISO build (check `.arg` used)
- [ ] Old ISOs cleaned up from hypervisor storage
- [ ] Old edge hosts deleted from Palette (prevents duplicate ID errors)

### Upload ISO to Hypervisor

Upload the versioned ISO to your hypervisor's ISO storage (e.g., via SCP, web UI, or API). After uploading:
- Verify the correct versioned ISO is present
- Remove stale ISOs to avoid accidentally booting old builds

### VM Creation

**Sizing considerations:**
| Use Case | Disk Size | Notes |
|----------|-----------|-------|
| Basic edge | 100GB | ~2.5GB free after OS for storage pools |
| With Piraeus file pool | 200GB+ | File pools use root partition space |
| With separate data disk | 100GB + data disk | Attach second disk for storage pool |

**Boot order is critical:**
- Disk first, then CD-ROM
- Empty disk falls through to CD on first boot
- After install, boots from disk (avoids reinstall loop)
- **Wrong order** = reinstall loop or hang

**VM creation steps:**
1. Create VM: 4+ CPU, 8GB+ RAM, disk sized for use case
2. Attach the **versioned** ISO (verify name before attaching)
3. Set boot order: disk first, then CD-ROM
4. Boot - installation is automatic
5. Verify in Palette: Clusters > Edge Hosts > Registered

## Automated Builds via SSH

For environments with a dedicated build machine, automate the entire process:

```bash
BUILD_HOST="<user>@<build-machine>"  # Your build machine hostname or IP

# Clone, configure, and build in one session
ssh $BUILD_HOST << 'ENDSSH'
cd ~
if [ -d "CanvOS" ]; then
  cd CanvOS && git fetch --tags && git pull
else
  git clone https://github.com/spectrocloud/CanvOS.git && cd CanvOS
fi
LATEST_TAG=$(git describe --tags --abbrev=0)
echo "Using CanvOS $LATEST_TAG"
git checkout "$LATEST_TAG"

cat << 'ARGFILE' > .arg
OS_DISTRIBUTION=ubuntu
OS_VERSION=22.04
K8S_DISTRIBUTION=k3s
K8S_VERSION=1.33.3
IMAGE_REGISTRY=ttl.sh
IMAGE_REPO=my-edge
CUSTOM_TAG=2node
ARCH=amd64
TWO_NODE=true
ARGFILE

cat << 'USERDATA' > user-data
#cloud-config
install:
  reboot: true
users:
  - name: kairos
    passwd: kairos
    groups: [sudo, admin]
    sudo: ALL=(ALL) NOPASSWD:ALL
stages:
  initramfs:
    - name: "Setup bridge networking"
      files:
        - path: /etc/systemd/network/20-dhcp.network
          content: |
            [Match]
            Name=en*
            [Network]
            Bridge=br0
            LinkLocalAddressing=no
        - path: /etc/systemd/network/bridge0.netdev
          content: |
            [NetDev]
            Name=br0
            Kind=bridge
        - path: /etc/systemd/network/bridge0.network
          content: |
            [Match]
            Name=br0
            [Network]
            DHCP=yes
stylus:
  site:
    paletteEndpoint: api.spectrocloud.com
    edgeHostToken: <TOKEN>
    projectName: <PROJECT>
USERDATA

earthly +iso  # Build ISO first - start imaging nodes while provider images push
earthly --push +provider-image
ENDSSH

# Copy ISO back with version name
scp $BUILD_HOST:~/CanvOS/build/palette-edge-installer.iso \
  "./palette-edge-k3s-1.33.3-$(date +%Y%m%d).iso"
```

## CI/CD Integration

See `references/cicd-workflow.md` for GitHub Actions and GitLab CI examples.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Registry errors | Verify `docker login`, ttl.sh needs no login but expires in 24h |
| ISO boot hangs | Check UEFI/BIOS mode, EFI partition size |
| Reinstall loop | Boot order wrong - must be disk first, then CD-ROM. See fix below. |
| Not registering | Check user-data, network, logs: `journalctl -u spectro-stylus-agent.service -f` |
| Re-imaging | Delete old edge host from Palette first |
| Wrong K8s version | Verify ISO name matches expected build, check for stale ISOs |
| Stale ISO used | List ISOs on hypervisor, delete old ones, re-upload versioned ISO |
| Storage pool too small | 100GB disk leaves ~2.5GB free - increase disk or add data disk |
| Cluster stuck Provisioning, no nodes | VMs likely in install loop - check boot order and power cycle |
| user-data changes not applied | Regenerate userdata: `kairos-agent notify agent.bootstrap` (see below) |

### User-Data and /oem Directory

All `#cloud-config` files in `/oem` are merged to generate `/run/stylus/userdata`. If you modify files in `/oem`, regenerate userdata:

```bash
# On the edge node - regenerates /run/stylus/userdata from /oem files
kairos-agent notify agent.bootstrap
```

**Use cases:**
- Debugging user-data issues: check `/run/stylus/userdata` for merged result
- Adding config post-install: place files in `/oem/*.yaml`, then regenerate
- Troubleshooting registration: verify stylus config in `/run/stylus/userdata`

### Fixing Install Loop (Boot Order)

**Symptom**: VMs keep reinstalling from ISO instead of booting from installed disk. Cluster stays in "Provisioning" with no nodes appearing for 30+ minutes.

**Cause**: Boot order is `ide2;scsi0` (CD-ROM first) instead of `scsi0;ide2` (disk first).

**Fix**:
1. Change boot order to disk first, then CD-ROM via your hypervisor's UI or API
2. **Full power off** (not reboot/reset!) — boot order changes may not apply on soft reboot
3. Power on after VM is fully stopped

## BYOOS Pack: Edge vs Agent Mode

The BYOOS pack is the **ONLY mode-specific pack** in an edge infrastructure profile. When cloning profiles from Reference Architectures, verify you're using the **edge** variant (e.g., `VMO-RA-Infra-Edge-*`), not the agent variant (`VMO-RA-Infra-Agent-*`).

See `spectrocloud-cluster-profiles` skill → "BYOOS Pack Values: Agent vs Edge Mode" for the full comparison (system.uri, containerd paths, spectro.slice).

**Quick check** — if your BYOOS pack values contain any of these, it's agent mode and WRONG for appliance deployments:
- `system.uri: "NA"`
- `/var/lib/spectro/containerd`
- `/run/spectro/containerd`
- `/opt/bin/runc`
- `spectro.slice`

## BYOOS Pack Version

**Always use the latest BYOOS pack version** when creating cluster profiles - never hardcode it. Query it with the "Get Latest BYOOS Version" query in the `spectrocloud-common` skill.

**Registry note**: BYOOS exists in two registries. Use **Public Repo** (type=`spectro`) for Terraform/API:
- Public Repo UID: `5eecc89d0b150045ae661cef`
- Type in Terraform: `type = "spectro"` (NOT "oci")

## Provider Image Tag

**Don't assume the tag format** - CanvOS generates tags based on `.arg` values but **includes Kairos version, not OS version**:
- Expected: `k3s-1.33.5-ubuntu-22.04-2node`
- Actual: `k3s-1.33.5-v4.8.1-2node` (Kairos version)

Always check the actual tag after build:

```bash
# Check local images after build
docker images | grep $IMAGE_REPO

# Check registry (for Docker Hub)
curl -s "https://hub.docker.com/v2/repositories/$IMAGE_REPO/tags" | jq '.results[].name'

# Check ttl.sh (use crane or skopeo)
crane ls ttl.sh/$IMAGE_REPO
```

**CRITICAL**: Use the EXACT tag from the build output in:
1. BYOOS pack `options.system.uri` in the cluster profile
2. Ensure K8s pack version matches what was built into the image

## Quick Reference

| Item | Value |
|------|-------|
| CanvOS | `https://github.com/spectrocloud/CanvOS` |
| ISO output | `build/palette-edge-installer.iso` (rename with version!) |
| Versioned ISO | `palette-edge-<K8S_VERSION>-<YYYYMMDD-HHMM>.iso` |
| Image tag | Check `docker images` after build - use exact tag |
| VM boot order | Disk first, then CD-ROM |
| SSH access | kairos / kairos |

## Additional Resources

- `references/networking-examples.yaml` - Bridge and bond configurations
- `references/user-data-examples.yaml` - Advanced user-data options
- `references/cicd-workflow.md` - CI/CD pipeline examples

## Links

- [EdgeForge Workflow](https://docs.spectrocloud.com/clusters/edge/edgeforge-workflow/)
- [Two-Node Architecture](https://docs.spectrocloud.com/clusters/edge/architecture/two-node/)
- [CanvOS GitHub](https://github.com/spectrocloud/CanvOS)
- [Edge Config Examples](https://github.com/spectrocloud/edge-config-examples)
