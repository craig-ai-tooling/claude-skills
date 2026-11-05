---
name: spectrocloud-maas-edge
description: "Deploy a Palette Edge (appliance mode, Kairos) image onto bare metal or VMs through Canonical MAAS PXE: build the MAAS image with CanvOS (IS_MAAS=true), upload it as a MAAS custom boot resource, deploy it with stylus registration in MAAS deploy-time user-data, watch the node register as an edge host, then release and reset. Use when Craig says: deploy the ISO with MAAS, PXE boot palette edge, MAAS custom image for edge, bare metal onboarding via MAAS, build a MAAS image with CanvOS, upload a custom image to MAAS, MAAS deploy user-data for stylus, edge host never registers after MAAS says Deployed, demo zero-touch edge onboarding with MAAS. Use spectrocloud-appliance-mode for the ISO/USB install path and spectrocloud-agent-mode when the host keeps its own OS."
---

# Palette Edge via MAAS (PXE deploy)

MAAS installs a raw disk image on the machine and hands it cloud-init user-data. CanvOS can produce that image: a Kairos disk plus a small Ubuntu bootstrap partition. The stylus site config (registration token, project) travels in the MAAS deploy-time user-data, so the image itself carries no secrets.

## Flow at a glance

1. Build `<name>.raw.gz` with CanvOS (`IS_MAAS=true`), matching the cluster profile's provider image.
2. Upload it to MAAS as a custom boot resource (`ddgz`).
3. Machine is Ready in MAAS (enlisted, commissioned, power configured).
4. Deploy with `distro_series=custom/<name>` and user_data containing `stylus.site`.
5. Wait. MAAS reports Deployed after about 7 minutes, Palette sees the edge host after about 19-20 minutes.
6. Release the machine and delete the edge host in Palette to reset.

## 1. Build the image

Use a copy of the CanvOS checkout so other builds are undisturbed. Pick the tag that matches the Palette release, then set `.arg`. The values must match the cluster profile's edge-k8s pack and provider image, or the node cannot join that profile later.

```shell
cp -a CanvOS CanvOS-maas && cd CanvOS-maas
rm -f user-data            # stylus config comes from MAAS at deploy time; a baked user-data would be used instead
cat > .arg <<'ARG'
CUSTOM_TAG=<tag used for the provider image, e.g. gpu>
IMAGE_REGISTRY=<registry of the profile's provider image, e.g. docker.io>
IMAGE_REPO=<org/repo of the provider image>
OS_DISTRIBUTION=ubuntu          # MAAS builds are Ubuntu only
OS_VERSION=22.04
K8S_DISTRIBUTION=kubeadm
K8S_VERSION=<same as the profile, e.g. 1.34.6>
ARCH=amd64
UPDATE_KERNEL=false
CIS_HARDENING=false
IS_MAAS=true
MAAS_IMAGE_NAME=<image-name>    # output is <image-name>.raw.gz
ARG
./earthly.sh +maas-image
```

The provider image tag is `<K8S_DISTRIBUTION>-<K8S_VERSION>-<PE_VERSION>-<CUSTOM_TAG>` under `IMAGE_REGISTRY/IMAGE_REPO`. Check it equals what the profile's edge-k8s layer references. An `IS_MAAS=true` build does not push the provider image; the node pulls it from the registry when a cluster is built, so it must already exist there.

How `+maas-image` works (`earthly.sh` special-cases the target):
- Step 1, earthly target `+kairos-raw-image`: converts the installer image to `build/kairos.raw` (about 13 GB) with auroraboot inside docker-in-docker.
- Step 2, `cloudconfigs/build-kairos-maas.sh build/kairos.raw <name>`: runs on the build host itself. It assembles a 16 GB disk: EFI, a 3 GB Ubuntu rootfs (noble cloud image, label UBUNTU_ROOTFS), OEM, recovery, plus an optional content partition if `content-*` bundles or `spc.tgz` exist. It adds `curtin-hooks` and a grub entry that boots the Ubuntu partition once. Output `<name>.raw.gz` (about 3.5 GB) lands in the CanvOS directory, then `earthly.sh` moves it to `build/` with a `.sha256`.
- Host needs: wget, tar, losetup, grub-editenv, qemu-img, parted, kpartx, rsync, blkid, ext2/ext4/vfat filesystem tools, root or sudo, and roughly 40 GB free (kairos.raw, the 16 GB raw, the gz).

Gotcha: step 2 can fail with `/dev/mapper/control: open failed: Permission denied` and `build-kairos-maas.sh failed with exit code 1`, because `earthly.sh` runs it as the unprivileged user. `build/kairos.raw` is already good, so finish by hand as root:

```shell
cp cloudconfigs/curtin-hooks ./curtin-hooks
sudo bash cloudconfigs/build-kairos-maas.sh build/kairos.raw <image-name>
sudo chown $USER <image-name>.raw.gz
mv <image-name>.raw.gz build/ && sha256sum build/<image-name>.raw.gz > build/<image-name>.raw.gz.sha256
rm -f curtin-hooks
sudo rm -f <image-name>.raw build/kairos.raw     # reclaim ~30 GB
```

Noise to ignore in the build log: `dracut-install: ERROR: installing 'libnvdimm'` and `iscsiuio` unit warnings. A warm earthly cache turns a 30-60 minute build into a few minutes.

If the image has a baked NVIDIA driver and the target has no GPU, the console fills with `NVRM: No NVIDIA GPU found`. It is harmless but makes console screenshots useless.

## 2. Upload to MAAS

From a host with the `maas` CLI logged in (`maas login <profile> http://<maas>:5240/MAAS <api-key>`; get the key with `maas apikey --username <user>` on the MAAS host and do not print it):

```shell
maas <profile> boot-resources create \
  name='custom/<image-name>' title='<human title shown in the UI>' \
  architecture='amd64/generic' filetype='ddgz' \
  content@=/path/to/<image-name>.raw.gz
maas <profile> boot-resources read     # the entry for <image-name> must show sets[].complete: true
```

Notes:
- The 3.5 GB upload exceeds typical tool timeouts. Run it in the background and poll.
- MAAS stores it as type `Uploaded` with name `<image-name>` (the `custom/` prefix is dropped) and `base_image` ubuntu/noble. You still deploy with `distro_series=custom/<image-name>`.
- UI route: Images > Upload custom image, format `dd.gz`. In the Deploy form the OS shows as `Custom` and the release is the title.

## 3. The machine must be Ready

For bare metal with BMCs this is ordinary MAAS enlist and commission. For KubeVirt VMs there is extra work:
- Pin the NIC `macAddress`. KubeVirt picks a random MAC per VMI otherwise, and MAAS loses the machine.
- Boot order: NIC first, disk second. EFI, secure boot off. A blank disk must PXE to enlist.
- MAAS needs a power driver. With kubevirtBMC use `redfish` (MAAS always speaks https to Redfish, so terminate TLS in front of kubevirtBMC). Without it, use the `webhook` power type pointing at a tiny service that sets the VM's `runStrategy`: `POST on`, `POST off`, `GET status` returning a body that matches `power_on_regex` / `power_off_regex`. Settings that matter:
  - `power_parameters_power_verify_ssl` accepts only `y` or `n`.
  - A bearer token goes in `power_parameters_power_token`.
  - Status must reflect the real VMI. Do not leave `runStrategy: Always` in place after starting. MAAS PXE-boots a Ready machine into a power-off ephemeral image (event "PXE Request power off"); with `Always` KubeVirt restarts the guest and it loops. Use `Always` to start, then switch to `RerunOnFailure`.
- Order: power the VM on once so it PXE-enlists (status New, no power type), set the power parameters, then run `maas <profile> machine commission <id> skip_bmc_config=1`. About 3-4 minutes to Ready. Rename with `machine update <id> hostname=<name>`.
- A `maas` CLI call inside `bash -s < script` swallows the script from stdin. Add `</dev/null` to every `maas` call in such scripts.
- Networks: the deployed node DHCPs on the PXE network. It must reach the Palette endpoint and the registry hosting the provider image. Check egress from that VLAN before building anything.

## 4. Deploy with stylus user-data

User-data is plain cloud-config. MAAS copies it to `/oem/userdata.yaml` on the node and stylus reads it from there.

```yaml
#cloud-config
stylus:
  vip:
    skip: true                      # single node; omit for a multi-node cluster with a VIP
  site:
    name: <edge-host-name>          # becomes the edge host name in Palette
    paletteEndpoint: api.spectrocloud.com
    edgeHostToken: <registration-token>
    projectName: <palette-project-name>
users:
  - name: kairos
    passwd: <password>
    groups: [sudo, admin]
    sudo: ALL=(ALL) NOPASSWD:ALL
    ssh_authorized_keys:
      - <public key>
```

API deploy (the same payload the UI sends):

```shell
maas <profile> machine deploy <system_id> \
  distro_series=custom/<image-name> user_data="$(base64 -w0 userdata.yaml)"
```

UI: Machines > select machine > Actions > Deploy > OS `Custom`, release `<title>`, paste the block into "Cloud-init user-data" > Start deployment. Never commit the real token; write `<registration-token>` in docs.

## 5. Timeline (measured on a 6 vCPU, 12 GiB VM writing to networked block storage)

| Elapsed from Deploy | Event |
|---|---|
| 0:00 | Deploying, machine powered on, PXE |
| ~1:00 | MAAS ephemeral environment loads |
| ~2:40 | Configuring storage, then Installing OS (writes the 8 GB image) |
| ~6:15 | Rebooting |
| ~7:00 | **MAAS reports Deployed** |
| 7-17 min | Node boots the Ubuntu bootstrap, then Kairos recovery runs reset and installs itself. Hostname `cos-recovery`. Nothing is visible in MAAS or Palette. |
| ~17 min | Reboot into the installed system, stylus starts |
| ~19-20 min | Edge host appears in Palette (health blank for a minute, then healthy) |

Deployed in MAAS does not mean registered. Set expectations with whoever is watching: the second half happens after MAAS has finished. Two MAAS events, "Node post-installation failure ... config-snap / config-ntp", appear around the Deployed mark and did not stop the install.

## Watching a node that has not registered

- The MAAS machine Events tab shows PXE, storage, install, reboot.
- After the first reboot, SSH in as `kairos` with the password from the user-data (through a jump host if the PXE VLAN is not routable). While `hostname` is `cos-recovery` it is still installing; `journalctl -u cos-setup-network` shows kairos-agent reset progress. When `/run/cos/active_mode` exists it is the installed system.
- `/oem/userdata.yaml` should hold your site block. `/var/log/stylus.log` says `generated final edge name: <name>` once it picks up the config.
- No serial output on VMs. Use a VNC screenshot (`virtctl vnc screenshot`).
- SSH host keys change between the bootstrap, recovery and active systems. Use `-o UserKnownHostsFile=/dev/null`.

## Verify and clean up

Palette: `POST /v1/dashboard/edgehosts/search` with `ApiKey` and `ProjectUid` headers lists hosts; the host's uid equals its name. Confirm by name, arch, cores and memory.

Reset after a test or demo:
1. If a cluster was built on it, delete the cluster first.
2. Delete only your host: `DELETE /v1/edgehosts/<name>` with the project header (204 expected). Do not touch other hosts in the project.
3. `maas <profile> machine release <id>` returns it to Ready in under a minute and powers it off. A redeploy overwrites the old Kairos install, so no wipe is needed.
4. To remove the machine entirely: `machine delete <id>`, then delete the VM and its disk if it is a test VM.
5. A machine stuck in `Releasing failed` leaves the allocatable pool silently; re-run `machine release`.
6. Delete large intermediates on the build host (`<image-name>.raw`, `build/kairos.raw`); keep the `.raw.gz` to re-upload.

## Troubleshooting quick table

| Symptom | Cause and fix |
|---|---|
| `build-kairos-maas.sh failed with exit code 1`, `/dev/mapper/control` | Step 2 ran unprivileged. Run it with sudo as above. |
| Machine enlists, then vanishes or never commissions (VM) | MAC not pinned. Pin `macAddress`. |
| Ready VM reboots forever | Power service leaves `runStrategy: Always`. Use `RerunOnFailure` after start. |
| `power_verify_ssl ... is not a valid` | Use `y` or `n`. |
| Deploy stays Deploying, VM Stopped | Power-on webhook failed. Query the status URL by hand. |
| Deployed but never in Palette | Wrong or expired token, no egress to Palette or the registry, or still in the 7-17 minute Kairos install. Check `/var/log/stylus.log`. |
| Node came up with the wrong site config | A `user-data` file was baked into the image. Remove it and rebuild. |
| Edge host name unexpected | It is `stylus.site.name`, not the MAAS hostname. |
