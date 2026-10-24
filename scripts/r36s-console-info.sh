#!/bin/sh
# Wait briefly for DHCP, then print the R36S address to the built-in console.

address=""
attempt=0
while [ "${attempt}" -lt 60 ]; do
	address=$(ip -4 -o addr show up scope global 2>/dev/null | awk 'NR == 1 { sub(/\/.*/, "", $4); print $4; exit }')
	[ -n "${address}" ] && break
	attempt=$((attempt + 1))
	sleep 1
done

if [ -n "${address}" ]; then
	printf '\nR36S Hybrid OS\nIP: %s\nSSH: ssh r36s@%s\n\n' "${address}" "${address}"
else
	printf '\nR36S Hybrid OS\nSin IP después de 60 s. Revisa la conexión Wi-Fi.\n\n'
fi
