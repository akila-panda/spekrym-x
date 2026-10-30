"""Dataset housekeeping for the Lab dashboard: protection, trash, restore.

A file is IN USE when its data version (or, if that is unknown, its file name) appears in a
locked experiment, an experiment record or a saved 9A model file. In-use files are refused for
deletion, so a locked experiment never points at a removed or replaced file. Everything else is
moved to ``<data folder>/.trash`` (recoverable) and only removed for good on a second, explicit
step. The browser only ever sends a file name; it is checked against the folder listing.
"""

from __future__ import annotations

import re
import shutil
from datetime import UTC, datetime
from pathlib import Path

from sx_data.importer import sidecar_path

TRASH = ".trash"
_SCAN_SUFFIXES = {".yaml", ".yml", ".json", ".jsonl", ".md"}
_MAX_SCAN_BYTES = 5_000_000
_TRASH_ID = re.compile(r"^\d{8}T\d{6}Z__[A-Za-z0-9_.-]+\.parquet$")


class AdminRefused(ValueError):
    """The action is not allowed; the message is shown to the owner."""


def _texts(dirs: list[Path]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for d in dirs:
        for p in sorted(d.rglob("*")) if d.is_dir() else []:
            if p.is_file() and p.suffix in _SCAN_SUFFIXES and p.stat().st_size <= _MAX_SCAN_BYTES:
                try:
                    out.append((f"{p.parent.name}/{p.name}", p.read_text(errors="ignore")))
                except OSError:
                    continue
    return out


def used_by(data_version: str | None, file: str, dirs: list[Path]) -> list[str]:
    """Names of the experiment / model files that mention this data version or file name."""
    needles = [n for n in (data_version, file) if n]
    return [name for name, text in _texts(dirs) if any(n in text for n in needles)]


def mark_in_use(rows: list[dict], dirs: list[Path]) -> list[dict]:
    texts = _texts(dirs)
    for r in rows:
        needles = [n for n in (r.get("data_version"), r["file"]) if n]
        r["in_use"] = [name for name, t in texts if any(n in t for n in needles)]
    return rows


def _resolve(folder: Path, file: str) -> Path:
    names = {p.name for p in folder.glob("*.parquet")} if folder.is_dir() else set()
    if file not in names:
        raise AdminRefused(f"{file} is not a dataset in the data folder")
    return folder / file


def move_to_trash(folder: Path, file: str, row: dict, dirs: list[Path]) -> str:
    path = _resolve(folder, file)
    users = used_by(row.get("data_version"), file, dirs)
    if users:
        raise AdminRefused(f"{file} is in use by {', '.join(users)}. It cannot be deleted from "
                           "here while a locked experiment or saved model refers to it.")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    trash = folder / TRASH
    trash.mkdir(exist_ok=True)
    tid = f"{stamp}__{file}"
    shutil.move(str(path), trash / tid)
    side = sidecar_path(path)
    if side.exists():
        shutil.move(str(side), trash / (tid + ".provenance.json"))
    return tid


def list_trash(folder: Path) -> list[dict]:
    out = []
    for p in sorted((folder / TRASH).glob("*.parquet")) if (folder / TRASH).is_dir() else []:
        if _TRASH_ID.match(p.name):
            stamp, _, name = p.name.partition("__")
            out.append({"id": p.name, "file": name, "size_bytes": p.stat().st_size,
                        "deleted_at": datetime.strptime(stamp, "%Y%m%dT%H%M%SZ")
                        .replace(tzinfo=UTC).isoformat().replace("+00:00", "Z")})
    return out


def _trash_path(folder: Path, tid: str) -> Path:
    if not _TRASH_ID.match(tid) or not (folder / TRASH / tid).is_file():
        raise AdminRefused("that item is not in the trash")
    return folder / TRASH / tid


def restore(folder: Path, tid: str) -> str:
    src = _trash_path(folder, tid)
    name = tid.partition("__")[2]
    if (folder / name).exists():
        raise AdminRefused(f"{name} exists again in the data folder; restore is refused so "
                           "nothing is overwritten")
    shutil.move(str(src), folder / name)
    side = src.with_name(src.name + ".provenance.json")
    if side.exists():
        shutil.move(str(side), sidecar_path(folder / name))
    return name


def purge(folder: Path, tid: str) -> None:
    src = _trash_path(folder, tid)
    src.unlink()
    src.with_name(src.name + ".provenance.json").unlink(missing_ok=True)
