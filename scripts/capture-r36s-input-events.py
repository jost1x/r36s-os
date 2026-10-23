#!/usr/bin/env python3
"""Capture Linux input events on an R36S without installing evtest."""

from __future__ import annotations

import argparse
import os
import select
import struct
import time
from pathlib import Path

INPUT_EVENT = struct.Struct("@llHHi")
EVENT_TYPES = {0: "SYN", 1: "KEY", 2: "REL", 3: "ABS", 4: "MSC", 5: "SW"}
ABS_CODES = {0: "X", 1: "Y", 2: "Z", 3: "RX", 4: "RY", 5: "RZ", 16: "HAT0X", 17: "HAT0Y"}
KEY_CODES = {
    1: "ESC", 28: "ENTER", 30: "A", 31: "S", 32: "D", 33: "F",
    44: "Z", 45: "X", 46: "C", 48: "B", 103: "UP", 105: "LEFT",
    106: "RIGHT", 108: "DOWN", 114: "VOLUME_DOWN", 115: "VOLUME_UP",
    158: "BACK", 315: "START", 314: "SELECT", 316: "MODE",
}


def device_name(path: str) -> str:
    name_path = Path("/sys/class/input") / Path(path).name / "device/name"
    try:
        return name_path.read_text().strip()
    except OSError:
        return "unknown"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=float, default=25)
    parser.add_argument("devices", nargs="*", default=["/dev/input/event0", "/dev/input/event2"])
    args = parser.parse_args()

    poller = select.poll()
    labels: dict[int, tuple[str, str]] = {}
    buffers: dict[int, bytearray] = {}
    counts: dict[str, int] = {}
    last_abs: dict[tuple[str, int], int] = {}
    opened: list[int] = []
    try:
        for path in args.devices:
            fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
            opened.append(fd)
            name = device_name(path)
            labels[fd] = (path, name)
            buffers[fd] = bytearray()
            counts[path] = 0
            poller.register(fd, select.POLLIN)
            print(f"LISTENING {path}: {name}", flush=True)

        deadline = time.monotonic() + args.duration
        while time.monotonic() < deadline:
            for fd, _ in poller.poll(max(1, int(min(500, (deadline - time.monotonic()) * 1000)))):
                try:
                    chunk = os.read(fd, 4096)
                except BlockingIOError:
                    continue
                buffers[fd].extend(chunk)
                while len(buffers[fd]) >= INPUT_EVENT.size:
                    raw = bytes(buffers[fd][: INPUT_EVENT.size])
                    del buffers[fd][: INPUT_EVENT.size]
                    sec, usec, event_type, code, value = INPUT_EVENT.unpack(raw)
                    path, name = labels[fd]
                    counts[path] += 1
                    if event_type == 0:
                        continue
                    if event_type == 3:
                        previous = last_abs.get((path, code))
                        last_abs[(path, code)] = value
                        if previous is not None and abs(value - previous) < 2:
                            continue
                    type_name = EVENT_TYPES.get(event_type, str(event_type))
                    if event_type == 3:
                        code_name = ABS_CODES.get(code, f"ABS_{code}")
                    elif event_type == 1:
                        code_name = KEY_CODES.get(code, f"KEY_{code}")
                    else:
                        code_name = str(code)
                    print(f"{sec}.{usec:06d} {path} [{name}] {type_name} {code_name}={value}", flush=True)
        print("COUNTS " + " ".join(f"{path}={count}" for path, count in counts.items()), flush=True)
    finally:
        for fd in opened:
            os.close(fd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
