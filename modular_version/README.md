# 物体属性标注工具 - 模块化版本

> 🎯 基于约定优于配置的架构，极简、灵活、易扩展

## 📁 目录结构

```
modular_version/
│
├── ui_configs/              # UI配置（一个任务一个文件）
│   ├── __init__.py
│   └── annotation_config.py  ← 标注任务配置
│
├── databases/               # 数据库（一个任务一个DB）
│   └── annotation.db         ← 导入后生成
│
├── importers/               # 导入器（一个任务一个导入器）
│   ├── __init__.py
│   ├── base_importer.py     ← 基础导入器类
│   └── annotation_importer.py ← 标注任务导入器（可直接运行）
│
├── routes.py                # 路由配置
│
├── src/                     # 核心代码
│   ├── db_models.py         ← 数据库模型（JSON字段）
│   ├── db_handler.py        ← 数据库操作
│   ├── field_processor.py   ← 字段处理
│   ├── ui_builder.py        ← UI构建
│   └── main_multi.py        ← 主程序
│
├── merged_attributes.jsonl  ← 原始数据
└── docs/                    ← 文档
```

## 🚀 快速开始

### 1. 导入数据

```bash
# 方式1：作为模块运行（推荐）
python -m importers.annotation_importer

# 方式2：直接运行
python importers/annotation_importer.py

# 其他选项
python -m importers.annotation_importer --source data.jsonl  # 指定文件
python -m importers.annotation_importer --clean              # 清空后导入
```

### 2. 启动程序

```bash
python src/main_multi.py --uid user1
```

### 3. 访问界面

浏览器打开：`http://localhost:7800`

---

## ⚙️ 配置说明

### 字段配置

编辑 `ui_configs/annotation_config.py` 中的 `FIELD_CONFIG`：

```python
FIELD_CONFIG = [
    {
        "key": "category",          # 字段名（自动对应数据库）
        "label": "Category (类别)",  # 显示标签
        "type": "textbox",          # 组件类型
        "lines": 1,
        "has_checkbox": True,
        "process": None             # 处理类型
    },
    # 添加更多字段...
]
```

### 路由配置

编辑 `routes.py`：

```python
ROUTES = [
    {
        "url": "/annotation",
        "task": "annotation",       # 自动关联：
        "port": 7800,              # - ui_configs/annotation_config.py
        "description": "物体属性标注" # - databases/annotation.db
    },                              # - importers/annotation_importer.py
]
```

---

## 📊 架构设计

### 约定优于配置

```
一个任务 = 三个同名文件（按 task 名称自动关联）

task = "annotation"
  ↓
├── ui_configs/annotation_config.py    ← UI配置
├── databases/annotation.db            ← 数据库
└── importers/annotation_importer.py   ← 导入器
```

### 字段自动映射

```python
# ui_configs/annotation_config.py
FIELD_CONFIG = [
    {"key": "category", ...},  # ← key名
]

# 数据库（db_models.py）
data = {
    "category": "chair"  # ← 相同的key，自动映射
}
```

### 数据库设计

使用 **JSON 字段** 存储业务数据，支持灵活字段：

```sql
CREATE TABLE annotations (
    model_id TEXT PRIMARY KEY,
    annotated BOOLEAN,
    uid TEXT,
    score INTEGER,
    data JSON,              -- 所有业务字段存这里
    created_at DATETIME,
    updated_at DATETIME
);
```

---

## 🔄 添加新任务

只需 3 步：

### 1. 创建 UI 配置

`ui_configs/review_config.py`：

```python
TASK_INFO = {"task_id": "review", ...}
FIELD_CONFIG = [...]  # 定义字段
UI_CONFIG = {...}
PATH_CONFIG = {...}
```

### 2. 创建导入器

`importers/review_importer.py`：

```python
from importers.base_importer import BaseImporter

class ReviewImporter(BaseImporter):
    def parse_source(self, source): ...
    def transform_record(self, attrs): ...

if __name__ == "__main__":
    # 命令行入口
    ...
```

### 3. 添加路由

在 `routes.py` 添加：

```python
{
    "url": "/review",
    "task": "review",      # ← 自动关联上面两个文件
    "port": 7801,
    "description": "质量审核"
}
```

完成！运行：
```bash
python -m importers.review_importer
python src/main_multi.py --uid user1
```

---

## 📚 核心模块

### importers/

每个导入器负责：
1. 读取原始数据（JSONL、CSV、Excel...）
2. 字段转换（原始格式 → 标准格式）
3. 写入数据库

**特点**：
- 继承 `BaseImporter`
- 可直接运行（`python -m importers.xxx_importer`）
- 独立的命令行参数

### ui_configs/

每个任务的UI配置：
- `TASK_INFO`: 任务信息
- `FIELD_CONFIG`: 字段定义
- `UI_CONFIG`: 界面配置
- `PATH_CONFIG`: 路径配置

### routes.py

定义任务路由映射，按约定自动关联文件。

---

## ✅ 优势总结

| 特性 | 说明 |
|------|------|
| **约定优于配置** | task名称自动关联3个文件 |
| **字段自动映射** | key名相同即可，无需手动配置 |
| **独立导入器** | 每个任务独立导入，可单独运行 |
| **灵活数据库** | JSON字段支持不同任务不同字段 |
| **易于扩展** | 添加新任务只需3个文件 |

---

## 🛠️ 常用命令

```bash
# 导入数据
python -m importers.annotation_importer

# 启动程序
python src/main_multi.py --uid user1 --port 7800

# 查看数据库
sqlite3 databases/annotation.db "SELECT COUNT(*) FROM annotations"
```

---

**开始使用**：
```bash
python -m importers.annotation_importer
python src/main_multi.py --uid your_name
```
