# 物体属性标注工具 - 模块化版本

> 🎯 基于配置驱动的模块化架构，易于扩展和维护

## 📁 目录结构

```
modular_version/
├── config.py              # 配置文件（核心配置）
├── field_processor.py     # 字段处理器
├── data_handler.py        # 数据处理模块
├── ui_builder.py          # UI构建模块
├── main.py               # 主程序
├── run.sh                # 启动脚本
└── README.md             # 说明文档（本文件）
```

## 🚀 快速开始

### 方法1：使用启动脚本（推荐）

```bash
# 使用默认配置启动
./run.sh

# 自定义端口
./run.sh --port 8000

# 指定用户ID
./run.sh --uid user1 --port 7801

# 查看所有选项
./run.sh --help
```

### 方法2：直接使用Python

```bash
python main.py --port 7801 --uid user1
```

## ⚙️ 配置说明

### 修改字段配置

编辑 `config.py` 中的 `FIELD_CONFIG`：

```python
FIELD_CONFIG = [
    {
        "key": "category",              # 字段唯一标识
        "label": "Category (类别)",      # 显示标签
        "type": "textbox",              # 组件类型
        "lines": 1,                     # 文本框行数
        "has_checkbox": True,           # 是否有勾选框
        "placeholder": "",              # 占位符提示
        "flex": 1,                      # 相对高度权重
        "process": None                 # 特殊处理类型
    },
    # ... 更多字段
]
```

### 添加新字段

只需在 `FIELD_CONFIG` 中添加配置项：

```python
{
    "key": "new_field",
    "label": "New Field (新字段)",
    "type": "textbox",
    "lines": 2,
    "has_checkbox": True,
    "placeholder": "请输入...",
    "flex": 1,
    "process": None
}
```

### 字段处理类型

在 `process` 字段中指定：

- `None`: 不处理，直接使用原值
- `"array_to_string"`: 数组 ↔ 逗号分隔字符串
- `"json"`: 对象 ↔ JSON字符串

**示例：**

```python
# placement字段自动转换数组和字符串
{
    "key": "placement",
    "process": "array_to_string",  # ["OnTable", "OnFloor"] ↔ "OnTable, OnFloor"
}
```

### UI配置

编辑 `config.py` 中的 `UI_CONFIG`：

```python
UI_CONFIG = {
    "title": "物体属性检查工具",
    "gif_height": None,              # None=自动高度，或指定像素值
    "info_column_height": None,      # None=自动高度
    "enable_checkboxes": True,       # 是否启用勾选框
    "checkbox_label": "✗",           # 勾选框标签
    "show_user_info": True,          # 显示用户信息栏
    "show_status": True,             # 显示标注状态
    "show_dropdowns": True,          # 显示类型下拉框
}
```

### 路径配置

编辑 `config.py` 中的 `PATH_CONFIG`：

```python
PATH_CONFIG = {
    "data_file": "/path/to/data.jsonl",
    "base_path": "/path/to/renderings",
    "gif_filename_pattern": "{model_id}_fixed.gif",
}
```

## 🎨 自定义样式

编辑 `config.py` 中的 `CUSTOM_CSS` 变量来修改界面样式。

## 📋 使用示例

### 示例1：添加新的"颜色"字段

编辑 `config.py`：

```python
FIELD_CONFIG = [
    # ... 现有字段 ...
    {
        "key": "color",
        "label": "Color (颜色)",
        "type": "textbox",
        "lines": 1,
        "has_checkbox": True,
        "placeholder": "例如: red, blue",
        "flex": 1
    }
]

# 同时更新映射（如果数据源字段名不同）
FIELD_MAPPING = {
    # ... 现有映射 ...
    "color": "color"  # 或映射到其他源字段名
}
```

### 示例2：修改字段顺序

只需调整 `FIELD_CONFIG` 列表中的顺序即可。

### 示例3：移除勾选框

将对应字段的 `has_checkbox` 设为 `False`：

```python
{
    "key": "category",
    "has_checkbox": False,  # 不显示勾选框
    # ... 其他配置
}
```

### 示例4：多用户标注

```bash
# 用户A
./run.sh --uid userA --port 7801

# 用户B
./run.sh --uid userB --port 7802

# 用户C
./run.sh --uid userC --port 7803
```

每个用户只能看到自己标注的数据和未标注的数据。

## 🔧 扩展功能

### 添加新的字段处理器

编辑 `field_processor.py`：

```python
@staticmethod
def process_load(field_config: Dict, value: Any) -> Any:
    process_type = field_config.get('process', None)
    
    # 添加新的处理类型
    if process_type == 'custom_type':
        # 自定义处理逻辑
        return custom_transform(value)
    
    # ... 现有逻辑 ...

@staticmethod
def process_save(field_config: Dict, value: Any) -> Any:
    process_type = field_config.get('process', None)
    
    # 添加对应的保存处理
    if process_type == 'custom_type':
        # 自定义保存逻辑
        return custom_reverse_transform(value)
    
    # ... 现有逻辑 ...
```

## 📊 数据格式

### 输入格式（JSONL）

```json
{"model-key": {"category": "chair", "description": "...", "placement": ["OnFloor"]}}
```

### 保存格式

```json
{"model-key": {
  "annotated": true,
  "uid": "user1",
  "score": 1,
  "data": "```json\n{...}\n```"
}}
```

## 🆚 对比原版本

| 特性 | 原版本 | 模块化版本 |
|------|--------|-----------|
| 添加字段 | 修改多处代码 | 只修改配置文件 |
| 修改UI | 修改主代码 | 修改配置文件 |
| 字段处理 | 硬编码 | 可配置处理器 |
| 代码维护 | 580+行单文件 | 5个模块分离 |
| 扩展性 | 较低 | 高 |
| 可读性 | 中等 | 高 |

## 🐛 故障排除

### 端口被占用

```bash
./run.sh --port 8000  # 使用其他端口
```

### 找不到数据文件

检查 `config.py` 中的 `PATH_CONFIG['data_file']` 路径是否正确。

### GIF不显示

检查：
1. `PATH_CONFIG['base_path']` 是否正确
2. `PATH_CONFIG['gif_filename_pattern']` 格式是否匹配
3. GIF文件是否存在

## 📝 开发文档

### 模块职责

- **config.py**: 所有配置项（字段、UI、路径等）
- **field_processor.py**: 字段值的转换和处理
- **data_handler.py**: 数据的加载、解析和保存
- **ui_builder.py**: 动态生成UI组件
- **main.py**: 整合所有模块，实现业务逻辑

### 数据流

```
数据文件 → DataHandler.load_data()
         → DataHandler.parse_item()
         → FieldProcessor.process_load()
         → UI显示

UI输入  → FieldProcessor.process_save()
        → DataHandler.build_save_data()
        → DataHandler.save_data()
        → 数据文件
```

## 📄 License

MIT License

## 👥 贡献

欢迎提交Issue和Pull Request！

---

**注意**：本版本与原版本数据格式完全兼容，可以无缝切换使用。

