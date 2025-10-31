# 物体属性标注工具 - 模块化版本

> 🎯 基于配置驱动的模块化架构，易于扩展和维护

## 📁 目录结构（清晰版）

```
modular_version/
│
├── 📦 src/                    ⭐ 主要代码（核心文件）
│   ├── config.py              配置文件（修改这里！）
│   ├── main.py                主程序
│   ├── data_handler.py        数据处理模块
│   ├── ui_builder.py          UI构建模块
│   ├── field_processor.py     字段处理器
│   └── __init__.py            包定义
│
├── 📚 docs/                   文档
│   ├── README.md              完整说明
│   ├── QUICKSTART.md          快速开始
│   ├── HOW_TO_ADAPT_NEW_DATA.md  适配新数据教程
│   ├── QUICK_REFERENCE.md     快速参考
│   ├── DATA_FORMAT.md         数据格式说明
│   └── COMPARISON.md          版本对比
│
├── 🧪 examples/               示例和测试
│   ├── config_example.py      配置示例
│   ├── config_custom_example.py  自定义配置示例
│   ├── example_data.jsonl     示例数据
│   └── test_modules.py        模块测试
│
├── 🚀 run.sh                  启动脚本（推荐使用）
├── 📖 README.md               本文件
└── ⚡ QUICKSTART.md           快速开始指南
```

## 🚀 快速开始

### 启动程序

```bash
# 方法1：使用启动脚本（推荐）
./run.sh --port 7801 --uid user1

# 方法2：直接运行Python
cd src
python main.py --port 7801 --uid user1
```

### 修改配置

只需编辑 `src/config.py` 文件：

```python
# 1. 修改字段配置
FIELD_CONFIG = [
    {"key": "category", "label": "类别", ...},
    {"key": "description", "label": "描述", ...},
    # 添加更多字段...
]

# 2. 修改数据路径
PATH_CONFIG = {
    "data_file": "/path/to/your/data.jsonl",
    ...
}
```

## ✨ 最新优化

### 1. 扁平化数据结构
- ✅ 去除 `FIELD_MAPPING`，直接用 key 匹配
- ✅ 元数据（annotated、uid、score）直接存储在数据中
- ✅ 简化的保存格式

### 2. 优化的UI布局
- ✅ GIF容器改为 **3:5 比例**（宽:高）
- ✅ 左右列宽度比例优化（3:5）
- ✅ 更适合查看长条形图片

### 3. 清晰的目录结构
- ✅ 核心代码放在 `src/`
- ✅ 文档放在 `docs/`
- ✅ 示例和测试放在 `examples/`

## 📊 数据格式示例

### 原始数据
```json
{
  "model-001": {
    "category": "chair",
    "description": "A modern chair",
    "material": "wood",
    "placement": ["OnFloor"]
  }
}
```

### 已标注数据（扁平结构）
```json
{
  "model-001": {
    "annotated": true,
    "uid": "user1",
    "score": 1,
    "category": "chair",
    "description": "A modern chair (edited)",
    "material": "wood",
    "placement": ["OnFloor"],
    "chk_category": false,
    "chk_description": false,
    "chk_material": false,
    "chk_placement": false
  }
}
```

## 🎯 常用操作

### 添加新字段

编辑 `src/config.py`：

```python
FIELD_CONFIG = [
    # ... 现有字段 ...
    {
        "key": "new_field",      # 对应数据中的字段名
        "label": "新字段",        # 界面显示名
        "type": "textbox",
        "lines": 1,
        "has_checkbox": True,
        "flex": 1
    }
]
```

### 调整UI布局

编辑 `src/config.py` 中的 `UI_CONFIG`：

```python
UI_CONFIG = {
    "title": "我的标注工具",
    "enable_checkboxes": True,
    "show_user_info": True,
    ...
}
```

### 修改GIF比例

编辑 `src/config.py` 中的 CSS：

```css
/* GIF容器样式 */
#gif_container {
    aspect-ratio: 3 / 5 !important;  /* 改成你想要的比例 */
}
```

## 📚 查看文档

- **快速开始**: `QUICKSTART.md`
- **适配新数据**: `docs/HOW_TO_ADAPT_NEW_DATA.md`
- **快速参考**: `docs/QUICK_REFERENCE.md`
- **数据格式**: `docs/DATA_FORMAT.md`
- **版本对比**: `docs/COMPARISON.md`

## 🧪 测试

```bash
cd examples
python test_modules.py
```

## 💡 提示

- ⭐ **核心文件**: `src/config.py` - 所有配置都在这里
- 📝 **添加字段**: 只需修改 `FIELD_CONFIG`
- 🎨 **调整UI**: 只需修改 `UI_CONFIG` 和 `CUSTOM_CSS`
- 🔄 **修改后**: 需要重启程序

## 🆚 与原版本对比

| 操作 | 原版本 | 模块化版本 |
|------|--------|-----------|
| 文件结构 | 1个文件653行 | 模块化分离 ✓ |
| 添加字段 | 修改6处代码 | 修改1个配置 ✓ |
| 数据格式 | 嵌套复杂 | 扁平简单 ✓ |
| 字段映射 | 需要FIELD_MAPPING | 直接匹配 ✓ |
| 目录结构 | 混乱 | 清晰分类 ✓ |

---

**开始使用**: `./run.sh --port 7801`

**需要帮助**: 查看 `docs/` 目录下的文档
