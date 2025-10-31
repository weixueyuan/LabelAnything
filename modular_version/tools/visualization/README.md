# 数据库可视化工具

用于查看和浏览数据库数据的工具。

## 工具列表

### 1. view_database.py - 命令行查看工具

快速查看数据库数据，支持搜索、统计等功能。

**使用方式**：
```bash
# 查看统计信息
python tools/visualization/view_database.py --stats

# 查看前10条数据
python tools/visualization/view_database.py

# 搜索关键词
python tools/visualization/view_database.py --search chair

# 查看特定model_id
python tools/visualization/view_database.py --model-id xxx
```

### 2. view_database_ui.py - Web可视化界面

提供友好的Web界面浏览数据库。

**使用方式**：
```bash
python tools/visualization/view_database_ui.py
# 然后访问 http://localhost:7900
```

**功能**：
- 📊 统计信息
- 📖 分页浏览
- 🔍 关键词搜索
- 📄 详细数据查看

## 快速开始

推荐使用Web界面（最直观）：
```bash
cd /root/projects/object_attributes_annotation_tool/modular_version
python tools/visualization/view_database_ui.py
```



