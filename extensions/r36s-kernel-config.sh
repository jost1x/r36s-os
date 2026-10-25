#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0

# The R36S Panel 4 DTS binds to the R36S mode in the NV3051D driver.
# The stock Rockchip64 kernel config does not enable this driver.
function custom_kernel_config__r36s_required_drivers() {
	opts_m+=(
		CONFIG_DRM_PANEL_NEWVISION_NV3051D
		CONFIG_JOYSTICK_ADC
		CONFIG_IIO_MUX
	)
}

# Keep the pstore RAM backend built into the kernel. The R36S DTB reserves
# the same 960 KiB region used by the inspected ArkOS DTB for ramoops.
function custom_kernel_config__r36s_pstore() {
	opts_y+=(
		CONFIG_PSTORE
		CONFIG_PSTORE_CONSOLE
		CONFIG_PSTORE_RAM
	)
}
