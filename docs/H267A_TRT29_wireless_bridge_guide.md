# ZTE ZXHN H267A TRT29 wireless bridge: reproduction guide

**Status: permanent installation and normal reboot verified, 2026-11-12.** This guide concerns the user-owned **ZTE ZXHN H267A, hardware V1.0.8, firmware V1.0.1_TRT29**. The modified image booted successfully from bank 1 after the OEM flash operation, then passed a separate normal H267A reboot. Both checks found the replacement 2.4 GHz driver, original 5 GHz driver, connected wireless uplink, both intended AP SSIDs, all four LAN ports in the bridge, and Internet reachability (3/3 replies). Private GUI DB-dump cleanup was verified separately during native startup and first permanent boot. The main PC kept its direct upstream connection throughout. A previous phone Internet test passed, and the owner subsequently confirmed Internet access from an Ethernet-connected client. Separate phone tests on both bands remain untested. The published source revision is pinned in sections 2 and 7.

This guide is published with the source port and uses generic placeholders for each owner's private inputs. It deliberately contains no real upstream router brand/model, SSID, password, device MAC address, account credential, or private configuration XML. Project documentation is English; the placeholders below are values to record privately.

## 1. Intended result and boundaries

The H267A joins an upstream access point over **2.4 GHz APCLI** and supplies its connection to the H267A LAN bridge, its 2.4 GHz AP, and its existing 5 GHz AP. The 5 GHz radio remains an AP using the OEM `mt7612e_ap` driver. It is not a 5 GHz wireless uplink.

All four H267A LAN interfaces were verified as bridge members after both permanent boots. Temporary tests isolated the inter-router cable/`eth0` path to prevent a bridge loop. The owner subsequently confirmed Internet access from an Ethernet-connected client. The specific LAN port and separate tests of every physical port were not recorded; all four interfaces were verified as bridge members.

Using the same SSID and password can let a client choose between access points. It does not establish mesh, coordinated roaming, 802.11r, or seamless handover. APCLI plus the driver's address translation is not a promise that every Layer 2 protocol works transparently.

Do not install a generic Padavan/OpenWrt router image. This fork supplies a driver port for the existing TRT29 system; the work preserves the original H267A kernel and 5 GHz driver. Other H267A firmware or hardware revisions require fresh compatibility evidence.

## 2. Verification record and remaining limits

The installation evidence and its limits are:

| Area | Evidence / limitation |
|---|---|
| Public source | Fork `main`, published commit [`64a197c04f6b8608e10477076a71edd59a242fd5`](https://github.com/cakmakfatih/rt-n56u/commit/64a197c04f6b8608e10477076a71edd59a242fd5). |
| Driver lifecycle | Native A/B root-cause isolation, three fixed-driver connect/unload cycles, full bridge operation and hot stock restoration passed. |
| Generic startup | Actual GUI DB values, original MAC handling, gateway/Internet checks and private DB-dump cleanup passed natively; 21 mock scenarios passed. |
| Persistent first boot | OEM flash followed by bank 1 boot, valid bank status, startup ready, both radio drivers/AP names, connected uplink, all LAN bridge members, and Internet 3/3 passed. |
| Normal reboot | `/bin/busybox reboot`, then the same bank 1/startup/radio/uplink/bridge/Internet checks passed again. |
| Image checks | Original kernel payload preserved; CRC/decrypt/capacity checks and full 1,422-entry filesystem manifest roundtrip passed; complete OTA RAM read-back matched before flashing. |
| Client testing | Previous phone Internet test passed; the owner subsequently confirmed Ethernet-client Internet access. Separate tests on every physical LAN port, phone tests on each band, and forced upstream interruption are not claimed. |
| Recovery | Private stock/config backups retained; hot stock restoration passed. Manual boot-bank selection and failed-image bootloader recovery remain unproven. Do not infer their commands from another ZTE model. |

The instructions below reproduce the tested software path with the owning unit's firmware/calibration. Remaining limits are reported as limits, not prerequisites requiring the main PC's cable to be moved or the upstream router to be changed.

## 3. Private worksheet

Record these values in a private note, separate from Git:

| Placeholder | Meaning |
|---|---|
| `UPSTREAM_SSID` | Exact 2.4 GHz upstream SSID, including case and spaces |
| `UPSTREAM_KEY` | WPA2-PSK key; normally 8–63 characters, or 64 hexadecimal digits |
| `UPSTREAM_IP` | Upstream LAN gateway address |
| `LAN_MASK` | Upstream LAN netmask |
| `DHCP_RANGE` | Upstream DHCP address pool |
| `H267A_IP` | An unused management address in that LAN, outside the DHCP pool or reserved for this device |
| `PC_IP` | Address of the management PC that will be allowed to reach diagnostics |
| `RADIO24_MAC`, `RADIO5_MAC` | This H267A's own `wlan0`/`wlan5g0` addresses, read from its stock state |
| `EEPROM_FILE` | This H267A's own verified 512-byte 2.4 GHz calibration dump |
| `SOURCE_COMMIT` | Exact tested commit of the user's fork |

Keep passwords out of shell command arguments, logs, screenshots, and public issues. The private EEPROM is device calibration, not a replacement for a wireless password. Do not copy another unit's calibration or write it to NVM.

## 4. Preserve the working Internet connection

1. Keep the main PC wired directly to the upstream router throughout the work. Do not move its working cable to the H267A to make a test convenient.
2. Power and configure the H267A separately. Use a phone connected to the H267A's own Wi-Fi for the initial LAN address and DHCP changes.
3. Select `H267A_IP` after checking the upstream subnet and DHCP pool. Give the H267A that management IP and `LAN_MASK`; disable the H267A DHCP server. Keep the upstream router as the only DHCP server for this shared LAN.
4. Reconnect the phone to the H267A at its new address and verify its management page. Save a configuration backup before changing diagnostic services.
5. Only after DHCP is disabled and the address is unique, temporarily connect one upstream LAN port to an H267A LAN port for management/staging.
6. Before adding the wireless uplink to `br0`, remove that inter-router Ethernet cable, or use the deliberately tested isolation stage. Restore the H267A's full Ethernet LAN bridge only after the inter-router cable is physically absent.

**Never leave a wired inter-router bridge and the wireless inter-router bridge active together.** This creates a Layer 2 loop unless an explicitly verified loop-prevention arrangement handles it. A local PC-to-H267A cable for an isolated test is a different connection; label cables so they cannot be confused.

All reboots, configuration imports, tests, and any eventual firmware operation in this guide affect the H267A only. No upstream reboot or configuration change is required for the baseline setup if it already offers a compatible 2.4 GHz network.

## 5. Establish stock configuration and authorized diagnostics

In the H267A web interface:

1. Confirm hardware `V1.0.8` and firmware `V1.0.1_TRT29` on the status page. Stop if they differ.
2. Export and retain the untouched configuration. Label it with the model, firmware, and date; calculate a local SHA-256 hash.
3. Configure the H267A's normal private **2.4 GHz SSID1** to `UPSTREAM_SSID` and `UPSTREAM_KEY`, using **WPA2-PSK/AES**. Do not use a guest/public SSID as the source.
4. Configure the normal **5 GHz SSID1** with the same desired client-facing SSID/key and WPA2-PSK/AES. During diagnostic work, a distinct temporary management SSID can help identify the H267A; restore the intended names only after access is verified.
5. Keep both SSIDs visible. The final runtime profiles must have `HideSSID=0` for both radios. A previous candidate hid the APs and was rejected.
6. Disable WDS for this APCLI setup. WDS and APCLI are different driver paths; enabling a GUI WDS checkbox does not add missing APCLI support to the stock driver.

The observed H267A SSH service on port 22 presents the OEM management CLI. A successful SSH login does **not** establish an interactive root shell or arbitrary command execution. FTP was kept disabled.

The actual root diagnostic path used in this work was **Telnet on TCP 2323**, enabled through an authorized private configuration edit with `TelnetCfg` and service firewall (`FWSC`) changes. Access was restricted to `PC_IP` on LAN, with other LAN sources and WAN denied. Existing account credentials were retained. Telnet carries credentials in plaintext; use it only on this controlled local network and retain the restrictions.

The decoder/encoder and exact generic service/ACL changes are documented in appendix A. Do not import another user's configuration or enable a WAN diagnostic service. The current user's already retained, validated private configuration backup may be reused on the same unit only after checking its LAN address and source restriction still match.

Once the shell is available, basic read-only checks are:

```sh
id
uname -a
cat /proc/mtd
cat /proc/modules
brctl show br0
/bin/ip link show
/bin/ip route show
```

Confirm `id` gives the intended root diagnostic context. Save raw output privately. Do not publish unredacted routes, addresses, profiles, or account data.

## 6. Capture recovery material before driver experiments

Retain all of the following outside the source checkout:

- Original binary configuration and decoded private XML, if decoding is needed.
- A known-good restricted diagnostic configuration and the configuration needed to disable diagnostics again.
- Stock 2.4 GHz and 5 GHz modules and generated runtime profiles.
- This unit's 512-byte 2.4 GHz factory calibration.
- The actual MTD map and boot-bank evidence.
- Original active kernel bank and immutable RAM rootfs bytes, with byte counts and SHA-256 hashes.
- The untouched firmware package or a locally reconstructed TRT29 package, plus its reconstruction evidence.

Before installation, the investigated unit's active bank was **2** and inactive bank **1**. Its original kernel-bank read was **4,194,304 bytes**, and immutable RAM rootfs read was **11,534,336 bytes (11 MiB)**. After installation and the separate normal reboot, current bank **1** was verified. These are observations, not universal partition identifiers. Re-read the map before any bank operation; never reuse a numeric `/dev/mtd*` target from a different boot/firmware.

The retained local evidence includes `telnet-root-active-kernel-export-metadata.json` and `telnet-root-ram-rootfs-export-metadata.json`. The rootfs was read through a verified static hex reader because the OEM userland lacked convenient export features. A separate bounded reader was used for 512-byte partition-prefix checks; radio calibration was read through the stock driver's read-only `e2p` ioctl. Preserve the raw binary, not just a transcript of hex text.

Appendix C gives the exact read-only export mechanism and byte-count checks. Do not replace it with an unverified flash command or an unrestricted full-device dump. The presence of a file named `dd`/`hexdump` cannot be assumed on this firmware.

On a Windows host, calculate a backup hash without printing its contents:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath 'C:\private-h267a\backup.bin'
```

Use a real private backup path. The example does not create or export a backup.

## 7. Obtain the source from the user's fork

Use Linux or WSL for the driver toolchain. Keep the working source on the Linux filesystem and private inputs/outputs in separate directories. The build wrapper rejects private work/output paths inside its Git checkout.

```sh
mkdir -p "$HOME/h267a-work"
cd "$HOME/h267a-work"
git clone --branch main --single-branch https://github.com/cakmakfatih/rt-n56u.git source
cd source
git checkout --detach 64a197c04f6b8608e10477076a71edd59a242fd5
test "$(git rev-parse HEAD)" = 64a197c04f6b8608e10477076a71edd59a242fd5
git rev-parse HEAD
test -f h267a/build_driver.py
test -f h267a/kernel.config
test -d h267a/network-overlay
```

Record `git rev-parse HEAD` as `SOURCE_COMMIT`; it must match the pinned published commit above. `main` is the fork's default branch, while the detached checkout makes this reproduction independent of later branch changes. If a required H267A file is missing, stop and check the checkout rather than substituting an unrelated snapshot or building a full router firmware.

The donor driver is **MT7603 AP/APCLI 4.1.2.0_20190222**, originally at upstream commit `23387b278a7cf728748af606760758f5d59d1451`, under:

```text
trunk/proprietary/rt_wifi/rtpci/4.1.X.X/mt76x3
```

The port combines the GPL **Linux 2.6.36** base with a measured TRT29 CSP network ABI overlay. The network layouts cannot be made compatible merely by copying a stock Linux version string. The overlay incorporates relevant Linux 3.4 network definitions and target-specific contracts. Use the fork's matched files together.

## 8. GPL base, cross compiler, and kernel preparation

The retained official GPL source archive is:

- [TP-Link Archer VR300 EU 2.0 GPL archive](https://static.tp-link.com/upload/gpl-code/2024/202405/20240509/Archer_VR300_EU_2.0.tar.gz)
- File: `Archer_VR300_EU_2.0.tar.gz`
- Size: `423621547` bytes
- SHA-256: `c2ebbce14af609d27ee9c3053be858e5d521ae1fe2d8ad7c32f538a48fc1ad7d`

This archive is a **build input**, not an image to flash on the H267A. Verify the download before extraction:

```sh
sha256sum Archer_VR300_EU_2.0.tar.gz
tar -tzf Archer_VR300_EU_2.0.tar.gz > vr300-archive-files.txt
```

The exact archive members are:

```text
Archer_VR300_EU_2.0/econet_bba_1_5_entry_fe/mtk/linux-2.6.36/
Archer_VR300_EU_2.0/econet_bba_1_5_entry_fe/mtk/tools/toolchain/mips-linux-uclibc-4.3.6-v2.tgz
```

The compiler archive is bundled inside the GPL package; no independent compiler download is required. The retained inventory gives its compressed size as `35337138` bytes. Extract those members in a private build directory; the kernel also uses the GPL package's corresponding `global_inc` headers, so preserve the matching directory layout or the verified include arrangement.

The verified compiler family is **MIPS big-endian GCC 4.3.6**, with prefix `mips-linux-`. The retained extraction uses `mips-linux-uclibc-4.3.6-v2/usr/bin/mips-linux-`. Its old host executables require a compatible i386 runtime; the existing build supplied runtime library directories through `--lib-dir`. Specifically, the private runtime was extracted from `libc6-i386_2.43-2ubuntu2.4_amd64.deb` and `lib32z1_1%3a1.3.dfsg+really1.3.1-1ubuntu3.2_amd64.deb`, and 35 host ELF interpreter entries were patched to its local loader. Do not replace it with a modern little-endian MIPS compiler or silently change the ABI.

The prepared kernel must contain `include/generated/autoconf.h` and the configuration from the fork's `h267a/kernel.config`.

The extraction/configuration sequence is:

```sh
BUILD="$HOME/h267a-work/private-build"
mkdir "$BUILD"
tar -xzf Archer_VR300_EU_2.0.tar.gz -C "$BUILD" --strip-components=3 \
  Archer_VR300_EU_2.0/econet_bba_1_5_entry_fe/mtk/linux-2.6.36 \
  Archer_VR300_EU_2.0/econet_bba_1_5_entry_fe/mtk/global_inc
tar -xOf Archer_VR300_EU_2.0.tar.gz \
  Archer_VR300_EU_2.0/econet_bba_1_5_entry_fe/mtk/tools/toolchain/mips-linux-uclibc-4.3.6-v2.tgz \
  > "$BUILD/toolchain.tgz"
mkdir "$BUILD/toolchain"
tar -xzf "$BUILD/toolchain.tgz" -C "$BUILD/toolchain"
KERNEL="$BUILD/linux-2.6.36"
CROSS="$BUILD/toolchain/mips-linux-uclibc-4.3.6-v2/usr/bin/mips-linux-"
cp "$HOME/h267a-work/source/h267a/kernel.config" "$KERNEL/.config"
```

The compiler must run with its matched i386 loader/libraries before kernel preparation. Complete appendix F's verified private-runtime setup first. With that arrangement:

```sh
export PATH="$(dirname "$CROSS"):$PATH"
export LD_LIBRARY_PATH="$BUILD/runtime-i386/root/usr/lib32:$BUILD/toolchain/mips-linux-uclibc-4.3.6-v2/usr/lib"
"${CROSS}gcc" --version
make -C "$KERNEL" ARCH=mips CROSS_COMPILE="$CROSS" \
  HOSTCFLAGS='-O2 -fcommon' prepare modules_prepare
test -s "$KERNEL/include/generated/autoconf.h"
```

This exact prepare command was subsequently verified from a **fresh extraction of 37,527 official GPL kernel/global-header members**, using the fork's `h267a/kernel.config`: `prepare modules_prepare` returned exit 0, followed by a successful build of the corrected public driver against that fresh tree. No extra kernel-source or generated-header patches were needed. Evidence is retained in `bootstrap-check-result.json` and the fresh build's `prepare.log`.

The kernel test reused the existing private GCC 4.3.6/i386 runtime. Appendix F subsequently reproduced the toolchain/runtime itself from fresh archive/package extraction on the observed Ubuntu 26.04 host, including all 35 host ELF interpreter patches, working GCC execution, and a byte-identical helper build. This closes the private-runtime reproduction step; installing a new WSL distribution itself was not part of that test.

The working local paths from this investigation are recorded in section 9. They are ephemeral `/tmp` paths; copy verified build prerequisites to durable private storage before relying on them after a host reboot.

## 9. Build the private driver

The public wrapper requires Python 3.9+ functionality (`Path.is_relative_to`); use Python 3.10 or later for all companion tools. It accepts exactly these arguments:

```text
--kernel-dir PREPARED_KERNEL
--cross-compile COMPILER_PREFIX
--eeprom THIS_UNIT_512_BYTE_DUMP
--work-dir NEW_DIRECTORY_OUTSIDE_CHECKOUT
--output NEW_MODULE_OUTSIDE_CHECKOUT
--lib-dir HOST_LIBRARY_DIRECTORY     (repeatable)
```

For a fresh checkout using the variables from section 8, place the verified private EEPROM outside the checkout, then build:

```sh
cd "$HOME/h267a-work/source"
python3 h267a/build_driver.py \
  --kernel-dir "$KERNEL" --cross-compile "$CROSS" \
  --eeprom "$HOME/h267a-work/private-inputs/factory-eeprom.bin" \
  --work-dir "$BUILD/driver-work-1" --output "$BUILD/mt7603-apcli-1.ko" \
  --lib-dir "$BUILD/runtime-i386/root/usr/lib32" \
  --lib-dir "$BUILD/toolchain/mips-linux-uclibc-4.3.6-v2/usr/lib"
```

This is the same verified wrapper interface with generic paths. Use fresh `work-dir` and `output` paths; existing ones are deliberately refused.

For the retained working environment, the concrete command is:

```sh
cd /tmp/h267a-driver-build-20261111/public-fork
python3 h267a/build_driver.py \
  --kernel-dir /tmp/h267a-driver-build-20261111/linux-2.6.36 \
  --cross-compile /tmp/h267a-driver-build-20261111/toolchain/mips-linux-uclibc-4.3.6-v2/usr/bin/mips-linux- \
  --eeprom /tmp/h267a-driver-build-20261111/factory-eeprom-private.bin \
  --work-dir /tmp/h267a-driver-build-20261111/repro-next \
  --output /tmp/h267a-driver-build-20261111/mt7603-repro-next.ko \
  --lib-dir /tmp/h267a-driver-build-20261111/runtime-i386/root/usr/lib32 \
  --lib-dir /tmp/h267a-driver-build-20261111/toolchain/mips-linux-uclibc-4.3.6-v2/usr/lib
```

For a new checkout, replace only the environment paths with the corresponding verified directories. The calibration must be from the intended H267A. The wrapper checks its size is 512 bytes and its radio signature is `9275` or `7592`, then embeds it in a private copied source tree. That signature check does not prove the data belongs to the correct physical unit; preserve the extraction provenance.

The build enables APCLI and MAT support, compiles MAC repeater support but keeps it disabled at runtime, disables WDS/ATE and flash calibration access, and uses `DEFAULT_RF_OFFSET=0`. Read the full `build.log` if compilation fails. A final JSON line gives the output module path, byte count, and log path; its existence is not runtime proof.

Keep the produced `.ko` private: it contains the unit's calibration. Source-only patches are suitable for the fork; calibration headers, private outputs, profiles, credentials, backups, and firmware images are not.

## 10. Source changes and compatibility checks

The source port must preserve these requirements:

| Area | Required behavior |
|---|---|
| Target ABI | Match measured `net_device`, `sk_buff`, and related TRT29 layouts and helper semantics; do not trust the base kernel version alone. |
| Kernel symbols | Resolve imports against the **3,941 actual target kernel exports**, rather than a generic source-tree symbol list. |
| Calibration | Use the owning unit's verified 512-byte EEPROM through the private build input; never write it to flash/NVM. |
| OEM 5 GHz coexistence | Preserve the original `mt7612e_ap.ko` and export compatibility with `WscDualbandSelect` as a **104-byte array**, plus `WscGlobalSelectSet`. |
| APCLI naming | Create the APCLI net device **as `wlan2` before registration**, inside `RtmpOSNetDevCreate`; keep its internal APCLI index 0. Do not rename a registered `wlan1` device. OEM `wlan1` is public Wi-Fi at index 5 and is isolated by the OEM bridge policy. |
| OEM LAN registration | Register `wlan2` as private LAN at index **6**, using the matched helper. A plain Linux `brctl addif` alone did not establish correct OEM forwarding. |
| SSID visibility | Render `HideSSID=0` in both radio profiles. |
| Upstream selection | Clear a fixed BSSID lock: `ApCliBssid=00:00:00:00:00:00`. Select the upstream by the configured SSID. |
| Reconnect | Use the verified `ApCliAutoConnect=1` recovery path. The donor periodic rescan requires MAC repeater mode; do not blindly enable that unverified combination. |

The retained baseline checks reported **45 ABI assertions** and **103 legacy 5 GHz WPS checks**, and the public-source reproduction built successfully. Re-run the matched check tools after any source or overlay change. Retained evidence is in `source-research/mt7603-apcli-public-repro-static-check.json`; static checks do not prove unload, driver lifetime, boot behavior, or packet forwarding.

The unload defect was isolated with a native A/B test: the old driver unloaded when left unrenamed/unbridged, but **renaming only `wlan1` to `wlan2`** made it hang in `Unloading`/`msleep`. The fix chooses `wlan2` before network-device registration instead of changing its name afterward. Three corrected connect/unload cycles passed (`DIRECT_UNLOAD_OK1/2/3`), followed by a positive full bridge test and a clean unload/stock restoration with the original 5 GHz radio. This is runtime evidence for that fix; it is not a reason to loosen the ABI checks.

## 11. RAM deployment and controlled wireless-only test

Use the matched reviewed deployment script and its tested rollback sequence. Appendix G gives the exact pre-flash RAM variant; the persistent rootfs uses the unmodified public startup.

The final staging bundle needs:

- The private `mt7603-apcli.ko` built from the selected source revision.
- A matched `h267a-register-wlan2` helper for private LAN index 6.
- Sanitized 2.4/5 GHz profile templates with both SSIDs visible.
- The fork's generic startup, `h267a/wireless-bridge.sh`, which exports the current GUI database via `sendcmd 1 DB pf WLANCfg` and `sendcmd 1 DB pf WLANPSK`, reads row 0 `ESSID` and `KeyPassphrase` (fallback `PreSharedKey`), renders both AP profiles/APCLI, and deletes the temporary private export.
- The generic script's captured stock `wlan0`, `wlan5g0`, and `br0` MACs, plus gateway handling described below.
- The matched rollback sequence, which restores the wired management path before radio unload/reload.

The generic registration helper source is public at `h267a/h267a-register-wlan2.c` (also retained in `source-research`). It contains no device credentials/calibration. The fork provides a guarded build wrapper and an offline verifier. With `CROSS`, `BUILD`, and the host runtime from section 8:

```sh
cd "$HOME/h267a-work/source"
python3 h267a/build_registration_helper.py --cross-compile "$CROSS" \
  --output "$BUILD/h267a-register-wlan2" \
  --lib-dir "$BUILD/runtime-i386/root/usr/lib32" \
  --lib-dir "$BUILD/toolchain/mips-linux-uclibc-4.3.6-v2/usr/lib"
python3 -m pip install pyelftools==0.33 unicorn==2.1.4
python3 h267a/test_registration_helper.py "$BUILD/h267a-register-wlan2"
sha256sum "$BUILD/h267a-register-wlan2"
```

The wrapper uses the independently verified GCC flags `-Os -mabi=32 -EB -march=mips32r2 -msoft-float -mno-abicalls -fno-pic -fno-stack-protector -nostdlib -static -Wl,--build-id=none -Wl,-e,_start`, then `strip --strip-all`. It reproduced the retained 900-byte helper **byte for byte**, SHA-256 `ca01396e0a86b02f21b880ee9c46a5aff16a111200ce06ef5b59e3139930bce1`. The verifier checks `br0`/`wlan2`/index 6 and success/socket-error/ioctl-error paths without contacting a device. This helper is specific to the observed TRT29 private-LAN registration.

Known internal runtime paths are:

```text
/tmp/h267a-apcli-test.dat
/var/tmp/dbtable
/var/tmp/MT7612E.dat
/lib/modules/mt7603-apcli.ko
/usr/sbin/h267a-register-wlan2
/etc/h267a-wireless/mt7603.dat
/etc/h267a-wireless/mt7612.dat
```

**Credential source:** `/var/tmp/MT7592.dat` is a factory radio template, not the current GUI settings. In the observed unit it contained the factory SSID and an empty key. Do not use it as a credential source. `sendcmd 1 DB p` masks credentials; `DB pf` writes their actual values to `/var/tmp/dbtable`. The startup reads only row 0, decodes the five XML entities, bounds the SSID/key lengths, and deletes the dump after each table read and on failure. Do not run these export commands interactively with logging enabled or display the resulting file.

Before radio changes, the generic startup captures the existing radio/bridge MACs and `br0` IPv4 address. It uses an existing IPv4 default route explicitly on `br0` when present; otherwise it falls back to the first three octets of `br0`'s address plus `.1`. Malformed/missing information aborts before radio changes. The fallback assumes a matching conventional `.1` gateway; it does not calculate a gateway from arbitrary subnet masks.

The staged load order brings down/detaches the existing radios, unloads stock 5 GHz before stock 2.4 GHz, loads replacement 2.4 GHz with APCLI created directly as `wlan2`, registers it with the OEM private LAN policy, then restores the original 5 GHz driver. The startup no longer executes an interface rename. That order matters because of the cross-radio compatibility imports. On rollback it first detaches the wireless uplink and restores the wired path, then unloads/reloads radios; this order was verified in the positive full teardown. Do not repeatedly unload any module that has already entered a blocked state.

Before execution:

1. Capture stock module/bridge/interface state privately.
2. Verify file hashes after transfer and check shell syntax with the device's `sh -n` against the exact script file.
3. Confirm the inter-router cable is removed or the tested isolation stage is active.
4. Keep the main PC's direct upstream Ethernet connection untouched.
5. Keep physical access and the saved management/configuration backups available.

The direct-name driver, full teardown, generic GUI-reader startup, permanent first boot, and normal reboot now have native evidence. Use the matched final public script rather than the old device-specific investigation script. The generic test connected the wireless station, read back the intended SSID on both APs, reached the gateway and Internet (3/3 replies), removed the private DB dump, and preserved the PC's direct upstream Internet connection. Its 21 mock scenarios also cover credential entity handling, key fallback, validation before radio changes, source selection, and cleanup. Appendix D describes the one-shot RAM-file transfer; appendix G reproduces the tested RAM-only isolation/startup variant before permanent installation.

After startup, use read-only checks:

```sh
cat /proc/modules
brctl show br0
/bin/ip link show dev wlan2
/bin/ip route show
iwpriv wlan2 show connStatus
```

Use the exact supported private ioctl name from the final verified driver; if `connStatus` is unavailable, inspect the matched driver's `iwpriv` command list rather than substituting a command from another chip. A bridge-ready log marker is useful, but must be accompanied by client tests.

With the inter-router cable **physically absent**, disable mobile data on a test phone and connect it specifically to the H267A AP. Verify:

1. Association to the expected H267A radio and visible SSID.
2. A DHCP lease from the upstream LAN, with the intended gateway and DNS.
3. Reachability of the H267A management address and upstream gateway.
4. DNS lookup and an actual Internet page/load, with mobile data still off.
5. When available later, repeat on the other H267A Wi-Fi band.
6. Test an Ethernet client on the H267A; the owner has confirmed Internet access over Ethernet on the installed unit. For a full per-port check, test each LAN port separately. Keep the main PC's direct upstream cable in place.
7. In a later planned test, verify recovery after a brief upstream wireless interruption without changing/rebooting the upstream router.

The user confirmed the wireless-only phone Internet test during this investigation. The corrected driver's later full bridge run retained both radio interfaces, reached the upstream gateway, and received **3/3 replies from an Internet address**, then fully restored stock after teardown. Permanent first boot and normal reboot separately passed their startup/bridge/Internet checks. These results do not establish the remaining per-band/per-LAN-port client matrix or long-duration stability.

## 12. Prepare a persistent rootfs locally

The tested installation is now persistent. Before section 13's firmware write, a RAM-only test does not survive reboot; after the verified installation, an ordinary H267A reboot reapplies the bridge from the modified rootfs. Keep these two phases distinct when reproducing the work.

The H267A OTA wrapper contains an encrypted SquashFS rootfs. The local `h267a_rootfs.py` is the [primary author's MIT-licensed H267A tool](https://gist.github.com/rajkosto/94e992bf8c2b9ebf4da41d9bc8fc3829). Retain its attribution and license. It requires Python 3.10+ and `cryptography`.

Use a private virtual environment:

```sh
python3 -m venv "$HOME/h267a-work/tool-env"
. "$HOME/h267a-work/tool-env/bin/activate"
python3 -m pip install cryptography
```

Copy the verified tool into a private tools directory; record its source revision/hash. For an existing **encrypted TRT29 OTA** named `stock-trt29.bin`, its supported commands include:

```sh
python3 h267a_rootfs.py info stock-trt29.bin
python3 h267a_rootfs.py verify stock-trt29.bin
python3 h267a_rootfs.py extract stock-trt29.bin stock-trt29.squashfs --trim
```

The generic public encryption key is `706b715f6c7377323031363034303700` (AES-128-ECB). It is part of the published firmware format, not a user's wireless password. Successful decryption does not establish that a firmware belongs to this exact unit/revision.

The observed filesystem is **SquashFS 4.0, little-endian, LZMA**, compression ID **2**, with 131072-byte blocks. Compression ID 2 means LZMA; it must not be casually replaced with XZ/LZMA2 merely because the names are similar. The fixed RAM rootfs capacity was **11 MiB**. The candidate has little spare room, so additions require actual size verification.

If the OTA is reconstructed from read-back kernel/rootfs instead of an original package, use the exact format and checks in appendix B. Do not use an old TRT21/TRT24 or another hardware variant as a substitute TRT29 image.

The intended filesystem delta is narrow:

| Change | Purpose |
|---|---|
| Update `etc/init.norm` | Start the wireless bridge only after required OEM startup/profile generation. |
| Add `etc/h267a-wireless/mt7603.dat` | Sanitized replacement 2.4 GHz template. |
| Add `etc/h267a-wireless/mt7612.dat` | Sanitized OEM 5 GHz template. |
| Add `lib/modules/mt7603-apcli.ko` | Private driver for this unit. |
| Add `usr/sbin/h267a-register-wlan2` | OEM private LAN registration. |
| Add `usr/sbin/h267a-wireless-bridge.sh` | Dynamic profile rendering and bridge startup/reconnect. |

Preserve every original file, owner, group, mode, symlink, device node, FIFO, and the original 5 GHz driver, except the explicit startup edit. A generic unprivileged copy can silently lose device nodes and ownership. Use the actual matched SquashFS tools and verify a complete extracted-tree manifest after repacking.

The final retained implementations are `source-research/prepare_bridge_direct_gui_rootfs.py` and `source-research/assemble_bridge_direct_gui_ota.py`. Appendix E gives the same staging/manifest operations with generic fork/private-input paths. Do not run the older `prepare_bridge_rootfs.py` unchanged: it targets a superseded driver and contains an old literal SSID replacement.

The exact verified rebuild command was:

```sh
mksquashfs bridge-final-rootfs new-trt29.squashfs \
  -comp lzma -b 131072 -noappend -no-xattrs -no-progress \
  -processors 4 -mkfs-time 1649693888
```

Run filesystem staging/build as local WSL root so the existing ownership/device nodes are preserved, after verifying the absolute staging/output paths stay in the intended private build directory. The build log shows LZMA, 128 KiB blocks, no xattrs, 248 device nodes, and one FIFO. Supply the matched driver/script and private personalized templates from appendix E, then require the same verification for your build. A rootfs made by a different command must be compared structurally; copying its displayed size is not equivalent.

The installed tools used for these builds were `/usr/bin/unsquashfs` and `/usr/bin/mksquashfs`, both version **4.7.5 (2026/03/01)**. Confirm the build's compressor list includes `lzma`; a build supporting only `xz` is not equivalent.

Given an independently verified replacement SquashFS, the published tool supports:

```sh
python3 h267a_rootfs.py repack stock-trt29.bin new-trt29.squashfs candidate-trt29.bin
python3 h267a_rootfs.py verify candidate-trt29.bin
python3 h267a_rootfs.py extract candidate-trt29.bin candidate-roundtrip.squashfs --trim
sha256sum candidate-trt29.bin new-trt29.squashfs candidate-roundtrip.squashfs
```

Compare trimmed filesystem data correctly: the tool uses the SquashFS `bytes_used`, while an input image can have trailing padding. Hash equality of untrimmed and trimmed files is not a valid automatic expectation. Verify all meaningful bytes and filesystem entries; inspect the tool's returned metadata and preserve the full checks.

Also verify the kernel payload is byte-identical to stock, every wrapper CRC is correct, encrypted rootfs length is AES-block aligned and fits both declared flash slots, and the decompressed rootfs fits the actual RAM allocation. Existing static work rejected deliberately corrupted CRC cases and round-tripped a candidate, but the final image must be tested again after source/script changes.

The `decrypt` command's full-image output is an **analysis intermediate** with preserved original CRC fields, not a firmware upload artifact. Upload only the correctly re-encrypted/repacked and fully verified OTA package. Section 16 records the installed unit's package/hash; another unit's calibration/private build will produce a different package.

## 13. Persistent installation and rollback

The verified write used the OEM **`/bin/fw_flashing`** utility while this unit was running bank **2**; the subsequent running bank **1** was verified directly. Preflight inspection supported the expectation that the OEM path would use the inactive bank. That expectation and the observed 2→1 boot result are separate evidence; no manual bank-selection interface was tested. Use the exact observed vendor invocation below, with the current bank/map checked, rather than substituting a raw MTD writer or guessing an option's meaning.

1. Retain verified original kernel/rootfs/config backups. An additional raw configuration backup was read from this unit's `/dev/mtd3` before the write: **2 MiB**, captured through the same read-only hex-reader mechanism. Partition numbers are observations, not defaults for another firmware. `sendcmd DB fc` was advertised but did not work and is not a verified backup method.
2. Verify the final OTA's CRCs, original kernel payload, filesystem roundtrip, size/capacity, and private-input provenance. Transfer it to `/var/tmp/h267a-transfer.bin` with appendix D, then read the complete RAM file back and compare byte count/SHA-256 against the host file. The tested OTA was `15668928` bytes.
3. Establish the tested RAM wireless path if needed (appendix G), then physically remove the inter-router Ethernet cable before permanent startup restores all LAN ports. Keep the main PC wired directly to the upstream router. Do not create an Ethernet/wireless bridge loop or move the PC cable.
4. With local physical access and stable H267A power, issue the observed vendor command in the authorized H267A root shell:

```sh
/bin/fw_flashing -r 1 -f /var/tmp/h267a-transfer.bin
```

The inspected `-r 1` path reports its result through OEM IPC and then requests a reboot after about ten seconds. It is **not a bank selector**. Keep the observed invocation; the utility has no verified manual bank-selection argument in this workflow.

The shell/session became unavailable during this operation. Completion was established by the subsequent bank/status/startup checks, not by assuming a missing shell response means failure or success. Allow the H267A to finish; keep its power stable and the PC's upstream path unchanged.

On the first permanent boot, verification at about **85 seconds uptime** found current bank **1** with CRC/integrity/bootable status `Y`, the replacement `mt7603e_ap` plus original `mt7612e_ap`, startup-ready marker, connected `wlan2`, intended SSIDs on both APs, all four LAN interfaces in `br0`, Internet 3/3, and no remaining private DB dump. Private metadata also confirmed both rendered `WPAPSK1` values matched the saved GUI key and both `HideSSID` values were `0`.

Then a separate normal reboot was issued:

```sh
/bin/busybox reboot
```

At about **77 seconds uptime**, bank **1**, the same driver/startup/uplink/AP/bridge state, and Internet 3/3 passed again. The main PC's direct upstream TCP Internet checks remained open during the work. The bridge therefore survives an ordinary H267A reboot.

**Rollback limits:** the corrected RAM driver passed hot teardown and stock-module restoration before the flash. After persistent installation, ordinary reboot retains the modified image; factory reset concerns configuration and is not driver/rootfs rollback. Manual bank selection and failed-image bootloader recovery were **not exercised**. Keep the original private backups, but do not invent `mtd write`, bootloader-variable, bank-switch, or other-model recovery commands. This untested recovery path remains a limitation of the completed installation.

## 14. Change the upstream router, SSID, or password later

This procedure is intentionally upstream-brand independent. It uses the existing H267A GUI as the source of wireless credentials; it does not require source-code changes for an ordinary SSID/key change.

1. Keep the PC connected directly to the new/working upstream router. Record its LAN subnet, gateway, DHCP pool, exact 2.4 GHz SSID, and WPA2-PSK/AES key privately.
2. Ensure the new upstream has a compatible **2.4 GHz WPA2-PSK/AES** network. WPA3-only, enterprise authentication, 5 GHz-only uplink, or a captive portal has not been validated. If band steering uses one name for both bands, verify a real 2.4 GHz BSS is available.
3. Access the H267A locally. If its old management address is outside the new LAN, temporarily isolate it and use its AP/appropriate local management addressing. Do not enable its DHCP server while it is joined to the upstream LAN.
4. If the upstream subnet changed, select a new free `H267A_IP` in that subnet, set `LAN_MASK`, keep DHCP disabled, update any gateway configuration and diagnostic source allowlist, and reconnect to the new H267A address.
5. In the H267A's normal **2.4 GHz SSID1** settings, enter the new SSID/key and WPA2-PSK/AES. The final startup exports current GUI DB tables and reads row 0 `WLANCfg/ESSID` plus `WLANPSK/KeyPassphrase` (fallback `PreSharedKey`); editing a temporary radio `.dat` profile is not a persistent credential change.
6. Set the normal **5 GHz SSID1** to the same intended client-facing name/key. Keep visibility enabled on both bands. Check the GUI actually saved the settings.
7. Remove any inter-router Ethernet cable before wireless bridging starts.
8. Reboot **only the H267A**, allow roughly two minutes for the tested startup path, then verify wireless uplink, both AP names and a client Internet connection. The installed image reapplies the bridge automatically. If reproducing only the pre-flash RAM phase, reboot instead returns to stock and the reviewed RAM deployment must be applied again.

The startup clears the APCLI BSSID lock, so an upstream radio replacement with the same SSID/key should not require carrying over its old MAC address. Channel discovery/reconnect still needs testing against the new upstream; the H267A's 2.4 GHz AP shares its radio with the uplink, and its behavior follows the tested APCLI implementation.

**Gateway rule:** the generic startup no longer contains a fixed device gateway. It prefers the existing IPv4 default route on `br0`, otherwise derives a `.1` address from the first three octets of `br0`'s IP. Mock tests cover a different conventional subnet and an explicit `.254` gateway. For another gateway or a nonconventional subnet, ensure the correct `dev br0` default route exists before startup; do not assume the `.1` fallback matches the upstream network. A physical router swap to a different subnet was not performed.

If only the password/SSID changes while the LAN remains unchanged, no new gateway/subnet setting is needed. Current GUI credential rendering and ordinary reboot persistence have both passed native tests. Use the H267A-only reboot/startup path rather than renaming or manually reloading only part of the radio stack. Changing to a new real SSID/password was not separately exercised; the procedure follows the tested DB reader and reboot path.

## 15. Troubleshooting

| Symptom | Check / action |
|---|---|
| H267A GUI disappears after LAN change | Use the recorded new address; verify the client is in the same subnet. Keep the upstream PC cable untouched. Check duplicate-address/DHCP-pool conflicts. |
| Telnet 2323 is refused from a new PC IP | The diagnostic source allowlist may still name the previous management address. Repair it only through the authorized local GUI/configuration path; do not expose diagnostics to WAN. |
| SSH authenticates but shell closes | This OEM service uses its own CLI. Use the separately validated diagnostic path; authentication does not imply root shell capability. |
| `Exec format error` or loader failure on host compiler | Check host i386 runtime, compiler interpreter, and library search paths. Do not confuse the host compiler executable format with its MIPS target output. |
| Driver builds but has unresolved symbols | Compare against actual TRT29 kernel exports and the legacy 5 GHz imports. Do not force-load or strip symbol checks to hide a mismatch. |
| Kernel fault, reference warning, or module unload hangs | Stop further loads/unloads. Preserve `dmesg`/module/task state privately and use the planned H267A recovery. Static ABI checks do not rule out wrong runtime semantics. |
| Upstream association works but LAN clients fail | Verify `wlan2`, OEM private LAN index 6 registration, and `br0` membership. OEM `wlan1` index 5 is public/isolated. Verify DHCP/ARP rather than assuming association means forwarding. |
| Only one radio appears | Verify `HideSSID=0` in both rendered profiles, the OEM 5 GHz module loaded after 2.4 GHz, and the WPS compatibility exports are present. Do not publish profile contents containing keys. |
| SSID/key change has no effect | Confirm normal 2.4 GHz SSID1 was saved and the script uses DB `pf` row 0, not factory `MT7592.dat` or masked DB `p` output. Never display the private dump; confirm it is removed. Apply through the reviewed restart path. |
| Phone appears to have Internet but Ethernet cable is connected | Repeat with the inter-router cable physically absent and phone mobile data disabled. Record the H267A radio/BSSID privately to prove the phone chose the intended AP. |
| Intermittent failure after adding Ethernet path | Check for an inter-router Layer 2 loop before changing drivers. Disconnect the duplicate path. |
| New upstream uses another subnet | Reassign H267A management IP/mask, DHCP exclusions, and source ACL. Verify an explicit correct default route on `br0`, or that the documented `.1` fallback matches the gateway. |
| Internet works, name resolution fails | Check the client's upstream DHCP-provided DNS and gateway; avoid introducing a second DHCP server as a workaround. |
| Image verification passes but boot is unknown | Keep the candidate local. CRC and SquashFS checks cannot prove boot-time driver lifecycle or recovery. |

## 16. Retained local evidence and completion record

The following records were retained in the original private analysis workspace. They are historical evidence references, are not included in this repository, and are not prerequisites supplied by the checkout. The reproduction instructions use the owner's own firmware, calibration, backups, and generated outputs.

```text
source-research/trt29-port-build-command.json
source-research/trt29-build-context-command.json
source-research/mt7603-apcli-public-repro-static-check.json
source-research/h267a_trt29_abi_contract.h
source-research/stock-5g-wps-relocations.json
source-research/rootfs-change-manifest.json
source-research/ota-build-verification.json
telnet-root-direct-name-three-unload-cycles.json
telnet-root-direct-full-unload-positive-result.json
telnet-root-generic-gui-native-result.json
ram-transfer-direct-module-verification.json
telnet-root-permanent-vendor-flash.json
telnet-root-permanent-first-boot-verification.json
telnet-root-permanent-credential-verification.json
telnet-root-permanent-normal-reboot-command.json
telnet-root-permanent-normal-reboot-verification.json
source-research/ota-direct-gui-verification.json
archived-firmware/vr300-gpl-manifest.json
telnet-root-active-kernel-export-metadata.json
telnet-root-ram-rootfs-export-metadata.json
driver-candidates/h267a-wireless-bridge.sh
h267a_rootfs.py
```

Evidence files can contain old timestamps, superseded limitations, device-specific paths, or private fields. Consult the final completion record before treating an earlier candidate as current; do not publish this directory wholesale.

The completion record for **2026-11-12** is:

| Item | Result |
|---|---|
| Public `main` commit | [`64a197c04f6b8608e10477076a71edd59a242fd5`](https://github.com/cakmakfatih/rt-n56u/commit/64a197c04f6b8608e10477076a71edd59a242fd5), published and verified on GitHub. |
| Private runtime + GPL bootstrap | Fresh private runtime/toolchain extraction and 35 interpreter patches worked; GCC 4.3.6 and byte-identical helper passed. Fresh official GPL kernel/global headers plus public config prepared and built the driver successfully. |
| Module lifecycle | Direct `wlan2` naming fix: three connect/unload cycles and full hot teardown/stock restoration passed. |
| Generic startup | Actual GUI DB row 0 read, MAC/gateway preservation, 21 mock cases and native bridge/cleanup tests passed. |
| Original kernel | Kernel payload remained byte-identical in the repacked OTA. |
| Final SquashFS | `11476992` bytes; SHA-256 `855042137b191d604c28ea92f837001b196acf609b40a49f9792fc9617d8e43f`; all `1422` extracted manifest entries matched. |
| Installed private OTA | `15668928` bytes; SHA-256 `148b8984ca54c44ce0f6d3f085e21e95ec9bfe6d46e02a238b59ee591e9075cf`; full RAM read-back matched before the OEM write. |
| Permanent boots | First boot and separate normal reboot both verified current bank 1 with valid status, startup ready, both drivers/AP names, `wlan2` connected, all four LAN members and Internet 3/3. |
| Credentials | Both runtime AP key fields matched saved GUI settings and both SSIDs were visible; private DB export removed. No credential values are recorded here. |
| Main Internet | Main PC stayed directly wired upstream; TCP Internet checks stayed open. |
| Ethernet client | The owner confirmed Internet access over an Ethernet cable after permanent installation. The specific port and a complete per-port test were not recorded. |
| Remaining untested | Separate physical tests of every LAN port, a new phone test on each band, a real upstream router/credential swap, forced reconnect, throughput/long-duration stability, multicast/IPv6/roaming, manual bank selection and failed-image recovery. |

The installed local filename retains the historical suffix `h267a-trt29-wireless-bridge-direct-gui-unflashed.bin`; that suffix does **not** describe its current state. The matching image was subsequently written and passed both permanent boot checks. Conversely, older reports with `flash_written: false` describe their earlier build stage and are superseded by the permanent-boot evidence above.

These image hashes identify this unit's private build, which includes its calibration and radio MACs. A fresh build for another unit or from a different build path/input revision can differ. Record and validate its own hashes instead of copying this private image. Rebuild/re-record all checks if a driver, startup, template, or packaging input changes.

## Appendix A. Reproduce the restricted diagnostic configuration

The retained decoder is [mkst/zte-config-utility](https://github.com/mkst/zte-config-utility), commit `e3a1a7f56c2df26a02f52f72b16173d0702d9ad0`, version `0.5.3`. Its declared dependency is `pycryptodomex==3.20.0`. The H267A backup in this work has signature **`ZXHN H267A V1.0`** and **payload type 2**; the utility recognizes its published key automatically. This config format is separate from the OTA firmware rootfs format.

Use the following in a private directory, with new output names. They operate on local files only:

```sh
git clone https://github.com/mkst/zte-config-utility.git zte-config-utility
git -C zte-config-utility checkout e3a1a7f56c2df26a02f52f72b16173d0702d9ad0
python3 -m venv config-env
. config-env/bin/activate
python3 -m pip install ./zte-config-utility
python3 zte-config-utility/examples/decode.py original-config.bin original-config.xml
python3 zte-config-utility/examples/encode.py \
  original-config.xml roundtrip-original.bin \
  --signature 'ZXHN H267A V1.0' --include-header --payload-type 2
python3 zte-config-utility/examples/decode.py \
  roundtrip-original.bin roundtrip-original.xml
cmp original-config.xml roundtrip-original.xml
```

These exact encode flags were rechecked against the retained original XML: the encoded output matched the retained roundtrip binary and its decoded XML matched byte for byte. The encoded binary need not match the OEM export byte for byte if the host uses a different zlib implementation; the retained Windows runtime was `1.3.1.zlib-ng`. Valid wrapper/compressed CRCs, correct signature/type, and exact decoded XML are the checks that matter. A size difference alone is not proof of corruption or correctness.

Make a separate `restricted-telnet.xml` copy of `original-config.xml`. The XML uses `DB/Tbl[@name=...]/Row/DM`, with values stored in the `val` attribute. Keep all account fields, wireless settings, and unrelated tables unchanged. The exact final `TelnetCfg`, row `No="0"`, service changes were:

| Field | Final value | Meaning in the observed firmware |
|---|---|---|
| `TS_Enable` | `1` | Enable Telnet service |
| `Wan_Enable` | `0` | Keep WAN service disabled |
| `Lan_Enable` | `1` | Allow LAN listener |
| `TS_Port` | `2323` | Diagnostic TCP port |
| `ProcType` | `0` | Shell path used by the observed daemon |
| `Level` | `1` | Root diagnostic level on this observed firmware |

Preserve `TS_UName`, `TS_UPwd`, maximum connection/authentication limits, and authentication lock time. The intermediate `Level=3` configuration did not supply the intended root context; the final change to `Level=1` was followed by root shell diagnostics. These meanings are firmware-specific, not a recommendation for other ZTE models.

For `FWSC`, preserve all existing rows and add the four Telnet rules below with unused, unique row numbers and matching `ViewName` identifiers. If there are already `N` rows numbered `0..N-1`, the next row is `No="N"`, with `ViewName="IGD.FWSc.FWSC(N+1)"`; increment for subsequent rows and update `Tbl`'s `RowCount` to the actual row count. Do not reuse an identifier, silently overwrite an existing rule, or leave `RowCount` stale.

All four new rows use these common fields exactly, including the OEM spelling `Servise`:

```text
IPMode=1
Enable=1
INCName=
MinSrcMask=0.0.0.0
Prefix=::
PrefixLen=0
Servise=0
ServiceList=TELNET,
```

The remaining rule fields are:

| `Name` | `INCViewName` | `MinSrcIp` | `MaxSrcIp` | `FilterTarget` |
|---|---|---|---|---|
| `tn_diag` | `DEV.IP.IF1` | `PC_IP` | `PC_IP` | `1` (allow) |
| `tn_lan_a` | `DEV.IP.IF1` | `1.0.0.0` | IPv4 address immediately before `PC_IP` | `0` (deny) |
| `tn_lan_b` | `DEV.IP.IF1` | IPv4 address immediately after `PC_IP` | `255.255.255.254` | `0` (deny) |
| `tn_wan` | `IGD.WANIF` | `0.0.0.0` | `0.0.0.0` | `0` (deny WAN wildcard) |

Use a normal unicast LAN `PC_IP`; compute its predecessor/successor as IPv4 integers, not by blindly editing the last octet. The two LAN ranges exclude that one allowed source. The original configuration's existing rules must also be reviewed for conflicting Telnet access; the observed original had no Telnet rule. IPv6 was disabled in the observed setup; do not assume these IPv4 rows restrict an independently enabled IPv6 service.

The observed intermediate SSH enablement was separate: `SSHCfg/SSH_Enable=1` with `SSH_ProcType=1` for the CLI, a source-specific `SSH,` allow row, and analogous two LAN deny ranges plus a WAN deny row. It is not needed to turn Telnet into a shell. Preserve or remove that optional service deliberately; do not copy its old source address. FTP stays disabled.

Encode and verify the modified file locally:

```sh
python3 zte-config-utility/examples/encode.py \
  restricted-telnet.xml restricted-telnet.bin \
  --signature 'ZXHN H267A V1.0' --include-header --payload-type 2
python3 zte-config-utility/examples/decode.py \
  restricted-telnet.bin restricted-telnet-roundtrip.xml
cmp restricted-telnet.xml restricted-telnet-roundtrip.xml
```

Compare the original and edited XML structurally before import: only the intended `TelnetCfg` fields and new `FWSC` rows should differ; account/password fields must match exactly. If enabling the optional SSH CLI from a disabled starting state, list its separate intended changes explicitly rather than accepting unexplained table differences. Keep both files private.

Import the verified binary through the **H267A's own configuration restore** page, with physical access and the original backup available. A configuration import can reboot the H267A; keep the main PC's upstream cable untouched. Reconnect at `H267A_IP`, then use a Telnet client supporting a custom port to connect to `H267A_IP:2323` with the preserved account. Confirm `id` reports the intended privilege, a different LAN source is denied, and WAN remains disabled. After testing, restore the saved service configuration if diagnostics are no longer required. Do not print account values in the guide or console transcript.

## Appendix B. Reconstruct the original TRT29 OTA from read-back data

The exact retained implementation is `source-research/assemble_bridge_ota.py`. It reconstructed an original OTA from `trt29-files/kernel2-active-mtd6.bin` and `trt29-files/ram-rootfs-mtd8.bin`, then built an earlier modified candidate. Its pinned input/candidate hashes and private filenames belong to the original experiment; use it as format evidence, not an installer.

The observed read-back kernel bank includes the ZTE wrapper. Its descriptor is at `0x3c`; the kernel payload begins at `0x100`; kernel payload plus header occupy `0x400000` bytes. The rootfs immediately follows at OTA offset `0x400000`. Rootfs encrypted length is a big-endian word at descriptor `+0x40`. The RAM rootfs is plaintext; encrypt exactly that many bytes, including the preserved original padding, to recover the original encrypted region. The existing descriptor stores CRCs for ciphertext, kernel payload, and descriptor header.

The local reconstruction below uses the published `h267a_rootfs.py` functions and stops if this exact TRT29 layout or any CRC does not match. Run it alongside that tool, replacing only private input/output paths; the output file must not already exist:

```sh
python3 - private-kernel-bank.bin private-ram-rootfs.bin stock-trt29.bin <<'PY'
from pathlib import Path
import struct
import sys
from h267a_rootfs import KEY, Layout, aes, decrypt_rootfs

kernel_path, ram_path, output_path = map(Path, sys.argv[1:])
kernel, ram = kernel_path.read_bytes(), ram_path.read_bytes()
assert len(kernel) == 0x400000
assert len(ram) == 0xb00000
descriptor = 0x14 + struct.unpack_from('>I', kernel, 0x10)[0]
assert descriptor == 0x3c
length = struct.unpack_from('>I', kernel, descriptor + 0x40)[0]
assert 96 <= length <= len(ram) and length % 16 == 0
image = kernel + aes(ram[:length], KEY, decrypt=False)
layout = Layout.parse(image)
assert (layout.kernel_offset, layout.rootfs_offset) == (0x100, 0x400000)
assert layout.version == 'V1.0.1_TRT29'
assert layout.rootfs_end == len(image)
layout.require_checksums(image)
assert decrypt_rootfs(image, layout, KEY) == ram[:length]
with output_path.open('xb') as output:
    output.write(image)
print('Verified reconstructed TRT29 OTA:', len(image), 'bytes')
PY
python3 h267a_rootfs.py verify stock-trt29.bin
```

Validate and record the input SHA-256 values against the independently verified read-back manifests before this step. The retained `assemble_bridge_ota.py` additionally compared the reconstructed ciphertext prefix against a direct rootfs-bank prefix read. Repeat that comparison for fresh read-back material; it proves the RAM-to-ciphertext reconstruction is the same observed bank data rather than simply a self-consistent new package.

For a replacement SquashFS, use the published tool's `repack` command in section 12. It sets the new encrypted rootfs length at descriptor `+0x40`, ciphertext CRC at `+0x48`, and descriptor CRC at `+0xa4`, while preserving the kernel payload. The retained original assembly also deliberately corrupted a descriptor byte, a kernel payload byte, and a rootfs ciphertext byte; all three cases were rejected. A malformed-input test does not establish that a well-formed image will boot.

## Appendix C. Export exact stock bytes and radio calibration

The OEM root shell has `printf` and `read` builtins, but lacks some common binary-transfer utilities. The working path used a tiny static MIPS big-endian stdin-to-hex reader, built and emulated locally before execution. Its source is `build_hexreader.py` in the analysis directory. Copy it to a fresh private tools directory and install the tested dependencies there:

```sh
python3 -m pip install keystone-engine==0.9.2 unicorn==2.1.4
python3 build_hexreader.py
```

The script self-tests empty input, every byte value, short reads/writes, and I/O errors, then produces `h267a-hexreader.mips` (368 bytes in the retained build). It writes its output beside its source; do not run it in a repository or overwrite an unrelated tool. Retain its printed SHA-256 hash.

To stage a new `/tmp/h267a-hexreader`, the verified shell bootstrap first copied an executable to preserve executable permissions, then replaced its bytes using octal `printf` chunks. Generate the exact device commands on the host:

```sh
python3 - h267a-hexreader.mips <<'PY'
from pathlib import Path
import sys
data = Path(sys.argv[1]).read_bytes()
assert data[:6] == b'\x7fELF\x01\x02' and 0 < len(data) < 4096
print('test ! -e /tmp/h267a-hexreader && cp /bin/busybox /tmp/h267a-hexreader')
for start in range(0, len(data), 192):
    octets = ''.join('\\%03o' % byte for byte in data[start:start + 192])
    redirect = '>' if start == 0 else '>>'
    print("printf '%s' %s /tmp/h267a-hexreader" % (octets, redirect))
PY
```

Review and enter those commands in the authorized H267A root shell, one at a time, checking the exit status. If the initial `test` fails, stop and identify the existing file; do not continue overwriting it. The two `printf` commands contain the known reader's bytes, never credentials. Verify the transferred executable by reading itself:

```sh
echo H267A_HEX_BEGIN
/tmp/h267a-hexreader < /tmp/h267a-hexreader
echo
echo H267A_HEX_END
```

Capture the complete hex stream privately, decode it with `bytes.fromhex`, and compare bytes and SHA-256 against the host binary before using it to back up anything else. The existing `restore-approved-hexreader-commands.json` holds the retained command sequence, and `telnet-root-approved-reader-restored.json` records the successful self-read.

For file exports, use one bounded, identified source at a time. These module exports are exact commands used in the investigation:

```sh
echo H267A_HEX_BEGIN; /tmp/h267a-hexreader < /lib/modules/mt7603eap.ko; echo; echo H267A_HEX_END
echo H267A_HEX_BEGIN; /tmp/h267a-hexreader < /lib/modules/mt7612e_ap.ko; echo; echo H267A_HEX_END
```

The observed read-back sizes were `2418955` bytes for stock 2.4 GHz and `2396420` bytes for stock 5 GHz. In this firmware, the real bytes must be read: the OEM `ls -l` display reported a misleading 10-byte size for these paths.

For the investigated active bank and RAM map only, the equivalent read-only sources were `/dev/mtdblock6` (4 MiB active kernel bank including wrapper) and `/dev/mtdblock8` (11 MiB immutable plaintext RAM rootfs). Confirm the current MTD map/bank evidence first. The command reads **from** the device node; it never redirects **to** it:

```sh
echo H267A_HEX_BEGIN; /tmp/h267a-hexreader < /dev/mtdblock6; echo; echo H267A_HEX_END
echo H267A_HEX_BEGIN; /tmp/h267a-hexreader < /dev/mtdblock8; echo; echo H267A_HEX_END
```

Use separate complete capture files for each command and allow for about twice the binary size as hexadecimal text. Terminal scrollback or tool-output truncation is not a backup. The existing local Telnet scripts have a complete-stream reader; before adapting them, remove their hardcoded device address, private XML path, and SSID assertion, keeping authentication private and bounded to the intended LAN target. Do not run these historical scripts unchanged on another network.

On the host, decode a capture containing exactly one marker block and verify the byte count. For example, for a kernel capture:

```sh
python3 - kernel-capture.txt private-kernel-bank.bin 4194304 <<'PY'
from pathlib import Path
import hashlib
import re
import sys
capture, output, count = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3])
text = capture.read_text(encoding='ascii')
blocks = re.findall(r'(?:^|\n)H267A_HEX_BEGIN\r?\n([0-9a-fA-F\r\n]+)\r?\nH267A_HEX_END(?:\r?\n|$)', text)
assert len(blocks) == 1, 'Need one complete marker block'
data = bytes.fromhex(blocks[0])
assert len(data) == count, 'Truncated or wrong source'
with output.open('xb') as stream:
    stream.write(data)
print(len(data), hashlib.sha256(data).hexdigest())
PY
```

Use `11534336` for the RAM rootfs. Re-read and compare hashes, then use the CRC/decryption and direct ciphertext-prefix checks in appendix B. A reader that returns the expected length has not independently proved the correct partition was selected.

For **radio calibration**, the stock driver's read-only syntax is `iwpriv wlan0 e2p ADDRESS_LIST`. Generate the exact eight 32-word requests on the host:

```sh
python3 - <<'PY'
for start in range(0, 512, 64):
    print('iwpriv wlan0 e2p ' + ','.join(f'{offset:04x}' for offset in range(start, start + 64, 2)))
PY
```

Run them while the stock 2.4 GHz driver owns `wlan0`, capturing the complete responses privately. Each request contains only addresses; **never append `=VALUE`**, which is the EEPROM write syntax. The retained read-only queries covered every even offset `0000` through `01fe`, 256 words in total.

The driver prints word reads as `[0xOFFSET]:0xVALUE`. Construct the 512-byte calibration by sorting unique offsets and storing each 16-bit word in the EEPROM's little-endian byte order. Require all 256 offsets exactly once, no missing/duplicate or unexpected offsets, then verify the first two bytes are the expected `9275` signature (`0x7592` word) for this unit. The public builder also accepts the opposite byte signature, but that is not permission to swap the entire dump blindly. Compare a repeated read byte for byte, retain its device provenance and hash, and pass that binary to `--eeprom`. Do not display the values or embed the binary in this guide.

## Appendix D. Transfer a module/image to RAM without a long Telnet upload

The fork includes `h267a/h267a_ram_receive.c` and `h267a/test_ram_receive.py`. This is a small **one-file receiver**, with no command execution and no flash I/O. Its public defaults bind to loopback and accept only loopback; for direct local staging, compile it with this H267A's LAN address and the one authorized management PC's address. Do not widen it to every interface/source.

The receiver accepts one connection, checks its source, reads a four-byte big-endian file length, then reads exactly that many bytes. It refuses zero length and more than **20 MiB**, creates `/var/tmp/h267a-transfer.bin` with `O_EXCL` and mode `0600`, flushes the file, replies `OK\n`, and exits. It has a 60-second process alarm and 30-second receive timeout. A rejected connection also consumes the one-shot listener; start a new instance only after checking why it failed. An incomplete transfer can leave a partial RAM file; identify and remove that exact file before a reviewed retry. No persistent daemon remains after the one-file process ends.

The host test covers exact binary transfer, oversized input, existing-file preservation, wrong peer, and short input:

```sh
cd "$HOME/h267a-work/source"
python3 h267a/test_ram_receive.py
```

With `CROSS`/host runtime from section 8 and privately assigned `H267A_IP`/`PC_IP` shell variables, validate their syntax and compile:

```sh
python3 - "$H267A_IP" "$PC_IP" <<'PY'
import ipaddress
import sys
for value in sys.argv[1:]:
    address = ipaddress.IPv4Address(value)
    assert not (address.is_unspecified or address.is_multicast)
PY
"${CROSS}gcc" -static -Os -march=mips32r2 -mabi=32 \
  -ffunction-sections -fdata-sections -Wl,--gc-sections -s \
  "-DBIND_ADDR=\"$H267A_IP\"" "-DALLOWED_ADDR=\"$PC_IP\"" \
  h267a/h267a_ram_receive.c -o "$BUILD/h267a-ram-receive"
```

Those compiler/linker flags were used for the native 13,792-byte receiver. The native test transferred a 2,511,188-byte driver in about 0.18 seconds, acknowledged completion, then independently read back the whole file through the verified hex reader and matched SHA-256. This timing is one local measurement, not a throughput guarantee. Rebuilding with different macro values or compiler settings can change the binary/hash.

Stage the small receiver through the already verified Telnet octal uploader once, using a new `/tmp` path and read-back verification. The historical `telnet_upload_verified.py`/`telnet_upload_pipelined.py` contain device-specific addresses and private XML assumptions; parameterize those before reuse rather than running them unchanged. The octal bootstrap mechanism in appendix C also applies, but its example is intentionally limited to the 368-byte reader: increase its file-size bound deliberately for this receiver and preserve per-chunk acknowledgement/read-back checks.

On the H267A, the verified executable-mode staging pattern was:

```sh
test ! -e /tmp/h267a-ram-receive-run && \
  cp /tmp/h267a-hexreader /tmp/h267a-ram-receive-run && \
  cat /tmp/h267a-ram-receive.mips > /tmp/h267a-ram-receive-run && \
  /tmp/h267a-ram-receive-run
```

Here `/tmp/h267a-ram-receive.mips` must already contain the verified compiled receiver bytes. Check that `/var/tmp/h267a-transfer.bin` does not already exist before launch. The foreground receiver waits for the one permitted host; send the file promptly from that host in a separate terminal:

```sh
python3 - "$H267A_IP" private-module-or-ota.bin <<'PY'
from pathlib import Path
import hashlib
import socket
import struct
import sys
data = Path(sys.argv[2]).read_bytes()
assert 0 < len(data) <= 20 * 1024 * 1024
with socket.create_connection((sys.argv[1], 18083), timeout=10) as connection:
    connection.settimeout(60)
    connection.sendall(struct.pack('>I', len(data)))
    connection.sendall(data)
    reply = b''
    while len(reply) < 3:
        part = connection.recv(3 - len(reply))
        assert part, 'Receiver closed before acknowledgement'
        reply += part
    assert reply == b'OK\n'
print('Transferred to RAM:', len(data), 'bytes; local SHA-256:', hashlib.sha256(data).hexdigest())
PY
```

`OK` proves the receiver completed its bounded write; it is not an independent content hash. Read `/var/tmp/h267a-transfer.bin` back through the known hex reader, decode the complete capture, and compare byte count and SHA-256 to the local file. Confirm the listener process has exited before proceeding. The verified direct-module read-back evidence is `ram-transfer-direct-module-verification.json`.

Transferring an OTA package to `/var/tmp` leaves it in RAM. It does **not** flash a bank, change boot selection, or authorize skipping the remaining image/rollback checks. Similarly, transferring a `.ko` does not load it; loading remains part of the reviewed bridge startup sequence.

## Appendix E. Stage a reproducible private rootfs from the fork

Use this only after obtaining a verified original TRT29 SquashFS and this unit's built driver. The generic template paths below are `h267a/profile-templates/mt7603.dat` and `mt7612.dat`; confirm they exist in `SOURCE_COMMIT` before proceeding. Their neutral SSID/key values are replaced by the GUI database reader at runtime. No real Wi-Fi key needs to be inserted during image construction. Public templates omit device MAC literals; the private staging code inserts **this unit's own stock radio MACs** to reproduce the natively verified configuration. The built driver also contains this unit's private calibration, so the resulting image remains private.

Create a new private firmware directory and extract the verified original filesystem while preserving ownership/device nodes:

```sh
mkdir "$BUILD/firmware"
sudo unsquashfs -d "$BUILD/firmware/stock-rootfs" stock-trt29.squashfs
```

The following parameterized staging code mirrors the final retained builder. Run in Linux/WSL, using the Python interpreter containing the tooling dependencies. Its `sudo` is for local filesystem ownership, not a router operation. Pass the source checkout, untouched extracted rootfs, private `.ko`, verified helper, and new staging directory:

```sh
sudo python3 - "$HOME/h267a-work/source" "$BUILD/firmware/stock-rootfs" \
  "$BUILD/mt7603-apcli-1.ko" "$BUILD/h267a-register-wlan2" \
  "$BUILD/firmware/bridge-rootfs" "$RADIO24_MAC" "$RADIO5_MAC" <<'PY'
from pathlib import Path
import hashlib
import json
import os
import re
import stat
import subprocess
import sys

source, stock, module, helper, staged = (Path(p).resolve() for p in sys.argv[1:6])
radio24_mac, radio5_mac = sys.argv[6:8]
for mac in (radio24_mac, radio5_mac):
    assert re.fullmatch(r'(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}', mac)
    assert mac != '00:00:00:00:00:00' and not (int(mac[:2], 16) & 1)
assert os.geteuid() == 0
assert stock.is_dir() and not staged.exists()
assert staged.parent == stock.parent and staged.name == 'bridge-rootfs'
assert not staged.is_relative_to(source)
report_path = staged.parent / 'rootfs-change-manifest.json'
assert not report_path.exists()

def manifest(root):
    rows = {}
    for path in sorted(root.rglob('*')):
        info = path.lstat()
        row = {'mode': info.st_mode, 'uid': info.st_uid, 'gid': info.st_gid}
        if stat.S_ISREG(info.st_mode):
            row['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        elif stat.S_ISLNK(info.st_mode):
            row['target'] = os.readlink(path)
        elif stat.S_ISCHR(info.st_mode) or stat.S_ISBLK(info.st_mode):
            row['device'] = [os.major(info.st_rdev), os.minor(info.st_rdev)]
        rows[path.relative_to(root).as_posix()] = row
    return rows

inputs = {
    'lib/modules/mt7603-apcli.ko': (module, 0o644),
    'usr/sbin/h267a-register-wlan2': (helper, 0o755),
    'usr/sbin/h267a-wireless-bridge.sh': (source / 'h267a/wireless-bridge.sh', 0o700),
    'etc/h267a-wireless/mt7603.dat': (source / 'h267a/profile-templates/mt7603.dat', 0o600),
    'etc/h267a-wireless/mt7612.dat': (source / 'h267a/profile-templates/mt7612.dat', 0o600),
}
assert all(path.is_file() for path, mode in inputs.values())
before = manifest(stock)
subprocess.run(['cp', '-a', str(stock), str(staged)], check=True)
for destination, (input_path, mode) in inputs.items():
    path = staged / destination
    assert not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = input_path.read_bytes()
    if destination.endswith('.dat'):
        lines = data.decode().splitlines()
        assert [line for line in lines if line.startswith('HideSSID=')] == ['HideSSID=0']
        mac = radio24_mac if destination.endswith('mt7603.dat') else radio5_mac
        lines = [line for line in lines if not line.startswith('MacAddress=')]
        data = ('\n'.join(lines + ['MacAddress=' + mac]) + '\n').encode()
    with path.open('xb') as output:
        output.write(data)
    os.chmod(path, mode)
    os.chown(path, 0, 0)
    os.utime(path, (1649693888, 1649693888))

init = staged / 'etc/init.norm'
original = init.read_bytes()
assert b'pc&' in original and b'h267a-wireless' not in original
init.write_bytes(original + b'\n/usr/sbin/h267a-wireless-bridge.sh > /var/log/h267a-wireless-bridge.log 2>&1 &\n')
for path in (init, staged / 'usr/sbin/h267a-wireless-bridge.sh'):
    subprocess.run(['/bin/sh', '-n', str(path)], check=True)
after = manifest(staged)
changed = [name for name in before if before[name] != after.get(name)]
added = [name for name in after if name not in before]
assert changed == ['etc/init.norm'], changed
assert set(added) == set(inputs) | {'etc/h267a-wireless'}, added
report = {'changed': changed, 'added': added,
          'preserved_original_entries': len(before) - 1,
          'staged_entries': len(after), 'flash_written': False,
          'expected_manifest': after}
image = staged.parent / 'new-trt29.squashfs'
roundtrip = staged.parent / 'roundtrip-rootfs'
assert not image.exists() and not roundtrip.exists()
subprocess.run(['mksquashfs', str(staged), str(image), '-comp', 'lzma',
                '-b', '131072', '-noappend', '-no-xattrs', '-no-progress',
                '-processors', '4', '-mkfs-time', '1649693888'], check=True)
assert image.stat().st_size <= 0xb00000
subprocess.run(['unsquashfs', '-d', str(roundtrip), str(image)], check=True)
assert manifest(roundtrip) == after, 'Roundtrip changed filesystem metadata/content'
report['image_bytes'] = image.stat().st_size
report['squashfs_sha256'] = hashlib.sha256(image.read_bytes()).hexdigest()
report['roundtrip_manifest_identical'] = True
with report_path.open('x') as output:
    json.dump(report, output, indent=2)
print('Built rootfs; original entries preserved:', len(before) - 1,
      '; full roundtrip manifest matched:', len(after))
PY
```

This produces `new-trt29.squashfs`, re-extracts it, and requires full manifest equality, including owners, modes, links, device nodes, and file hashes. Its report records the image size/hash and expected manifest privately. The latest retained final candidate passed this full check with 1,422 entries. Keep the MAC parameters from the intended physical unit; do not replace them with another unit's addresses or assume a missing `MacAddress` field has the same precedence on this legacy driver.

For the OTA wrapper, appendix B reconstructs/validates the original package from this unit's verified kernel and RAM rootfs. The generic `h267a_rootfs.py repack` command then trims the replacement filesystem to SquashFS `bytes_used`, pads to 16-byte AES alignment, encrypts it, updates the rootfs length/ciphertext CRC/descriptor CRC, and preserves the original kernel payload. This is the same essential format operation as the final local `assemble_bridge_direct_gui_ota.py`; use the generic tool to avoid its investigation-specific input paths and pinned hashes. Re-run all CRC/decrypt/roundtrip/kernel-identity/capacity checks against the produced **OTA package**, not only the SquashFS file.

## Appendix F. Reproduce the private i386 host runtime

The observed build host is **Ubuntu 26.04 LTS, amd64, in WSL**. It uses normal host build tools (`cc`, `make`, `git`, `python3`, `tar`, `dpkg-deb`, and GNU binutils) plus the SquashFS tools/version recorded in section 12. Install those host prerequisites through the distribution's normal package manager; they are separate from the old MIPS compiler.

The old compiler executables are 32-bit x86 host programs. Instead of altering system libraries or installing the ancient toolchain globally, the verified method extracts two official Ubuntu runtime packages into `BUILD/runtime-i386/root`, then updates only the **private copy** of the toolchain's ELF interpreter paths.

The exact pinned packages and SHA-256 values are:

| Package | SHA-256 |
|---|---|
| `libc6-i386_2.43-2ubuntu2.4_amd64.deb` | `03c4702b069d9e6549df388d38f73cab5270ad3d2b1e7569e0b93c6a3d752816` |
| `lib32z1`, version `1:1.3.dfsg+really1.3.1-1ubuntu3.2`, amd64 | `93e287af69d7005691c4312ce7118d060d76fcf045b6e4725b8a85152bcd3d73` |

Their hashes were verified against both local package bytes and the official repository metadata. Use the official repository/archive if the pinned version is no longer in the current mirror; do not silently substitute a different runtime and assume the result was validated. Downloading the packages does not install them system-wide:

```sh
mkdir "$BUILD/runtime-i386"
cd "$BUILD/runtime-i386"
apt download libc6-i386=2.43-2ubuntu2.4 \
  lib32z1=1:1.3.dfsg+really1.3.1-1ubuntu3.2
sha256sum ./*.deb
mkdir root
dpkg-deb -x libc6-i386_2.43-2ubuntu2.4_amd64.deb root
dpkg-deb -x lib32z1_*.deb root
```

Require exactly one matching `lib32z1` archive and verify its hash before extraction. Repository/download tooling can encode the version's colon as `%3a`, use a literal colon, or omit the epoch from the filename; match the package version/hash rather than relying on that filename detail. `root`'s parent directory must exist before `dpkg-deb -x`.

The following patch appends the private loader pathname and updates the `PT_INTERP` program-header offset/length for **ELF32 little-endian x86 host executables only**. It skips symlinks and all MIPS target binaries/libraries. It never changes the system loader or the public source checkout. Run it only on the freshly extracted private toolchain copy from section 8; moving that toolchain/runtime afterward requires repatching the absolute loader pathname.

```sh
python3 - "$BUILD/toolchain/mips-linux-uclibc-4.3.6-v2" \
  "$BUILD/runtime-i386/root/usr/lib32/ld-linux.so.2" <<'PY'
from pathlib import Path
import struct
import sys

base, loader = (Path(p).resolve() for p in sys.argv[1:])
assert base.is_dir() and loader.is_file()
encoded = str(loader).encode() + b'\0'
assert len(encoded) < 4096
changed = 0
for path in sorted(base.rglob('*')):
    if path.is_symlink() or not path.is_file():
        continue
    data = bytearray(path.read_bytes())
    if len(data) < 52 or data[:6] != b'\x7fELF\x01\x01':
        continue
    if struct.unpack_from('<H', data, 18)[0] != 3:
        continue
    offset = struct.unpack_from('<I', data, 28)[0]
    size, count = struct.unpack_from('<HH', data, 42)
    assert size == 32 and offset + size * count <= len(data)
    for index in range(count):
        header = offset + index * size
        if struct.unpack_from('<I', data, header)[0] != 3:
            continue
        previous = struct.unpack_from('<I', data, header + 4)[0]
        length = struct.unpack_from('<I', data, header + 16)[0]
        assert previous + length <= len(data)
        if data[previous:previous + length] == encoded:
            continue
        new_offset = len(data)
        data.extend(encoded)
        struct.pack_into('<I', data, header + 4, new_offset)
        struct.pack_into('<II', data, header + 16, len(encoded), len(encoded))
        path.write_bytes(data)
        changed += 1
print('Patched private host executables:', changed)
PY
export PATH="$(dirname "$CROSS"):$PATH"
export LD_LIBRARY_PATH="$BUILD/runtime-i386/root/usr/lib32:$BUILD/toolchain/mips-linux-uclibc-4.3.6-v2/usr/lib"
"${CROSS}gcc" --version
```

The fresh reproduction patched **35** host executables, printed `mips-linux-gcc (Buildroot 2012.05) 4.3.6`, and then rebuilt the 900-byte registration helper with its expected SHA-256. Evidence is retained in `/tmp/h267a-guide-bootstrap-runtime/guide-bootstrap-verification.json`. A second run in the same location can report zero patches because the path already matches; that does not replace the initial fresh-extraction evidence. After verifying this step, continue with kernel preparation in section 8 and the private driver build in section 9.

## Appendix G. Reproduce the tested pre-flash RAM startup

This optional test belongs **before the first persistent write**, while the OEM `mt7603eap` and original `mt7612e_ap` are running. Do not run it again on an already active replacement-driver session. It uses the private files built in appendix E, with the same credentials read dynamically from the H267A GUI DB.

The tested RAM variant differs from the persistent script only in staged file/lock paths and leaving `eth0` down at successful startup. That isolation permits initial staging over the temporary inter-router cable without creating a loop when the wireless uplink is added. The main PC stays directly wired upstream. Before the eventual persistent boot, remove that inter-router cable physically because persistent startup restores all LAN ports.

Generate the exact tested RAM variant from the fork without editing its source:

```sh
python3 - "$HOME/h267a-work/source/h267a/wireless-bridge.sh" \
  "$BUILD/h267a-generic-gui-runtime.sh" <<'PY'
from pathlib import Path
import sys
source, output = map(Path, sys.argv[1:])
script = source.read_text()
replacements = {
    '/etc/h267a-wireless/mt7603.dat': '/tmp/h267a-apcli-final.dat',
    '/etc/h267a-wireless/mt7612.dat': '/tmp/h267a-5g-final.dat',
    '/lib/modules/mt7603-apcli.ko': '/tmp/h267a-direct.ko',
    '/usr/sbin/h267a-register-wlan2': '/tmp/h267a-register-wlan2-run',
    '/tmp/h267a-wireless-bridge.lock': '/tmp/h267a-generic-gui.lock',
}
for original, replacement in replacements.items():
    assert original in script
    script = script.replace(original, replacement)
original = 'brctl addif br0 wlan5g0\nifconfig eth0 up\nbrctl addif br0 eth0\nping'
replacement = 'brctl addif br0 wlan5g0\n# Leave the cabled uplink disabled during this RAM-only validation.\nping'
assert script.count(original) == 1
script = script.replace(original, replacement)
with output.open('x') as stream:
    stream.write(script)
PY
```

This transformation was checked byte for byte against the natively tested 9,202-byte RAM script, SHA-256 `496c6428bff7d5b3225f4c42d85c8b912ac44e1783494425d826ba1c557f806e`. If a future source revision changes the script, revalidate the transformation rather than deleting its assertions.

Transfer these files individually with appendix D, verifying each complete RAM read-back before copying it to its final RAM staging path:

| Local private input | H267A RAM path |
|---|---|
| `BUILD/mt7603-apcli-1.ko` | `/tmp/h267a-direct.ko` |
| `BUILD/h267a-register-wlan2` | `/tmp/h267a-register-wlan2-run` |
| `BUILD/firmware/bridge-rootfs/etc/h267a-wireless/mt7603.dat` | `/tmp/h267a-apcli-final.dat` |
| `BUILD/firmware/bridge-rootfs/etc/h267a-wireless/mt7612.dat` | `/tmp/h267a-5g-final.dat` |
| `BUILD/h267a-generic-gui-runtime.sh` | `/tmp/h267a-generic-gui-runtime.sh` |

For each module/profile/script, use `test ! -e DESTINATION && cp /var/tmp/h267a-transfer.bin DESTINATION` with the exact destination from the table. For the executable registration helper, preserve executable mode using the same pattern as the receiver:

```sh
test ! -e /tmp/h267a-register-wlan2-run && \
  cp /tmp/h267a-hexreader /tmp/h267a-register-wlan2-run && \
  cat /var/tmp/h267a-transfer.bin > /tmp/h267a-register-wlan2-run
```

After checking each staged file against the local input, remove **only** the completed receiver output with `/bin/busybox rm -f /var/tmp/h267a-transfer.bin`, then launch a fresh one-shot receiver for the next file. Its exclusive-create behavior deliberately refuses a leftover output. If a staging destination already exists, stop and identify the prior test state instead of silently overwriting a running test's files.

With all five files present and verified, check shell syntax and launch the exact tested detached form in the H267A root shell:

```sh
/bin/sh -n /tmp/h267a-generic-gui-runtime.sh
(trap '' HUP; . /tmp/h267a-generic-gui-runtime.sh) > /tmp/h267a-generic-gui.log 2>&1 &
echo $! > /tmp/h267a-generic-gui.pid
```

Allow startup to finish, then check `/tmp/h267a-generic-gui.log` for `H267A_WIRELESS_BRIDGE_READY`, `wlan2` association, radio/bridge membership and gateway/Internet reachability. Do not dump profiles or GUI DB exports to the log. Confirm the PC's upstream Internet path is intact. In this RAM variant, the inter-router `eth0` path remains disabled; prove the wireless path works, physically unplug that cable, then proceed with the verified image transfer/OEM write in section 13. The persistent script restores all four LAN ports on boot.
