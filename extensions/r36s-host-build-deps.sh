#!/usr/bin/env bash
# Add the Python modules required by mainline U-Boot binman/pylibfdt builds.
function add_host_dependencies__r36s_uboot_python() {
	EXTRA_BUILD_DEPS+=("python3-pyelftools" "python3-setuptools")
}

# Armbian's Debian Trixie container has QEMU registrations in systemd-binfmt's
# /usr/lib/binfmt.d format, while this Armbian revision calls update-binfmts.
# Mount a small compatibility shim only into the build container.
function host_pre_docker_launch__r36s_binfmt_compat() {
	DOCKER_EXTRA_ARGS+=("--mount" "type=bind,source=${SRC}/userpatches/extensions/r36s-update-binfmts,target=/usr/sbin/update-binfmts")
}
