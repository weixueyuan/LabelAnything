# 数据格式说明

## 📊 新的扁平化数据格式（推荐）

### 原始数据格式
```json
{
  "model-key-001": {
    "category": "chair",
    "description": "A modern chair",
    "material": "wood",
    "dimensions": "0.6 * 0.6 * 0.8",
    "placement": ["OnFloor"]
  }
}
```

### 已标注数据格式（扁平结构）
```json
{
  "model-key-001": {
    "annotated": true,
    "uid": "user1",
    "score": 1,
    "category": "chair",
    "description": "A modern chair (edited)",
    "material": "wood",
    "dimensions": "0.6 * 0.6 * 0.8",
    "placement": ["OnFloor"],
    "chk_category": false,
    "chk_description": false,
    "chk_material": false,
    "chk_dimensions": false,
    "chk_placement": false
  }
}
```

## 🎯 数据结构说明

### 元数据字段（由系统自动添加）
- `annotated` (bool): 是否已标注
- `uid` (string): 标注者ID
- `score` (int): 质量分数（0=有问题，1=正常）

### 业务字段（根据config.py配置）
- 直接在对象根层级
- 字段名对应 `FIELD_CONFIG` 中的 `key`
- 有就显示，没有就留空

### 勾选框字段（可选）
- 格式：`chk_{字段名}`
- 例如：`chk_category`, `chk_description`
- 值为 `true` 表示该字段有问题

## ✨ 优化点

### 1. 去除FIELD_MAPPING

**之前**：需要显式映射
```python
FIELD_MAPPING = {
    "category": "category",
    "description": "desc",  # 映射到数据中的"desc"字段
}
```

**现在**：直接匹配
```python
# FIELD_MAPPING 已废弃
# 直接用 FIELD_CONFIG 中的 key 去数据中查找
# 有就显示，没有就空着
```

### 2. 扁平化数据结构

**之前**：嵌套结构
```json
{
  "annotated": true,
  "uid": "user1",
  "score": 1,
  "data": "```json\n{\"category\": \"chair\", ...}\n```"
}
```

**现在**：扁平结构
```json
{
  "annotated": true,
  "uid": "user1",
  "score": 1,
  "category": "chair",
  "description": "...",
  "material": "...",
  ...
}
```

### 3. 灵活的字段匹配

```python
# config.py
FIELD_CONFIG = [
    {"key": "category", ...},
    {"key": "description", ...},
    {"key": "new_field", ...},  # 新增字段
]

# 数据中没有 new_field？没问题！
# 系统会自动留空，不会报错
```

## 🔄 兼容性

### 自动兼容旧格式

系统会自动识别两种格式：

```python
# 旧格式（包含'data'字段）- 仍然支持
{
  "annotated": true,
  "data": "```json\n{...}\n```"
}

# 新格式（扁平结构）- 推荐使用
{
  "annotated": true,
  "category": "...",
  ...
}
```

### 混合格式支持

同一个文件中可以包含两种格式的数据：

```jsonl
{"key1": {"category": "chair", "description": "..."}}
{"key2": {"annotated": true, "uid": "user1", "category": "table", ...}}
{"key3": {"annotated": true, "data": "```json\n{...}\n```"}}
```

## 📝 实际示例

### 示例1：你的原始数据
```json
{
  "home-others-other-0a82acc4": {
    "category": "panel",
    "description": "The object is a rectangular panel...",
    "material": "light gray matte surface - panel body...",
    "dimensions": "0.6 * 0.3 * 0.02",
    "mass": 0.8,
    "placement": ["OnWall"]
  }
}
```

**配置**：
```python
FIELD_CONFIG = [
    {"key": "category", ...},
    {"key": "description", ...},
    {"key": "material", ...},
    {"key": "dimensions", ...},
    {"key": "mass", ...},        # 数据中有mass字段，自动显示
    {"key": "placement", ...},
]
```

### 示例2：添加新字段
```python
# 在配置中添加新字段
FIELD_CONFIG = [
    {"key": "category", ...},
    {"key": "description", ...},
    {"key": "color", ...},       # 新增字段
]

# 数据中没有color？
{"model-001": {"category": "chair", "description": "..."}}

# 结果：color字段显示为空，不会报错
```

### 示例3：保存后的数据
```json
{
  "home-others-other-0a82acc4": {
    "annotated": true,
    "uid": "user1",
    "score": 0,
    "category": "panel",
    "description": "The object is a rectangular panel (edited)",
    "material": "plastic",
    "dimensions": "0.6 * 0.3 * 0.02",
    "mass": 0.8,
    "placement": ["OnWall"],
    "chk_category": false,
    "chk_description": true,
    "chk_material": false,
    "chk_dimensions": false,
    "chk_mass": false,
    "chk_placement": false
  }
}
```

## 🚀 迁移指南

### 从旧格式迁移到新格式

不需要手动迁移！系统自动兼容两种格式。

### 生成新格式数据

保存数据时，系统会自动使用新的扁平格式。

## 💡 最佳实践

1. **新项目**：直接使用扁平格式
2. **旧项目**：无需迁移，系统自动兼容
3. **字段命名**：配置中的key直接对应数据中的字段名
4. **灵活扩展**：添加新字段只需修改配置，数据自动适配

## 🔍 调试技巧

### 查看数据解析结果

在 `data_handler.py` 的 `parse_item` 方法中添加打印：

```python
def parse_item(self, value_data):
    result = self._parse_simple(value_data)
    print(f"解析结果: {result}")  # 调试用
    return result
```

### 检查字段匹配

```python
# 数据
data = {"category": "chair", "desc": "..."}

# 配置
FIELD_CONFIG = [
    {"key": "category", ...},  # ✓ 匹配成功
    {"key": "description", ...},  # ✗ 没有匹配（数据中是"desc"）
]

# 结果
# category: "chair"
# description: ""  (空)
```

---

**总结**：新的扁平化格式更简单、更直观、更易维护！

