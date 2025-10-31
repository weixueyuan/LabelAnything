# 快速开始指南

## 🚀 两步启动

### 1. 导入数据

```bash
cd /root/projects/object_attributes_annotation_tool/modular_version
python -m importers.annotation_importer
```

### 2. 启动程序

```bash
./run.sh --uid user1
# 或
python src/main_multi.py --uid user1
```

### 3. 访问界面

浏览器打开：`http://localhost:7800`

---

## ⚙️ 自定义配置

### 添加/修改字段

编辑 `ui_configs/annotation_config.py`：

```python
FIELD_CONFIG = [
    {
        "key": "category",          # 字段名（自动对应数据库）
        "label": "Category (类别)",  # 显示标签
        "type": "textbox",
        "lines": 1,
        "has_checkbox": True,
    },
    # 添加新字段
    {
        "key": "color",
        "label": "Color (颜色)",
        "type": "textbox",
        "lines": 1,
        "has_checkbox": True,
    },
]
```

### 修改路径配置

编辑 `ui_configs/annotation_config.py` 中的 `PATH_CONFIG`：

```python
PATH_CONFIG = {
    "base_path": "/your/path/to/images",
    "gif_filename_pattern": "{model_id}_fixed.gif",
}
```

---

## 📊 常用命令

```bash
# 导入数据
python -m importers.annotation_importer
python -m importers.annotation_importer --source data.jsonl  # 指定文件
python -m importers.annotation_importer --clean              # 清空后导入

# 启动程序
./run.sh --uid user1 --port 7800
python src/main_multi.py --uid user1

# 查看数据库
sqlite3 databases/annotation.db "SELECT COUNT(*) FROM annotations"
sqlite3 databases/annotation.db "SELECT * FROM annotations WHERE annotated=1 LIMIT 5"
```

---

## 🔧 多人标注

每个人使用不同的用户ID：

```bash
# 用户1
./run.sh --uid user1 --port 7800

# 用户2（新终端）
./run.sh --uid user2 --port 7801
```

每个用户只能看到自己未标注的或自己已标注的数据。

---

## 📁 核心文件

| 文件 | 说明 |
|------|------|
| `ui_configs/annotation_config.py` | **UI配置**（添加字段） |
| `importers/annotation_importer.py` | **导入器**（数据导入） |
| `databases/annotation.db` | **数据库**（导入后生成） |
| `src/main_multi.py` | **主程序** |
| `routes.py` | **路由配置** |

---

## 🆘 常见问题

### Q: 数据库不存在？
**A**: 运行 `python -m importers.annotation_importer` 导入数据

### Q: 如何添加新字段？
**A**: 编辑 `ui_configs/annotation_config.py` 的 `FIELD_CONFIG`

### Q: 如何重新导入数据？
**A**: 运行 `python -m importers.annotation_importer --clean`

### Q: 端口被占用？
**A**: 使用 `--port` 参数：`./run.sh --port 8000`

---

**完整文档**: 查看 `README.md`
