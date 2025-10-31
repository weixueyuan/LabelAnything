"""
自定义配置示例：适配新数据格式

假设你的数据格式是：
{
  "furniture-chair-001": {
    "object_type": "办公椅",
    "detailed_desc": "黑色皮质办公椅",
    "main_material": "皮革+金属",
    "size_info": "60x60x100 cm",
    "weight_kg": 15.5,
    "color": "黑色",
    "brand": "宜家",
    "price": 599,
    "suitable_places": ["办公室", "书房"],
    "is_fragile": false
  }
}

使用方法：
1. 将本文件重命名为 config.py（先备份原 config.py）
2. 修改下面的配置以匹配你的实际数据
3. 重启程序
"""

# ========================
# 字段配置 - 根据你的数据定义
# ========================
FIELD_CONFIG = [
    {
        "key": "object_type",
        "label": "物体类型",
        "type": "textbox",
        "lines": 1,
        "has_checkbox": True,
        "placeholder": "例如: 办公椅",
        "flex": 1
    },
    {
        "key": "detailed_desc",
        "label": "详细描述",
        "type": "textbox",
        "lines": 3,
        "has_checkbox": True,
        "placeholder": "描述物体的详细特征",
        "flex": 2  # 占据2倍高度
    },
    {
        "key": "main_material",
        "label": "主要材质",
        "type": "textbox",
        "lines": 1,
        "has_checkbox": True,
        "placeholder": "例如: 皮革+金属",
        "flex": 1
    },
    {
        "key": "size_info",
        "label": "尺寸信息",
        "type": "textbox",
        "lines": 1,
        "has_checkbox": True,
        "placeholder": "例如: 60x60x100 cm",
        "flex": 1
    },
    {
        "key": "weight_kg",
        "label": "重量 (kg)",
        "type": "textbox",
        "lines": 1,
        "has_checkbox": True,
        "placeholder": "例如: 15.5",
        "flex": 1
    },
    {
        "key": "color",
        "label": "颜色",
        "type": "textbox",
        "lines": 1,
        "has_checkbox": True,
        "placeholder": "例如: 黑色, 白色",
        "flex": 1
    },
    {
        "key": "brand",
        "label": "品牌",
        "type": "textbox",
        "lines": 1,
        "has_checkbox": True,
        "placeholder": "例如: 宜家, 无印良品",
        "flex": 1
    },
    {
        "key": "price",
        "label": "价格 (元)",
        "type": "textbox",
        "lines": 1,
        "has_checkbox": True,
        "placeholder": "例如: 599",
        "flex": 1
    },
    {
        "key": "suitable_places",
        "label": "适用场所",
        "type": "textbox",
        "lines": 1,
        "has_checkbox": True,
        "placeholder": "例如: 办公室, 书房, 客厅",
        "flex": 1,
        "process": "array_to_string"  # 自动处理数组↔字符串转换
    },
    {
        "key": "is_fragile",
        "label": "是否易碎",
        "type": "textbox",
        "lines": 1,
        "has_checkbox": True,
        "placeholder": "true 或 false",
        "flex": 1
    }
]

# ========================
# 数据映射配置
# ========================
# 如果你的数据源字段名和显示字段名不同，在这里映射
# 例如：数据中是 "desc"，但你想叫它 "detailed_desc"
FIELD_MAPPING = {
    "object_type": "object_type",
    "detailed_desc": "detailed_desc",
    "main_material": "main_material",
    "size_info": "size_info",
    "weight_kg": "weight_kg",
    "color": "color",
    "brand": "brand",
    "price": "price",
    "suitable_places": "suitable_places",
    "is_fragile": "is_fragile"
}

# ========================
# UI配置
# ========================
UI_CONFIG = {
    "title": "家具属性标注工具",  # 改成你的标题
    "gif_height": None,  # None=自动高度，或指定如 600
    "info_column_height": None,
    "enable_checkboxes": True,  # 是否启用勾选框
    "checkbox_label": "✗",
    "show_user_info": True,
    "show_status": True,
    "show_dropdowns": True,  # 是否显示类型/子类型下拉框
}

# ========================
# 路径配置 - 修改成你的实际路径
# ========================
PATH_CONFIG = {
    "data_file": "/path/to/your/data.jsonl",  # 👈 改成你的数据文件路径
    "base_path": "/path/to/your/images",      # 👈 改成你的图片基础路径
    "gif_filename_pattern": "{model_id}.gif",  # 图片文件名格式
}

# ========================
# 默认参数
# ========================
DEFAULT_ARGS = {
    "port": 7801,
    "uid": "default_user"
}

# ========================
# CSS自定义配置（保持不变或自定义）
# ========================
CUSTOM_CSS = """
/* 搜索行 */
#search_row {
    display: flex !important;
    align-items: stretch !important;
}
#search_row .gradio-column {
    display: flex !important;
    align-items: stretch !important;
}
#search_row .gradio-textbox {
    display: flex !important;
    flex-direction: column !important;
}
#search_row .gradio-html {
    flex: 1 !important;
    display: flex !important;
    flex-direction: column !important;
}
#search_row .gradio-html > div {
    flex: 1 !important;
    display: flex !important;
}

/* 主内容区 */
#main_content_row {
    display: flex !important;
    align-items: stretch !important;
}
#main_content_row > .gradio-column {
    display: flex !important;
    flex-direction: column !important;
}

/* GIF容器 */
#gif_container .gradio-image {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}
#gif_container .gradio-image img {
    max-width: 100% !important;
    max-height: 100% !important;
    width: auto !important;
    height: auto !important;
    object-fit: contain !important;
    margin: auto !important;
}

/* 右侧信息列 */
#info_column {
    display: flex !important;
    flex-direction: column !important;
    gap: 4px !important;
}
#info_column > .gradio-column {
    display: flex !important;
    flex-direction: column !important;
    width: 100% !important;
}
#info_column .gradio-checkbox {
    margin-bottom: 0px !important;
}
#info_column .gradio-textbox {
    flex: 1 1 0 !important;
    min-height: 0 !important;
    display: flex !important;
    flex-direction: column !important;
    width: 100% !important;
}
#info_column .gradio-textbox textarea {
    flex: 1 !important;
    min-height: 0 !important;
}

/* 让description输入框占据2倍空间 */
#info_column > div:nth-child(2) {
    flex: 2 1 0 !important;
}

/* 确认弹窗 */
#confirm_modal {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.6);
    z-index: 9999;
    display: flex !important;
    align-items: center;
    justify-content: center;
    backdrop-filter: blur(3px);
    animation: fadeIn 0.15s ease;
}

#confirm_card {
    width: min(400px, 80vw);
    max-height: min(280px, 45vh);
    overflow-y: auto;
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.25);
    padding: 28px 24px 24px;
    animation: slideIn 0.2s ease;
}

#confirm_card h2, #confirm_card p {
    font-size: 20px !important;
    margin: 0 0 10px;
    color: #222;
    text-align: center;
    font-weight: 600;
    line-height: 1.3;
}

#confirm_card button,
#confirm_card .gradio-button,
#confirm_card .gradio-button > span {
    font-size: 14px !important;
    font-weight: 600 !important;
    min-height: 48px !important;
    padding: 12px 20px !important;
    border-radius: 8px !important;
    line-height: 1.2 !important;
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

@keyframes slideIn {
    from { transform: translateY(-30px); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
}

@media (max-width: 600px) {
    #confirm_card {
        width: 92vw;
        max-height: 65vh;
    }
    #confirm_card h2, #confirm_card p { 
        font-size: 14px !important; 
    }
}
"""

