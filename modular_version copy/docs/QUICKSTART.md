# 快速开始指南

## 📦 安装依赖

确保已安装 Python 3.8+ 和 Gradio：

```bash
pip install gradio
```

## 🚀 启动工具

### 方法1：使用启动脚本（推荐）

```bash
cd /root/projects/object_attributes_annotation_tool/modular_version
./run.sh --port 7801 --uid user1
```

### 方法2：直接运行Python

```bash
cd /root/projects/object_attributes_annotation_tool/modular_version
python main.py --port 7801 --uid user1
```

## ⚙️ 快速自定义

### 1. 添加新字段（只需3步）

**步骤1**：编辑 `config.py`，在 `FIELD_CONFIG` 中添加：

```python
{
    "key": "color",
    "label": "Color (颜色)",
    "type": "textbox",
    "lines": 1,
    "has_checkbox": True,
    "placeholder": "输入颜色",
    "flex": 1
}
```

**步骤2**：保存文件

**步骤3**：重启程序

就这样！新字段会自动出现在界面上。

### 2. 修改字段顺序

在 `config.py` 中调整 `FIELD_CONFIG` 列表顺序即可。

### 3. 移除字段

从 `FIELD_CONFIG` 中删除对应配置项。

### 4. 修改GIF文件路径

编辑 `config.py` 中的 `PATH_CONFIG`：

```python
PATH_CONFIG = {
    "gif_filename_pattern": "{model_id}_original.gif",  # 改为 _original.gif
}
```

### 5. 自定义UI

编辑 `config.py` 中的 `UI_CONFIG`：

```python
UI_CONFIG = {
    "title": "我的标注工具",  # 修改标题
    "gif_height": 600,        # 固定GIF高度
    "enable_checkboxes": False,  # 禁用勾选框
}
```

## 📊 常用命令

```bash
# 查看帮助
./run.sh --help

# 使用不同端口
./run.sh --port 8000

# 指定用户ID（多人标注）
./run.sh --uid user1 --port 7801
./run.sh --uid user2 --port 7802

# 使用自定义数据文件
./run.sh --data_file /path/to/data.jsonl
```

## 🔍 测试模块

运行测试脚本检查模块是否正常：

```bash
python test_modules.py
```

## 📁 目录说明

- `config.py` - **核心配置文件（主要修改这个）**
- `main.py` - 主程序（一般不需要修改）
- `run.sh` - 启动脚本
- `README.md` - 详细文档
- `test_modules.py` - 测试脚本

## 💡 提示

1. **修改配置后需要重启程序**
2. **配置文件语法错误会导致程序无法启动**
3. **建议先备份 `config.py` 再修改**
4. **查看 `config_example.py` 了解更多配置示例**

## 🆘 常见问题

### Q: 端口被占用怎么办？
A: 使用 `--port` 参数指定其他端口

### Q: 如何添加新字段？
A: 编辑 `config.py` 中的 `FIELD_CONFIG`，添加字段配置

### Q: 数据保存在哪里？
A: 保存在原数据文件，备份在 `backups/` 目录

### Q: 如何让多人同时标注？
A: 每个人使用不同的 `--uid` 和 `--port`

---

**完整文档**: 查看 `README.md`

