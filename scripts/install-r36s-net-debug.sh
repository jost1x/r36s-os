#!/bin/sh
# Install the automatic network diagnostic collector on a mounted Armbian rootfs.
set -eu

if [ "$(id -u)" -ne 0 ]; then
	printf 'Run this installer as root (for example with pkexec).\n' >&2
	exit 1
fi
if [ "$#" -ne 1 ]; then
	printf 'Usage: %s MOUNTED_ROOTFS\n' "$0" >&2
	exit 2
fi

root=$(readlink -f "$1")
if [ ! -f "$root/etc/armbian-release" ] || [ ! -d "$root/etc/systemd/system" ]; then
	printf 'Not an Armbian root filesystem: %s\n' "$root" >&2
	exit 1
fi
if ! mountpoint -q "$root"; then
	printf 'Rootfs path is not a mountpoint: %s\n' "$root" >&2
	exit 1
fi

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
install -D -o root -g root -m 0755 "$script_dir/collect-r36s-net-debug.sh" "$root/usr/local/sbin/r36s-net-debug"
install -D -o root -g root -m 0644 "$script_dir/r36s-net-debug.service" "$root/etc/systemd/system/r36s-net-debug.service"
mkdir -p "$root/etc/systemd/system/multi-user.target.wants"
ln -sfn ../r36s-net-debug.service "$root/etc/systemd/system/multi-user.target.wants/r36s-net-debug.service"
sync
printf 'Installed automatic Wi-Fi diagnostics on %s. The next boot writes r36s-net-debug.txt to the FAT boot partition (or /var/log if it is unavailable).\n' "$root"
