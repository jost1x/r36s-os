#!/usr/bin/env python3
"""Read-only structural and optional filesystem checks for an Armbian R36S image."""

from __future__ import annotations

import argparse
from io import BytesIO
import hashlib
import shutil
import struct
import subprocess
import sys
import tarfile
import tempfile
import uuid
import zlib
from dataclasses import dataclass
from pathlib import Path

SECTOR_SIZE = 512
UBOOT_LEGACY_MAGIC = 0x27051956
UBOOT_SCRIPT_TYPE = 6
EXT4_MAGIC = 0xEF53
# Armbian's Rockchip installer writes this binary with dd bs=32k seek=1.
UBOOT_IMAGE_OFFSET = 32768


class ImageError(Exception):
    pass


@dataclass(frozen=True)
class Partition:
    index: int
    type_id: int
    start: int
    sectors: int


@dataclass(frozen=True)
class FatEntry:
    name: str
    short_name: str
    attributes: int
    cluster: int
    size: int


class FatVolume:
    def __init__(self, image: Path, partition: Partition):
        self.image = image
        self.offset = partition.start * SECTOR_SIZE
        self.partition_bytes = partition.sectors * SECTOR_SIZE
        with image.open("rb") as stream:
            boot = self._read(stream, self.offset, SECTOR_SIZE)

        if boot[510:512] != b"\x55\xaa":
            raise ImageError("FAT boot sector has no 0x55AA signature")

        self.bytes_per_sector = struct.unpack_from("<H", boot, 11)[0]
        self.sectors_per_cluster = boot[13]
        self.reserved_sectors = struct.unpack_from("<H", boot, 14)[0]
        self.fat_count = boot[16]
        root_entries = struct.unpack_from("<H", boot, 17)[0]
        total16 = struct.unpack_from("<H", boot, 19)[0]
        fat16 = struct.unpack_from("<H", boot, 22)[0]
        total32 = struct.unpack_from("<I", boot, 32)[0]
        fat32 = struct.unpack_from("<I", boot, 36)[0]
        self.root_cluster = struct.unpack_from("<I", boot, 44)[0] & 0x0FFFFFFF

        if self.bytes_per_sector != SECTOR_SIZE:
            raise ImageError(f"Unsupported FAT sector size: {self.bytes_per_sector}")
        if not self.sectors_per_cluster or not self.fat_count:
            raise ImageError("Invalid FAT BPB: zero cluster size or FAT count")

        self.total_sectors = total16 or total32
        self.fat_sectors = fat16 or fat32
        self.root_dir_sectors = (root_entries * 32 + SECTOR_SIZE - 1) // SECTOR_SIZE
        self.data_start_sector = (
            self.reserved_sectors + self.fat_count * self.fat_sectors + self.root_dir_sectors
        )
        data_sectors = self.total_sectors - self.data_start_sector
        if data_sectors <= 0 or self.total_sectors * SECTOR_SIZE > self.partition_bytes:
            raise ImageError("FAT volume size exceeds its partition or has no data area")

        cluster_count = data_sectors // self.sectors_per_cluster
        self.is_fat32 = cluster_count >= 65525
        self.kind = "FAT32" if self.is_fat32 else "FAT16"
        self.fat_offset = self.offset + self.reserved_sectors * SECTOR_SIZE
        self.data_offset = self.offset + self.data_start_sector * SECTOR_SIZE
        self.fixed_root_offset = self.offset + (
            self.reserved_sectors + self.fat_count * self.fat_sectors
        ) * SECTOR_SIZE
        self.root_entry_count = root_entries

    @staticmethod
    def _read(stream, offset: int, size: int) -> bytes:
        stream.seek(offset)
        data = stream.read(size)
        if len(data) != size:
            raise ImageError(f"Unexpected end of image at byte {offset}")
        return data

    def _cluster_chain(self, stream, first: int):
        cluster = first
        seen = set()
        fat_entry_size = 4 if self.is_fat32 else 2
        eoc = 0x0FFFFFF8 if self.is_fat32 else 0xFFF8
        mask = 0x0FFFFFFF if self.is_fat32 else 0xFFFF
        cluster_count = (self.total_sectors - self.data_start_sector) // self.sectors_per_cluster

        while 2 <= cluster < cluster_count + 2:
            if cluster in seen:
                raise ImageError("FAT cluster chain contains a loop")
            seen.add(cluster)
            yield cluster
            raw = self._read(stream, self.fat_offset + cluster * fat_entry_size, fat_entry_size)
            next_cluster = int.from_bytes(raw, "little") & mask
            if next_cluster >= eoc:
                return
            if next_cluster < 2:
                raise ImageError(f"Invalid next cluster value: {next_cluster}")
            cluster = next_cluster
        raise ImageError(f"FAT cluster out of range: {cluster}")

    def _cluster_bytes(self, stream, cluster: int) -> bytes:
        cluster_size = self.sectors_per_cluster * SECTOR_SIZE
        offset = self.data_offset + (cluster - 2) * cluster_size
        return self._read(stream, offset, cluster_size)

    @staticmethod
    def _short_name(entry: bytes) -> str:
        raw = entry[:11]
        if raw[0] == 0x05:
            raw = b"\xE5" + raw[1:]
        base = raw[:8].decode("cp437", errors="replace").rstrip()
        extension = raw[8:11].decode("cp437", errors="replace").rstrip()
        return f"{base}.{extension}" if extension else base

    @staticmethod
    def _long_name_piece(entry: bytes) -> str:
        raw = entry[1:11] + entry[14:26] + entry[28:32]
        return raw.decode("utf-16le", errors="replace").replace("\uffff", "")

    def _directory_entries(self, stream, cluster: int | None = None):
        if cluster is None and not self.is_fat32:
            raw = self._read(stream, self.fixed_root_offset, self.root_entry_count * 32)
        else:
            first = self.root_cluster if cluster is None else cluster
            raw = b"".join(self._cluster_bytes(stream, item) for item in self._cluster_chain(stream, first))

        long_parts: dict[int, str] = {}
        for start in range(0, len(raw), 32):
            entry = raw[start : start + 32]
            if len(entry) < 32 or entry[0] == 0:
                break
            if entry[0] == 0xE5:
                long_parts.clear()
                continue
            attributes = entry[11]
            if attributes == 0x0F:
                ordinal = entry[0] & 0x1F
                if entry[0] & 0x40:
                    long_parts.clear()
                long_parts[ordinal] = self._long_name_piece(entry)
                continue
            if attributes & 0x08:
                long_parts.clear()
                continue

            short_name = self._short_name(entry)
            long_name = "".join(long_parts[index] for index in sorted(long_parts))
            long_name = long_name.split("\0", 1)[0].rstrip()
            long_parts.clear()
            high = struct.unpack_from("<H", entry, 20)[0] if self.is_fat32 else 0
            low = struct.unpack_from("<H", entry, 26)[0]
            first_cluster = (high << 16) | low
            size = struct.unpack_from("<I", entry, 28)[0]
            yield FatEntry(long_name or short_name, short_name, attributes, first_cluster, size)

    def _find(self, stream, directory_cluster: int | None, name: str) -> FatEntry:
        wanted = name.casefold()
        for entry in self._directory_entries(stream, directory_cluster):
            if entry.name.casefold() == wanted or entry.short_name.casefold() == wanted:
                return entry
        raise ImageError(f"FAT path component not found: {name}")

    def read_file(self, path: str) -> bytes:
        components = [item for item in path.replace("\\", "/").split("/") if item]
        if not components or any(item in (".", "..") for item in components):
            raise ImageError(f"Invalid FAT path: {path}")
        with self.image.open("rb") as stream:
            directory_cluster = None
            entry = None
            for index, component in enumerate(components):
                entry = self._find(stream, directory_cluster, component)
                if index < len(components) - 1:
                    if not entry.attributes & 0x10:
                        raise ImageError(f"Not a FAT directory: {component}")
                    directory_cluster = entry.cluster
            assert entry is not None
            if entry.attributes & 0x10:
                raise ImageError(f"FAT path is a directory: {path}")
            if entry.size == 0:
                return b""
            content = b"".join(
                self._cluster_bytes(stream, cluster)
                for cluster in self._cluster_chain(stream, entry.cluster)
            )
            if len(content) < entry.size:
                raise ImageError(f"FAT file has a short cluster chain: {path}")
            return content[: entry.size]


def read_partitions(image: Path) -> list[Partition]:
    with image.open("rb") as stream:
        mbr = FatVolume._read(stream, 0, SECTOR_SIZE)
    if mbr[510:512] != b"\x55\xaa":
        raise ImageError("Image has no MBR signature")
    partitions = []
    for index in range(4):
        entry = mbr[446 + index * 16 : 462 + index * 16]
        type_id = entry[4]
        start, sectors = struct.unpack_from("<II", entry, 8)
        if type_id and sectors:
            partitions.append(Partition(index + 1, type_id, start, sectors))
    if len(partitions) != 2:
        raise ImageError(f"Expected two primary partitions, found {len(partitions)}")
    return partitions


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _ar_member(archive: bytes, wanted: str) -> bytes:
    if not archive.startswith(b"!<arch>\n"):
        raise ImageError("U-Boot package is not a Debian ar archive")
    offset = 8
    while offset + 60 <= len(archive):
        header = archive[offset : offset + 60]
        if header[58:60] != b"`\n":
            raise ImageError("Invalid Debian package ar member header")
        name = header[:16].decode("ascii", errors="replace").strip().rstrip("/")
        size_text = header[48:58].decode("ascii", errors="strict").strip()
        size = int(size_text)
        data_start = offset + 60
        data_end = data_start + size
        if data_end > len(archive):
            raise ImageError(f"Truncated Debian package member: {name}")
        if name == wanted:
            return archive[data_start:data_end]
        offset = data_end + (size & 1)
    raise ImageError(f"Debian package member not found: {wanted}")


def _read_uboot_binary(package_path: Path) -> bytes:
    if not package_path.is_file():
        raise ImageError(f"U-Boot package not found: {package_path}")
    archive = package_path.read_bytes()
    data_tar = _ar_member(archive, "data.tar")
    with tarfile.open(fileobj=BytesIO(data_tar), mode="r:*") as package_data:
        candidates = [
            item
            for item in package_data.getmembers()
            if item.isfile() and item.name.endswith("/u-boot-rockchip.bin")
        ]
        if len(candidates) != 1:
            raise ImageError(f"Expected one packaged u-boot-rockchip.bin, found {len(candidates)}")
        binary = package_data.extractfile(candidates[0])
        if binary is None:
            raise ImageError("Unable to read packaged u-boot-rockchip.bin")
        return binary.read()


def _matches_embedded_uboot(image: Path, boot: Partition, binary: bytes) -> bool:
    end = UBOOT_IMAGE_OFFSET + len(binary)
    if end > boot.start * SECTOR_SIZE:
        return False
    with image.open("rb") as stream:
        embedded = FatVolume._read(stream, UBOOT_IMAGE_OFFSET, len(binary))
    return embedded == binary


def _find_matching_uboot_package(image: Path, boot: Partition, packages_dir: Path) -> Path:
    if not packages_dir.is_dir():
        raise ImageError(f"U-Boot packages directory not found: {packages_dir}")
    packages = sorted(packages_dir.glob("linux-u-boot-r36s-current*.deb"))
    if not packages:
        raise ImageError(f"No R36S U-Boot .deb packages found in {packages_dir}")

    matches = [
        package
        for package in packages
        if _matches_embedded_uboot(image, boot, _read_uboot_binary(package))
    ]
    if not matches:
        raise ImageError(
            f"No package in {packages_dir} matches the U-Boot binary embedded in the image"
        )
    if len(matches) > 1:
        print(
            f"U-Boot package selection: {len(matches)} packages contain the same matching binary; "
            f"using {matches[0].name}"
        )
    else:
        print(f"U-Boot package selection: {matches[0].name} (exact image match)")
    return matches[0]


def _copy_partition(image: Path, partition: Partition, destination: Path) -> None:
    offset = partition.start * SECTOR_SIZE
    remaining = partition.sectors * SECTOR_SIZE
    with image.open("rb") as source, destination.open("wb") as target:
        source.seek(offset)
        while remaining:
            block = source.read(min(8 * 1024 * 1024, remaining))
            if not block:
                raise ImageError(f"Image ended while copying partition {partition.index}")
            target.write(block)
            remaining -= len(block)


def _run_filesystem_checks(path: Path, boot: Partition, root: Partition) -> None:
    checks = (
        ("FAT32 boot", "fsck.fat", ["-n", "-v"], boot),
        ("ext4 root", "e2fsck", ["-f", "-n"], root),
    )
    missing = [tool for _, tool, _, _ in checks if shutil.which(tool) is None]
    if missing:
        raise ImageError("filesystem checks require host tools: " + ", ".join(missing))

    with tempfile.TemporaryDirectory(prefix="r36s-image-check-") as temp_dir:
        for label, tool, options, partition in checks:
            copy_path = Path(temp_dir) / f"partition-{partition.index}.img"
            _copy_partition(path, partition, copy_path)
            result = subprocess.run(
                [tool, *options, str(copy_path)],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            print(f"--- {label} read-only check ---")
            print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
            if result.returncode != 0:
                raise ImageError(
                    f"{label} filesystem check failed with exit status {result.returncode}"
                )
            copy_path.unlink()


def verify(
    path: Path,
    uboot_package: Path | None = None,
    check_filesystems: bool = False,
    uboot_packages_dir: Path | None = None,
) -> None:
    if not path.is_file():
        raise ImageError(f"Image not found: {path}")
    partitions = read_partitions(path)
    boot, root = partitions
    image_sectors = path.stat().st_size // SECTOR_SIZE
    for part in partitions:
        if part.start + part.sectors > image_sectors:
            raise ImageError(f"Partition {part.index} extends beyond the image")
    if boot.start != 32768:
        raise ImageError(f"Unexpected boot partition start sector: {boot.start}")
    if root.type_id != 0x83 or root.start < boot.start + boot.sectors:
        raise ImageError("Second MBR partition is not a non-overlapping Linux partition")

    fat = FatVolume(path, boot)
    if fat.kind != "FAT32":
        raise ImageError(f"Expected FAT32 boot partition, found {fat.kind}")

    boot_cmd = fat.read_file("boot.cmd")
    boot_script = fat.read_file("boot.scr")
    env_raw = fat.read_file("armbianEnv.txt")
    if not fat.read_file("Image") or not fat.read_file("uInitrd"):
        raise ImageError("Kernel Image or uInitrd is empty")
    env = {}
    for line in env_raw.decode("ascii", errors="strict").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip()
    dtb_path = env.get("fdtfile", "")
    rootdev = env.get("rootdev", "")
    if not dtb_path or not rootdev.startswith("UUID="):
        raise ImageError("armbianEnv.txt lacks fdtfile or a UUID rootdev")
    if not fat.read_file(f"dtb/{dtb_path}"):
        raise ImageError(f"DTB referenced by fdtfile is empty: {dtb_path}")
    dtb_digest = hashlib.sha256(fat.read_file(f"dtb/{dtb_path}")).hexdigest()

    if len(boot_script) < 64:
        raise ImageError("boot.scr is shorter than a legacy U-Boot image header")
    magic, header_crc, _, data_size, _, _, data_crc = struct.unpack_from(">7I", boot_script)
    if magic != UBOOT_LEGACY_MAGIC or boot_script[30] != UBOOT_SCRIPT_TYPE:
        raise ImageError("boot.scr is not a legacy U-Boot script image")
    header = bytearray(boot_script[:64])
    struct.pack_into(">I", header, 4, 0)
    if zlib.crc32(header) & 0xFFFFFFFF != header_crc:
        raise ImageError("boot.scr header CRC mismatch")
    payload = boot_script[64 : 64 + data_size]
    if len(payload) != data_size or 64 + data_size != len(boot_script):
        raise ImageError("boot.scr payload size does not match its file size")
    if zlib.crc32(payload) & 0xFFFFFFFF != data_crc:
        raise ImageError("boot.scr data CRC mismatch")
    if len(payload) < 8:
        raise ImageError("boot.scr has no legacy script length table")
    script_size = struct.unpack_from(">I", payload)[0]
    if (
        script_size != len(boot_cmd)
        or payload[4:8] != b"\0\0\0\0"
        or payload[8:] != boot_cmd
    ):
        raise ImageError("boot.scr legacy script payload does not match boot.cmd")

    with path.open("rb") as stream:
        superblock_offset = root.start * SECTOR_SIZE + 1024
        superblock = FatVolume._read(stream, superblock_offset, 1024)
    if struct.unpack_from("<H", superblock, 56)[0] != EXT4_MAGIC:
        raise ImageError("Root partition does not contain an ext4 superblock")
    root_uuid = str(uuid.UUID(hex=bytes(superblock[104:120]).hex()))
    expected_uuid = rootdev.removeprefix("UUID=").lower()
    if root_uuid != expected_uuid:
        raise ImageError(f"Root UUID mismatch: armbianEnv={expected_uuid}, ext4={root_uuid}")

    uboot_digest = None
    uboot_size = 0
    if uboot_package is not None and uboot_packages_dir is not None:
        raise ImageError("Choose either --uboot-package or --uboot-packages-dir, not both")
    if uboot_packages_dir is not None:
        uboot_package = _find_matching_uboot_package(path, boot, uboot_packages_dir)
    if uboot_package is not None:
        uboot_binary = _read_uboot_binary(uboot_package)
        uboot_size = len(uboot_binary)
        boot_offset = UBOOT_IMAGE_OFFSET
        boot_end = boot_offset + uboot_size
        boot_partition_offset = boot.start * SECTOR_SIZE
        if boot_end > boot_partition_offset:
            raise ImageError("Embedded U-Boot overlaps the first partition")
        with path.open("rb") as stream:
            embedded = FatVolume._read(stream, boot_offset, uboot_size)
        if embedded != uboot_binary:
            raise ImageError("U-Boot package binary does not match the copy embedded in the image")
        uboot_digest = hashlib.sha256(uboot_binary).hexdigest()

    if check_filesystems:
        _run_filesystem_checks(path, boot, root)
        print("Filesystems: PASS (read-only checks)")

    print("Image structure: PASS")
    print(f"Image SHA-256: {sha256(path)}")
    print(f"Boot: {fat.kind}, start={boot.start}, sectors={boot.sectors}")
    print(f"Root: ext4, start={root.start}, sectors={root.sectors}, UUID={root_uuid}")
    print(f"boot.scr: U-Boot script, header/data CRC PASS, script matches boot.cmd ({script_size} bytes)")
    print(f"Kernel/initramfs: Image={len(fat.read_file('Image'))} bytes, uInitrd={len(fat.read_file('uInitrd'))} bytes")
    print(f"DTB: dtb/{dtb_path}, SHA-256={dtb_digest}")
    if uboot_digest is not None:
        print(
            f"Embedded U-Boot: exact package match ({uboot_package.name}) at byte offset "
            f"{UBOOT_IMAGE_OFFSET}, size={uboot_size} bytes, SHA-256={uboot_digest}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, help="Armbian .img file to inspect")
    parser.add_argument(
        "--uboot-package",
        type=Path,
        help="optional matching linux-u-boot-r36s-current .deb; verifies the binary written into the image",
    )
    parser.add_argument(
        "--uboot-packages-dir",
        type=Path,
        help="select the R36S U-Boot .deb whose binary exactly matches the image",
    )
    parser.add_argument(
        "--check-filesystems",
        action="store_true",
        help=(
            "run fsck.fat -n and e2fsck -fn on temporary partition copies "
            "(requires both host tools and temporary disk space)"
        ),
    )
    args = parser.parse_args()
    try:
        verify(
            args.image,
            uboot_package=args.uboot_package,
            check_filesystems=args.check_filesystems,
            uboot_packages_dir=args.uboot_packages_dir,
        )
    except (ImageError, OSError, UnicodeError, struct.error, subprocess.SubprocessError) as error:
        print(f"Image verification failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
