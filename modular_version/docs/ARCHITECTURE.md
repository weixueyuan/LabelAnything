# 架构总览

## 📁 目录结构

```
modular_version/
│
├── ui_configs/                      # UI配置（一个任务一个文件）
│   ├── __init__.py
│   └── annotation_config.py         ← 标注任务配置
│
├── importers/                       # 导入器（一个任务一个导入器）
│   ├── __init__.py
│   ├── base_importer.py             ← 基础导入器类
│   └── annotation_importer.py       ← 标注导入器（可直接运行）
│
├── databases/                       # 数据库（一个任务一个DB）
│   └── annotation.db                ← 导入后生成
│
├── src/                             # 核心代码
│   ├── __init__.py
│   ├── db_models.py                 ← 数据库模型（通用，支持JSON）
│   ├── db_handler.py                ← 数据库操作
│   ├── field_processor.py           ← 字段处理
│   ├── ui_builder.py                ← UI构建
│   └── main_multi.py                ← 主程序
│
├── docs/                            # 文档
│   ├── ARCHITECTURE.md              ← 本文档
│   ├── DATABASE_GUIDE.md            ← 数据库操作指南
│   ├── HOW_TO_ADAPT_NEW_DATA.md     ← 适配新数据教程
│   └── DATA_FORMAT.md               ← 数据格式说明
│
├── routes.py                        # 路由配置
├── run.sh                           # 启动脚本
├── merged_attributes.jsonl          # 原始数据
├── README.md                        # 项目说明
├── QUICKSTART.md                    # 快速开始
└── .gitignore                       # Git忽略配置
```

---

## 🎯 设计原则

### 1. 约定优于配置

```
一个任务 = 三个同名文件（按 task 名称自动关联）

task = "annotation"
  ↓
├── ui_configs/annotation_config.py    ← UI配置
├── databases/annotation.db            ← 数据库
└── importers/annotation_importer.py   ← 导入器
```

**好处**：
- 无需手动配置映射关系
- 文件命名即配置
- 添加新任务只需3个文件

---

### 2. 字段自动映射

```python
# UI配置
FIELD_CONFIG = [
    {"key": "category", ...},  # ← 字段名
]

# 数据库
data = {"category": "chair"}  # ← 相同的key，自动映射

# 导入器
def transform_record(self, attrs):
    return {"category": attrs.get("原始字段名")}  # ← 转换到标准字段名
```

**好处**：
- 无需FIELD_MAPPING配置
- 减少出错可能
- 代码更简洁

---

### 3. 模块职责分离

```
ui_configs/     → 定义界面如何显示
importers/      → 定义数据如何导入
databases/      → 存储标准化数据
src/            → 核心逻辑（不需要修改）
routes.py       → 定义任务映射
```

**好处**：
- 清晰的职责边界
- 便于维护和扩展
- 核心代码稳定

---

## 🔄 数据流程

### 导入流程

```
原始数据（merged_attributes.jsonl）
  ↓
【导入器】annotation_importer.py
  ├─ parse_source()     # 读取原始文件
  ├─ transform_record() # 字段映射：原始 → 标准
  └─ import_to_db()     # 写入数据库
  ↓
【数据库】databases/annotation.db
  ├─ model_id (主键)
  ├─ annotated, uid, score (元数据)
  └─ data (JSON字段：所有业务数据)
```

### 运行流程

```
【启动】python src/main_multi.py --uid user1
  ↓
【路由】routes.py
  ├─ 读取任务配置: task="annotation"
  └─ 自动关联:
      ├─ ui_configs/annotation_config.py
      └─ databases/annotation.db
  ↓
【TaskManager】
  ├─ 加载UI配置（字段、路径等）
  ├─ 连接数据库
  ├─ 过滤用户可见数据
  └─ 构建Gradio界面
  ↓
【界面显示】
  ├─ 加载数据 (load_data)
  ├─ 保存数据 (save_data)
  └─ 导航操作 (prev/next)
```

---

## 🗃️ 数据库设计

### 表结构

```sql
CREATE TABLE annotations (
    model_id TEXT PRIMARY KEY,       -- 模型ID
    annotated BOOLEAN DEFAULT 0,     -- 是否已标注
    uid TEXT DEFAULT '',             -- 标注者ID
    score INTEGER DEFAULT 1,         -- 质量分数
    data JSON DEFAULT '{}',          -- 业务数据（JSON）
    created_at DATETIME,             -- 创建时间
    updated_at DATETIME              -- 更新时间
);
```

### 为什么使用 JSON 字段？

✅ **灵活性**：
- 不同任务可以有不同字段
- 无需为每个任务修改表结构

✅ **扩展性**：
- 添加新字段无需数据迁移
- 支持复杂的嵌套数据

✅ **简洁性**：
- 一个表支持所有任务
- 代码逻辑统一

### 数据示例

```json
{
  "model_id": "type-subtype-category-001",
  "annotated": true,
  "uid": "user1",
  "score": 1,
  "data": {
    "category": "chair",
    "description": "A modern chair",
    "material": "wood",
    "placement": "OnFloor",
    "chk_category": false,
    "chk_description": false,
    "chk_material": false,
    "chk_placement": false
  }
}
```

---

## 🧩 核心模块说明

### 1. ui_configs/

**职责**：定义任务的UI配置

**配置内容**：
- `TASK_INFO`: 任务基本信息
- `FIELD_CONFIG`: 字段定义（key、label、type等）
- `UI_CONFIG`: 界面配置（标题、勾选框等）
- `PATH_CONFIG`: 路径配置（图片路径模板）

**示例**：
```python
FIELD_CONFIG = [
    {
        "key": "category",          # 数据库字段名
        "label": "Category",        # 显示标签
        "type": "textbox",          # 组件类型
        "lines": 1,                 # 行数
        "has_checkbox": True,       # 是否显示勾选框
        "process": None             # 处理方式
    }
]
```

---

### 2. importers/

**职责**：将各种格式的原始数据导入到数据库

**核心方法**：
- `parse_source()`: 读取原始数据
- `transform_record()`: 字段转换（原始→标准）
- `import_to_db()`: 写入数据库

**特点**：
- 继承 `BaseImporter`
- 可作为模块导入：`from importers.annotation_importer import AnnotationImporter`
- 可直接运行：`python -m importers.annotation_importer`

---

### 3. src/

**职责**：核心业务逻辑（一般不需要修改）

**主要文件**：
- `db_models.py`: SQLAlchemy模型定义
- `db_handler.py`: 数据库CRUD操作
- `field_processor.py`: 字段处理（加载/保存时的类型转换）
- `ui_builder.py`: UI构建工具（暂未使用）
- `main_multi.py`: 主程序入口

---

### 4. routes.py

**职责**：定义任务路由映射

**示例**：
```python
ROUTES = [
    {
        "url": "/annotation",       # URL路径
        "task": "annotation",       # 任务名（关联文件）
        "port": 7800,               # 端口
        "description": "物体属性标注"
    }
]
```

**约定**：
- `task` 字段用于自动关联配置文件
- `task="annotation"` → `ui_configs/annotation_config.py`
- `task="annotation"` → `databases/annotation.db`
- `task="annotation"` → `importers/annotation_importer.py`

---

## 🚀 添加新任务流程

### 步骤1：创建UI配置
`ui_configs/review_config.py`

### 步骤2：创建导入器
`importers/review_importer.py`

### 步骤3：添加路由
在 `routes.py` 添加一行

### 步骤4：导入数据
```bash
python -m importers.review_importer
```

### 步骤5：启动
```bash
python src/main_multi.py --uid user1
```

**详细教程**：查看 [HOW_TO_ADAPT_NEW_DATA.md](HOW_TO_ADAPT_NEW_DATA.md)

---

## ✅ 优势总结

| 特性 | 说明 | 好处 |
|------|------|------|
| **约定优于配置** | task名称自动关联文件 | 减少配置工作 |
| **字段自动映射** | key名相同即映射 | 无需手动配置 |
| **模块化设计** | 清晰的职责分离 | 易于维护 |
| **灵活数据库** | JSON字段动态存储 | 支持不同任务 |
| **独立导入器** | 可单独运行 | 便于测试和调试 |
| **可扩展** | 添加新任务只需3个文件 | 快速扩展 |

---

## 📚 相关文档

- [README.md](../README.md) - 项目总览
- [QUICKSTART.md](../QUICKSTART.md) - 快速开始
- [DATABASE_GUIDE.md](DATABASE_GUIDE.md) - 数据库操作
- [HOW_TO_ADAPT_NEW_DATA.md](HOW_TO_ADAPT_NEW_DATA.md) - 适配新数据
- [DATA_FORMAT.md](DATA_FORMAT.md) - 数据格式

---

**当前状态**：单任务架构（annotation），支持轻松扩展到多任务。


