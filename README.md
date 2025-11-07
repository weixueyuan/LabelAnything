# 标注工具平台

这是一个模块化的、支持多任务、多用户的标注工具平台。该平台基于 Gradio 构建，具有高度的可扩展性和可配置性。

## 核心特性

- **模块化设计**: 每个标注任务都是一个独立的模块，拥有自己的UI配置、组件和逻辑。
- **多任务支持**: 系统可以同时运行和管理多个不同的标注任务。
- **多用户系统**: 支持用户登录和权限管理，数据会根据用户进行隔离。
- **可配置UI**: 通过简单的Python配置文件即可定义和修改标注界面，无需编写前端代码。
- **数据后端**: 支持 JSONL 文件（用于调试）和 SQLite 数据库（用于生产）。

## 目录结构

```
.
├── config/                # 用户和管理员配置文件
├── database_jsonl/        # 用于Debug模式的JSONL数据文件
├── databases/             # SQLite数据库文件
├── exports/               # 导出数据存放目录
├── src/                   # 核心源代码
│   ├── importers/         # 数据导入脚本
│   ├── ui_configs/        # 各任务的UI配置文件
│   ├── __init__.py
│   ├── auth_handler.py    # 用户认证
│   ├── component_factory.py # Gradio组件工厂
│   ├── db_handler.py      # 数据库操作
│   ├── db_models.py       # 数据库模型
│   ├── field_processor.py # 字段处理器
│   ├── jsonl_handler.py   # JSONL文件操作
│   ├── main_multi.py      # 主程序入口
│   └── routes.py          # 任务路由配置
└── tools/                 # 辅助工具脚本
```

## 快速开始

### 1. 环境准备

建议使用 Python 3.10+。

```bash
pip install -r requirements.txt
```
*(注意: `requirements.txt` 文件需要您根据实际依赖创建)*

### 2. 初始化数据

在使用数据库模式前，需要先将原始数据导入到指定任务的数据库中。

例如，为 `whole_annotation` 任务导入数据：
```bash
python -m src.importers.generic_importer --task whole_annotation --file /path/to/your/data.jsonl
```

### 3. 运行标注任务

你可以运行一个特定的标注任务，或者列出所有可用的任务。

**列出所有可用任务:**
```bash
python src/main_multi.py --list-tasks
```

**运行 "整体物体标注" (`whole_annotation`) 任务:**
```bash
python src/main_multi.py --task whole_annotation
```
然后浏览器访问 `http://0.0.0.0:7801`。

**运行 "部件标注" (`part_annotation`) 任务:**
```bash
python src/main_multi.py --task part_annotation --port 7802
```
然后浏览器访问 `http://0.0.0.0:7802`。

### 4. 开发模式

使用 `--dev` 标志可以跳过登录界面，直接以开发者身份进入。
```bash
python src/main_multi.py --task whole_annotation --dev --uid my_dev_user
```

## 如何添加一个新任务

1.  **创建UI配置文件**: 在 `src/ui_configs/` 目录下创建一个新的 `[your_task_name]_config.py` 文件。参考 `whole_annotation_config.py` 的结构，定义 `COMPONENTS`, `LAYOUT_CONFIG` 等。
2.  **添加入口路由**: 在 `src/routes.py` 文件中，为你的新任务添加一条新的路由记录，指定 `task`, `port` 等信息。
3.  **创建数据导入器 (可选)**: 如果需要，可以在 `src/importers/` 中为新任务创建特定的数据导入逻辑。
4.  **运行**: 使用 `python src/main_multi.py --task [your_task_name]` 启动新任务。

## UI 配置详解

每个任务的 UI 都是通过其在 `src/ui_configs/` 目录下的配置文件（例如 `whole_annotation_config.py`）来定义的。核心配置项包括 `COMPONENTS`、`LAYOUT_CONFIG` 和 `CUSTOM_CSS`。

### 1. `COMPONENTS`: 定义所有组件

`COMPONENTS` 是一个列表，其中每个元素都是一个字典，用于定义一个 Gradio 组件。

-   `id`: 组件的唯一标识符，**非常重要**，用于在布局和后台逻辑中引用该组件。建议直接使用数据字段名。
-   `type`: 组件的类型，例如 `textbox`, `image`, `slider`, `checkbox`。
-   `label`: 组件在界面上显示的标签。
-   `data_field`: （可选）指定该组件对应于数据库中哪个字段。如果省略，则默认使用 `id` 作为字段名。
-   `has_checkbox`: （可选）如果为 `True`，会自动在该组件上方添加一个“标记为错误”的复选框。
-   其他参数: 所有其他键值对都会被直接传递给对应的 Gradio 组件构造函数（例如 `lines`, `placeholder`, `minimum`, `maximum` 等）。

**示例:**
```python
COMPONENTS = [
    # 图片预览
    {
        "id": "image_url",
        "type": "image",
        "label": "GIF预览",
    },
    # 文本输入框
    {
        "id": "object_name",
        "type": "textbox",
        "label": "物体名称",
        "has_checkbox": True, # 带错误标记
    },
    # 滑块
    {
        "id": "scale_slider",
        "type": "slider",
        "label": "尺度调整",
        "minimum": 0.1,
        "maximum": 2.0,
        "value": 1.0,
        "target_field": "dimension" # 特殊字段，用于指定滑块控制的目标
    }
]
```

### 2. `LAYOUT_CONFIG`: 组织页面布局

`LAYOUT_CONFIG` 是一个字典，它以树状结构定义了所有组件在页面上的排列方式。

-   `type`: 布局容器的类型，目前支持 `hstack` (水平排列) 和 `vstack` (垂直排列)。
-   `children`: 一个列表，包含了要放入该容器的子项。
    -   如果子项是**字符串**，它必须是 `COMPONENTS` 中定义过的一个组件 `id`。
    -   如果子项是**字典**，它本身就是一个嵌套的布局容器。

**示例:**
```python
# 定义一个两栏布局：左边是图片，右边是所有输入字段
LAYOUT_CONFIG = {
    "type": "hstack", # 最外层是水平布局
    "children": [
        # 左栏
        {
            "type": "vstack",
            "children": ["image_url"] # 左栏只放图片
        },
        # 右栏
        {
            "type": "vstack",
            "children": [
                "object_name",
                "scale_slider",
                "progress_box" # progress_box 是一个内置组件
            ]
        }
    ]
}
```

### 3. `CUSTOM_CSS` (高级)

`CUSTOM_CSS` 是一个字符串，允许你为当前任务的界面注入自定义的 CSS 样式，以实现更精细的视觉调整。

**示例:**
```python
CUSTOM_CSS = """
/* 让主内容区域的左右两栏等高 */
#main_content_row {
    align-items: stretch !important;
}

/* 给尺寸调整模块加一个背景和边框 */
#dimension_block {
    background: rgba(0, 0, 0, 0.02);
    border: 1px solid rgba(0, 0, 0, 0.08);
    border-radius: 10px;
    padding: 12px;
}
"""
```