"""
主程序：整合所有模块，启动标注工具

模块化架构：
- config.py: 配置文件
- field_processor.py: 字段处理器
- data_handler.py: 数据处理模块
- ui_builder.py: UI构建模块
- main.py: 主程序（本文件）
"""

import os
import argparse
import gradio as gr
from typing import Dict, List, Tuple

from config import FIELD_CONFIG, UI_CONFIG, PATH_CONFIG, DEFAULT_ARGS, CUSTOM_CSS
from data_handler import DataHandler
from ui_builder import UIBuilder
from field_processor import FieldProcessor


def build_gif_path(key: str, base_path: str) -> str:
    """
    构建GIF文件路径
    
    Args:
        key: 模型key (格式: type-subtype-category-model_id)
        base_path: 基础路径
        
    Returns:
        GIF文件路径
    """
    parts = key.split('-')
    if len(parts) >= 4:
        type_folder = f"{parts[0]}_objects"
        subtype_folder = parts[1]
        category_folder = parts[2]
        model_id = parts[3]
        filename = PATH_CONFIG['gif_filename_pattern'].format(model_id=model_id)
        return os.path.join(
            base_path, type_folder, subtype_folder, category_folder,
            "thumbnails/merged_views", model_id, filename
        )
    return None


def start_annotation(server_port: int, data_file: str, base_path: str, user_uid: str):
    """
    启动标注工具
    
    Args:
        server_port: 服务器端口
        data_file: 数据文件路径
        base_path: 基础路径
        user_uid: 用户ID
    """
    # 初始化模块
    data_handler = DataHandler(data_file)
    ui_builder = UIBuilder(FIELD_CONFIG)
    field_processor = FieldProcessor()
    
    # 加载数据
    ALL_DATA = data_handler.load_data()
    
    # 过滤数据：只保留当前用户可见的数据
    DATA_DICT = {}
    for key, value in ALL_DATA.items():
        attrs = data_handler.parse_item(value)
        item_uid = attrs.get('uid', '')
        if not item_uid or item_uid == user_uid:
            DATA_DICT[key] = value
    
    KEYS_LIST = list(DATA_DICT.keys())
    total_count = len(ALL_DATA)
    visible_count = len(DATA_DICT)
    
    # 打印统计信息
    print("=" * 60)
    print(f"👤 当前用户: {user_uid}")
    print(f"📂 加载的数据文件: {data_file}")
    print(f"📊 数据总数: {total_count} 个模型")
    print(f"👁️  可见数据: {visible_count} 个模型 (你的 + 未标注的)")
    print(f"🔒 被其他用户标注: {total_count - visible_count} 个模型")
    print("🔑 示例:", KEYS_LIST[:3])
    print("=" * 60)
    
    # ===== 辅助函数 =====
    
    def get_parts(k: str) -> Dict:
        """解析key的各个部分"""
        p = k.split('-')
        return {'type': p[0], 'subtype': p[1], 'category': p[2], 'model_id': p[3]} if len(p) >= 4 else {}
    
    def get_uniques() -> Dict:
        """获取所有唯一的类型、子类型、类别、模型ID"""
        t, s, c, m = set(), set(), set(), set()
        for k in KEYS_LIST:
            p = get_parts(k)
            if p:
                t.add(p['type'])
                s.add(p['subtype'])
                c.add(p['category'])
                m.add(p['model_id'])
        return dict(types=sorted(t), subtypes=sorted(s), categories=sorted(c), model_ids=sorted(m))
    
    def build_key(t, st, cat, mid) -> str:
        """构建key"""
        return f"{t}-{st}-{cat}-{mid}" if all([t, st, cat, mid]) else None
    
    def neighbor(k: str, direction: str) -> str:
        """获取相邻的key"""
        if not k or k not in KEYS_LIST:
            return ""
        i = KEYS_LIST.index(k)
        return KEYS_LIST[(i + 1) % len(KEYS_LIST)] if direction == "next" else KEYS_LIST[(i - 1) % len(KEYS_LIST)]
    
    def get_stats() -> Tuple[int, int, int]:
        """计算当前用户的数据统计"""
        visible = 0
        others = 0
        for value in ALL_DATA.values():
            attrs = data_handler.parse_item(value)
            item_uid = attrs.get('uid', '')
            if not item_uid or item_uid == user_uid:
                visible += 1
            else:
                others += 1
        return visible, others, len(ALL_DATA)
    
    def render_user_info():
        """生成用户信息栏HTML"""
        visible, others, _ = get_stats()
        return ui_builder.render_user_info_html(user_uid, visible, others)
    
    # ===== 核心业务逻辑 =====
    
    def load_all_data(k: str):
        """
        统一的数据加载函数
        返回所有需要更新的组件值
        """
        if not k or k not in DATA_DICT:
            # 空数据状态
            empty_values = [""] * len(ui_builder.get_field_keys())
            empty_checkboxes = [False] * len(ui_builder.get_all_checkbox_components())
            return (
                gr.update(value=""),  # key
                None,  # gif
                *empty_values,  # 所有输入框
                *empty_checkboxes,  # 所有勾选框
                gr.update(value=False),  # is_mod
                ui_builder.render_status_html(False),  # status
                render_user_info(),  # user_info
                gr.update(value=""), gr.update(value=""), gr.update(value=""), gr.update(value="")  # 下拉框
            )
        
        # 加载GIF和属性
        gif = build_gif_path(k, base_path)
        a = data_handler.parse_item(DATA_DICT[k])
        parts = get_parts(k)
        
        # 构建输入框值列表
        field_values = [a.get(field['key'], '') for field in FIELD_CONFIG]
        
        # 构建勾选框值列表
        checkbox_values = [
            a.get(field_processor.get_checkbox_key(field['key']), False)
            for field in FIELD_CONFIG if field.get('has_checkbox', False)
        ]
        
        return (
            gr.update(value=k),  # key
            gif if gif and os.path.exists(gif) else None,  # gif
            *field_values,  # 所有输入框
            *checkbox_values,  # 所有勾选框
            gr.update(value=False),  # is_mod
            ui_builder.render_status_html(a.get('annotated', False)),  # status
            render_user_info(),  # user_info
            gr.update(value=parts.get('type', '')),  # type
            gr.update(value=parts.get('subtype', '')),  # subtype
            gr.update(value=parts.get('category', '')),  # category
            gr.update(value=parts.get('model_id', ''))  # model_id
        )
    
    def modified(k: str, *all_values):
        """检查是否有修改"""
        if not k or k not in DATA_DICT:
            return False
        
        o = data_handler.parse_item(DATA_DICT[k])
        
        # 分离输入框值和勾选框值
        field_count = len(FIELD_CONFIG)
        field_values = all_values[:field_count]
        checkbox_values = all_values[field_count:]
        
        # 检查输入框
        for idx, field in enumerate(FIELD_CONFIG):
            if field_values[idx] != o.get(field['key'], ''):
                return True
        
        # 检查勾选框
        chk_idx = 0
        for field in FIELD_CONFIG:
            if field.get('has_checkbox', False):
                chk_key = field_processor.get_checkbox_key(field['key'])
                if chk_idx < len(checkbox_values) and checkbox_values[chk_idx] != o.get(chk_key, False):
                    return True
                chk_idx += 1
        
        return False
    
    def save_one(k: str, *all_values):
        """保存单个数据"""
        if not k:
            return gr.update(), ui_builder.render_status_html(False), render_user_info()
        
        # 分离输入框值和勾选框值
        field_count = len(FIELD_CONFIG)
        field_values_list = all_values[:field_count]
        checkbox_values_list = all_values[field_count:]
        
        # 构建字典
        field_values = {field['key']: field_values_list[idx] for idx, field in enumerate(FIELD_CONFIG)}
        
        checkbox_values = {}
        chk_idx = 0
        for field in FIELD_CONFIG:
            if field.get('has_checkbox', False):
                checkbox_values[field['key']] = checkbox_values_list[chk_idx] if chk_idx < len(checkbox_values_list) else False
                chk_idx += 1
        
        # 保存数据
        saved_data = data_handler.build_save_data(field_values, checkbox_values, user_uid)
        DATA_DICT[k] = saved_data
        ALL_DATA[k] = saved_data
        data_handler.save_data(ALL_DATA)
        
        return gr.update(value=False), ui_builder.render_status_html(True), render_user_info()
    
    # ===== 构建UI =====
    
    uniq = get_uniques()
    
    with gr.Blocks(title=UI_CONFIG['title'], css=CUSTOM_CSS, theme=gr.themes.Default(spacing_size="sm").set(body_text_size="sm")) as demo:
        gr.Markdown(f"# {UI_CONFIG['title']}")
        
        # 用户信息栏
        if UI_CONFIG.get('show_user_info', True):
            user_info = gr.HTML(render_user_info())
        else:
            user_info = gr.HTML("")
        
        is_mod = gr.State(value=False)
        nav_dir = gr.State(value="next")
        
        # 类型选择下拉框
        if UI_CONFIG.get('show_dropdowns', True):
            with gr.Row(equal_height=True):
                t = gr.Dropdown(choices=uniq['types'], label="类型 (Type)")
                st = gr.Dropdown(choices=uniq['subtypes'], label="子类型 (Subtype)")
                c = gr.Dropdown(choices=uniq['categories'], label="类别 (Category)")
                mid = gr.Dropdown(choices=uniq['model_ids'], label="模型ID (Model ID)")
        else:
            t = gr.State(value="")
            st = gr.State(value="")
            c = gr.State(value="")
            mid = gr.State(value="")
        
        # 搜索行
        with gr.Row(equal_height=True, elem_id="search_row"):
            key = gr.Textbox(label="模型检索", interactive=True, placeholder="输入模型ID快速检索...", scale=3, container=True)
            if UI_CONFIG.get('show_status', True):
                with gr.Column(scale=1, min_width=120):
                    status = gr.HTML(ui_builder.render_status_html(False))
            else:
                status = gr.HTML("")
        
        # 主内容区
        with gr.Row(elem_id="main_content_row"):
            # 左侧：GIF（按CSS比例渲染）
            with gr.Column(scale=1, elem_id="gif_container"):
                gif = gr.Image(
                    label="物体渲染视频",
                    elem_id="gif_box",
                    container=True,
                    show_download_button=False
                )
            
            # 右侧：属性字段（动态生成，与左侧1:1）
            with gr.Column(scale=1, elem_id="info_column"):
                field_components = ui_builder.build_field_components()
                # 操作按钮（放入右侧列的底部，自动紧贴最长内容）
                with gr.Row(equal_height=True, elem_id="button_row"):
                    prev_btn = gr.Button("⬅️ 上一个", variant="secondary", size="lg")
                    save_btn = gr.Button("💾 保存", variant="primary", size="lg")
                    next_btn = gr.Button("➡️ 下一个", variant="secondary", size="lg")
        
        # 确认弹窗
        with gr.Column(visible=False, elem_id="confirm_modal") as confirm:
            with gr.Column(elem_id="confirm_card"):
                gr.HTML("<h2>⚠️ 有未保存的修改</h2><p>是否继续？</p>")
                with gr.Row():
                    save_next = gr.Button("💾 保存继续", variant="primary", size="sm")
                    cancel = gr.Button("❌ 取消", variant="secondary", size="sm")
                skip = gr.Button("⚠️ 放弃更改", variant="stop", size="sm")
        
        # 定义输出组件列表
        ALL_OUTPUTS = [
            key, gif,
            *ui_builder.get_all_input_components(),
            *ui_builder.get_all_checkbox_components(),
            is_mod, status, user_info,
            t, st, c, mid
        ]
        
        # ===== 事件绑定 =====
        
        # 下拉框改变
        if UI_CONFIG.get('show_dropdowns', True):
            def on_dropdown_change(t_val, st_val, c_val, mid_val):
                k = build_key(t_val, st_val, c_val, mid_val)
                if k and k in KEYS_LIST:
                    return gr.update(value=k)
                return gr.update(value="")
            
            for dd in (t, st, c, mid):
                dd.change(on_dropdown_change, inputs=[t, st, c, mid], outputs=[key])
        
        # 搜索功能
        def on_search(search_text):
            if not search_text:
                return load_all_data("")
            if search_text in KEYS_LIST:
                return load_all_data(search_text)
            matched = [k for k in KEYS_LIST if search_text in k]
            if matched:
                return load_all_data(matched[0])
            return load_all_data("")
        
        key.submit(on_search, inputs=[key], outputs=ALL_OUTPUTS)
        
        # 失焦补全
        def on_key_blur(search_text):
            if search_text in KEYS_LIST:
                return gr.update(value=search_text)
            matched = [k for k in KEYS_LIST if search_text in k]
            if matched:
                return gr.update(value=matched[0])
            return gr.update()
        
        key.blur(on_key_blur, inputs=[key], outputs=[key])
        
        # key变化时加载数据
        key.change(lambda k: load_all_data(k), inputs=[key], outputs=ALL_OUTPUTS)
        
        # 输入框和勾选框变化时标记为已修改
        def mark():
            return gr.update(value=True)
        
        for comp in ui_builder.get_all_components():
            comp.change(mark, inputs=[], outputs=[is_mod])
        
        # 保存按钮
        save_btn.click(
            save_one,
            inputs=[key, *ui_builder.get_all_input_components(), *ui_builder.get_all_checkbox_components()],
            outputs=[is_mod, status, user_info]
        )
        
        # 导航按钮
        def on_nav(*args):
            direction = args[-1]
            k = args[0]
            all_values = args[1:-1]
            
            if modified(k, *all_values):
                return gr.update(), gr.update(visible=True), gr.update(value=direction)
            
            next_key = neighbor(k, direction)
            return gr.update(value=next_key), gr.update(visible=False), gr.update(value=direction)
        
        next_btn.click(
            on_nav,
            inputs=[key, *ui_builder.get_all_input_components(), *ui_builder.get_all_checkbox_components(), gr.State("next")],
            outputs=[key, confirm, nav_dir]
        )
        
        prev_btn.click(
            on_nav,
            inputs=[key, *ui_builder.get_all_input_components(), *ui_builder.get_all_checkbox_components(), gr.State("prev")],
            outputs=[key, confirm, nav_dir]
        )
        
        # 保存并继续
        def on_save_and_go(*args):
            direction = args[-1]
            k = args[0]
            all_values = args[1:-1]
            
            save_one(k, *all_values)
            next_key = neighbor(k, direction)
            return gr.update(value=next_key), gr.update(visible=False), gr.update(value=False), render_user_info()
        
        save_next.click(
            on_save_and_go,
            inputs=[key, *ui_builder.get_all_input_components(), *ui_builder.get_all_checkbox_components(), nav_dir],
            outputs=[key, confirm, is_mod, user_info]
        )
        
        # 放弃修改并继续
        def on_skip_and_go(k, direction):
            next_key = neighbor(k, direction)
            return gr.update(value=next_key), gr.update(visible=False)
        
        skip.click(on_skip_and_go, inputs=[key, nav_dir], outputs=[key, confirm])
        
        # 取消弹窗
        cancel.click(lambda: gr.update(visible=False), inputs=[], outputs=[confirm])
        
        # 页面加载时自动加载第一个数据
        demo.load(lambda: KEYS_LIST[0] if KEYS_LIST else "", inputs=[], outputs=[key])
    
    # 启动服务
    demo.queue()
    demo.launch(server_name='0.0.0.0', server_port=server_port, allowed_paths=[base_path])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="物体属性标注工具 - 模块化版本")
    parser.add_argument('--data_file', type=str, default=PATH_CONFIG['data_file'], help="数据文件路径")
    parser.add_argument('--base_path', type=str, default=PATH_CONFIG['base_path'], help="GIF文件基础路径")
    parser.add_argument('--port', type=int, default=DEFAULT_ARGS['port'], help="服务器端口")
    parser.add_argument('--uid', type=str, default=DEFAULT_ARGS['uid'], help="用户唯一标识符")
    args = parser.parse_args()
    
    start_annotation(args.port, args.data_file, args.base_path, args.uid)

