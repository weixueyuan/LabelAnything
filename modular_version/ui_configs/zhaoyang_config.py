"""
物体属性标注任务配置（参考旧版本config.py）
"""

# 任务信息
TASK_INFO = {
    "task_id": "annotation",
    "task_name": "物体属性标注",
    "description": "标注物体的基本属性信息"
}

# 字段配置（通用版本，支持多种数据格式）
# 说明：
# - "key": 数据字段名称
# - "label": UI显示标签
# - "type": 组件类型（目前只支持textbox）
# - "lines": 文本框行数
# - "has_checkbox": 是否显示错误标记勾选框
# - "placeholder": 占位符文本
# - "flex": 布局弹性系数（数字越大占用空间越多）
# - "process": 字段处理方式（"array_to_string"表示数组转字符串）
FIELD_CONFIG = [
    {
        "key": "object_name",
        "label": "Object Name (物体名称)",
        "type": "textbox",
        "lines": 1,
        "has_checkbox": True,
        "flex": 1,
        "process": None
    },
    {
        "key": "dimension",
        "label": "Dimension (尺寸)",
        "type": "textbox",
        "lines": 1,
        "has_checkbox": True,
        "flex": 1,
        "process": None
    },
    {
        "key": "overall_description",
        "label": "Overall Description (整体描述)",
        "type": "textbox",
        "lines": 5,
        "has_checkbox": True,
        "flex": 3,
        "process": "array_to_string"  # 数据中是数组格式，需要转换为逗号分隔字符串显示
    }
]

# UI配置（从旧版config.py迁移）
UI_CONFIG = {
    "title": "物体属性检查工具",
    "gif_height": None,
    "info_column_height": None,
    "enable_checkboxes": True,
    "checkbox_label": "✗",
    "show_user_info": True,
    "show_status": True,
}

# 路径配置（从旧版config.py迁移）
# 说明：一个配置对应一个 JSONL 文件，通过 jsonl_file 指定数据源
PATH_CONFIG = {
    # 数据源：JSONL 文件路径（必需）
    "jsonl_file": "/mnt/inspurfs/IDC_t/lvzhaoyang_group/digital_content/lianxinyu/datasets/partnet_mobility_by_category_processed/box/main_jsonl",
    
    # GIF 图片基础路径
    "base_path": "/mnt/data/GRScenes-100/instances/renderings",
    
    # GIF 文件名模式
    "gif_filename_pattern": "{model_id}_fixed.gif",
}

# CSS配置（从旧版config.py迁移）
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
    min-width: 0 !important;
}

/* GIF容器：保持1:1比例，自适应宽度（横向更宽） */
#gif_container {
    aspect-ratio: 1 / 1 !important;
    width: 100% !important;
}
#gif_box, #gif_container .gradio-image {
    aspect-ratio: 1 / 1 !important;
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
#info_column > .gradio-row:last-child {
    margin-top: 8px !important;
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
