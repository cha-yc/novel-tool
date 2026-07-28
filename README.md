# novel-tool

小说文本 ↔ 源码 双向转换工具。

将 `.txt` 小说伪装成多种编程语言的源码文件，支持批量、分卷、增量追加、逆转换。

## 快速开始

```bash
# 拖拽 .txt 到 src/novel2code.py 上 → 一键转 Java

# 或命令行
python src/novel2code.py novel.txt                     # 默认 Java
python src/novel2code.py novel.txt -l python           # Python
python src/novel2code.py novel.txt -m review           # 审查评论模式
python src/novel2code.py novel.txt --split             # 多卷分片
python src/novel2code.py novel.txt --append            # 增量追加
python src/novel2code.py all.java --reverse            # 逆转换
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
    └── novel2code.py      # 核心工具
```

## 依赖

Python 3.9+，无需额外安装依赖。
