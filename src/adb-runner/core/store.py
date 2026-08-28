# -*- coding: utf-8 -*-
"""JsonStore — 分组与脚本数据的读写（沿用并扩展现有 JSON 格式）。

文件命名约定（沿用）：
  - 当前分组 -> scriptList.json
  - 其他分组 -> {分组名}_scriptList.json，如 Test_scriptList.json

扩展字段（兼容旧格式，缺失时按默认值补齐）：
  - scriptSet.json: version / sets[{name,order,file}] / settings{...}
  - scriptList.json: 每条脚本增加 order/enabled/category/description
"""

import json
import threading
from pathlib import Path

DEFAULT_SETTINGS = {
    "multi_device": True,
    "last_device": "",
    "log_mode": "error_only",   # all | error_only | off
    "log_keep_days": 7,
    "log_max_mb": 10,
    "long_press_ms": 500,
    "theme": "dark",            # dark | light
}


class JsonStore:
    """管理 data 目录下的 scriptSet.json 与各分组脚本文件。"""

    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._script_set_path = self.data_dir / "scriptSet.json"
        self._script_set = None
        self._scripts_cache = {}

    # ---------------- scriptSet ----------------

    def load_script_set(self, force=False):
        """加载分组定义与设置，兼容旧格式（sets 为字符串数组）。"""
        with self._lock:
            if self._script_set is not None and not force:
                return self._script_set
            data = {}
            if self._script_set_path.exists():
                try:
                    data = json.loads(self._script_set_path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    data = {}
            if not isinstance(data, dict):
                data = {}
            raw_sets = data.get("sets", []) or []
            current = data.get("current_set") or (raw_sets[0] if raw_sets else "")
            sets = []
            for idx, s in enumerate(raw_sets):
                if isinstance(s, str):
                    name = s
                    sets.append({
                        "name": name,
                        "order": idx,
                        "file": self._infer_file(name, name == current),
                    })
                elif isinstance(s, dict):
                    name = s.get("name") or f"组{idx}"
                    sets.append({
                        "name": name,
                        "order": s.get("order", idx),
                        "file": s.get("file") or self._infer_file(name, name == current),
                    })
            data["version"] = data.get("version", 1)
            data["current_set"] = current
            data["sets"] = sets
            settings = data.get("settings")
            if not isinstance(settings, dict):
                settings = {}
            for k, v in DEFAULT_SETTINGS.items():
                settings.setdefault(k, v)
            data["settings"] = settings
            self._script_set = data
            return data

    def _infer_file(self, name, is_current):
        """推断分组对应的脚本文件（优先使用已存在的文件）。"""
        candidate = f"{name}_scriptList.json"
        if (self.data_dir / candidate).exists():
            return candidate
        if is_current and (self.data_dir / "scriptList.json").exists():
            return "scriptList.json"
        return "scriptList.json" if is_current else candidate

    def save_script_set(self):
        """写回 scriptSet.json（原子写入，持久化显式 file 映射与 settings）。"""
        with self._lock:
            if self._script_set is None:
                return
            data = {
                "version": self._script_set.get("version", 1),
                "current_set": self._script_set["current_set"],
                "sets": [
                    {"name": s["name"], "order": s["order"], "file": s["file"]}
                    for s in self._script_set["sets"]
                ],
                "settings": self._script_set["settings"],
            }
            self._atomic_write(self._script_set_path, data)

    def switch_set(self, set_name):
        """切换当前分组并持久化。"""
        with self._lock:
            self.load_script_set()
            if set_name in [s["name"] for s in self._script_set["sets"]]:
                self._script_set["current_set"] = set_name
                self.save_script_set()
                return True
            return False

    # ---------------- 组管理 ----------------

    def list_group_names(self):
        return [s["name"] for s in self.load_script_set()["sets"]]

    def create_group(self, name):
        """新建分组（空脚本文件），并设为当前分组。"""
        with self._lock:
            self.load_script_set()
            if name in [s["name"] for s in self._script_set["sets"]]:
                return False
            idx = len(self._script_set["sets"])
            self._script_set["sets"].append({
                "name": name, "order": idx, "file": f"{name}_scriptList.json",
            })
            self._script_set["current_set"] = name
            self.save_script_set()
            self.save_scripts(name, [])  # 创建空的脚本文件
            return True

    def rename_group(self, old, new):
        """重命名分组（保留原脚本文件映射，文件不重命名）。"""
        with self._lock:
            self.load_script_set()
            found = False
            for s in self._script_set["sets"]:
                if s["name"] == old:
                    s["name"] = new
                    found = True
            if not found:
                return False
            if self._script_set["current_set"] == old:
                self._script_set["current_set"] = new
            if old in self._scripts_cache:
                self._scripts_cache[new] = self._scripts_cache.pop(old)
            self.save_script_set()
            return True

    def delete_group(self, name):
        """删除分组，并物理删除其脚本数据文件（真实删除，不留孤儿文件）。"""
        with self._lock:
            self.load_script_set()
            sets = [s for s in self._script_set["sets"] if s["name"] != name]
            if len(sets) == len(self._script_set["sets"]):
                return False
            # 先记下数据文件名，再从分组定义中移除
            file_name = next(
                (s.get("file") for s in self._script_set["sets"] if s["name"] == name),
                None)
            self._script_set["sets"] = sets
            if self._script_set["current_set"] == name:
                self._script_set["current_set"] = sets[0]["name"] if sets else ""
            self._scripts_cache.pop(name, None)
            self.save_script_set()
            # 物理删除该分组的脚本数据文件
            if file_name:
                path = self.data_dir / file_name
                try:
                    if path.exists():
                        path.unlink()
                except OSError:
                    pass
            return True

    # ---------------- scriptList ----------------

    def script_file_for(self, set_name):
        script_set = self.load_script_set()
        for s in script_set["sets"]:
            if s["name"] == set_name:
                return s["file"]
        return self._infer_file(set_name, set_name == script_set["current_set"])

    def load_scripts(self, set_name, force=False):
        """加载指定分组的脚本列表，补齐扩展字段并按 order 排序。"""
        with self._lock:
            if set_name in self._scripts_cache and not force:
                return self._scripts_cache[set_name]
            path = self.data_dir / self.script_file_for(set_name)
            data = {}
            if path.exists():
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    data = {}
            scripts = data.get("scripts", []) if isinstance(data, dict) else []
            for i, s in enumerate(scripts):
                s.pop("enabled", None)  # 彻底移除启用字段（兼容旧数据残留）
                s["order"] = s.get("order", i)
                s["category"] = s.get("category", "")
                s["description"] = s.get("description", "")
                s["name"] = s.get("name", "")
                s["command"] = s.get("command", "")
            scripts.sort(key=lambda s: (s.get("order", 0), s.get("id", 0)))
            self._scripts_cache[set_name] = scripts
            return scripts

    def save_scripts(self, set_name, scripts):
        """写回指定分组的脚本列表（order 按数组顺序重排）。"""
        with self._lock:
            for i, s in enumerate(scripts):
                s["order"] = i
            path = self.data_dir / self.script_file_for(set_name)
            self._atomic_write(path, {"version": 1, "scripts": scripts})
            self._scripts_cache[set_name] = scripts

    # ---------------- 通用 ----------------

    @staticmethod
    def _atomic_write(path: Path, data: dict):
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp.replace(path)
