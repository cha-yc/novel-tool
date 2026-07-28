#!/usr/bin/env python3
"""
novel2code v2.0 — 小说文本 ↔ 源码 双向转换工具
================================================
功能: 将 .txt 小说伪装成多种语言源码 | 支持批量、多卷、评论模式、逆转换

用法:
  python novel2code.py novel.txt                    一键转换(Java)
  python novel2code.py novel.txt -l python          转为Python
  python novel2code.py novel.txt -l cpp --split     多卷分片C++
  python novel2code.py novel.txt -m review           代码审查评论模式
  python novel2code.py ./novels/ -r                  批量转换目录
  python novel2code.py all.java --reverse            逆转换: 源码→小说
  python novel2code.py --init-config                 生成配置文件
"""

import argparse
import json
import os
import random
import re
import sys
import time
from pathlib import Path

# ============================================================
# 一、语言模板
# ============================================================

LANG = {
    "java": {
        "name": "Java",
        "ext": ".java",
        "cmt": "//",
        "header": lambda c: [
            f"package {c.pkg};\n\n",
        ],
        "imports": [
            "org.slf4j.Logger", "org.slf4j.LoggerFactory",
            "java.util.*", "java.util.concurrent.*",
            "java.util.concurrent.atomic.*", "java.util.stream.Collectors",
            "java.io.*", "java.nio.file.*", "java.time.*", "java.math.*",
        ],
        "class_decl": lambda c, n: f"public class {n} {{\n",
        "logger": '    private static final Logger logger = LoggerFactory.getLogger({class_name}.class);\n\n',
        "member_var": lambda t, n, v: f"    private final {t} {n} = {v};\n",
        "static_const": lambda n, v: f"    private static final int {n} = {v};\n",
        "static_block_start": "    static {\n",
        "static_block_end": "    }\n\n",
        "method_javadoc": lambda title: f"    /**\n     * {title}\n     */\n",
        "method_sig": lambda name, ptype, pvar: f"    public Object {name}({ptype} {pvar}) {{\n",
        "null_check": lambda v: f'        if ({v} == null) {{\n            throw new IllegalArgumentException("{v} must not be null");\n        }}\n',
        "close": "    }\n\n",
        "class_close": "}\n",
        "stmt": [
            "var {0} = {1}.stream().filter(x -> x != null).collect(Collectors.toList());",
            "var {0} = Optional.ofNullable({1}).orElseGet(() -> Collections.emptyList());",
            "var {0} = String.valueOf({1});",
            "var {0} = new StringBuilder().append({1}).toString();",
            "var {0} = new TreeMap<>();",
            "var {0} = Collections.emptyList();",
            "{0}.addAll({1});",
            "{0}.put({1}, Collections.emptyList());",
            "{0}.put({1}, {2}.stream().collect(Collectors.toList()));",
            "{0}.put({1}, new HashMap<String, Object>());",
            "if ({0} != null) {1}.clear();",
            "int {0} = {1}.size();",
            "{0} = Collections.emptyList();",
            'logger.info("{msg}");',
            'logger.error("{msg}", {0});',
            'if ({0} == null) throw new IllegalStateException("{msg}");',
            "if (!{0}.containsKey({1})) {0}.put({1}, {2}.stream().collect(Collectors.toList()));",
            "{0}.put({1}, new StringBuilder().append({2}).toString());",
            "return {0} != null;",
        ],
        "block_if": 'if ({0} != null && {1}.size() > 0) {{\n{body}}}\n',
        "block_else": ' else {{\n{body}}}\n',
        "block_try": 'try {{\n{body}}} catch (Exception {0}) {{\n    logger.error("{msg}", {0});\n}}\n',
        "block_while": 'while ({0}.hasNext() && {1}.size() < {n}) {{\n{body}}}\n',
        "block_switch": 'switch ({0}.hashCode() % 3) {{\n{body}}}\n',
        "block_case": '    case {n}:\n{body}        break;\n',
        "block_default": '    default:\n{body}        break;\n',
        "var_types": ["Map<String, Object>", "List<String>", "Queue<Runnable>",
                      "AtomicInteger", "Properties", "ExecutorService",
                      "ConcurrentHashMap<String, Object>", "AtomicLong",
                      "Set<String>", "List<Object>", "Map<String, Object>"],
        "var_inits": ["new HashMap<>()", "new ArrayList<>()", "new LinkedBlockingQueue<>()",
                      "new AtomicInteger(0)", "new Properties()", "Executors.newFixedThreadPool(4)",
                      "new ConcurrentHashMap<>()", "new AtomicLong(0)",
                      "new TreeMap<>()", "new HashSet<>()", "new CopyOnWriteArrayList<>()",
                      "new LinkedHashMap<>()", "new Vector<>()", "new ConcurrentLinkedQueue<>()"],
        "method_names": ["validateRequest","configureBuffer","handleProvider","updateConnection",
                         "registerSession","collectObserver","commitProperty","acquireValidator",
                         "configureQueue","submitController","buildFactory","acquireProcessor",
                         "convertResolver","acquireWrapper","iterateRepository","submitFormatter",
                         "mergeValidator","filterPipeline","scheduleConfig","notifyEntity",
                         "configureEntity","resolveMapping","executePipeline","formatOutput",
                         "validateInput","processRequest","handleResponse","releaseResources"],
        "param_types": ["Set<String>","Map<String, Object>","List<String>","Queue<Runnable>",
                        "Optional<Object>","ConcurrentHashMap<String, Object>","Object",
                        "Iterator<String>","Collection<Object>"],
        "log_msgs": ["processing request","checkpoint reached","releasing resource",
                     "validating input","context updated","cache miss","session expired",
                     "connection reset","data flushed","pipeline completed"],
    },

    "python": {
        "name": "Python",
        "ext": ".py",
        "cmt": "#",
        "header": lambda c: [
            f'"""Auto-generated module - {c.pkg}"""\n',
            "from __future__ import annotations\n",
            "import logging\nimport threading\nimport asyncio\n",
            "from typing import Any, Dict, List, Optional, Set, Callable\n",
            "from dataclasses import dataclass\n",
            "from collections import defaultdict, OrderedDict\n",
            "import json\nimport hashlib\nimport time\n\n",
        ],
        "imports": [],  # Python uses header imports
        "class_decl": lambda c, n: f"class {n}:\n",
        "logger": '    _logger = logging.getLogger(__name__)\n\n',
        "member_var": lambda t, n, v: f"    {n}: {t} = {v}\n",
        "static_const": lambda n, v: f"    {n}: int = {v}\n",
        "static_block_start": "    def __init__(self) -> None:\n",
        "static_block_end": "\n",
        "method_javadoc": lambda title: f'    #  {title}\n',
        "method_sig": lambda name, ptype, pvar: f"    def {name}(self, {pvar}: {ptype}) -> Any:\n",
        "null_check": lambda v: f'        if {v} is None:\n            raise ValueError("{v} must not be None")\n',
        "close": "\n",
        "class_close": "\n",
        "stmt": [
            "result = [x for x in {0} if x is not None]",
            "{0} = {1} or []",
            "{0} = str({1})",
            "{0} = OrderedDict()",
            "{0}.extend({1})",
            "{0}[{1}] = []",
            "{0}[{1}] = list({2})",
            "{0}[{1}] = dict()",
            "if {0} is not None: {1}.clear()",
            "{0} = len({1})",
            "{0} = []",
            'self._logger.info("{msg}")',
            'self._logger.error("{msg}", exc_info=True)',
            "if {0} is None: raise RuntimeError('{msg}')",
            "if {1} not in {0}: {0}[{1}] = list({2})",
            "{0}[{1}] = str({2})",
            "return {0} is not None",
        ],
        "block_if": '        if {0} is not None and len({1}) > 0:\n{body}',
        "block_else": '        else:\n{body}',
        "block_try": '        try:\n{body}        except Exception as {0}:\n            self._logger.error("{msg}")\n',
        "block_while": '        while {0} and len({1}) < {n}:\n{body}',
        "block_switch": '        match hash(str({0})) % 3:\n{body}',
        "block_case": '            case {n}:\n{body}',
        "block_default": '            case _:\n{body}',
        "var_types": ["Dict[str, Any]", "List[str]", "Set[str]", "Optional[Dict]",
                      "List[Any]", "OrderedDict", "defaultdict"],
        "var_inits": ["dict()", "[]", "set()", "None", "OrderedDict()", "defaultdict(list)"],
        "method_names": ["validate_request","configure_buffer","handle_provider",
                         "update_connection","register_session","collect_observer",
                         "commit_property","acquire_validator","configure_queue",
                         "submit_controller","build_factory","acquire_processor",
                         "convert_resolver","acquire_wrapper","merge_validator",
                         "filter_pipeline","schedule_config","notify_entity",
                         "resolve_mapping","execute_pipeline","format_output",
                         "validate_input","process_request","handle_response"],
        "param_types": ["Dict[str, Any]", "List[str]", "Optional[Dict]", "Set[str]",
                        "Callable", "Any", "Iterator"],
        "log_msgs": ["processing request","checkpoint reached","releasing resource",
                     "validating input","context updated","cache miss"],
    },

    "cpp": {
        "name": "C++",
        "ext": ".cpp",
        "cmt": "//",
        "header": lambda c: [
            f'// Auto-generated - {c.pkg}\n',
            '#include <iostream>\n#include <string>\n#include <vector>\n',
            '#include <map>\n#include <set>\n#include <queue>\n#include <mutex>\n',
            '#include <thread>\n#include <memory>\n#include <functional>\n',
            '#include <algorithm>\n#include <chrono>\n#include <atomic>\n',
            '#include <optional>\n#include <any>\n\n',
            'using namespace std;\n\n',
        ],
        "imports": [],
        "class_decl": lambda c, n: f"class {n} {{\npublic:\n",
        "logger": '    // Logger would be injected here\n\n',
        "member_var": lambda t, n, v: f"    {t} {n}{{{v}}};\n",
        "static_const": lambda n, v: f"    static constexpr int {n} = {v};\n",
        "static_block_start": "    {class_name}() {{\n",
        "static_block_end": "    }\n\n",
        "method_javadoc": lambda title: f"    /** {title} */\n",
        "method_sig": lambda name, ptype, pvar: f"    auto {name}({ptype} {pvar}) -> std::any {{\n",
        "null_check": lambda v: f"        if ({v}.empty() && !{v}) throw std::runtime_error(\"null {v}\");\n",
        "close": "    }\n\n",
        "class_close": "};\n",
        "stmt": [
            "auto {0} = std::make_shared<{1}>();",
            "auto {0} = {1}.value_or(std::vector<int>{{}});",
            "{0}.push_back({1});",
            "{0}[{1}] = {{}};",
            "if ({0}) {1}->clear();",
            "auto {0} = {1}.size();",
            "{0} = {{}};",
            'std::cerr << "{msg}" << std::endl;',
            'if (!{0}) throw std::runtime_error("{msg}");',
            "return {0} != nullptr;",
        ],
        "block_if": '        if ({0} && !{1}.empty()) {{\n{body}        }}\n',
        "block_else": '        else {{\n{body}        }}\n',
        "block_try": '        try {{\n{body}        }} catch (const std::exception& {0}) {{\n            std::cerr << "{msg}" << std::endl;\n        }}\n',
        "block_while": '        while (!{0}.empty() && {1}.size() < {n}) {{\n{body}        }}\n',
        "block_switch": '        switch (std::hash<std::string>{{}}({0}) % 3) {{\n{body}        }}\n',
        "block_case": '            case {n}:\n{body}            break;\n',
        "block_default": '            default:\n{body}            break;\n',
        "var_types": ["std::map<std::string, std::any>", "std::vector<std::string>",
                      "std::queue<std::function<void()>>", "std::atomic<int>",
                      "std::set<std::string>", "std::shared_ptr<std::vector<int>>"],
        "var_inits": ["{}", "{}", "{}", "0", "{}", "nullptr"],
        "method_names": ["validateRequest","configureBuffer","handleProvider",
                         "updateConnection","registerSession","collectObserver",
                         "commitProperty","acquireValidator","configureQueue",
                         "submitController","buildFactory","acquireProcessor"],
        "param_types": ["const std::vector<std::string>&", "std::map<std::string, std::any>&",
                        "std::shared_ptr<std::vector<int>>", "std::optional<std::string>",
                        "std::set<std::string>&", "std::any"],
        "log_msgs": ["processing request","checkpoint reached","releasing resource",
                     "validating input","context updated"],
    },

    "javascript": {
        "name": "JavaScript",
        "ext": ".js",
        "cmt": "//",
        "header": lambda c: [
            f"// Auto-generated module - {c.pkg}\n",
            "const EventEmitter = require('events');\n",
            "const crypto = require('crypto');\n",
            "const { v4: uuidv4 } = require('uuid');\n\n",
        ],
        "imports": [],
        "class_decl": lambda c, n: f"class {n} {{\n",
        "logger": "    static #logger = console;\n\n",
        "member_var": lambda t, n, v: f"    #{n} = {v};\n",
        "static_const": lambda n, v: f"    static {n} = {v};\n",
        "static_block_start": "    constructor() {\n",
        "static_block_end": "    }\n\n",
        "method_javadoc": lambda title: f"    /** {title} */\n",
        "method_sig": lambda name, ptype, pvar: f"    {name}({pvar}) {{\n",
        "null_check": lambda v: f'        if (!{v}) throw new Error("{v} is required");\n',
        "close": "    }\n\n",
        "class_close": "}\n\nmodule.exports = { All };\n",
        "stmt": [
            "const {0} = [...{1}].filter(x => x != null);",
            "const {0} = {1} ?? [];",
            "{0}.push(...{1});",
            "{0}.set({1}, []);",
            "{0}.set({1}, [...{2}]);",
            "if ({0}) {1}.clear();",
            "const {0} = {1}.size;",
            "{0} = [];",
            'console.log("{msg}");',
            'console.error("{msg}");',
            'if (!{0}) throw new Error("{msg}");',
            "if (!{0}.has({1})) {0}.set({1}, [...{2}]);",
            "return {0} != null;",
        ],
        "block_if": '        if ({0} && {1}.size > 0) {{\n{body}        }}\n',
        "block_else": '        else {{\n{body}        }}\n',
        "block_try": '        try {{\n{body}        }} catch ({0}) {{\n            console.error("{msg}");\n        }}\n',
        "block_while": '        while ({0} && {1}.size < {n}) {{\n{body}        }}\n',
        "block_switch": '',
        "block_case": '',
        "block_default": '',
        "var_types": ["Map", "Array", "Set", "Object"],
        "var_inits": ["new Map()", "[]", "new Set()", "{}"],
        "method_names": ["validateRequest","configureBuffer","handleProvider",
                         "updateConnection","registerSession","collectObserver",
                         "commitProperty","acquireValidator","configureQueue",
                         "submitController","buildFactory","acquireProcessor",
                         "convertResolver","mergeValidator","filterPipeline"],
        "param_types": ["Set<String>","Map<String, Object>","Array<String>","Object","Iterator"],
        "log_msgs": ["processing request","checkpoint reached","releasing resource",
                     "validating input","context updated"],
    },

    "go": {
        "name": "Go",
        "ext": ".go",
        "cmt": "//",
        "header": lambda c: [
            f"// Auto-generated package - {c.pkg}\n",
            "package main\n\n",
            'import (\n\t"context"\n\t"errors"\n\t"fmt"\n\t"sync"\n\t"time"\n)\n\n',
        ],
        "imports": [],
        "class_decl": lambda c, n: f"type {n} struct {{\n",
        "logger": "\t// logger would be injected\n\n",
        "member_var": lambda t, n, v: f"\t{n} {t}\n",
        "static_const": lambda n, v: f"const {n} = {v}\n",
        "static_block_start": "func New{class_name}() *{class_name} {{\n\treturn &{class_name}{{\n",
        "static_block_end": "\t}\n}\n\n",
        "method_javadoc": lambda title: f"// {title}\n",
        "method_sig": lambda c, name, ptype, pvar: (
            f"func ({c.receiver()} *{c._class_name()}) "
            f"{name}({pvar} {ptype}) interface{{}} {{\n"
        ),
        "null_check": lambda v: f'\tif {v} == nil {{\n\t\treturn nil, errors.New("{v} is nil")\n\t}}\n',
        "close": "}\n\n",
        "class_close": "",
        "stmt": [
            "{0} := make([]string, 0)",
            "{0} = append({0}, {1}...)",
            "{0}[{1}] = nil",
            "{0}[{1}] = {2}",
            "if {0} != nil {{ {1} = nil }}",
            "{0} := len({1})",
            "{0} = nil",
            'fmt.Println("{msg}")',
            'if {0} == nil {{ return nil, errors.New("{msg}") }}',
            "return {0} != nil",
        ],
        "block_if": '\tif {0} != nil && len({1}) > 0 {{\n{body}\t}}\n',
        "block_else": '\telse {{\n{body}\t}}\n',
        "block_try": '',  # Go uses explicit error returns
        "block_while": '\tfor {0} && len({1}) < {n} {{\n{body}\t}}\n',
        "block_switch": '\tswitch hash({0}) % 3 {{\n{body}\t}}\n',
        "block_case": '\tcase {n}:\n{body}\n',
        "block_default": '\tdefault:\n{body}\n',
        "var_types": ["map[string]interface{}", "[]string", "chan struct{}",
                      "sync.Mutex", "*sync.WaitGroup", "context.Context"],
        "var_inits": ["make(map[string]interface{})", "make([]string, 0)", "make(chan struct{})",
                      "sync.Mutex{}", "&sync.WaitGroup{}", "context.Background()"],
        "method_names": ["validateRequest","configureBuffer","handleProvider",
                         "updateConnection","registerSession","collectObserver",
                         "commitProperty","acquireValidator","configureQueue",
                         "submitController","buildFactory"],
        "param_types": ["map[string]interface{}", "[]string", "context.Context",
                        "interface{}", "chan struct{}"],
        "log_msgs": ["processing request","checkpoint reached","releasing resource",
                     "validating input","context updated"],
    },
}

# ============================================================
# 二、评论模式
# ============================================================

REVIEW_PREFIXES = [
    "TODO: ", "FIXME: ", "NOTE: ", "HACK: ", "REVIEW: ",
    "OPTIMIZE: ", "WARNING: ", "INFO: ", "XXX: ", "IDEA: ",
]

# 中文评论前缀（更自然的中文代码审查）
REVIEW_PREFIXES_CN = [
    "待办: ", "修复: ", "注意: ", "临时方案: ", "需审查: ",
    "优化: ", "警告: ", "提示: ", "标记: ", "想法: ",
]

# ============================================================
# 三、默认配置
# ============================================================

DEFAULT_CONFIG = {
    "language": "java",
    "chunk_size": 50,
    "comment_mode": "inline",      # "inline" | "review"
    "review_style": "mixed",       # "en" | "cn" | "mixed"
    "split_volumes": False,
    "volume_lines": 10000,         # 每卷输入行数
    "detect_chapters": True,
    "seed": None,
    "preamble_lines": 20,
    "package_name": "com.acme.core",
    "class_name": "All",
}

# ============================================================
# 四、配置管理
# ============================================================

class Config:
    """配置管理器：命令行参数 > JSON配置文件 > 默认值"""

    def __init__(self, **overrides):
        self.data = dict(DEFAULT_CONFIG)
        for k, v in overrides.items():
            if v is not None and k in self.data:
                self.data[k] = v

    def __getattr__(self, name):
        return self.data.get(name, DEFAULT_CONFIG.get(name))

    @staticmethod
    def load_from_json(path: str) -> dict:
        """从JSON文件加载配置"""
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def save_default(path: str):
        """生成默认配置文件"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
        print(f"[配置] 已生成: {path}")

    def _class_name(self, volume: int = 0) -> str:
        """获取类名（多卷时自动编号）"""
        name = self.data["class_name"]
        if volume > 0 and self.data["split_volumes"]:
            return f"{name}V{volume + 1}"
        return name

    def receiver(self) -> str:
        """Go语言receiver名"""
        name = self.data["class_name"].lower()
        return name[0] if name else "a"

    @property
    def pkg(self):
        return self.data["package_name"]

    @property
    def lang(self):
        return LANG.get(self.data["language"], LANG["java"])

    @property
    def cmt_mode(self):
        return self.data["comment_mode"]


# ============================================================
# 五、代码生成器（语言无关）
# ============================================================

class CodeGen:
    """语言感知的随机代码生成器"""

    def __init__(self, cfg: Config, rng: random.Random):
        self.cfg = cfg
        self.rng = rng
        self.lang = cfg.lang

    def v(self) -> str:
        """随机变量名（从方法名池取）"""
        return self.rng.choice(self.lang["method_names"])

    def m(self) -> str:
        """随机方法名"""
        return self.rng.choice(self.lang["method_names"])

    def vt(self) -> str:
        """随机变量类型"""
        pool = self.lang.get("var_types", ["Object"])
        return self.rng.choice(pool)

    def vi(self) -> str:
        """随机变量初始化值"""
        pool = self.lang.get("var_inits", ["null"])
        return self.rng.choice(pool)

    def pt(self) -> str:
        """随机参数类型"""
        pool = self.lang.get("param_types", ["Object"])
        return self.rng.choice(pool)

    def log(self) -> str:
        return self.rng.choice(self.lang["log_msgs"])

    def stmt(self, indent="        ") -> str:
        """生成一条随机语句"""
        templates = self.lang["stmt"]
        if not templates:
            return ""
        tmpl = self.rng.choice(templates)
        try:
            return indent + tmpl.format(self.v(), self.v(), self.v(), msg=self.log(), n=self.rng.randint(5, 30))
        except (IndexError, KeyError):
            return indent + tmpl.format(self.v(), self.v(), msg=self.log())

    def block(self, indent="        ") -> list[str]:
        """生成一个随机代码块"""
        lang = self.cfg.data["language"]
        kind = self.rng.randint(0, 3 if lang == "go" else 4)
        lines = []

        if kind == 0 and self.lang.get("block_if"):
            inner = self._indent(self.stmt(""), "    ")
            for _ in range(self.rng.randint(1, 2)):
                inner += self._indent(self.stmt(""), "    ")
            tmpl = self.lang["block_if"]
            body = tmpl.format(self.v(), self.v(), body=inner)
            lines.append(indent + body.rstrip("\n"))
            if self.rng.random() < 0.4 and self.lang.get("block_else"):
                inner2 = self._indent(self.stmt(""), "    ")
                tmpl2 = self.lang["block_else"]
                body2 = tmpl2.format(self.v(), self.v(), body=inner2)
                lines.append(indent + body2.rstrip("\n"))

        elif kind == 1 and self.lang.get("block_try"):
            inner = self._indent(self.stmt(""), "    ")
            tmpl = self.lang["block_try"]
            body = tmpl.format(self.v(), msg=self.log(), body=inner)
            lines.append(indent + body.rstrip("\n"))

        elif kind == 2 and self.lang.get("block_while"):
            inner = self._indent(self.stmt(""), "    ")
            tmpl = self.lang["block_while"]
            body = tmpl.format(self.v(), self.v(), n=self.rng.randint(5, 30), body=inner)
            lines.append(indent + body.rstrip("\n"))

        elif kind == 3 and self.lang.get("block_switch"):
            inner = ""
            for c in range(3):
                case_inner = self._indent(self.stmt(""), "    ")
                if c < 2 and self.lang.get("block_case"):
                    inner += self.lang["block_case"].format(n=c, body=case_inner)
                elif self.lang.get("block_default"):
                    inner += self.lang["block_default"].format(body=case_inner)
            tmpl = self.lang["block_switch"]
            body = tmpl.format(self.v(), body=inner)
            lines.append(indent + body.rstrip("\n"))

        else:
            for _ in range(self.rng.randint(1, 3)):
                lines.append(self.stmt(indent))

        return [l for l in lines if l.strip()]

    def _indent(self, text: str, prefix: str) -> str:
        return "\n".join(prefix + l for l in text.split("\n") if l)

    def make_comment(self, text: str, indent="        ") -> str:
        """根据评论模式生成注释行"""
        prefix = self.lang["cmt"]

        if self.cfg.cmt_mode == "review" and text.strip():
            style = self.cfg.data.get("review_style", "mixed")
            if style == "cn":
                pool = REVIEW_PREFIXES_CN
            elif style == "en":
                pool = REVIEW_PREFIXES
            else:
                pool = REVIEW_PREFIXES + REVIEW_PREFIXES_CN
            tag = self.rng.choice(pool)
            return f"{indent}{prefix} {tag}{text}\n"
        else:
            return f"{indent}{prefix} {text}\n" if text.strip() else ""

    def make_preamble_comment(self, text: str) -> str:
        """生成preamble中的注释（行首无缩进）"""
        if self.cfg.cmt_mode == "review" and text.strip():
            tag = self.rng.choice(REVIEW_PREFIXES)
            return f"{self.lang['cmt']} {tag}{text}\n"
        else:
            return f"{self.lang['cmt']} {text}\n" if text.strip() else ""


# ============================================================
# 六、卷管理器（多文件输出）
# ============================================================

class VolumeWriter:
    """管理多卷文件输出，支持增量追加"""

    def __init__(self, base_path: str, cfg: Config, append: bool = False,
                 start_volume: int = 0, start_lines: int = 0):
        self.base_path = base_path
        self.cfg = cfg
        self.volume = start_volume
        self.lines_written = start_lines  # 当前卷已处理行数
        self.fout = None
        self._append = append
        self._first_vol = start_volume
        self._state = None  # 待写入文件的状态数据
        self._open_next()

    def _volume_dir(self) -> str:
        if not self.cfg.data["split_volumes"]:
            return str(Path(self.base_path).parent)
        stem = Path(self.base_path).stem
        return str(Path(self.base_path).parent / stem)

    def _volume_path(self) -> str:
        stem = Path(self.base_path).stem
        ext = Path(self.base_path).suffix
        folder = self._volume_dir()
        if self.volume == 0:
            return str(Path(folder) / f"{stem}{ext}")
        return str(Path(folder) / f"{stem}_{self.volume + 1:03d}{ext}")

    def _open_next(self):
        if self.fout:
            self.fout.write(self.cfg.lang.get("class_close", "}\n"))
            self.fout.close()

        path = self._volume_path()
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

        if self._append and self.volume == self._first_vol and not self.cfg.data["split_volumes"]:
            # 追加模式 + 不分卷：在现有文件末尾追加（去掉尾部 } 和 @N2C 标记）
            self.fout = open(path, "r+", encoding="utf-8", buffering=1024 * 1024)
            content = self.fout.read()
            # 移除末尾的 @N2C 行和 class_close
            marker = self.cfg.lang["cmt"] + " @N2C:"
            lines = content.split("\n")
            # 从后往前找到最后一个有效代码行（跳过空行、@N2C行、class_close行）
            cut = len(lines)
            while cut > 0:
                stripped = lines[cut - 1].strip()
                if stripped == "" or stripped.startswith(marker) or stripped == "}":
                    cut -= 1
                else:
                    break
            # 截断并重新写入
            self.fout.seek(0)
            self.fout.truncate()
            self.fout.write("\n".join(lines[:cut]) + "\n")
        else:
            self.fout = open(path, "w", encoding="utf-8", buffering=1024 * 1024)

        if self.volume == self._first_vol and self.cfg.data["split_volumes"]:
            print(f"  [目录] → {self._volume_dir()}/")
        if self.volume > self._first_vol:
            print(f"  [分卷] → {Path(path).name}")

    def write(self, text: str):
        self.fout.write(text)

    def add_lines(self, n: int):
        self.lines_written += n
        if self.cfg.data["split_volumes"] and self.lines_written >= self.cfg.data["volume_lines"]:
            self.volume += 1
            self._open_next()

    def set_state(self, data: dict):
        """设置状态数据，close时会写入文件末尾"""
        self._state = data

    def close(self):
        if self.fout:
            # 写入状态标记（在 class_close 之前）
            if self._state is not None:
                cmt = self.cfg.lang["cmt"]
                state_line = f"    {cmt} @N2C:{json.dumps(self._state, ensure_ascii=False)}\n"
                self.fout.write(state_line)
            self.fout.write(self.cfg.lang.get("class_close", "}\n"))
            self.fout.close()
            self.fout = None

    @property
    def total_volumes(self):
        return self.volume + 1

    @property
    def first_volume(self):
        return self._first_vol


# ============================================================
# 七、核心转换器
# ============================================================

CHAPTER_RE = re.compile(r"^第[零一二两三四五六七八九十百千\d]+[章节卷回]")


class Novel2Code:
    """小说 ↔ 源码 双向转换器"""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.rng = random.Random(cfg.data["seed"] or int(time.time() * 1000))
        self.gen = CodeGen(cfg, self.rng)
        self.method_count = 0

    def _is_chapter(self, line: str) -> bool:
        if not self.cfg.data["detect_chapters"]:
            return False
        s = line.strip()
        return bool(CHAPTER_RE.match(s)) and len(s) <= 50

    # ==================== 正向转换 ====================

    _STATE_MARKER = "@N2C:"

    def _load_state(self, output_path: str) -> dict | None:
        """从输出文件末尾注释中加载上次转换状态"""
        vol0_path = self._volume_path(output_path, 0)
        if not os.path.exists(vol0_path):
            return None
        try:
            # 读取文件最后几KB，找 @N2C: 标记
            with open(vol0_path, "r", encoding="utf-8", errors="replace") as f:
                f.seek(0, os.SEEK_END)
                size = f.tell()
                chunk_size = 4096
                f.seek(max(0, size - chunk_size))
                tail = f.read()
                # 查找 @N2C:{...}
                marker_idx = tail.rfind(self._STATE_MARKER)
                if marker_idx >= 0:
                    json_start = marker_idx + len(self._STATE_MARKER)
                    json_str = tail[json_start:].strip()
                    # 截取到第一个换行或 }
                    end = json_str.find("\n")
                    if end > 0:
                        json_str = json_str[:end]
                    return json.loads(json_str)
        except Exception:
            pass
        return None

    def _build_state(self, last_line: int, total_volumes: int, input_path: str) -> dict:
        """构建状态字典"""
        return {
            "last_line": last_line,
            "total_volumes": total_volumes,
            "input_mtime": os.path.getmtime(input_path),
            "input_path": os.path.abspath(input_path),
            "language": self.cfg.data["language"],
        }

    def convert(self, input_path: str, output_path: str = None, append: bool = False):
        """单文件转换，支持增量追加"""
        if output_path is None:
            output_path = str(Path(input_path).with_suffix(self.cfg.lang["ext"]))
        t0 = time.time()

        # ── 增量模式：加载状态 ──
        start_line = 0
        start_volume = 0
        state = None
        if append:
            state = self._load_state(output_path)
            if state and os.path.abspath(input_path) == state.get("input_path"):
                start_line = state.get("last_line", 0)
                start_volume = state.get("total_volumes", 0)
                print(f"[增量] 从第 {start_line + 1} 行开始追加 "
                      f"(已处理 {start_line} 行, {start_volume} 卷)")
            elif state:
                print("[增量] 输入文件已变更，将重新全量转换")
                append = False
            else:
                print("[增量] 未找到状态文件，将全量转换")
                append = False

        # 扫描章节
        chapter_lines = set()
        total_lines = 0
        with open(input_path, "r", encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f):
                total_lines += 1
                if i >= start_line and self._is_chapter(line):
                    chapter_lines.add(i)

        new_lines = total_lines - start_line
        if new_lines <= 0:
            print(f"[完成] 无新增内容 (当前{total_lines}行, 已处理{start_line}行)")
            return

        print(f"[扫描] {total_lines} 行 ({new_lines} 新增), {len(chapter_lines)} 章节 | "
              f"语言={self.cfg.lang['name']} | 评论={self.cfg.cmt_mode} "
              f"({'分卷' if self.cfg.data['split_volumes'] else '单文件'})"
              f"{' 增量' if append else ''} "
              f"({time.time()-t0:.1f}s)")

        # 构建分段（仅新增部分）
        segments = self._build_segments(total_lines, chapter_lines, skip_before=start_line)

        # 增量 + 不分卷：追加到现有文件，不需要 preamble
        # 全量 / 分卷：创建新文件
        vw = VolumeWriter(output_path, self.cfg,
                          append=append and not self.cfg.data["split_volumes"],
                          start_volume=start_volume if self.cfg.data["split_volumes"] else 0,
                          start_lines=start_line % self.cfg.data["volume_lines"]
                          if self.cfg.data["split_volumes"] else 0)

        with open(input_path, "r", encoding="utf-8", errors="replace") as fin:
            # Preamble（增量追加时跳过）
            preamble_skip = 0
            if not append or self.cfg.data["split_volumes"]:
                preamble_limit = min(
                    self.rng.randint(10, 30),
                    segments[0][0] if segments else total_lines,
                    total_lines - max(len(segments) * 3, 3)
                )
                preamble_lines = []
                fin.seek(0)
                for i, line in enumerate(fin):
                    if i >= preamble_limit:
                        break
                    preamble_lines.append(line.rstrip("\n").rstrip("\r"))
                self._write_preamble(vw, preamble_lines)
                preamble_skip = len(preamble_lines)

            # 方法体（单遍流式，增量模式下跳过头 start_line 行）
            effective_skip = max(preamble_skip, start_line)
            fin.seek(0)
            seg_idx = 0
            method_lines = []
            method_title = ""
            total_to_process = total_lines - effective_skip
            processed = 0
            last_pct = -1

            for line_no, line in enumerate(fin):
                if line_no < effective_skip:
                    continue
                processed += 1

                # 进度
                pct = processed * 100 // max(total_to_process, 1)
                if pct != last_pct and pct % 5 == 0:
                    elapsed = time.time() - t0
                    eta = elapsed / max(pct, 1) * (100 - pct)
                    bar = "#" * (pct // 5) + "-" * (20 - pct // 5)
                    print(f"\r[进度] [{bar}] {pct}% | {processed}/{total_to_process} | "
                          f"已耗时 {elapsed:.0f}s | 预计剩余 {eta:.0f}s  ", end="", flush=True)
                    last_pct = pct

                # 段边界检测
                while seg_idx < len(segments) and line_no >= segments[seg_idx][1]:
                    if method_lines:
                        try:
                            self._write_method(vw, method_title, method_lines)
                        except Exception as e:
                            print(f"\n[跳过] 第{seg_idx}段写入失败: {e}")
                        method_lines = []
                    seg_idx += 1

                if seg_idx >= len(segments):
                    break

                seg_start, seg_end, seg_title = segments[seg_idx]
                if line_no < seg_start:
                    if method_lines:
                        try:
                            self._write_method(vw, method_title, method_lines)
                        except Exception as e:
                            print(f"\n[跳过] 第{seg_idx}段写入失败: {e}")
                        method_lines = []
                    continue

                if not method_lines:
                    method_title = seg_title
                method_lines.append(line)

            # 最后一个段
            if method_lines and seg_idx < len(segments):
                try:
                    self._write_method(vw, method_title, method_lines)
                except Exception as e:
                    print(f"\n[跳过] 末段写入失败: {e}")

            # 完成
            elapsed = time.time() - t0
            print(f"\r[进度] [####################] 100% | {processed}/{total_to_process} | "
                  f"耗时 {elapsed:.1f}s                     ")

            # 诊断：检查是否有遗漏行
            if processed < total_to_process:
                missing = total_to_process - processed
                first_miss = effective_skip + processed + 1
                print(f"[警告] {missing} 行未处理！处理止于第 {first_miss - 1} 行附近。")
                print(f"       检查原文第 {first_miss} 行内容: 可能有编码损坏或异常字符。")

        # 嵌入状态到输出文件末尾（先set_state再close）
        vw.set_state(self._build_state(total_lines, vw.total_volumes, input_path))
        vw.close()

        input_size = os.path.getsize(input_path)
        output_size = sum(
            os.path.getsize(self._volume_path(output_path, v))
            for v in range(vw.total_volumes)
            if os.path.exists(self._volume_path(output_path, v))
        )
        if self.cfg.data["split_volumes"]:
            print(f"[完成] {input_size/1024:.1f}KB → {output_size/1024/1024:.1f}MB "
                  f"({self.method_count}方法, {vw.total_volumes}卷, → {self._volume_path(output_path, 0)})")
        else:
            print(f"[完成] {input_size/1024:.1f}KB → {output_size/1024/1024:.1f}MB "
                  f"({self.method_count}方法, 总耗时{time.time()-t0:.1f}s)"
                  f"{' (增量追加)' if append else ''}")

    def _volume_path(self, base: str, vol: int) -> str:
        stem = Path(base).stem
        ext = Path(base).suffix
        folder = Path(base).parent if not self.cfg.data["split_volumes"] else Path(base).parent / stem
        if vol == 0:
            return str(folder / f"{stem}{ext}")
        return str(folder / f"{stem}_{vol + 1:03d}{ext}")

    def convert_batch(self, paths: list[str], recursive: bool = False):
        """批量转换"""
        files = []
        for p in paths:
            p = p.strip('"')
            if os.path.isdir(p):
                pattern = "**/*.txt" if recursive else "*.txt"
                for f in Path(p).glob(pattern):
                    files.append(str(f))
            elif os.path.isfile(p) and p.lower().endswith(".txt"):
                files.append(p)
            else:
                print(f"[跳过] 非txt文件: {p}")

        if not files:
            print("[错误] 未找到可处理的 .txt 文件")
            return

        print(f"[批量] 共 {len(files)} 个文件\n")
        for i, f in enumerate(files, 1):
            print(f"[{i}/{len(files)}] {f}")
            self.method_count = 0
            self.convert(f)
            print()

    # ==================== 逆转换 ====================

    def reverse(self, input_path: str, output_path: str = None):
        """从 .java/.py/.cpp 等源码文件提取原始小说文本"""
        if output_path is None:
            stem = Path(input_path).stem
            # 去掉 _001 等分卷后缀
            stem = re.sub(r"_\d{3,}$", "", stem)
            output_path = str(Path(input_path).with_name(f"{stem}_restored.txt"))

        # 检测语言以确定注释前缀
        ext = Path(input_path).suffix.lower()
        cmt_prefix = "//"
        for lang_key, tmpl in LANG.items():
            if tmpl["ext"] == ext:
                cmt_prefix = tmpl["cmt"]
                break

        lines_out = 0
        with open(input_path, "r", encoding="utf-8", errors="replace") as fin, \
             open(output_path, "w", encoding="utf-8") as fout:

            for line in fin:
                stripped = line.strip()
                # 跳过状态标记行
                if f"{cmt_prefix} @N2C:" in stripped:
                    continue
                # 匹配注释行（可能是 review 模式带前缀的）
                if stripped.startswith(cmt_prefix):
                    content = stripped[len(cmt_prefix):].strip()
                    # 去掉 review 前缀
                    for prefixes in [REVIEW_PREFIXES, REVIEW_PREFIXES_CN]:
                        for prefix in prefixes:
                            if content.startswith(prefix):
                                content = content[len(prefix):]
                                break
                    if content and not content.startswith("*") and not content.startswith("/"):
                        fout.write(content + "\n")
                        lines_out += 1

        print(f"[逆转换] {input_path} → {output_path}")
        print(f"[完成] 提取 {lines_out} 行文本")

    # ==================== 内部方法 ====================

    def _build_segments(self, total_lines: int, chapter_lines: set,
                         skip_before: int = 0) -> list:
        segments = []
        if chapter_lines and self.cfg.data["detect_chapters"]:
            sorted_ch = [c for c in sorted(chapter_lines) if c >= skip_before]
            if not sorted_ch:
                # 无新章节：按chunk分块
                cs = self.cfg.data["chunk_size"]
                for s in range(skip_before, total_lines, cs):
                    segments.append((s, min(s + cs, total_lines), ""))
                return segments
            sorted_ch.append(total_lines)
            for i in range(len(sorted_ch) - 1):
                start, end = sorted_ch[i], sorted_ch[i + 1]
                span = end - start
                if span > 200:
                    sub = self.rng.randint(60, 120)
                    for s in range(start, end, sub):
                        segments.append((s, min(s + sub, end), ""))
                else:
                    segments.append((start, end, ""))
        else:
            cs = self.cfg.data["chunk_size"]
            for s in range(skip_before, total_lines, cs):
                segments.append((s, min(s + cs, total_lines), ""))
        return segments

    def _write_preamble(self, vw: VolumeWriter, lines: list[str]):
        """写文件头"""
        lang = self.cfg.lang
        it = iter(lines)

        def next_cmt():
            try:
                line = next(it)
                return self.gen.make_preamble_comment(line)
            except StopIteration:
                return None

        # Header (package/imports for Java-like; module doc for Python-like)
        for h in lang["header"](self.cfg):
            vw.write(h)

        # Imports interspersed with novel comments
        for imp in lang.get("imports", []):
            if self.rng.random() < 0.4:
                cmt = next_cmt()
                if cmt:
                    vw.write(cmt)
            vw.write(f"import {imp};\n")

        # Remaining preamble as comments
        while True:
            cmt = next_cmt()
            if cmt is None:
                break
            vw.write(cmt)
        vw.write("\n")

        # Class declaration
        vw.write(lang["method_javadoc"]("------------"))
        vw.write(lang["class_decl"](self.cfg, self.cfg._class_name()))
        class_name = self.cfg._class_name()
        if "{class_name}" in lang["logger"]:
            vw.write(lang["logger"].format(class_name=class_name))
        else:
            vw.write(lang["logger"])

        # Member variables
        num_vars = self.rng.randint(7, 14)
        used = set()
        count = 0
        for _ in range(num_vars):
            n = self.gen.v()
            if n in used:
                continue
            used.add(n)
            vw.write(lang["member_var"](self.gen.vt(), n, self.gen.vi()))
            count += 1
        vw.write("\n")

        # Static constants
        for name, val in [("MAX_RETRIES","3"),("DEFAULT_TIMEOUT","5000"),
                          ("BATCH_SIZE","100"),("CACHE_TTL","30000"),("MAX_POOL_SIZE","16")]:
            vw.write(lang["static_const"](name, val))
        vw.write("\n")

        # Static block / constructor
        sbs = lang["static_block_start"]
        if callable(sbs):
            sbs = sbs(self.cfg)
        elif "{class_name}" in sbs:
            sbs = sbs.format(class_name=class_name)
        vw.write(sbs)
        for _ in range(self.rng.randint(2, 4)):
            vw.write(f"        {self.gen.v()}_ = {self.gen.v()}_\n")
        vw.write(lang["static_block_end"])

    def _write_method(self, vw: VolumeWriter, title: str, lines: list[str]):
        """写一个方法"""
        self.method_count += 1
        lang = self.cfg.lang

        # Javadoc / docstring
        javadoc = title if title else (lines[0].strip()[:80] if lines else "---")
        vw.write(lang["method_javadoc"](javadoc))

        # Signature
        name = self.gen.m()
        ptype = self.gen.pt()
        pvar = self.gen.v()
        # 部分语言(Go)的method_sig需要config参数
        sig = lang["method_sig"]
        try:
            vw.write(sig(self.cfg, name, ptype, pvar))
        except TypeError:
            vw.write(sig(name, ptype, pvar))

        # Null check
        vw.write(lang["null_check"](pvar))

        # Body: text comments + random code
        idx = 0
        while idx < len(lines):
            batch = self.rng.randint(1, 3)
            for _ in range(batch):
                if idx >= len(lines):
                    break
                cmt = self.gen.make_comment(lines[idx].rstrip("\n").rstrip("\r"))
                if cmt:
                    vw.write(cmt)
                idx += 1

            if idx >= len(lines):
                break

            if self.rng.random() < 0.3:
                for bl in self.gen.block():
                    vw.write(f"{bl}\n")
            else:
                vw.write(f"{self.gen.stmt()}\n")

        # Tail statements
        for _ in range(self.rng.randint(2, 5)):
            vw.write(f"{self.gen.stmt()}\n")

        vw.write(lang["close"])
        vw.add_lines(len(lines))


# ============================================================
# 八、CLI
# ============================================================

def interactive_mode():
    """交互模式（双击运行）"""
    print("=" * 55)
    print("  novel2code v2.0 - 小说文本 <-> 源码 双向转换")
    print("=" * 55)
    print()
    print("支持语言: Java | Python | C++ | JavaScript | Go")
    print("支持模式: 拖拽秒转 | 批量目录 | 多卷分片 | 评论伪装 | 逆转换")
    print()

    # 选择操作
    print("请选择操作:")
    print("  1. 正向转换 (txt → 源码)")
    print("  2. 逆转换   (源码 → txt)")
    choice = input("请输入 (1/2): ").strip()

    if choice == "2":
        src = input("源码文件路径: ").strip().strip('"')
        if src and os.path.isfile(src):
            out = input("输出路径 (直接回车=自动): ").strip().strip('"') or None
            cfg = Config()
            converter = Novel2Code(cfg)
            converter.reverse(src, out)
        return

    # 正向转换
    inp = input("输入路径 (文件/目录): ").strip().strip('"')
    if not inp or not os.path.exists(inp):
        print("路径不存在，退出。")
        return

    is_dir = os.path.isdir(inp)

    # 语言选择
    print("\n语言: 1=Java  2=Python  3=C++  4=JavaScript  5=Go")
    lang_map = {"1":"java","2":"python","3":"cpp","4":"javascript","5":"go"}
    lang = lang_map.get(input("选择 (默认1): ").strip(), "java")

    # 评论模式
    print("\n评论模式: 1=行内注释  2=代码审查风格")
    cm = "review" if input("选择 (默认1): ").strip() == "2" else "inline"

    # 分卷
    split = input("\n多卷分片? (y/n, 默认n): ").strip().lower() == "y"
    vol_lines = 10000
    if split:
        vs = input("每卷行数 (默认10000): ").strip()
        vol_lines = int(vs) if vs else 10000

    # 输出路径（仅单文件时询问）
    out = None
    if not is_dir:
        out = input("\n输出路径 (直接回车=自动): ").strip().strip('"') or None

    cfg = Config(
        language=lang, comment_mode=cm,
        split_volumes=split, volume_lines=vol_lines,
    )
    append = input("\n增量追加? (y/n, 默认n): ").strip().lower() == "y"

    converter = Novel2Code(cfg)

    if is_dir:
        recursive = input("递归子目录? (y/n, 默认n): ").strip().lower() == "y"
        converter.convert_batch([inp], recursive)
    else:
        converter.convert(inp, out, append=append)


def main():
    # 无参数 → 交互模式
    if len(sys.argv) <= 1:
        interactive_mode()
        return

    # 拖拽模式（仅1个参数=文件路径）
    if len(sys.argv) == 2 and not sys.argv[1].startswith("-") and os.path.isfile(sys.argv[1]):
        path = sys.argv[1].strip('"')
        ext_lower = Path(path).suffix.lower()

        # 检测是否是源码文件 → 自动逆转换
        code_exts = {".java", ".py", ".cpp", ".js", ".go", ".ts", ".cs", ".rs"}
        if ext_lower in code_exts:
            print(f"检测到源码文件 → 自动逆转换: {path}")
            cfg = Config()
            converter = Novel2Code(cfg)
            converter.reverse(path)
        else:
            cfg = Config()
            converter = Novel2Code(cfg)
            output_path = str(Path(path).with_suffix(cfg.lang["ext"]))
            print(f"拖拽模式: {path} → {output_path}")
            converter.convert(path, output_path)
        return

    # 命令行模式
    parser = argparse.ArgumentParser(
        description="novel2code v2.0 - 小说文本 ↔ 源码 双向转换",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python novel2code.py novel.txt                    默认转换(Java)
  python novel2code.py novel.txt -l python          转为Python
  python novel2code.py novel.txt -l cpp --split     多卷C++
  python novel2code.py novel.txt -m review           代码审查评论模式
  python novel2code.py novel.txt --review-cn         中文审查前缀
  python novel2code.py novel.txt --append            增量追加：只转新增内容
  python novel2code.py ./novels/ -b -r              批量递归目录
  python novel2code.py all.java --reverse            逆转换: 源码→小说
  python novel2code.py --init-config                 生成配置文件
  python novel2code.py novel.txt -c myconfig.json    使用自定义配置
        """,
    )
    parser.add_argument("input", nargs="*", help="输入文件/目录路径")
    parser.add_argument("-o", "--output", default=None, help="输出路径")
    parser.add_argument("-l", "--lang", default="java",
                        choices=["java","python","cpp","javascript","go"],
                        help="目标语言 (默认: java)")
    parser.add_argument("-m", "--mode", default="inline",
                        choices=["inline","review"],
                        help="注释模式 (默认: inline)")
    parser.add_argument("--review-cn", action="store_true",
                        help="审查模式使用中文前缀")
    parser.add_argument("--review-en", action="store_true",
                        help="审查模式使用英文前缀")
    parser.add_argument("--split", action="store_true", help="启用多卷分片")
    parser.add_argument("--vol-lines", type=int, default=10000,
                        help="每卷输入行数 (默认: 10000)")
    parser.add_argument("--chunk", type=int, default=50, help="分块大小")
    parser.add_argument("--seed", type=int, default=None, help="随机种子")
    parser.add_argument("--no-chapter", action="store_true", help="不检测章节")
    parser.add_argument("-b", "--batch", action="store_true", help="批量模式")
    parser.add_argument("-r", "--recursive", action="store_true",
                        help="递归处理子目录")
    parser.add_argument("--reverse", action="store_true", help="逆转换模式")
    parser.add_argument("--append", action="store_true",
                        help="增量追加：只转换txt新增内容，追加到现有文件")
    parser.add_argument("-c", "--config", default=None, help="JSON配置文件路径")
    parser.add_argument("--init-config", action="store_true",
                        help="生成默认配置文件 novel2code.json")

    args = parser.parse_args()

    # 生成配置文件
    if args.init_config:
        Config.save_default("novel2code.json")
        return

    # 加载配置
    overrides = {}
    if args.config and os.path.exists(args.config):
        overrides = Config.load_from_json(args.config)

    # 确定审查风格
    review_style = "mixed"
    if args.review_cn:
        review_style = "cn"
    elif args.review_en:
        review_style = "en"

    overrides.update({
        "language": args.lang,
        "comment_mode": args.mode,
        "review_style": review_style,
        "split_volumes": args.split,
        "volume_lines": args.vol_lines,
        "chunk_size": args.chunk,
        "seed": args.seed,
        "detect_chapters": not args.no_chapter,
    })
    # 移除None值
    overrides = {k: v for k, v in overrides.items() if v is not None}

    cfg = Config(**overrides)
    converter = Novel2Code(cfg)

    # 逆转换
    if args.reverse:
        if not args.input:
            print("[错误] 请指定要逆转换的源码文件")
            return
        for inp in args.input:
            converter.reverse(inp.strip('"'))
        return

    # 批量模式
    if args.batch or len(args.input) > 1:
        paths = [p.strip('"') for p in args.input]
        converter.convert_batch(paths, args.recursive)
        return

    # 单目录（隐式批量）
    if args.input and os.path.isdir(args.input[0].strip('"')):
        converter.convert_batch([args.input[0].strip('"')], args.recursive)
        return

    # 单文件转换
    if args.input:
        inp = args.input[0].strip('"')
        converter.convert(inp, args.output, append=args.append)
    else:
        interactive_mode()


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        pass
    except Exception as e:
        print(f"\n[错误] {e}")
    finally:
        try:
            input("\n按回车键退出...")
        except EOFError:
            pass
