"""File Manager service.

Performs filesystem operations and returns structured responses.
"""
from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import Optional


def _now() -> float:
    return time.time()


def _wrap(action: str, target: str, status: str, message: str, start: float, data: Optional[dict] = None) -> dict:
    return {
        "action": action,
        "target": target,
        "status": status,
        "message": message,
        "execution_time": round(time.time() - start, 4),
        "data": data or {},
    }


class FileManager:
    def open_file(self, path: str) -> dict:
        start = _now()
        p = Path(path)
        if not p.exists() or not p.is_file():
            return _wrap("open", path, "failure", "file not found", start)
        try:
            content = p.read_text(encoding="utf-8")
            return _wrap("open", path, "success", "opened", start, {"content": content})
        except Exception as exc:
            return _wrap("open", path, "failure", str(exc), start)

    def open_folder(self, path: str) -> dict:
        start = _now()
        p = Path(path)
        if not p.exists() or not p.is_dir():
            return _wrap("open_folder", path, "failure", "folder not found", start)
        try:
            items = sorted([x.name for x in p.iterdir()])
            return _wrap("open_folder", path, "success", "opened", start, {"items": items})
        except Exception as exc:
            return _wrap("open_folder", path, "failure", str(exc), start)

    def create_file(self, path: str) -> dict:
        start = _now()
        p = Path(path)
        try:
            if p.parent:
                p.parent.mkdir(parents=True, exist_ok=True)
            p.touch(exist_ok=True)
            return _wrap("create_file", path, "success", "created", start)
        except Exception as exc:
            return _wrap("create_file", path, "failure", str(exc), start)

    def create_folder(self, path: str) -> dict:
        start = _now()
        p = Path(path)
        try:
            p.mkdir(parents=True, exist_ok=True)
            return _wrap("create_folder", path, "success", "created", start)
        except Exception as exc:
            return _wrap("create_folder", path, "failure", str(exc), start)

    def rename(self, src: str, dst: str) -> dict:
        start = _now()
        s = Path(src)
        d = Path(dst)
        if not s.exists():
            return _wrap("rename", src, "failure", "source not found", start)
        try:
            if d.parent:
                d.parent.mkdir(parents=True, exist_ok=True)
            s.rename(d)
            return _wrap("rename", f"{src} -> {dst}", "success", "renamed", start)
        except Exception as exc:
            return _wrap("rename", f"{src} -> {dst}", "failure", str(exc), start)

    def delete(self, path: str) -> dict:
        start = _now()
        p = Path(path)
        if not p.exists():
            return _wrap("delete", path, "failure", "not found", start)
        try:
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
            return _wrap("delete", path, "success", "deleted", start)
        except Exception as exc:
            return _wrap("delete", path, "failure", str(exc), start)

    def move(self, src: str, dst: str) -> dict:
        start = _now()
        try:
            # ensure destination parent exists
            d = Path(dst)
            if d.parent:
                d.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(src, dst)
            return _wrap("move", f"{src} -> {dst}", "success", "moved", start)
        except Exception as exc:
            return _wrap("move", f"{src} -> {dst}", "failure", str(exc), start)

    def copy(self, src: str, dst: str) -> dict:
        start = _now()
        s = Path(src)
        d = Path(dst)
        try:
            if s.is_dir():
                # copy tree
                if d.exists():
                    return _wrap("copy", f"{src} -> {dst}", "failure", "destination exists", start)
                shutil.copytree(src, dst)
            else:
                if d.is_dir():
                    # copy into directory
                    shutil.copy2(src, d / s.name)
                else:
                    if d.parent:
                        d.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
            return _wrap("copy", f"{src} -> {dst}", "success", "copied", start)
        except Exception as exc:
            return _wrap("copy", f"{src} -> {dst}", "failure", str(exc), start)


_default: Optional[FileManager] = None


def get_file_manager() -> FileManager:
    global _default
    if _default is None:
        _default = FileManager()
    return _default
