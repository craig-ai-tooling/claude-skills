---
name: spectrocloud-agent-mode
description: "Install and manage the Palette agent on a host that already has its own OS -- bring-your-own-OS edge devices, bare metal, VMs or cloud instances -- covering registration tokens, user-data, node validation, BYOOS-pack cluster profiles and uninstall. Use when Craig says: install the agent on this box, use agent mode, bring your own OS, register this existing host with Palette, add this VM as an edge host without building an ISO, create a registration token, why will the agent not register, uninstall the palette agent. Use spectrocloud-appliance-mode instead when the node is being shipped a Palette Edge ISO; note agent mode supports 1 or 3+ nodes and never 2."
---

# Spectro Cloud Agent Mode Deployment

Agent Mode lets you bring your own host and OS to be managed by Palette. The Palette agent is installed on existing infrastructure - bare metal, VMs, cloud instances, or edge devices.

## Key Constraints

- **Node counts**: 1-node or 3+ nodes only. **No 2-node deployments** in agent mode.
- **BYOOS pack**: Must use the **Agent Mode** preset, which sets `system.uri: "NA"` (not a custom provider image)
- **Architecture**: AMD64 and ARM64 supported

For API auth and project UID lookup, use the `spectrocloud-common` skill.

## Prerequisites

### Hardware
- CPU: 4+ cores
- Memory: 8+ GB
- Storage: 100+ GB SSD

### Software (Ubuntu example)
```bash
sudo apt-get update && sudo apt-get install -y \
  bash jq zstd rsync systemd-timesyncd conntrack iptables rsyslog \
  --no-install-recommends
```

Required services:
- `systemd-resolved` (for DNS/overlay networks)
- `systemd-networkd` (for static IP/overlay networks)

## Registration Tokens

Tokens link Edge hosts to a Palette project. Create via UI:

1. Log in as **Tenant Admin**
2. Go to **Tenant Settings → Registration Tokens**
3. Click **Add New Registration Token**
4. Set name, optional description, **Default Project**, and expiration
5. Save immediately - full token only shown once

**Important**: Either set a Default Project on the token OR provide `stylus.site.projectName` in user-data.

## Installation (Central Management Mode)

### Step 1: SSH to host
```bash
ssh -i /path/to/key ubuntu@<host-ip>
```

### Step 2: Export token
```bash
export TOKEN=<your-registration-token>
```

### Step 3: Create user-data

**Minimal configuration** (required fields only):
```yaml
#cloud-config
install:
  reboot: true
stylus:
  site:
    edgeHostToken: <registration-token>
    paletteEndpoint: api.spectrocloud.com
    projectName: <project-name>
```

**Before proceeding, ask if the user needs any advanced configurations:**
- Custom edge host name (`stylus.site.name`)
- Static IP / network configuration
- Custom partition sizes
- Proxy settings
- Custom CA certificates
- Tags/labels for the edge host

**Advanced configuration example:**
```yaml
#cloud-config
install:
  reboot: true
  partitions:
    oem:
      size: 5120      # MB
      fs: ext4
    system:
      size: 8192
    recovery-system:
      size: 10000
    passive:
      size: 8192

stylus:
  site:
    edgeHostToken: <registration-token>
    paletteEndpoint: api.spectrocloud.com
    projectName: <project-name>
    name: custom-edge-host-name        # Optional: custom name instead of auto-generated
    network:
      httpProxy: http://proxy:8080
      httpsProxy: http://proxy:8080
      noProxy: localhost,127.0.0.1,.local
    caCerts:
      - |
        -----BEGIN CERTIFICATE-----
        <CA cert content>
        -----END CERTIFICATE-----
    tags:
      environment: production
      location: datacenter-1
  installationMode: connected          # connected or airgap
  managementMode: central              # central or local
```

Create the user-data file:
```bash
cat << EOF > user-data
#cloud-config
install:
  reboot: true
stylus:
  site:
    edgeHostToken: $TOKEN
    paletteEndpoint: api.spectrocloud.com
    projectName: <project-name>
EOF
```

### Step 4: Download and run installer
```bash
# Latest version (SaaS)
curl -LO https://github.com/spectrocloud/agent-mode/releases/latest/download/palette-agent-install.sh
chmod +x palette-agent-install.sh

# For FIPS compliance, use palette-agent-install-fips.sh

export USERDATA=./user-data
sudo --preserve-env ./palette-agent-install.sh
```

Host reboots automatically after installation.

### For Dedicated/On-Prem Palette

Get your Palette's agent version first:
```bash
curl -s "https://<palette-endpoint>/v1/services/stylus/version" \
  -H "Content-Type: application/json" \
  -H "Apikey: <api-key>" | \
  jq -r '.spec.latestVersion.content | match("version: ([^\n]+)").captures[0].string'
```

Then download matching version:
```bash
curl -LO "https://github.com/spectrocloud/agent-mode/releases/download/v<version>/palette-agent-install.sh"
```

## Validate Registration

1. Log into Palette console
2. Navigate to **Clusters → Edge Hosts** tab
3. Verify host appears with status **Registered**

**Troubleshooting**: If previously registered, delete the Edge host from Palette first - duplicate IDs cause registration failure.

## Create Cluster Profile

1. Go to **Profiles → Add Cluster Profile**
2. Select type: **Full**
3. Select cloud type: **Edge Native**
4. Add **BYOS Edge OS** pack (version 2.1.0+)
5. **Critical**: Select **Agent Mode** preset in pack values
6. Add remaining layers (K8s, CNI, CSI, add-ons)

## Agent Services & Logs

### Check agent status
```bash
sudo systemctl status spectro-stylus-agent.service
sudo systemctl status spectro-stylus-operator.service
```

### View logs
```bash
journalctl -u spectro-stylus-agent.service -f
journalctl -u spectro-stylus-operator.service -f
```

### Key log files
- `/var/log/stylus-upgrade.log`
- `/var/log/kube-init.log`
- `/var/log/kube-join.log`

## Uninstall Agent

No official uninstall documentation exists. Manual cleanup:

### 1. Delete from Palette
Remove the Edge host from Palette console first (**Clusters → Edge Hosts → Delete**)

### 2. Stop services
```bash
sudo systemctl stop spectro-stylus-agent.service
sudo systemctl stop spectro-stylus-operator.service
sudo systemctl disable spectro-stylus-agent.service
sudo systemctl disable spectro-stylus-operator.service
```

### 3. Remove Palette directories
```bash
sudo rm -rf /usr/local/spectrocloud/
sudo rm -rf /var/lib/spectro/
sudo rm -rf /opt/spectrocloud/
```

### 4. Clean up Kubernetes (if cluster was deployed)
```bash
# Reset kubeadm if used
sudo kubeadm reset -f

# Remove K8s directories
sudo rm -rf /etc/kubernetes/
sudo rm -rf /var/lib/kubelet/
sudo rm -rf /var/lib/etcd/
sudo rm -rf ~/.kube/
```

### 5. Remove systemd units
```bash
sudo rm -f /etc/systemd/system/spectro-*.service
sudo systemctl daemon-reload
```

### 6. Reboot
```bash
sudo reboot
```

## Proxy Configuration

If behind a proxy, export before installation:
```bash
export http_proxy=http://proxy:port
export https_proxy=http://proxy:port
export HTTP_PROXY=http://proxy:port
export HTTPS_PROXY=http://proxy:port
```

## Quick Reference

| Item | Value |
|------|-------|
| Install script | `https://github.com/spectrocloud/agent-mode/releases/latest/download/palette-agent-install.sh` |
| FIPS script | `...palette-agent-install-fips.sh` |
| Agent service | `spectro-stylus-agent.service` |
| Operator service | `spectro-stylus-operator.service` |
| Config location | `/var/lib/spectro/userdata` |
| Default API endpoint | `api.spectrocloud.com` |

## Links

- [Agent Mode Overview](https://docs.spectrocloud.com/deployment-modes/agent-mode/)
- [Install Agent](https://docs.spectrocloud.com/deployment-modes/agent-mode/install-agent-host/)
- [Create Registration Token](https://docs.spectrocloud.com/clusters/edge/site-deployment/site-installation/create-registration-token/)
- [Edge Troubleshooting](https://docs.spectrocloud.com/troubleshooting/edge/)
- [GitHub Releases](https://github.com/spectrocloud/agent-mode/releases)
