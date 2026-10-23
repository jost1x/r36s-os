#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
ARMBIAN_REF="$(tr -d '[:space:]' < "${ROOT_DIR}/config/armbian/ARMBIAN_COMMIT")"
ARMBIAN_BUILD_IMAGE="ghcr.io/armbian/docker-armbian-build@sha256:bffb2b34becdefe1d13872a02455f5044c9ba200b8543a2e7fb19fbf33e9009a"
# Armbian's pinned build framework normally pulls this mutable tag as the base
# for its build container. Keep the tag expected by that framework, but ensure
# every pull and Dockerfile build resolves to the reviewed immutable digest.
ARMBIAN_BUILD_BASE_TAG="ghcr.io/armbian/docker-armbian-build:armbian-debian-trixie-latest"
ARMBIAN_BUILD_BASE_IMAGE="ghcr.io/armbian/docker-armbian-build@sha256:bffb2b34becdefe1d13872a02455f5044c9ba200b8543a2e7fb19fbf33e9009a"
WORK_DIR="${ROOT_DIR}/work/armbian-build"
ACTION="${1:-build}"
BOARD_SRC="${ROOT_DIR}/config/armbian/boards/r36s.wip"
BOARD_DST="${WORK_DIR}/userpatches/config/boards/r36s.wip"
HOST_DEPS_SRC="${ROOT_DIR}/extensions/r36s-host-build-deps.sh"
HOST_DEPS_DST="${WORK_DIR}/userpatches/extensions/r36s-host-build-deps.sh"
BINFMT_COMPAT_SRC="${ROOT_DIR}/extensions/r36s-update-binfmts"
BINFMT_COMPAT_DST="${WORK_DIR}/userpatches/extensions/r36s-update-binfmts"
KERNEL_PATCH_SRC="${ROOT_DIR}/config/armbian/patches/kernel/r36s-6.18/0001-r36s-panel-and-device-tree.patch"
KERNEL_PATCH_DST="${WORK_DIR}/userpatches/kernel/r36s-6.18/0001-r36s-panel-and-device-tree.patch"
UBOOT_PATCH_SRC="${ROOT_DIR}/config/armbian/patches/u-boot/r36s/0001-r36s-boot-from-sdmmc.patch"
UBOOT_PATCH_DST="${WORK_DIR}/userpatches/u-boot/r36s/0001-r36s-boot-from-sdmmc.patch"
KERNEL_CONFIG_EXT_SRC="${ROOT_DIR}/extensions/r36s-kernel-config.sh"
KERNEL_CONFIG_EXT_DST="${WORK_DIR}/userpatches/extensions/r36s-kernel-config.sh"
DIAGNOSTICS_SRC="${ROOT_DIR}/scripts/collect-r36s-diagnostics.sh"
DIAGNOSTICS_DST="${WORK_DIR}/userpatches/scripts/collect-r36s-diagnostics.sh"

usage() {
	cat <<'EOF'
Usage: scripts/build-armbian.sh [prepare|build]

  prepare  Clone/check out the pinned Armbian tree and install the local WIP
           board definition. Does not compile anything.
  build    Do the same preparation, then run a minimal Debian Bookworm image
           build through Armbian's compile.sh.

The build tree is isolated under ./work/armbian-build. No storage device is
written by this script.
EOF
}

case "${ACTION}" in
	prepare|build) ;;
	-h|--help|help) usage; exit 0 ;;
	*) usage >&2; exit 2 ;;
esac

if [[ ! -d "${WORK_DIR}/.git" ]]; then
	if [[ -e "${WORK_DIR}" ]]; then
		echo "Refusing to use non-git work directory: ${WORK_DIR}" >&2
		exit 1
	fi
	mkdir -p "$(dirname -- "${WORK_DIR}")"
	git clone https://github.com/armbian/build.git "${WORK_DIR}"
fi

if [[ -n "$(git -C "${WORK_DIR}" status --porcelain --untracked-files=no)" ]]; then
	echo "Armbian checkout has tracked changes; refusing to reset it." >&2
	exit 1
fi

git -C "${WORK_DIR}" fetch --quiet origin "${ARMBIAN_REF}"
git -C "${WORK_DIR}" checkout --quiet --detach "${ARMBIAN_REF}"

mkdir -p "$(dirname -- "${UBOOT_PATCH_DST}")"
if [[ -e "${UBOOT_PATCH_DST}" ]] && ! cmp -s "${UBOOT_PATCH_SRC}" "${UBOOT_PATCH_DST}"; then
	echo "Existing R36S U-Boot patch differs from this project: ${UBOOT_PATCH_DST}" >&2
	echo "Review it manually; the script will not overwrite it." >&2
	exit 1
fi
if [[ ! -e "${UBOOT_PATCH_DST}" ]]; then
	if [[ -w "$(dirname -- "${UBOOT_PATCH_DST}")" ]]; then
		install -m 0644 "${UBOOT_PATCH_SRC}" "${UBOOT_PATCH_DST}"
	else
		docker run --rm --user 0 \
			-v "${ROOT_DIR}:/r36s:ro" -v "${WORK_DIR}:/armbian" \
			"${ARMBIAN_BUILD_IMAGE}" \
			sh -ec 'install -D -m 0644 "/r36s/config/armbian/patches/u-boot/r36s/0001-r36s-boot-from-sdmmc.patch" "/armbian/userpatches/u-boot/r36s/0001-r36s-boot-from-sdmmc.patch"'
	fi
fi

mkdir -p "$(dirname -- "${BOARD_DST}")"
if [[ -e "${BOARD_DST}" ]] && ! cmp -s "${BOARD_SRC}" "${BOARD_DST}"; then
	echo "Existing board definition differs from this project: ${BOARD_DST}" >&2
	echo "Review it manually; the script will not overwrite it." >&2
	exit 1
fi
install -m 0644 "${BOARD_SRC}" "${BOARD_DST}"

mkdir -p "$(dirname -- "${HOST_DEPS_DST}")"
if [[ -e "${HOST_DEPS_DST}" ]] && ! cmp -s "${HOST_DEPS_SRC}" "${HOST_DEPS_DST}"; then
	echo "Existing host dependency extension differs from this project: ${HOST_DEPS_DST}" >&2
	echo "Review it manually; the script will not overwrite it." >&2
	exit 1
fi
install -m 0644 "${HOST_DEPS_SRC}" "${HOST_DEPS_DST}"

if [[ -e "${BINFMT_COMPAT_DST}" ]] && ! cmp -s "${BINFMT_COMPAT_SRC}" "${BINFMT_COMPAT_DST}"; then
	echo "Existing binfmt compatibility shim differs from this project: ${BINFMT_COMPAT_DST}" >&2
	echo "Review it manually; the script will not overwrite it." >&2
	exit 1
fi
install -m 0755 "${BINFMT_COMPAT_SRC}" "${BINFMT_COMPAT_DST}"

mkdir -p "$(dirname -- "${KERNEL_PATCH_DST}")"
if [[ -e "${KERNEL_PATCH_DST}" ]] && ! cmp -s "${KERNEL_PATCH_SRC}" "${KERNEL_PATCH_DST}"; then
	echo "Existing R36S kernel patch differs from this project: ${KERNEL_PATCH_DST}" >&2
	echo "Review it manually; the script will not overwrite it." >&2
	exit 1
fi
if [[ ! -e "${KERNEL_PATCH_DST}" ]]; then
	if [[ -w "$(dirname -- "${KERNEL_PATCH_DST}")" ]]; then
		install -m 0644 "${KERNEL_PATCH_SRC}" "${KERNEL_PATCH_DST}"
	else
		# Armbian's container may leave userpatches/kernel root-owned on the host.
		docker run --rm --user 0 \
			-v "${ROOT_DIR}:/r36s:ro" -v "${WORK_DIR}:/armbian" \
			"${ARMBIAN_BUILD_IMAGE}" \
			sh -ec 'install -D -m 0644 "/r36s/config/armbian/patches/kernel/r36s-6.18/0001-r36s-panel-and-device-tree.patch" "/armbian/userpatches/kernel/r36s-6.18/0001-r36s-panel-and-device-tree.patch"'
	fi
fi

if [[ -e "${KERNEL_CONFIG_EXT_DST}" ]] && ! cmp -s "${KERNEL_CONFIG_EXT_SRC}" "${KERNEL_CONFIG_EXT_DST}"; then
	echo "Existing kernel config extension differs from this project: ${KERNEL_CONFIG_EXT_DST}" >&2
	echo "Review it manually; the script will not overwrite it." >&2
	exit 1
fi
install -m 0644 "${KERNEL_CONFIG_EXT_SRC}" "${KERNEL_CONFIG_EXT_DST}"

echo "Armbian pinned at $(git -C "${WORK_DIR}" rev-parse HEAD)"
echo "WIP board definition installed at ${BOARD_DST}"
echo "U-Boot build dependencies installed at ${HOST_DEPS_DST}"
echo "Debian Trixie binfmt compatibility shim installed at ${BINFMT_COMPAT_DST}"
echo "R36S Panel 4 kernel patch installed at ${KERNEL_PATCH_DST}"
echo "R36S SD-first U-Boot patch installed at ${UBOOT_PATCH_DST}"
echo "R36S kernel config extension installed at ${KERNEL_CONFIG_EXT_DST}"

mkdir -p "$(dirname -- "${DIAGNOSTICS_DST}")"
if [[ -e "${DIAGNOSTICS_DST}" ]] && ! cmp -s "${DIAGNOSTICS_SRC}" "${DIAGNOSTICS_DST}"; then
	echo "Existing R36S diagnostics script differs from this project: ${DIAGNOSTICS_DST}" >&2
	echo "Review it manually; the script will not overwrite it." >&2
	exit 1
fi
if [[ ! -e "${DIAGNOSTICS_DST}" ]]; then
	if [[ -w "$(dirname -- "${DIAGNOSTICS_DST}")" ]]; then
		install -m 0755 "${DIAGNOSTICS_SRC}" "${DIAGNOSTICS_DST}"
	else
		docker run --rm --user 0 \
			-v "${ROOT_DIR}:/r36s:ro" -v "${WORK_DIR}:/armbian" \
			"${ARMBIAN_BUILD_IMAGE}" \
			sh -ec 'install -D -m 0755 "/r36s/scripts/collect-r36s-diagnostics.sh" "/armbian/userpatches/scripts/collect-r36s-diagnostics.sh"'
	fi
fi
echo "R36S diagnostics script installed at ${DIAGNOSTICS_DST}"
echo "Review docs/armbian-support-survey.md before using the generated image."

if [[ "${ACTION}" == "prepare" ]]; then
	exit 0
fi

cd "${WORK_DIR}"
R36S_REAL_DOCKER="$(command -v docker)"
export R36S_REAL_DOCKER
export R36S_ARMBIAN_BUILD_BASE_TAG="${ARMBIAN_BUILD_BASE_TAG}"
export R36S_ARMBIAN_BUILD_BASE_IMAGE="${ARMBIAN_BUILD_BASE_IMAGE}"
export PATH="${ROOT_DIR}/scripts/docker-compat:${PATH}"

# The framework's cache marker is keyed by a mutable tag. Refresh the local tag
# from the pinned digest before invoking it, so even a valid marker cannot hide
# a different image previously assigned to that tag.
"${R36S_REAL_DOCKER}" pull "${ARMBIAN_BUILD_BASE_IMAGE}"
"${R36S_REAL_DOCKER}" tag "${ARMBIAN_BUILD_BASE_IMAGE}" "${ARMBIAN_BUILD_BASE_TAG}"

binfmt_dir="/proc/sys/fs/binfmt_misc"
binfmt_before=()
if [[ -d "${binfmt_dir}" ]]; then
	mapfile -t binfmt_before < <(find "${binfmt_dir}" -maxdepth 1 -type f -name 'qemu-*' -printf '%f\n' 2>/dev/null | sort)
fi

set +e
./compile.sh \
	PREFER_DOCKER=yes \
	BOARD=r36s \
	BRANCH=current \
	RELEASE=bookworm \
	EXPERT=yes \
	BUILD_MINIMAL=yes \
	BUILD_DESKTOP=no \
	KERNEL_CONFIGURE=no \
	KERNEL_BTF=no
build_status=$?
set -e

# The build registers QEMU binfmt handlers through a privileged container.
# These registrations affect the host kernel, so remove only handlers that
# were absent before this build.
binfmt_after=()
if [[ -d "${binfmt_dir}" ]]; then
	mapfile -t binfmt_after < <(find "${binfmt_dir}" -maxdepth 1 -type f -name 'qemu-*' -printf '%f\n' 2>/dev/null | sort)
fi
binfmt_new=()
for handler in "${binfmt_after[@]}"; do
	if [[ ! " ${binfmt_before[*]} " == *" ${handler} "* ]]; then
		binfmt_new+=("${handler}")
	fi
done

cleanup_status=0
if [[ ${#binfmt_new[@]} -gt 0 ]]; then
	if ! docker run --rm --privileged --ulimit nofile=1048576:1048576 \
		"${ARMBIAN_BUILD_IMAGE}" \
		sh -lc 'mount -t binfmt_misc binfmt_misc /proc/sys/fs/binfmt_misc 2>/dev/null || true; for name in "$@"; do handler="/proc/sys/fs/binfmt_misc/$name"; [ ! -e "$handler" ] || printf "%s\n" "-1" > "$handler"; done' \
		r36s-cleanup "${binfmt_new[@]}"; then
		echo "Failed to remove temporary QEMU binfmt handlers: ${binfmt_new[*]}" >&2
		cleanup_status=1
	fi
fi

if [[ ${build_status} -ne 0 ]]; then
	exit "${build_status}"
fi
exit "${cleanup_status}"
