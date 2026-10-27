#!/usr/bin/env python3
"""Capture Linux input events on an R36S without installing evtest."""

from __future__ import annotations

import argparse
import collections
import fcntl
import os
import select
import struct
import statistics
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
ABS_STATE = struct.Struct("@iiiiii")


def device_name(path: str) -> str:
    name_path = Path("/sys/class/input") / Path(path).name / "device/name"
    try:
        return name_path.read_text().strip()
    except OSError:
        return "unknown"


def read_events(
    poller: select.poll,
    labels: dict[int, tuple[str, str]],
    buffers: dict[int, bytearray],
    duration: float,
    counts: dict[str, int],
    last_abs: dict[tuple[str, int], int],
    phase: str | None = None,
) -> dict[tuple[str, int], list[int]]:
    samples: dict[tuple[str, int], list[int]] = collections.defaultdict(list)
    deadline = time.monotonic() + duration
    while time.monotonic() < deadline:
        timeout = max(1, int(min(250, (deadline - time.monotonic()) * 1000)))
        for fd, _ in poller.poll(timeout):
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
                    key = (path, code)
                    previous = last_abs.get(key)
                    last_abs[key] = value
                    if phase is not None:
                        samples[key].append(value)
                    if previous is not None and abs(value - previous) < 2:
                        continue
                if phase is None:
                    type_name = EVENT_TYPES.get(event_type, str(event_type))
                    if event_type == 3:
                        code_name = ABS_CODES.get(code, f"ABS_{code}")
                    elif event_type == 1:
                        code_name = KEY_CODES.get(code, f"KEY_{code}")
                    else:
                        code_name = str(code)
                    print(f"{sec}.{usec:06d} {path} [{name}] {type_name} {code_name}={value}", flush=True)
    return samples


def clear_pending_events(
    labels: dict[int, tuple[str, str]], buffers: dict[int, bytearray]
) -> None:
    for fd in labels:
        buffers[fd].clear()
        while True:
            try:
                if not os.read(fd, 4096):
                    break
            except BlockingIOError:
                break


def read_abs_state(labels: dict[int, tuple[str, str]]) -> dict[tuple[str, int], int]:
    state: dict[tuple[str, int], int] = {}
    for fd, (path, _) in labels.items():
        for code in ABS_CODES:
            request = (2 << 30) | (ABS_STATE.size << 16) | (ord("E") << 8) | (0x40 + code)
            try:
                data = bytearray(ABS_STATE.size)
                fcntl.ioctl(fd, request, data, True)
            except OSError:
                continue
            state[(path, code)] = ABS_STATE.unpack(data)[0]
    return state


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=float, default=25)
    parser.add_argument(
        "--guided", action="store_true",
        help="prompt for center and each direction on both analog sticks",
    )
    parser.add_argument(
        "--step-duration", type=float, default=3.0,
        help="seconds to sample each guided position (default: 3)",
    )
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
        device_names = {path: name for path, name in labels.values()}

        if args.guided:
            if args.step_duration <= 0:
                parser.error("--step-duration must be greater than zero")
            phases = [
                ("Reposo", "Deja ambos sticks sueltos y centrados."),
                ("Izquierdo arriba", "Coloca el stick izquierdo completamente ARRIBA."),
                ("Izquierdo abajo", "Coloca el stick izquierdo completamente ABAJO."),
                ("Izquierdo izquierda", "Coloca el stick izquierdo completamente a la IZQUIERDA."),
                ("Izquierdo derecha", "Coloca el stick izquierdo completamente a la DERECHA."),
                ("Derecho arriba", "Coloca el stick derecho completamente ARRIBA."),
                ("Derecho abajo", "Coloca el stick derecho completamente ABAJO."),
                ("Derecho izquierda", "Coloca el stick derecho completamente a la IZQUIERDA."),
                ("Derecho derecha", "Coloca el stick derecho completamente a la DERECHA."),
            ]
            print(f"Prueba guiada: cada posición se captura durante {args.step_duration:g} s.")
            for title, instruction in phases:
                input(
                    f"\n{title}: {instruction} Luego pulsa Enter; "
                    "mantén esa posición hasta el resumen..."
                )
                clear_pending_events(labels, buffers)
                start_state = read_abs_state(labels)
                print(f"Capturando {title.lower()}...", flush=True)
                samples = read_events(
                    poller, labels, buffers, args.step_duration, counts, last_abs, title
                )
                end_state = read_abs_state(labels)
                axes = sorted(set(start_state) | set(end_state) | set(samples))
                for path, code in axes:
                    values = samples.get((path, code), [])
                    name = device_names[path]
                    axis = ABS_CODES.get(code, f"ABS_{code}")
                    values_text = (
                        f"min={min(values)} max={max(values)} "
                        f"promedio={statistics.fmean(values):.1f} muestras={len(values)}"
                        if values else "sin cambios durante la captura"
                    )
                    print(
                        f"  {name} {axis}: inicio={start_state.get((path, code), 'n/d')} "
                        f"fin={end_state.get((path, code), 'n/d')} {values_text}"
                    )
            print("\nPrueba guiada terminada.")
        else:
            read_events(poller, labels, buffers, args.duration, counts, last_abs)
        print("COUNTS " + " ".join(f"{path}={count}" for path, count in counts.items()), flush=True)
    finally:
        for fd in opened:
            os.close(fd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
