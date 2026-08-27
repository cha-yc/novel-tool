# novel-tool

小说文本 ↔ 源码 双向转换工具。

将 `.txt` 小说伪装成多种编程语言的源码文件，支持批量、分卷、增量追加、逆转换。

## 快速开始

```bash
# 拖拽 .txt 到 src/novel2code/novel2code.py 上 → 一键转 Java

# 或命令行
python src/novel2code/novel2code.py novel.txt                     # 默认 Java
python src/novel2code/novel2code.py novel.txt -l python           # Python
python src/novel2code/novel2code.py novel.txt -m review           # 审查评论模式
python src/novel2code/novel2code.py novel.txt --split             # 多卷分片
python src/novel2code/novel2code.py novel.txt --append            # 增量追加
python src/novel2code/novel2code.py all.java --reverse            # 逆转换
```

## 功能

| 功能 | 说明 |
|------|------|
| **5种语言** | Java / Python / C++ / JavaScript / Go |
| **评论模式** | 小说文本伪装成 TODO/FIXME/NOTE 等审查注释 |
| **多卷分片** | 长篇小说自动拆分成多文件项目 |
| **增量追加** | 小说更新后只转新增内容 |
| **逆转换** | 从生成的源码提取回原始 .txt |
| **批量处理** | 拖入文件夹一次性转换所有 .txt |

## 目录结构

```
novel-tool/
├── README.md
├── .gitignore
└── src/
    ├── novel2code/
    │   └── novel2code.py   # 核心工具（小说转代码）
    ├── adb-runner/
    │   ├── main.py         # ADB 脚本工具入口
    │   ├── core/           # store / adb / logger
    │   ├── ui/             # 主窗口 / 设备面板 / 输出区
    │   └── data/           # 脚本数据（由 src/temp 复制种子）
    └── temp/               # 脚本数据（暂存，非本工具）
```

## ADB 脚本工具

`src/adb-runner/` 是一个基于 PySide6 的可视化 ADB 脚本执行工具，支持设备切换、长按拖拽排序、边界自动滚动、分组计数、三档日志与秒开启动。

### 运行方式

```bash
# 1. 双击 src/adb-runner/启动ADB脚本工具.vbs（推荐：隐藏启动、无 cmd 窗口闪烁）
# 2. 双击 src/adb-runner/启动ADB脚本工具.bat（会闪一下 cmd 窗口，便于看到报错）
# 3. 命令行
.\.venv\Scripts\python src\adb-runner\main.py
```

> 注意：不要直接双击 `main.py`——系统 Python 没装 PySide6，会启动失败。

### 打包成 exe

双击 `src/adb-runner/打包exe.bat` 即可自动安装 PyInstaller 并打包，产物在 `src/adb-runner/dist/ADB脚本工具.exe`，脚本数据自动复制到 exe 同目录 `data\`。

> exe 约 36MB，几乎全部来自 PySide6 的 Qt 运行库和 Python 解释器（本工具自己的代码 + 数据不足 200KB）。已卸载 PySide6-Addons 只保留 Essentials 精简过体积。

### 数据

脚本数据位于 `src/adb-runner/data/`，如需同步 `src/temp/` 的更新，复制对应 JSON 覆盖即可。

## 依赖

Python 3.9+，无需额外安装依赖。
