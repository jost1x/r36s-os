#!/bin/sh
# Collect boot, Wi-Fi, driver and DHCP diagnostics without reading Netplan secrets.
set -u
umask 077

report_name=r36s-net-debug.txt
if command -v mountpoint >/dev/null 2>&1 && mountpoint -q /boot/firmware && [ -w /boot/firmware ]; then
	output="/boot/firmware/$report_name"
elif command -v mountpoint >/dev/null 2>&1 && mountpoint -q /boot && [ -w /boot ]; then
	output="/boot/$report_name"
else
	output="/var/log/$report_name"
fi

if ! : > "$output"; then
	printf 'Cannot write diagnostic report: %s\n' "$output" >&2
	exit 1
fi
exec >> "$output" 2>&1

section() { printf '\n\n========== %s ==========\n' "$1"; }
run() {
	command -v "$1" >/dev/null 2>&1 || { printf '[not installed: %s]\n' "$1"; return 0; }
	"$@" || printf '[exit status: %s]\n' "$?"
}

section 'Report metadata'
date -u
printf 'hostname: '; hostname 2>/dev/null || true
printf 'boot_id: '; cat /proc/sys/kernel/random/boot_id 2>/dev/null || true
printf 'uptime: '; cat /proc/uptime 2>/dev/null || true
printf 'output: %s\n' "$output"

section 'Kernel, board and boot arguments'
run uname -a
for path in /proc/device-tree/model /proc/cmdline; do
	if [ -r "$path" ]; then printf '\n--- %s ---\n' "$path"; tr '\000' '\n' < "$path"; fi
done

section 'Network interfaces and addresses'
run ip -details link show
run ip -brief address
run ip route show table all
run ip neigh show
run networkctl list --all
run networkctl status --all

section 'Wireless interfaces and radio state'
run iw dev
run iw phy
run rfkill list all
run lsusb
run lsmod
for iface in /sys/class/net/*; do
	[ -e "$iface" ] || continue
	name=${iface##*/}
	printf '\n--- %s ---\n' "$name"
	for path in "$iface/operstate" "$iface/address" "$iface/phy80211/name" "$iface/device/modalias" "$iface/device/uevent"; do
		if [ -r "$path" ]; then printf '%s: ' "$path"; tr '\000' '\n' < "$path"; fi
	done
	if [ -L "$iface/device/driver" ]; then printf 'driver: %s\n' "$(readlink -f "$iface/device/driver")"; fi
done

section 'Network-related systemd units'
run systemctl --failed --no-legend
run systemctl list-units --all --no-legend 'netplan-wpa*'
run systemctl status --no-pager systemd-networkd.service systemd-networkd-wait-online.service wpa_supplicant.service

section 'Network and Wi-Fi journal for this boot'
run journalctl -b --no-pager -o short-monotonic -u systemd-networkd.service -u systemd-networkd-wait-online.service -u wpa_supplicant.service
if command -v journalctl >/dev/null 2>&1; then
	journalctl -b --no-pager -o short-monotonic 2>&1 | grep -Ei 'netplan|wpa|wlan|wifi|80211|rtl8|firmware|dhcp|networkd' || true
fi

section 'Kernel messages related to Wi-Fi, USB and firmware'
if command -v dmesg >/dev/null 2>&1; then
	dmesg 2>&1 | grep -Ei 'wlan|wifi|80211|rtl8|8188|usb|firmware|cfg80211|mac80211|netdev|failed|error' || true
fi

section 'Installed driver and firmware files'
for path in /lib/modules/"$(uname -r)"/kernel/drivers/net/wireless/realtek/rtl8xxxu/rtl8xxxu.ko* /lib/firmware/rtlwifi/rtl8188eufw.bin; do
	[ -e "$path" ] && ls -l "$path"
done
run modinfo rtl8xxxu

section 'End of report'
date -u
sync
