# LabelAnything

A modular, multi-task, multi-user annotation platform built on Gradio. Highly extensible and configurable, designed for efficient data labeling in research and production.

[中文说明见此](#中文说明)

---

## Features

- **Modular Design**: Each annotation task is an independent module with its own UI configuration, components, and logic.
- **Multi-Task Support**: Run and manage multiple annotation tasks simultaneously.
- **Multi-User System**: User login and permission management, with data isolation per user.
- **Configurable UI**: Define and modify annotation interfaces via simple Python config files—no frontend coding required.
- **Flexible Backend**: Supports JSONL files (for debugging) and SQLite databases (for production).

---

## Installation & Quick Start

### 1. Environment

Python 3.10 recommended.

```bash
pip install -r requirements.txt
```
*(Note: Please ensure `requirements.txt` matches your actual dependencies.)*

### 2. Data Initialization

Before using database mode, import your raw data into the target task's database.

Example for `whole_annotation` task:

```bash
python -m src.importers.generic_importer --task whole_annotation --file /path/to/your/data.jsonl
```

### 3. Run Annotation Tasks

**List all available tasks:**
```bash
python src/main_multi.py --list-tasks
```

**Run "Whole Object Annotation" (`whole_annotation`):**
```bash
python src/main_multi.py --task whole_annotation
```
Then visit http://0.0.0.0:7801 in your browser.

**Run "Part Annotation" (`part_annotation`):**
```bash
python src/main_multi.py --task part_annotation --port 7802
```
Then visit http://0.0.0.0:7802.

### 4. Development Mode

Skip login and enter as developer:
```bash
python src/main_multi.py --task whole_annotation --dev --uid my_dev_user
```

---

## Project Structure

```
.
├── config/                # User and admin config files
├── database_jsonl/        # JSONL data files for debug mode
├── databases/             # SQLite database files
├── exports/               # Exported data
├── src/                   # Core source code
│   ├── importers/         # Data import scripts
│   ├── ui_configs/        # UI config files for each task
│   ├── __init__.py
│   ├── auth_handler.py    # User authentication
│   ├── component_factory.py # Gradio component factory
│   ├── db_handler.py      # Database operations
│   ├── db_models.py       # Database models
│   ├── field_processor.py # Field processor
│   ├── jsonl_handler.py   # JSONL file operations
│   ├── main_multi.py      # Main entry point
│   └── routes.py          # Task routing config
└── tools/                 # Utility scripts
```

---

## How to Add a New Task

1. **Create UI Config**: Add a new `[your_task_name]_config.py` in `src/ui_configs/`. Refer to `whole_annotation_config.py` for structure—define `COMPONENTS`, `LAYOUT_CONFIG`, etc.
2. **Add Route**: In `src/routes.py`, add a new route for your task, specifying `task`, `port`, etc.
3. **Create Importer (Optional)**: If needed, add a custom data importer in `src/importers/`.
4. **Run**: Start your new task with `python src/main_multi.py --task [your_task_name]`.

---

## UI Configuration

- **COMPONENTS**: List of Gradio components for the task UI.
- **LAYOUT_CONFIG**: Tree structure defining component layout.
- **CUSTOM_CSS**: (Optional) Custom CSS for advanced UI styling.

See `src/ui_configs/whole_annotation_config.py` for a full example.

---

## License

This project is licensed under the Apache 2.0 License.

---

## 中文说明

### 项目介绍

LabelAnything 是一个模块化、支持多任务、多用户的标注工具平台，基于 Gradio 构建，具有高度的可扩展性和可配置性。

### 核心特性

- **模块化设计**：每个标注任务都是独立模块，拥有自己的 UI 配置、组件和逻辑。
- **多任务支持**：可同时运行和管理多个不同的标注任务。
- **多用户系统**：支持用户登录和权限管理，数据按用户隔离。
- **可配置 UI**：通过 Python 配置文件定义和修改标注界面，无需前端开发。
- **数据后端**：支持 JSONL 文件（调试用）和 SQLite 数据库（生产用）。

### 快速开始

1. 安装依赖（建议 Python 3.10）：
   ```bash
   pip install -r requirements.txt
   ```
2. 数据初始化：
   ```bash
   python -m src.importers.generic_importer --task whole_annotation --file /path/to/your/data.jsonl
   ```
3. 运行标注任务：
   - 列出所有任务：
     ```bash
     python src/main_multi.py --list-tasks
     ```
   - 运行整体物体标注：
     ```bash
     python src/main_multi.py --task whole_annotation
     ```
     浏览器访问 http://0.0.0.0:7801
   - 运行部件标注：
     ```bash
     python src/main_multi.py --task part_annotation --port 7802
     ```
     浏览器访问 http://0.0.0.0:7802

4. 开发模式（跳过登录）：
   ```bash
   python src/main_multi.py --task whole_annotation --dev --uid my_dev_user
   ```

### 目录结构

```
.
├── config/                # 用户和管理员配置
├── database_jsonl/        # Debug 用 JSONL 数据
├── databases/             # SQLite 数据库
├── exports/               # 导出数据
├── src/                   # 核心代码
│   ├── importers/         # 数据导入脚本
│   ├── ui_configs/        # 各任务 UI 配置
│   ├── ...
└── tools/                 # 辅助工具
```

### 如何添加新任务

1. 在 `src/ui_configs/` 下新建 `[your_task_name]_config.py`，参考 `whole_annotation_config.py`。
2. 在 `src/routes.py` 添加路由。
3. （可选）在 `src/importers/` 添加数据导入器。
4. 运行新任务。

### UI 配置说明

- `COMPONENTS`：定义所有组件。
- `LAYOUT_CONFIG`：页面布局。
- `CUSTOM_CSS`：自定义样式（可选）。

详细示例见 `src/ui_configs/whole_annotation_config.py`。

---

如需详细说明或遇到问题，请提交 Issue。