"""
配置文件示例：演示如何自定义字段

这是一个示例配置，展示了如何：
1. 添加新字段
2. 修改现有字段
3. 使用不同的字段处理器
4. 自定义UI

使用方法：
1. 复制本文件为 config_custom.py
2. 修改配置
3. 将 config.py 中的内容替换为自定义配置
"""

# ========================
# 示例1：基础配置
# ========================
BASIC_FIELD_CONFIG = [
    {
        "key": "category",
        "label": "Category (类别)",
        "type": "textbox",
        "lines": 1,
        "has_checkbox": True,
        "placeholder": "",
        "flex": 1
    },
    {
        "key": "description",
        "label": "Description (描述)",
        "type": "textbox",
        "lines": 3,
        "has_checkbox": True,
        "placeholder": "",
        "flex": 2
    },
]

# ========================
# 示例2：扩展配置（添加更多字段）
# ========================
EXTENDED_FIELD_CONFIG = [
    {
        "key": "category",
        "label": "Category (类别)",
        "type": "textbox",
        "lines": 1,
        "has_checkbox": True,
        "flex": 1
    },
    {
        "key": "description",
        "label": "Description (描述)",
        "type": "textbox",
        "lines": 3,
        "has_checkbox": True,
        "flex": 2
    },
    {
        "key": "material",
        "label": "Material (材质)",
        "type": "textbox",
        "lines": 1,
        "has_checkbox": True,
        "flex": 1
    },
    {
        "key": "color",  # 新增：颜色字段
        "label": "Color (颜色)",
        "type": "textbox",
        "lines": 1,
        "has_checkbox": True,
        "placeholder": "例如: red, blue, green",
        "flex": 1
    },
    {
        "key": "dimensions",
        "label": "Dimensions (尺寸)",
        "type": "textbox",
        "lines": 1,
        "has_checkbox": True,
        "placeholder": "例如: 0.6 * 0.4 * 0.02",
        "flex": 1
    },
    {
        "key": "weight",  # 新增：重量字段
        "label": "Weight (重量)",
        "type": "textbox",
        "lines": 1,
        "has_checkbox": True,
        "placeholder": "例如: 2.5 kg",
        "flex": 1
    },
    {
        "key": "placement",
        "label": "Placement (放置位置)",
        "type": "textbox",
        "lines": 1,
        "has_checkbox": True,
        "placeholder": "例如: OnTable, OnFloor",
        "flex": 1,
        "process": "array_to_string"
    },
    {
        "key": "tags",  # 新增：标签字段（使用数组处理）
        "label": "Tags (标签)",
        "type": "textbox",
        "lines": 1,
        "has_checkbox": True,
        "placeholder": "例如: furniture, indoor, movable",
        "flex": 1,
        "process": "array_to_string"
    },
]

# ========================
# 示例3：简化配置（移除勾选框）
# ========================
SIMPLE_FIELD_CONFIG = [
    {
        "key": "category",
        "label": "Category (类别)",
        "type": "textbox",
        "lines": 1,
        "has_checkbox": False,  # 不使用勾选框
        "flex": 1
    },
    {
        "key": "description",
        "label": "Description (描述)",
        "type": "textbox",
        "lines": 5,
        "has_checkbox": False,
        "flex": 3
    },
    {
        "key": "material",
        "label": "Material (材质)",
        "type": "textbox",
        "lines": 1,
        "has_checkbox": False,
        "flex": 1
    },
]

# ========================
# 示例4：自定义UI配置
# ========================
CUSTOM_UI_CONFIG = {
    "title": "我的标注工具",
    "gif_height": 600,  # 固定GIF高度
    "info_column_height": 600,
    "enable_checkboxes": True,
    "checkbox_label": "⚠️",  # 自定义勾选框标签
    "show_user_info": True,
    "show_status": True,
    "show_dropdowns": False,  # 不显示下拉框
}

# ========================
# 示例5：数据映射配置
# ========================
# 如果你的数据源字段名与显示字段名不同，可以使用映射
CUSTOM_FIELD_MAPPING = {
    # 显示字段名: 数据源字段名
    "category": "object_type",
    "description": "desc",
    "material": "mat",
    "dimensions": "size",
    "placement": "location"
}

# ========================
# 使用示例配置
# ========================
# 将以下代码复制到 config.py 来使用扩展配置：
"""
from config_example import EXTENDED_FIELD_CONFIG, CUSTOM_UI_CONFIG

FIELD_CONFIG = EXTENDED_FIELD_CONFIG
UI_CONFIG = CUSTOM_UI_CONFIG
"""

