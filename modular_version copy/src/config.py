"""
配置文件：定义所有字段和UI配置

通过修改 FIELD_CONFIG 来添加、删除或修改字段
"""

# ========================
# 字段配置
# ========================
FIELD_CONFIG = [
    {
        "key": "category",
        "label": "Category (类别)",
        "type": "textbox",
        "lines": 1,
        "has_checkbox": True,
        "placeholder": "",
        "flex": 1,  # 相对高度权重
        "process": None  # 特殊处理类型：None, 'array_to_string', 'json'
    },
    {
        "key": "description",
        "label": "Description (描述)",
        "type": "textbox",
        "lines": 3,
        "has_checkbox": True,
        "placeholder": "",
        "flex": 2  # 占据2倍空间
    },
    {
        "key": "material",
        "label": "Material (材质)",
        "type": "textbox",
        "lines": 1,
        "has_checkbox": True,
        "placeholder": "",
        "flex": 1
    },
    # {
    #     "key": "dimensions",
    #     "label": "Dimensions (尺寸)",
    #     "type": "textbox",
    #     "lines": 1,
    #     "has_checkbox": True,
    #     "placeholder": "例如: 0.6 * 0.4 * 0.02",
    #     "flex": 1
    # },
    {
        "key": "placement",
        "label": "Placement (放置位置)",
        "type": "textbox",
        "lines": 1,
        "has_checkbox": True,
        "placeholder": "例如: OnTable, OnFloor",
        "flex": 1,
        "process": "array_to_string"  # 数组与字符串互转
    }
]

# ========================
# 数据映射配置（已废弃）
# ========================
# 现在直接用 FIELD_CONFIG 中的 key 去数据中查找
# 如果数据中有该字段就显示，没有就留空
# 不再需要显式映射
FIELD_MAPPING = None  # 保留兼容性，但不使用

# ========================
# UI配置
# ========================
UI_CONFIG = {
    "title": "物体属性检查工具",
    "gif_height": None,  # None表示自动高度，或指定像素值如 580
    "info_column_height": None,  # None表示自动高度
    "enable_checkboxes": True,  # 是否启用勾选框功能
    "checkbox_label": "✗",  # 勾选框标签
    "show_user_info": True,  # 是否显示用户信息栏
    "show_status": True,  # 是否显示标注状态
    "show_dropdowns": True,  # 是否显示类型/子类型等下拉框
}

# ========================
# 路径配置
# ========================
PATH_CONFIG = {
    "data_file": "/root/projects/object_attributes_annotation_tool/merged_attributes.jsonl",
    "base_path": "/mnt/data/GRScenes-100/instances/renderings",
    "gif_filename_pattern": "{model_id}_fixed.gif",  # 可用占位符: {model_id}
    # GIF路径模板：{base_path}/{type}_objects/{subtype}/{category}/thumbnails/merged_views/{model_id}/{filename}
    
    # 示例数据路径（用于测试）
    # "data_file": "../examples/example_data.jsonl",
}

# ========================
# 默认参数
# ========================
DEFAULT_ARGS = {
    "port": 7800,
    "uid": "default_user"
}

# ========================
# CSS自定义配置
# ========================
CUSTOM_CSS = """
/* 全局：响应式布局，消除不必要的空白，页面全宽显示 */
.gradio-app, .gradio-container {
    max-width: 100% !important;
    width: 100% !important;
}

.gradio-container {
    padding-left: 12px !important;
    padding-right: 12px !important;
}

.gradio-container > .gradio-column {
    gap: 8px !important;
    width: 100% !important;
}

/* 搜索行：模型检索和状态框高度对齐 */
#search_row {
    display: flex !important;
    align-items: stretch !important;
    width: 100% !important;
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

/* 主内容行：左右列根据内容自适应高度 */
#main_content_row {
    display: flex !important;
    align-items: flex-start !important;
    gap: 12px !important;
    width: 100% !important;
}
#main_content_row > .gradio-column {
    display: flex !important;
    flex-direction: column !important;
    min-width: 0 !important; /* 防止子元素撑破比例布局 */
}

/* GIF容器：保持5:3比例，自适应宽度（横向更宽） */
#gif_container {
    aspect-ratio: 5 / 3 !important; /* width / height */
    width: 100% !important;
}
#gif_box, #gif_container .gradio-image { /* 双保险绑定到具体image */
    aspect-ratio: 5 / 3 !important; /* keep inner the same */
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}
#gif_box img, #gif_container .gradio-image img {
    max-width: 100% !important;
    max-height: 100% !important;
    width: auto !important;
    height: auto !important;
    object-fit: contain !important;
    margin: auto !important;
}

/* 右侧信息列：自动填充空间 */
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
#info_column > .gradio-row:last-child { /* 按钮行 */
    margin-top: 8px !important;    /* 与上方保持最小间距 */
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

/* 确认弹窗样式 */
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

