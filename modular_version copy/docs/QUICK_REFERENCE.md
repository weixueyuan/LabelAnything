# 快速参考卡片

## 🎯 适配新数据：只需3步

```
1️⃣  打开 config.py
2️⃣  修改 FIELD_CONFIG（添加/删除/修改字段）
3️⃣  重启程序
```

## 📝 添加一个字段的模板

```python
{
    "key": "字段名",              # ⭐ 必填：数据中的字段名
    "label": "显示名称",          # ⭐ 必填：界面显示的标签
    "type": "textbox",           # ⭐ 必填：固定为 "textbox"
    "lines": 1,                  # 可选：文本框行数，默认1
    "has_checkbox": True,        # 可选：是否有勾选框，默认False
    "placeholder": "提示文字",   # 可选：占位符
    "flex": 1,                   # 可选：高度权重，默认1
    "process": None              # 可选：特殊处理类型
}
```

## 🔧 常用配置速查

### 单行文本框
```python
{"key": "brand", "label": "品牌", "type": "textbox", "lines": 1, "has_checkbox": True}
```

### 多行文本框
```python
{"key": "desc", "label": "描述", "type": "textbox", "lines": 5, "has_checkbox": True, "flex": 3}
```

### 数组字段（自动转换）
```python
{"key": "tags", "label": "标签", "type": "textbox", "process": "array_to_string"}
# 数据: ["tag1", "tag2"] ↔ 显示: "tag1, tag2"
```

### 不带勾选框
```python
{"key": "id", "label": "ID", "type": "textbox", "has_checkbox": False}
```

## 📊 flex 权重示例

```python
# flex=1 占1份高度
{"key": "name", "flex": 1}     # 高度: 50px

# flex=2 占2份高度  
{"key": "desc", "flex": 2}     # 高度: 100px

# flex=3 占3份高度
{"key": "detail", "flex": 3}   # 高度: 150px
```

## 🎨 process 类型速查

| process 值 | 作用 | 示例 |
|-----------|------|------|
| `None` | 不处理 | `"text"` → `"text"` |
| `"array_to_string"` | 数组↔字符串 | `["a","b"]` ↔ `"a, b"` |
| `"json"` | 对象↔JSON | `{k:v}` ↔ `'{"k":"v"}'` |

## 🔄 字段名映射

如果数据字段名和显示名不同：

```python
# 数据: {"desc": "..."}
# 但你想在配置中用 "description"

FIELD_CONFIG = [
    {"key": "description", ...}  # 用你想要的名字
]

FIELD_MAPPING = {
    "description": "desc"  # 映射到数据中的实际字段名
}
```

## 📁 路径配置

```python
PATH_CONFIG = {
    "data_file": "/path/to/data.jsonl",          # 数据文件
    "base_path": "/path/to/images",              # 图片基础路径
    "gif_filename_pattern": "{model_id}.gif",    # 图片文件名
}
```

## 🎛️ UI 配置

```python
UI_CONFIG = {
    "title": "标题",              # 界面标题
    "gif_height": None,           # None=自动 或 600
    "enable_checkboxes": True,    # 启用勾选框
    "show_user_info": True,       # 显示用户信息
    "show_status": True,          # 显示标注状态
    "show_dropdowns": True,       # 显示类型下拉框
}
```

## 🚀 启动命令

```bash
# 基本启动
./run.sh

# 指定端口
./run.sh --port 8000

# 指定用户
./run.sh --uid user1 --port 7801

# 指定数据文件
./run.sh --data_file /path/to/data.jsonl
```

## 🔍 调试检查清单

启动后检查：
- [ ] 终端显示加载了多少数据？
- [ ] 界面上字段都显示了吗？
- [ ] 字段顺序正确吗？
- [ ] 数据能正确显示吗？
- [ ] 保存功能正常吗？

## 💡 常见错误

### 语法错误
```python
# ❌ 错误：缺少逗号
{
    "key": "name"
    "label": "名称"  # 前面少了逗号
}

# ✅ 正确
{
    "key": "name",
    "label": "名称"
}
```

### 字段名错误
```python
# ❌ 错误：数据中是 "desc"，配置用了 "description"
{"key": "description", ...}

# ✅ 方法1：使用实际字段名
{"key": "desc", ...}

# ✅ 方法2：使用映射
{"key": "description", ...}
FIELD_MAPPING = {"description": "desc"}
```

## 📚 相关文档

- 详细教程：`HOW_TO_ADAPT_NEW_DATA.md`
- 完整说明：`README.md`
- 配置示例：`config_example.py`
- 自定义示例：`config_custom_example.py`

---

**记住**：修改配置后需要重启程序！

