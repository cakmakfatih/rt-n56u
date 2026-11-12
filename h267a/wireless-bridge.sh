#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-only
# Remove the inter-router Ethernet cable before enabling wireless bridging.
set -e
PATH=/sbin:/bin:/usr/bin:/usr/sbin
export PATH
mkdir /tmp/h267a-wireless-bridge.lock || exit 0
radio_changed=0
gui_dump_active=0
bridge_has() {
    bridge_state="$(brctl show br0)"
    case "$bridge_state" in *"$1"*) return 0;; *) return 1;; esac
}
module_loaded() {
    while read -r module_name module_fields; do
        if [ "$module_name" = "$1" ]; then return 0; fi
    done < /proc/modules
    return 1
}
valid_mac() {
    [ "${#1}" -eq 17 ] || return 1
    case "$1" in ''|*[!0-9a-fA-F:]*) return 1;; esac
    local IFS=:
    set -- $1
    [ "$#" -eq 6 ] || return 1
    for mac_octet in "$@"; do [ "${#mac_octet}" -eq 2 ] || return 1; done
}
valid_ipv4() {
    case "$1" in ''|.*|*.|*..*|*[!0-9.]*) return 1;; esac
    local IFS=.
    set -- $1
    [ "$#" -eq 4 ] || return 1
    for ipv4_octet in "$@"; do
        [ -n "$ipv4_octet" ] && [ "$ipv4_octet" -le 255 ] 2>/dev/null || return 1
    done
}
read_interface_mac() {
    while read -r link_kind link_mac link_rest; do
        if [ "$link_kind" = link/ether ]; then
            valid_mac "$link_mac" || return 1
            printf '%s\n' "$link_mac"
            return 0
        fi
    done
    return 1
}
read_bridge_ipv4() {
    while read -r address_kind address_cidr address_rest; do
        if [ "$address_kind" = inet ]; then
            bridge_address=${address_cidr%/*}
            valid_ipv4 "$bridge_address" || return 1
            printf '%s\n' "$bridge_address"
            return 0
        fi
    done
    return 1
}
read_bridge_gateway() {
    while read -r route_kind route_fields; do
        [ "$route_kind" = default ] || continue
        route_gateway= route_device= route_previous=
        for route_field in $route_fields; do
            case "$route_previous" in
                via) route_gateway=$route_field;;
                dev) route_device=$route_field;;
            esac
            route_previous=$route_field
        done
        if [ "$route_device" = br0 ] && valid_ipv4 "$route_gateway"; then
            printf '%s\n' "$route_gateway"
            return 0
        fi
    done
    return 1
}
decode_xml() {
    local xml_remaining="$1" xml_decoded= xml_prefix
    while [ -n "$xml_remaining" ]; do
        case "$xml_remaining" in
            *'&'*)
                xml_prefix=${xml_remaining%%&*}
                xml_decoded=$xml_decoded$xml_prefix
                xml_remaining=${xml_remaining#*&}
                case "$xml_remaining" in
                    amp\;*) xml_decoded="${xml_decoded}&"; xml_remaining=${xml_remaining#amp;};;
                    quot\;*) xml_decoded="${xml_decoded}\""; xml_remaining=${xml_remaining#quot;};;
                    lt\;*) xml_decoded="${xml_decoded}<"; xml_remaining=${xml_remaining#lt;};;
                    gt\;*) xml_decoded="${xml_decoded}>"; xml_remaining=${xml_remaining#gt;};;
                    apos\;*) xml_decoded="${xml_decoded}'"; xml_remaining=${xml_remaining#apos;};;
                    *) xml_decoded="${xml_decoded}&";;
                esac;;
            *) xml_decoded=$xml_decoded$xml_remaining; xml_remaining=;;
        esac
    done
    printf '%s' "$xml_decoded"
}
read_db_field() {
    local db_field="$1" db_row=0 db_line db_value
    while IFS= read -r db_line; do
        case "$db_line" in
            *'<Row No="0">'*) db_row=1;;
            *'<Row '*|*'</Row>'*) db_row=0;;
        esac
        if [ "$db_row" = 1 ]; then
            case "$db_line" in
                *"<DM name=\"$db_field\" val=\""*)
                    db_value=${db_line#*' val="'}
                    db_value=${db_value%%'"'*}
                    decode_xml "$db_value"
                    return 0;;
            esac
        fi
    done
    return 1
}
cleanup_gui_dump() {
    if [ "$gui_dump_active" = 1 ]; then
        /bin/busybox rm -f /var/tmp/dbtable
        gui_dump_active=0
    fi
}
render_profile() {
    while IFS= read -r profile_line; do
        case "$profile_line" in
            SSID1=*|ApCliSsid=*) printf '%s=%s\n' "${profile_line%%=*}" "$bridge_ssid";;
            WPAPSK1=*|ApCliWPAPSK=*) printf '%s=%s\n' "${profile_line%%=*}" "$bridge_key";;
            ApCliBssid=*) printf '%s\n' 'ApCliBssid=00:00:00:00:00:00';;
            HideSSID=*) printf '%s\n' 'HideSSID=0';;
            *) printf '%s\n' "$profile_line";;
        esac
    done < "$1" > "$2"
}
restore_stock() {
    exit_status=$?
    trap - 0
    set +e
    cleanup_gui_dump
    if [ "$radio_changed" = 1 ]; then
        ifconfig wlan2 down
        if bridge_has wlan2; then brctl delif br0 wlan2; fi
        if ! bridge_has wlan2; then
            ifconfig eth0 up
            if ! bridge_has eth0; then brctl addif br0 eth0; fi
        fi
        ifconfig wlan5g0 down
        if bridge_has wlan5g0; then brctl delif br0 wlan5g0; fi
        ifconfig wlan0 down
        if bridge_has wlan0; then brctl delif br0 wlan0; fi
        if module_loaded mt7612e_ap; then rmmod mt7612e_ap; fi
        if module_loaded mt7603e_ap; then rmmod mt7603e_ap; fi
        cp /tmp/h267a-stock-MT7612E.dat /var/tmp/MT7612E.dat
        if ! module_loaded mt7603eap; then insmod /lib/modules/mt7603eap.ko mac="$stock24_mac"; fi
        if ! module_loaded mt7612e_ap; then insmod /lib/modules/mt7612e_ap.ko mac="$stock5_mac"; fi
        ifconfig wlan0 up
        if ! bridge_has wlan0; then brctl addif br0 wlan0; fi
        ifconfig wlan5g0 up
        if ! bridge_has wlan5g0; then brctl addif br0 wlan5g0; fi
        ifconfig eth0 up
        if ! bridge_has eth0; then brctl addif br0 eth0; fi
        echo H267A_STOCK_RESTORED
    fi
    exit "$exit_status"
}
trap restore_stock 0

ready=0
for attempt in 1 2 3 4 5 6 7 8 9 10 11 12; do
    if module_loaded mt7603eap && module_loaded mt7612e_ap &&
       /bin/ip link show dev br0 >/dev/null 2>&1 &&
       /bin/ip link show dev wlan0 >/dev/null 2>&1 &&
       /bin/ip link show dev wlan5g0 >/dev/null 2>&1 &&
       [ -s /var/tmp/MT7612E.dat ] && [ -s /var/tmp/MT7592.dat ]; then
        ready=1
        break
    fi
    ping -c 11 127.0.0.1 >/dev/null 2>&1 || true
done
[ "$ready" = 1 ]
[ -s /etc/h267a-wireless/mt7603.dat ]
[ -s /etc/h267a-wireless/mt7612.dat ]
[ -x /usr/sbin/h267a-register-wlan2 ]
[ -s /lib/modules/mt7603-apcli.ko ]
stock24_mac=$(/bin/ip link show dev wlan0 | read_interface_mac)
stock5_mac=$(/bin/ip link show dev wlan5g0 | read_interface_mac)
bridge_mac=$(/bin/ip link show dev br0 | read_interface_mac)
bridge_ipv4=$(/bin/ip -4 addr show dev br0 | read_bridge_ipv4)
bridge_gateway=$(/bin/ip -4 route show default | read_bridge_gateway) || bridge_gateway=
if [ -z "$bridge_gateway" ]; then bridge_gateway="${bridge_ipv4%.*}.1"; fi
valid_ipv4 "$bridge_gateway"
umask 077
# DB pf exports current unmasked GUI values; the radio .dat file is a factory template.
gui_dump_active=1
/bin/busybox rm -f /var/tmp/dbtable
sendcmd 1 DB pf WLANCfg >/dev/null 2>&1
bridge_ssid=$(read_db_field ESSID < /var/tmp/dbtable)
cleanup_gui_dump
gui_dump_active=1
sendcmd 1 DB pf WLANPSK >/dev/null 2>&1
bridge_key=$(read_db_field KeyPassphrase < /var/tmp/dbtable) || bridge_key=
if [ -z "$bridge_key" ]; then
    bridge_key=$(read_db_field PreSharedKey < /var/tmp/dbtable) || bridge_key=
fi
cleanup_gui_dump
if [ "${#bridge_ssid}" -lt 1 ] || [ "${#bridge_ssid}" -gt 32 ]; then exit 1; fi
if [ "${#bridge_key}" -lt 8 ] || [ "${#bridge_key}" -gt 64 ]; then exit 1; fi
if [ "${#bridge_key}" = 64 ]; then
    case "$bridge_key" in *[!0-9a-fA-F]*) exit 1;; esac
fi
cp /var/tmp/MT7612E.dat /tmp/h267a-stock-MT7612E.dat
render_profile /etc/h267a-wireless/mt7603.dat /tmp/h267a-apcli-test.dat

radio_changed=1
ifconfig wlan5g0 down
if bridge_has wlan5g0; then brctl delif br0 wlan5g0; fi
ifconfig wlan0 down
if bridge_has wlan0; then brctl delif br0 wlan0; fi
rmmod mt7612e_ap
rmmod mt7603eap
insmod /lib/modules/mt7603-apcli.ko mac="$stock24_mac"
ifconfig wlan0 up
iwpriv wlan0 set Debug=2
/usr/sbin/h267a-register-wlan2
ifconfig wlan2 up
iwpriv wlan2 set ApCliAutoConnect=1
brctl addif br0 wlan0
ping -c 11 127.0.0.1 >/dev/null 2>&1 || true

if bridge_has eth0; then brctl delif br0 eth0; fi
ifconfig eth0 down
brctl addif br0 wlan2
/bin/ip route replace default via "$bridge_gateway" dev br0
echo 1 > /proc/sys/net/ipv4/conf/all/arp_ignore
echo 1 > /proc/sys/net/ipv4/conf/br0/arp_ignore
echo 1 > /proc/sys/net/ipv4/conf/br0/arp_notify
ifconfig br0 hw ether "$bridge_mac"

connected=0
for attempt in 1 2 3 4 5 6; do
    if ping -c 2 "$bridge_gateway"; then connected=1; break; fi
    ping -c 6 127.0.0.1 >/dev/null 2>&1 || true
done
[ "$connected" = 1 ]
render_profile /etc/h267a-wireless/mt7612.dat /var/tmp/MT7612E.dat
insmod /lib/modules/mt7612e_ap.ko mac="$stock5_mac"
ifconfig wlan5g0 up
iwpriv wlan5g0 set WscConfMode=0
brctl addif br0 wlan5g0
ifconfig eth0 up
brctl addif br0 eth0
ping -c 2 "$bridge_gateway"
trap - 0
echo H267A_WIRELESS_BRIDGE_READY

# The donor's periodic rescan requires MAC-repeater mode, which stays disabled.
while :; do
    ping -c 31 127.0.0.1 >/dev/null 2>&1 || true
    if ! ping -c 2 "$bridge_gateway" >/dev/null 2>&1; then
        iwpriv wlan2 set ApCliAutoConnect=1 || true
    fi
done
