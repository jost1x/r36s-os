#!/bin/sh
# Show a startup banner immediately, then print the Wi-Fi address when available.

address=$(ip -4 -o addr show up scope global 2>/dev/null | awk 'NR == 1 { sub(/\/.*/, "", $4); print $4; exit }')

case "${1:---banner}" in
  --banner)
    if [ -n "${address}" ]; then
      printf '\nR36S Hybrid OS\nIP: %s\nSSH: ssh r36s@%s\n\n' "${address}" "${address}"
    else
      printf '\nR36S Hybrid OS\nWi-Fi: conectando...\n\n'
    fi
    ;;
  --check)
    [ -n "${address}" ] || exit 0
    printf '\nWi-Fi conectado\nIP: %s\nSSH: ssh r36s@%s\n\n' "${address}" "${address}"
    systemctl stop r36s-show-ip.timer 2>/dev/null || true
    ;;
  *)
    echo "Usage: $0 [--banner|--check]" >&2
    exit 2
    ;;
esac
