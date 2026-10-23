#!/bin/sh
# Collect a read-only hardware/software snapshot on a booted R36S Armbian system.
# The only writes are the report files in the selected output directory.
set -u
umask 077

stamp=$(date -u +%Y%m%dT%H%M%SZ 2>/dev/null || echo unknown-time)
out=${1:-"/root/r36s-diagnostics-$stamp"}
if ! mkdir -p "$out"; then
    printf 'Cannot create report directory: %s\n' "$out" >&2
    exit 1
fi
report="$out/report.md"
if ! : > "$report"; then
    printf 'Cannot write report: %s\n' "$report" >&2
    exit 1
fi

section() {
    printf '\n## %s\n\n' "$1" >> "$report"
}

run() {
    command -v "$1" >/dev/null 2>&1 || {
        printf '[command not installed: %s]\n' "$1" >> "$report"
        return
    }
    "$@" >> "$report" 2>&1 || printf '[command exited %s]\n' "$?" >> "$report"
}

read_path() {
    path=$1
    [ -r "$path" ] || return
    printf '%s: ' "$path" >> "$report"
    cat "$path" >> "$report" 2>/dev/null || printf '[read failed]\n' >> "$report"
}

section 'Collection metadata'
printf 'UTC: ' >> "$report"
date -u >> "$report" 2>&1
printf 'Hostname: ' >> "$report"
hostname >> "$report" 2>&1 || true
printf 'Report directory: %s\n' "$out" >> "$report"

section 'System and root filesystem'
run uname -a
for path in /proc/device-tree/model /proc/device-tree/compatible; do
    if [ -r "$path" ]; then
        printf '%s: ' "$path" >> "$report"
        tr '\000' '\n' < "$path" >> "$report" 2>/dev/null || printf '[read failed]\n' >> "$report"
    fi
done
run findmnt /
read_path /etc/os-release
run uptime
run free -h
run lsblk -o NAME,MODEL,SIZE,TYPE,FSTYPE,MOUNTPOINTS

section 'Boot arguments and kernel messages'
read_path /proc/cmdline
run dmesg

section 'Display'
for path in /sys/class/drm/card*-*/status /sys/class/drm/card*-*/modes /sys/class/graphics/fb*/name /sys/class/graphics/fb*/virtual_size; do
    [ -e "$path" ] && read_path "$path"
done
run sh -c 'ls -l /dev/dri /dev/fb* 2>&1'

section 'CPU frequency and thermal zones'
for path in /sys/devices/system/cpu/cpufreq/policy*/*; do
    case "${path##*/}" in
        scaling_available_frequencies|scaling_cur_freq|scaling_governor|scaling_min_freq|scaling_max_freq|cpuinfo_cur_freq|cpuinfo_min_freq|cpuinfo_max_freq)
            read_path "$path" ;;
    esac
done
for zone in /sys/class/thermal/thermal_zone*; do
    [ -d "$zone" ] || continue
    read_path "$zone/type"
    read_path "$zone/temp"
done

section 'Regulators'
for regulator in /sys/class/regulator/regulator*; do
    [ -d "$regulator" ] || continue
    printf '\n[%s]\n' "${regulator##*/}" >> "$report"
    for attr in name regulator_name state status microvolts min_microvolts max_microvolts; do
        read_path "$regulator/$attr"
    done
done

section 'Power supplies'
for supply in /sys/class/power_supply/*; do
    [ -d "$supply" ] || continue
    printf '\n[%s]\n' "${supply##*/}" >> "$report"
    for attr in type status health present online capacity voltage_now current_now current_max charge_now charge_full charge_full_design temp; do
        read_path "$supply/$attr"
    done
done

section 'Input devices'
if [ -r /proc/bus/input/devices ]; then
    cat /proc/bus/input/devices >> "$report"
else
    printf '[not available]\n' >> "$report"
fi
run sh -c 'ls -l /dev/input /dev/snd 2>&1'
run lsmod
run sh -c 'command -v evtest || echo "evtest not installed"'

section 'Audio'
run aplay -l
run amixer -c 0 scontents
run sh -c 'ls -l /dev/snd 2>&1'

section 'MMC and block devices'
for path in /sys/block/mmcblk*/size /sys/block/mmcblk*/device/name /sys/block/mmcblk*/device/type /sys/block/mmcblk*/device/cid /sys/block/mmcblk*/queue/logical_block_size; do
    [ -e "$path" ] && read_path "$path"
done
run sh -c 'for f in /sys/bus/mmc/devices/*/uevent; do [ -r "$f" ] && { echo "--- $f"; cat "$f"; }; done'

section 'Resultado'
printf 'Informe generado en `%s`.\n' "$report" >> "$report"
printf 'Report written to %s\n' "$report"
printf 'Diagnostic data may contain device identifiers and kernel logs; review before sharing.\n'
