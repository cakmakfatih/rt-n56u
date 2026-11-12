# ZTE ZXHN H267A wireless bridge

Turn a ZTE ZXHN H267A running **V1.0.1_TRT29** into a wireless extender: it receives an existing network over **2.4 GHz Wi-Fi** and shares that connection through its LAN bridge and 2.4/5 GHz access points.

This fork contains the modified MT7603 driver, build tools, startup script, and installation guide used for the H267A port.

## What it does

- Connects to a 2.4 GHz WPA2-PSK/AES network using APCLI.
- Uses the upstream network's SSID and Wi-Fi password for both H267A access points, keeping the original 5 GHz driver.
- Includes all four LAN interfaces in the bridge for Ethernet clients.
- Starts the bridge automatically after reboot and fixes the driver unload stall caused by renaming the APCLI interface after registration.

The 5 GHz radio serves clients; the wireless uplink uses 2.4 GHz. Sharing an SSID does not provide mesh or coordinated roaming.

## Installation overview

Follow the **[complete installation and network-change guide](docs/H267A_TRT29_wireless_bridge_guide.md)** for exact commands, prerequisites, compatibility checks, and recovery limits. The tested device was **H267A hardware V1.0.8 with V1.0.1_TRT29**; other revisions need their own compatibility checks.

```sh
git clone --branch main --single-branch https://github.com/cakmakfatih/rt-n56u.git
cd rt-n56u
```

1. **Prepare and back up the H267A.** Preserve its original firmware and configuration, establish the guide's restricted local diagnostic access, and extract this unit's own calibration. Keep the working PC connected directly to the upstream router.
2. **Build the driver and helper.** Prepare the documented kernel/toolchain environment and use the [H267A tools](h267a/) with this unit's private EEPROM input. Build outputs contain device-specific calibration and must remain private.
3. **Configure and test in RAM.** Give the H267A a free address in the upstream LAN, disable its DHCP server, and save the upstream SSID/key in its Wi-Fi settings. Follow the guide's RAM test before permanent installation. Remove the inter-router Ethernet cable before enabling the complete wireless bridge to avoid a loop.
4. **Install the verified private image.** Package the tested driver/startup with the original TRT29 kernel and 5 GHz driver, complete the image and transfer checks, then use the documented OEM update path. Reboot the H267A and verify automatic startup and client Internet access.

The guide also explains how to change the upstream router, SSID, password, or management subnet later. It includes the tested source revision and the full verification record.

## Verified status

Wireless Internet to a phone, driver load/unload tests, permanent installation, and a separate normal reboot passed on the tested unit. Both AP names and all four LAN bridge members were verified. Internet access from an Ethernet-connected client was also confirmed. Separate phone tests on each band have not yet been validated.

## About this fork and upstream

This repository is a fork of **[hanwckf/rt-n56u](https://github.com/hanwckf/rt-n56u)**, a Padavan-based firmware tree for supported routers. The upstream tree is retained; this fork focuses on the H267A TRT29 driver port and its supporting tools under [`h267a/`](h267a/). The modified driver is under [`mt76x3`](trunk/proprietary/rt_wifi/rtpci/4.1.X.X/mt76x3/).

- [Original repository](https://github.com/hanwckf/rt-n56u)
- [Original README at the fork's base revision](https://github.com/hanwckf/rt-n56u/blob/23387b278a7cf728748af606760758f5d59d1451/README.md)

The H267A procedure preserves its OEM system and uses a device-specific driver build. Generic upstream Padavan firmware images and installation instructions are not the H267A installation path. Existing upstream license and copyright notices are retained.
