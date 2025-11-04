#!/usr/bin/env python
"""
多任务主程序

目前只有一个任务（annotation），但架构支持以后轻松添加新任务
"""

import os
import sys
import importlib
import argparse
import gradio as gr
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.db_handler import DatabaseHandler
from src.jsonl_handler import JSONLHandler
from src.field_processor import FieldProcessor
from routes import ROUTES, DEFAULT_PORT


class TaskManager:
    """任务管理器"""
    
    def __init__(self, task_config, user_uid="default_user", debug=False):
        self.task_config = task_config
        self.user_uid = user_uid
        self.task_name = task_config['task']
        self.debug = debug
        
        # 加载UI配置
        config_module = importlib.import_module(f"ui_configs.{self.task_name}_config")
        self.field_configs = config_module.FIELD_CONFIG
        self.ui_config = config_module.UI_CONFIG
        self.task_info = config_module.TASK_INFO
        self.custom_css = getattr(config_module, 'CUSTOM_CSS', '')
        
        # 数据库路径
        self.db_path = f"databases/{self.task_name}.db"
        
        # 初始化
        self.field_processor = FieldProcessor()
        self._load_data()
    
    def _load_data(self):
        """加载数据（支持数据库模式和 JSONL debug 模式）"""
        # Debug 模式：使用 test.jsonl
        if self.debug:
            jsonl_file = 'test.jsonl'
            if os.path.exists(jsonl_file):
                print(f"🐛 Debug 模式: {jsonl_file}")
                self.data_handler = JSONLHandler(jsonl_file)
                self.data_source = 'jsonl'
            else:
                print(f"⚠️  Debug 模式：未找到 {jsonl_file}")
                print(f"   创建空的测试文件...")
                # 创建空的 test.jsonl
                with open(jsonl_file, 'w', encoding='utf-8'):
                    pass
                self.data_handler = JSONLHandler(jsonl_file)
                self.data_source = 'jsonl'
                self.all_data = {}
                self.visible_keys = []
                print(f"   ✓ 已创建空的 {jsonl_file}")
                return
        else:
            # 正常模式：使用数据库
            if os.path.exists(self.db_path):
                print(f"🗄️  数据库模式: {self.db_path}")
                self.data_handler = DatabaseHandler(self.db_path)
                self.data_source = 'database'
            else:
                print(f"❌ 未找到数据库: {self.db_path}")
                print(f"   请先导入数据: python -m importers.annotation_importer")
                self.data_handler = None
                self.all_data = {}
                self.visible_keys = []
                return
        
        # 加载所有数据
        self.all_data = self.data_handler.load_data()
        
        # 过滤可见数据
        self.visible_keys = []
        for key, value in self.all_data.items():
            attrs = self.data_handler.parse_item(value)
            item_uid = attrs.get('uid', '')
            if not item_uid or item_uid == self.user_uid:
                self.visible_keys.append(key)
        
        print(f"✓ 加载完成")
        print(f"  总数: {len(self.all_data)}, 可见: {len(self.visible_keys)}")
    
    def build_annotation_components(self, demo=None):
        """
        构建标注界面组件（可用于嵌入到其他界面中）
        
        Args:
            demo: 已有的Blocks对象，如果为None则创建新的
        
        Returns:
            组件字典和事件绑定函数
        """
        if not self.data_handler:
            return None, None, None
        
        components = {}
        bindings = {}
        
        # 创建所有组件（但不绑定到demo）
        with gr.Column() if demo is None else gr.Column():
            # 用户信息
            if self.ui_config.get('show_user_info'):
                other_count = len(self.all_data) - len(self.visible_keys)
                components['user_info'] = gr.HTML(self._render_user_info(len(self.visible_keys), other_count))
            
            current_index = gr.State(value=0)
            components['current_index'] = current_index
            nav_direction = gr.State(value="next")
            components['nav_direction'] = nav_direction
            
            # Model ID 和状态框
            with gr.Row(equal_height=True, elem_id="search_row"):
                model_id_display = gr.Textbox(label="Model ID", interactive=False, scale=3)
                components['model_id_display'] = model_id_display
                status_box = gr.HTML(value="") if self.ui_config.get('show_status') else None
                if status_box:
                    components['status_box'] = status_box
            
            # GIF 和属性字段
            with gr.Row(elem_id="main_content_row"):
                with gr.Column(scale=1, elem_id="gif_container"):
                    gif_display = gr.Image(label="物体可视化", type="filepath", height=580, container=True, show_download_button=False)
                    components['gif_display'] = gif_display
                
                with gr.Column(scale=1, elem_id="info_column"):
                    field_components = []
                    checkbox_components = []
                    
                    for field in self.field_configs:
                        with gr.Column():
                            if field.get('has_checkbox') and self.ui_config.get('enable_checkboxes'):
                                chk = gr.Checkbox(
                                    label=f"{self.ui_config.get('checkbox_label', '✗')} {field['label']}", 
                                    value=False, container=False
                                )
                                checkbox_components.append(chk)
                            
                            comp = gr.Textbox(
                                label="",
                                lines=field.get('lines', 1),
                                placeholder=field.get('placeholder', ''),
                                show_label=False
                            )
                            field_components.append(comp)
                    
                    components['field_components'] = field_components
                    components['checkbox_components'] = checkbox_components
            
            # 按钮和进度
            with gr.Row():
                prev_btn = gr.Button("⬅️ 上一个", size="lg")
                save_btn = gr.Button("💾 保存", variant="primary", size="lg")
                next_btn = gr.Button("➡️ 下一个", size="lg")
                components['prev_btn'] = prev_btn
                components['save_btn'] = save_btn
                components['next_btn'] = next_btn
            
            progress = gr.Textbox(label="进度", interactive=False)
            components['progress'] = progress
            
            # 导出按钮
            if not self.debug and self.data_source == 'database':
                with gr.Row():
                    export_btn = gr.Button("📤 导出为JSONL", variant="secondary", size="lg")
                    export_status = gr.Textbox(label="导出状态", interactive=False, visible=False)
                    components['export_btn'] = export_btn
                    components['export_status'] = export_status
            
            # 确认弹窗
            with gr.Column(visible=False, elem_id="confirm_modal") as confirm_modal:
                with gr.Column(elem_id="confirm_card"):
                    gr.HTML("<h2>⚠️ 有未保存的修改</h2><p>是否继续？</p>")
                    with gr.Row():
                        save_and_continue = gr.Button("💾 保存并继续", variant="primary", size="sm")
                        cancel_nav = gr.Button("❌ 取消", variant="secondary", size="sm")
                    skip_changes = gr.Button("⚠️ 放弃更改", variant="stop", size="sm")
                    components['confirm_modal'] = confirm_modal
                    components['save_and_continue'] = save_and_continue
                    components['cancel_nav'] = cancel_nav
                    components['skip_changes'] = skip_changes
        
        # 返回组件字典（用于后续绑定事件）
        return components, bindings
    
    def build_interface(self):
        """构建界面"""
        if not self.data_handler:
            with gr.Blocks() as demo:
                gr.Markdown(f"# ⚠️ 数据库未初始化\n运行: `python tools/import_to_db.py`")
            return demo
        
        with gr.Blocks(title=self.ui_config['title'], css=self.custom_css) as demo:
            gr.Markdown(f"# {self.ui_config['title']}")
            
            # 用户信息
            if self.ui_config.get('show_user_info'):
                other_count = len(self.all_data) - len(self.visible_keys)
                _ = gr.HTML(self._render_user_info(len(self.visible_keys), other_count))
            
            current_index = gr.State(value=0)
            nav_direction = gr.State(value="next")
            
            # Model ID 和状态框（单独一行）
            with gr.Row(equal_height=True, elem_id="search_row"):
                model_id_display = gr.Textbox(label="Model ID", interactive=False, scale=3)
                status_box = gr.HTML(value="") if self.ui_config.get('show_status') else None
            
            # GIF 和属性字段（分两列）
            with gr.Row(elem_id="main_content_row"):
                # 左：GIF
                with gr.Column(scale=1, elem_id="gif_container"):
                    gif_display = gr.Image(label="物体可视化", type="filepath", height=580, container=True, show_download_button=False)
                
                # 右：字段
                with gr.Column(scale=1, elem_id="info_column"):
                    # 字段组件
                    field_components = []
                    checkbox_components = []
                    
                    # 尺度滑块相关（用于dimensions字段）
                    scale_slider = None
                    original_dimensions = gr.State(value="")  # 存储原始dimensions值
                    
                    for field in self.field_configs:
                        with gr.Column():
                            if field.get('has_checkbox') and self.ui_config.get('enable_checkboxes'):
                                chk = gr.Checkbox(
                                    label=f"{self.ui_config.get('checkbox_label', '✗')} {field['label']}", 
                                    value=False, container=False
                                )
                                checkbox_components.append(chk)
                            
                            comp = gr.Textbox(
                                label="",
                                lines=field.get('lines', 1),
                                placeholder=field.get('placeholder', ''),
                                show_label=False
                            )
                            field_components.append(comp)
                            
                            # 为dimensions字段添加尺度滑块
                            if field['key'] == 'dimensions':
                                scale_slider = gr.Slider(
                                    minimum=0.01,
                                    maximum=2.0,
                                    value=1.0,
                                    step=0.01,
                                    label="尺度缩放 (Scale)",
                                    info="调整尺寸的缩放比例"
                                )
            
            # 按钮和进度（单独在下面）
            with gr.Row():
                prev_btn = gr.Button("⬅️ 上一个", size="lg")
                save_btn = gr.Button("💾 保存", variant="primary", size="lg")
                next_btn = gr.Button("➡️ 下一个", size="lg")
            
            progress = gr.Textbox(label="进度", interactive=False)
            
            # 导出按钮（仅在正常模式下显示）
            export_btn = None
            export_status = None
            if not self.debug and self.data_source == 'database':
                with gr.Row():
                    export_btn = gr.Button("📤 导出为JSONL", variant="secondary", size="lg")
                    export_status = gr.Textbox(label="导出状态", interactive=False, visible=False)
            
            # 确认弹窗
            with gr.Column(visible=False, elem_id="confirm_modal") as confirm_modal:
                with gr.Column(elem_id="confirm_card"):
                    gr.HTML("<h2>⚠️ 有未保存的修改</h2><p>是否继续？</p>")
                    with gr.Row():
                        save_and_continue = gr.Button("💾 保存并继续", variant="primary", size="sm")
                        cancel_nav = gr.Button("❌ 取消", variant="secondary", size="sm")
                    skip_changes = gr.Button("⚠️ 放弃更改", variant="stop", size="sm")
            
            # 事件处理
            def load_data(index):
                if not self.visible_keys or index >= len(self.visible_keys):
                    empty_count = 2 + len(field_components) + len(checkbox_components) + (1 if status_box else 0) + 1 + 2  # +2 for original_dimensions and scale_slider
                    return [""] * (empty_count - 1) + [1.0]  # last element is scale_slider value
                
                model_id = self.visible_keys[index]
                item = self.all_data[model_id]
                attrs = self.data_handler.parse_item(item)
                
                # 【关键改动】浏览即占有：如果数据未分配，立即分配给当前用户
                current_uid = attrs.get('uid', '')
                if not current_uid or current_uid == '':
                    # 数据未分配，立即占有（只设置uid，不触碰其他数据）
                    self.data_handler.assign_to_user(model_id, self.user_uid)
                    print(f"🔒 占有数据: {model_id} -> {self.user_uid}")
                    # 刷新缓存
                    self.all_data = self.data_handler.load_data()
                    # 重新计算可见数据（排除其他用户已占有的数据）
                    self.visible_keys = []
                    for key, value in self.all_data.items():
                        item_attrs = self.data_handler.parse_item(value)
                        item_uid = item_attrs.get('uid', '')
                        if not item_uid or item_uid == self.user_uid:
                            self.visible_keys.append(key)
                    # 重新获取属性（现在包含了uid）
                    item = self.all_data[model_id]
                    attrs = self.data_handler.parse_item(item)
                
                # 直接使用 image_url（数据源已提供：数据库导入时生成，JSONL读取时生成）
                gif_path = attrs.get('image_url', None)
                
                # 检查文件是否存在
                if gif_path and not os.path.exists(gif_path):
                    gif_path = None
                
                field_values = []
                checkbox_values = []
                for field in self.field_configs:
                    value = attrs.get(field['key'], '')
                    field_values.append(self.field_processor.process_load(field, value))
                    
                    if field.get('has_checkbox'):
                        checkbox_values.append(attrs.get(f"chk_{field['key']}", False))
                
                prog = f"{index + 1} / {len(self.visible_keys)}"
                
                # 获取原始dimensions值（用于尺度调整）
                orig_dims = attrs.get('dimensions', '')
                
                result = [gif_path, model_id] + field_values + checkbox_values
                if status_box:
                    status_html = self._render_status(attrs.get('annotated', False))
                    result.append(status_html)
                result.append(prog)
                
                # 添加原始dimensions和重置slider
                result.append(orig_dims)  # original_dimensions state
                result.append(1.0)  # reset scale_slider to 1.0
                
                return result
            
            def scale_dimensions(original_dims, scale_value):
                """根据尺度滑块值计算缩放后的dimensions"""
                if not original_dims or not original_dims.strip():
                    return ""
                
                try:
                    # 解析dimensions字符串，格式如 "0.6 * 0.4 * 0.02"
                    parts = original_dims.replace('*', ' ').split()
                    numbers = [float(p.strip()) for p in parts if p.strip()]
                    
                    if not numbers:
                        return original_dims
                    
                    # 应用缩放
                    scaled_numbers = [n * scale_value for n in numbers]
                    
                    # 重新组装字符串
                    result = ' * '.join([f"{n:.2f}" if n >= 0.01 else f"{n:.4f}" for n in scaled_numbers])
                    return result
                    
                except Exception as e:
                    print(f"⚠️  尺度计算错误: {e}")
                    return original_dims
            
            def _resolve_model(index, model_id):
                """根据索引和model_id解析当前记录"""
                resolved_model = None
                resolved_index = index
                if model_id and model_id in self.visible_keys:
                    resolved_model = model_id
                    resolved_index = self.visible_keys.index(model_id)
                elif 0 <= index < len(self.visible_keys):
                    resolved_model = self.visible_keys[index]
                return resolved_index, resolved_model

            def save_data(index, model_id, *values):
                resolved_index, resolved_model = _resolve_model(index, model_id)
                if resolved_model is None:
                    return load_data(resolved_index)
                
                num_fields = len(self.field_configs)
                field_values = values[:num_fields]
                checkbox_values = values[num_fields:]
                
                save_dict = {}
                checkbox_idx = 0
                has_error = False  # 检查是否有任何勾选框被选中
                
                for idx, field in enumerate(self.field_configs):
                    key = field['key']
                    save_dict[key] = self.field_processor.process_save(field, field_values[idx])
                    if field.get('has_checkbox'):
                        chk_value = checkbox_values[checkbox_idx]
                        save_dict[f"chk_{key}"] = chk_value
                        if chk_value:  # 如果有任何勾选框被选中
                            has_error = True
                        checkbox_idx += 1
                
                # 计算 score：如果任意勾选框被选中，score=0；否则score=1
                score = 0 if has_error else 1
                
                # 保存（传递 uid）
                self.data_handler.save_item(resolved_model, save_dict, score=score, uid=self.user_uid)
                print(f"✅ 保存: {resolved_model}, score={score}, uid={self.user_uid}")
                
                # 更新缓存（重新加载以获取最新的文件内容）
                self.all_data = self.data_handler.load_data()
                
                # 重新加载数据
                return load_data(resolved_index)
            
            # 修改检测函数（简化版：直接比较，避免类型转换问题）
            def check_modified(index, model_id, *values):
                """检查当前数据是否被修改"""
                if not self.visible_keys:
                    return False
                
                resolved_index, resolved_model = _resolve_model(index, model_id)
                if resolved_model is None or not (0 <= resolved_index < len(self.visible_keys)):
                    return False
                
                item = self.all_data.get(resolved_model)
                if item is None:
                    # 尝试刷新缓存
                    self.all_data = self.data_handler.load_data()
                    item = self.all_data.get(resolved_model)
                    if item is None:
                        return False
                attrs = self.data_handler.parse_item(item)
                
                num_fields = len(self.field_configs)
                field_values = values[:num_fields]
                checkbox_values = values[num_fields:]
                
                # 构建当前显示的原始值（和 load_data 相同的处理）
                original_values = []
                for field in self.field_configs:
                    value = attrs.get(field['key'], '')
                    original_values.append(self.field_processor.process_load(field, value))
                
                # 比较每个字段（处理 None 和空字符串的等价性）
                for idx in range(num_fields):
                    orig = original_values[idx] if original_values[idx] is not None else ''
                    curr = field_values[idx] if field_values[idx] is not None else ''
                    if str(orig) != str(curr):
                        return True
                
                # 比较勾选框
                checkbox_idx = 0
                for field in self.field_configs:
                    if field.get('has_checkbox'):
                        original_chk = attrs.get(f"chk_{field['key']}", False)
                        current_chk = checkbox_values[checkbox_idx]
                        if original_chk != current_chk:
                            return True
                        checkbox_idx += 1
                
                return False
            
            # 导航函数（带修改检测）
            def navigate_with_check(index, model_id, direction, *values):
                """导航前检查是否有修改"""
                resolved_index, resolved_model = _resolve_model(index, model_id)
                modified = check_modified(resolved_index, resolved_model, *values)
                if modified:
                    # 有修改，显示弹窗
                    return [gr.update(value=resolved_index), gr.update(visible=True), gr.update(value=direction)] + [gr.update()] * len(outputs)
                else:
                    # 无修改，直接跳转并加载数据
                    if direction == "next":
                        new_index = min(len(self.visible_keys) - 1, resolved_index + 1)
                    else:
                        new_index = max(0, resolved_index - 1)
                    
                    load_result = load_data(new_index)
                    return [gr.update(value=new_index), gr.update(visible=False), gr.update()] + load_result
            
            # 保存并继续
            def save_and_nav(index, model_id, direction, *values):
                """保存当前数据并跳转"""
                # 先保存
                _ = save_data(index, model_id, *values)
                
                # 再跳转并加载数据
                resolved_index, _ = _resolve_model(index, model_id)
                if direction == "next":
                    new_index = min(len(self.visible_keys) - 1, resolved_index + 1)
                else:
                    new_index = max(0, resolved_index - 1)
                
                load_result = load_data(new_index)
                return [gr.update(value=new_index), gr.update(visible=False)] + load_result
            
            # 放弃更改并继续
            def skip_and_nav(index, model_id, direction):
                """放弃更改并跳转"""
                resolved_index, _ = _resolve_model(index, model_id)
                if direction == "next":
                    new_index = min(len(self.visible_keys) - 1, resolved_index + 1)
                else:
                    new_index = max(0, resolved_index - 1)
                
                load_result = load_data(new_index)
                return [gr.update(value=new_index), gr.update(visible=False)] + load_result
            
            # 绑定事件
            status_outputs = [status_box] if status_box else []
            outputs = [gif_display, model_id_display] + field_components + checkbox_components + status_outputs + [progress, original_dimensions, scale_slider]
            
            # 找到dimensions字段的索引
            dimensions_idx = None
            for idx, field in enumerate(self.field_configs):
                if field['key'] == 'dimensions':
                    dimensions_idx = idx
                    break
            
            # 绑定尺度滑块事件（如果找到dimensions字段）
            if dimensions_idx is not None and scale_slider is not None:
                scale_slider.change(
                    fn=scale_dimensions,
                    inputs=[original_dimensions, scale_slider],
                    outputs=[field_components[dimensions_idx]]
                )
            
            # 初始加载
            demo.load(lambda: load_data(0), outputs=outputs)
            
            # 保存按钮
            save_btn.click(
                save_data,
                inputs=[current_index, model_id_display] + field_components + checkbox_components,
                outputs=outputs
            )
            
            # 导航按钮（带修改检测）
            prev_btn.click(
                navigate_with_check,
                inputs=[current_index, model_id_display, gr.State("prev")] + field_components + checkbox_components,
                outputs=[current_index, confirm_modal, nav_direction] + outputs
            )
            
            next_btn.click(
                navigate_with_check,
                inputs=[current_index, model_id_display, gr.State("next")] + field_components + checkbox_components,
                outputs=[current_index, confirm_modal, nav_direction] + outputs
            )
            
            # 确认弹窗按钮
            save_and_continue.click(
                save_and_nav,
                inputs=[current_index, model_id_display, nav_direction] + field_components + checkbox_components,
                outputs=[current_index, confirm_modal] + outputs
            )
            
            skip_changes.click(
                skip_and_nav,
                inputs=[current_index, model_id_display, nav_direction],
                outputs=[current_index, confirm_modal] + outputs
            )
            
            cancel_nav.click(
                lambda: gr.update(visible=False),
                outputs=[confirm_modal]
            )
            
            # 导出按钮事件（仅在正常模式下）
            if not self.debug and self.data_source == 'database':
                def export_data():
                    """导出数据库数据为JSONL文件"""
                    try:
                        if hasattr(self.data_handler, 'export_to_jsonl'):
                            filepath = self.data_handler.export_to_jsonl()
                            filename = os.path.basename(filepath)
                            return gr.update(value=f"✅ 导出成功: {filename}", visible=True)
                        else:
                            return gr.update(value="❌ 导出功能不可用（当前数据源不支持）", visible=True)
                    except Exception as e:
                        return gr.update(value=f"❌ 导出失败: {str(e)}", visible=True)
                
                export_btn.click(
                    export_data,
                    inputs=[],
                    outputs=[export_status]
                )
        
        return demo
    
    def _render_status(self, annotated):
        if annotated:
            return '''<div style="
                height: 100%;
                min-height: 56px;
                background-color: #d4edda;
                border: 2px solid #c3e6cb;
                padding: 8px;
                font-size: 14px;
                text-align: center;
                font-weight: 600;
                border-radius: 6px;
                display: flex;
                align-items: center;
                justify-content: center;
                box-sizing: border-box;
                color: #155724;
            ">✅ 已标注</div>'''
        return '''<div style="
            height: 100%;
            min-height: 56px;
            background-color: #f8d7da;
            border: 2px solid #f5c6cb;
            padding: 8px;
            font-size: 14px;
            text-align: center;
            font-weight: 600;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-sizing: border-box;
            color: #721c24;
        ">❌ 未标注</div>'''
    
    def _render_user_info(self, visible, others):
        return f'<div style="background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:12px;border-radius:8px;text-align:center;">👤 用户：{self.user_uid} | 📊 可见：{visible} | 🔒 其他：{others}</div>'
    
    def get_allowed_paths(self):
        """
        从数据库数据中提取允许访问的基础路径（用于Gradio的allowed_paths）
        
        从image_url字段中提取第一个路径段，适配不同项目的路径结构
        """
        # 默认路径（如果数据库为空）
        default_path = "/mnt"
        
        if not self.all_data:
            return [default_path]
        
        # 从第一个数据项的image_url中提取基础路径
        first_item = list(self.all_data.values())[0]
        attrs = self.data_handler.parse_item(first_item)
        image_url = attrs.get('image_url', '')
        
        if image_url and image_url.startswith('/'):
            # 提取第一个路径段（根目录下的第一级目录）
            # 例如: /mnt/data/... -> /mnt
            #      /data/images/... -> /data
            #      /home/user/... -> /home
            parts = image_url.split('/')
            if len(parts) >= 2 and parts[1]:
                base_path = f"/{parts[1]}"
                return [base_path]
        
        # 如果没有找到有效路径，使用默认值
        return [default_path]


def create_login_interface(auth_handler, task_config, debug):
    """创建统一的登录和标注界面，登录成功后直接切换显示"""
    
    # 先创建标注界面管理器（使用临时用户，获取配置）
    temp_manager = TaskManager(task_config, "temp_user", debug=debug)
    
    # 如果数据未初始化，直接返回错误提示
    if not temp_manager.data_handler:
        with gr.Blocks() as error_demo:
            gr.Markdown("# ⚠️ 数据库未初始化\n运行: `python -m importers.annotation_importer`")
        return error_demo
    
    with gr.Blocks(title="物体属性标注工具", css=temp_manager.custom_css) as unified_demo:
        logged_in_user = gr.State(value=None)
        current_manager_state = gr.State(value=None)
        
        # 登录面板（初始显示）
        with gr.Column(visible=True, elem_id="login_panel") as login_panel:
            gr.Markdown("# 🔐 物体属性标注工具")
            gr.Markdown("## 登录")
            
            with gr.Column():
                login_username = gr.Textbox(label="用户名", placeholder="输入用户名")
                login_password = gr.Textbox(label="密码", type="password", placeholder="输入密码")
                login_btn = gr.Button("登录", variant="primary", size="lg")
                login_status = gr.Textbox(label="状态", interactive=False, visible=False)
        
        # 标注界面面板（登录后显示，预先创建但初始隐藏）
        with gr.Column(visible=False) as annotation_panel:
            # 预先创建标注界面的所有组件（初始隐藏）
            # 这些组件会在登录成功后激活
            annotation_components = {}
            
            # 用户信息
            if temp_manager.ui_config.get('show_user_info'):
                annotation_components['user_info'] = gr.HTML(value="")
            
            annotation_components['current_index'] = gr.State(value=0)
            annotation_components['nav_direction'] = gr.State(value="next")
            
            # Model ID 和状态框
            with gr.Row(equal_height=True, elem_id="search_row"):
                annotation_components['model_id_display'] = gr.Textbox(label="Model ID", interactive=False, scale=3)
                if temp_manager.ui_config.get('show_status'):
                    annotation_components['status_box'] = gr.HTML(value="")
            
            # GIF 和属性字段
            with gr.Row(elem_id="main_content_row"):
                with gr.Column(scale=1, elem_id="gif_container"):
                    annotation_components['gif_display'] = gr.Image(label="物体可视化", type="filepath", height=580, container=True, show_download_button=False)
                
                with gr.Column(scale=1, elem_id="info_column"):
                    field_components = []
                    checkbox_components = []
                    
                    for field in temp_manager.field_configs:
                        with gr.Column():
                            if field.get('has_checkbox') and temp_manager.ui_config.get('enable_checkboxes'):
                                chk = gr.Checkbox(
                                    label=f"{temp_manager.ui_config.get('checkbox_label', '✗')} {field['label']}", 
                                    value=False, container=False
                                )
                                checkbox_components.append(chk)
                            
                            comp = gr.Textbox(
                                label="",
                                lines=field.get('lines', 1),
                                placeholder=field.get('placeholder', ''),
                                show_label=False
                            )
                            field_components.append(comp)
                    
                    annotation_components['field_components'] = field_components
                    annotation_components['checkbox_components'] = checkbox_components
            
            # 按钮和进度
            with gr.Row():
                annotation_components['prev_btn'] = gr.Button("⬅️ 上一个", size="lg")
                annotation_components['save_btn'] = gr.Button("💾 保存", variant="primary", size="lg")
                annotation_components['next_btn'] = gr.Button("➡️ 下一个", size="lg")
            
            annotation_components['progress'] = gr.Textbox(label="进度", interactive=False)
            
            # 导出按钮
            if not debug and temp_manager.data_source == 'database':
                with gr.Row():
                    annotation_components['export_btn'] = gr.Button("📤 导出为JSONL", variant="secondary", size="lg")
                    annotation_components['export_status'] = gr.Textbox(label="导出状态", interactive=False, visible=False)
            
            # 确认弹窗
            with gr.Column(visible=False, elem_id="confirm_modal") as confirm_modal:
                with gr.Column(elem_id="confirm_card"):
                    gr.HTML("<h2>⚠️ 有未保存的修改</h2><p>是否继续？</p>")
                    with gr.Row():
                        annotation_components['save_and_continue'] = gr.Button("💾 保存并继续", variant="primary", size="sm")
                        annotation_components['cancel_nav'] = gr.Button("❌ 取消", variant="secondary", size="sm")
                    annotation_components['skip_changes'] = gr.Button("⚠️ 放弃更改", variant="stop", size="sm")
                    annotation_components['confirm_modal'] = confirm_modal
        
        # 登录逻辑
        def do_login(username, password):
            if not username or not password:
                return (
                    gr.update(value="请输入用户名和密码", visible=True),
                    None,
                    None,
                    gr.update(visible=True),  # 保持登录面板可见
                    gr.update(visible=False)  # 保持标注面板隐藏
                ) + tuple([gr.update()] * 20)  # 空更新
            
            result = auth_handler.login(username, password)
            if result["success"]:
                # 登录成功：创建标注界面管理器并初始化界面
                username_value = result["user"]["username"]
                manager = TaskManager(task_config, username_value, debug=debug)
                
                # 初始化标注界面数据
                init_data = load_annotation_data(manager, 0)
                
                # 隐藏登录面板，显示标注面板，并加载初始数据
                return (
                    gr.update(visible=False),  # 隐藏登录状态
                    username_value,  # 保存用户名
                    manager,  # 保存manager
                    gr.update(visible=False),  # 隐藏登录面板
                    gr.update(visible=True)    # 显示标注面板
                ) + tuple(init_data)  # 加载初始数据
            else:
                return (
                    gr.update(value=result["message"], visible=True),
                    None,
                    None,
                    gr.update(visible=True),  # 保持登录面板可见
                    gr.update(visible=False)  # 保持标注面板隐藏
                ) + tuple([gr.update()] * 20)  # 空更新
        
        # 标注界面数据加载函数（复用 TaskManager 的逻辑）
        def load_annotation_data(manager, index):
            """加载标注界面数据"""
            if not manager or not manager.visible_keys or index >= len(manager.visible_keys):
                # 返回空数据
                field_count = len(manager.field_configs) if manager else len(temp_manager.field_configs)
                checkbox_count = sum(1 for f in (manager.field_configs if manager else temp_manager.field_configs) if f.get('has_checkbox'))
                status_count = 1 if (manager.ui_config if manager else temp_manager.ui_config).get('show_status') else 0
                total = 2 + field_count + checkbox_count + status_count + 1  # gif + model_id + fields + checkboxes + status + progress
                return [gr.update()] * total
            
            model_id = manager.visible_keys[index]
            item = manager.all_data[model_id]
            attrs = manager.data_handler.parse_item(item)
            
            # 【关键改动】浏览即占有：如果数据未分配，立即分配给当前用户
            current_uid = attrs.get('uid', '')
            if not current_uid or current_uid == '':
                # 数据未分配，立即占有（只设置uid，不触碰其他数据）
                manager.data_handler.assign_to_user(model_id, manager.user_uid)
                print(f"🔒 占有数据: {model_id} -> {manager.user_uid}")
                # 刷新缓存
                manager.all_data = manager.data_handler.load_data()
                # 重新计算可见数据（排除其他用户已占有的数据）
                manager.visible_keys = []
                for key, value in manager.all_data.items():
                    item_attrs = manager.data_handler.parse_item(value)
                    item_uid = item_attrs.get('uid', '')
                    if not item_uid or item_uid == manager.user_uid:
                        manager.visible_keys.append(key)
                # 重新获取属性（现在包含了uid）
                item = manager.all_data[model_id]
                attrs = manager.data_handler.parse_item(item)
            
            gif_path = attrs.get('image_url', None)
            if gif_path and not os.path.exists(gif_path):
                gif_path = None
            
            field_values = []
            checkbox_values = []
            for field in manager.field_configs:
                value = attrs.get(field['key'], '')
                field_values.append(manager.field_processor.process_load(field, value))
                
                if field.get('has_checkbox'):
                    checkbox_values.append(attrs.get(f"chk_{field['key']}", False))
            
            prog = f"{index + 1} / {len(manager.visible_keys)}"
            
            result = [gr.update(value=v) for v in [gif_path, model_id] + field_values + checkbox_values]
            
            if manager.ui_config.get('show_status'):
                status_html = manager._render_status(attrs.get('annotated', False))
                result.append(gr.update(value=status_html))
            
            result.append(gr.update(value=prog))
            
            return result
        
        # 标注界面的事件处理函数（需要manager状态）
        def _resolve_model_for_annotation(manager, index, model_id):
            """解析当前模型（用于标注界面）"""
            if not manager or not manager.visible_keys:
                return 0, None
            resolved_model = None
            resolved_index = index
            if model_id and model_id in manager.visible_keys:
                resolved_model = model_id
                resolved_index = manager.visible_keys.index(model_id)
            elif 0 <= index < len(manager.visible_keys):
                resolved_model = manager.visible_keys[index]
            return resolved_index, resolved_model
        
        def save_annotation_data(manager, index, model_id, *values):
            """保存标注数据"""
            if not manager:
                return tuple([gr.update()] * 20)
            
            resolved_index, resolved_model = _resolve_model_for_annotation(manager, index, model_id)
            if resolved_model is None:
                return tuple(load_annotation_data(manager, resolved_index))
            
            num_fields = len(manager.field_configs)
            field_values = values[:num_fields]
            checkbox_values = values[num_fields:]
            
            save_dict = {}
            checkbox_idx = 0
            has_error = False
            
            for idx, field in enumerate(manager.field_configs):
                key = field['key']
                save_dict[key] = manager.field_processor.process_save(field, field_values[idx])
                if field.get('has_checkbox'):
                    chk_value = checkbox_values[checkbox_idx]
                    save_dict[f"chk_{key}"] = chk_value
                    if chk_value:
                        has_error = True
                    checkbox_idx += 1
            
            score = 0 if has_error else 1
            manager.data_handler.save_item(resolved_model, save_dict, score=score, uid=manager.user_uid)
            print(f"✅ 保存: {resolved_model}, score={score}, uid={manager.user_uid}")
            
            manager.all_data = manager.data_handler.load_data()
            return tuple(load_annotation_data(manager, resolved_index))
        
        def check_modified_annotation(manager, index, model_id, *values):
            """检查标注数据是否修改"""
            if not manager or not manager.visible_keys:
                return False
            
            resolved_index, resolved_model = _resolve_model_for_annotation(manager, index, model_id)
            if resolved_model is None:
                return False
            
            item = manager.all_data.get(resolved_model)
            if item is None:
                return False
            
            attrs = manager.data_handler.parse_item(item)
            num_fields = len(manager.field_configs)
            field_values = values[:num_fields]
            checkbox_values = values[num_fields:]
            
            original_values = []
            for field in manager.field_configs:
                value = attrs.get(field['key'], '')
                original_values.append(manager.field_processor.process_load(field, value))
            
            for idx in range(num_fields):
                orig = original_values[idx] if original_values[idx] is not None else ''
                curr = field_values[idx] if field_values[idx] is not None else ''
                if str(orig) != str(curr):
                    return True
            
            checkbox_idx = 0
            for field in manager.field_configs:
                if field.get('has_checkbox'):
                    original_chk = attrs.get(f"chk_{field['key']}", False)
                    current_chk = checkbox_values[checkbox_idx]
                    if original_chk != current_chk:
                        return True
                    checkbox_idx += 1
            
            return False
        
        def navigate_annotation_with_check(manager, index, model_id, direction, *values):
            """标注界面导航（带修改检测）"""
            if not manager:
                return tuple([gr.update()] * 20)
            
            resolved_index, resolved_model = _resolve_model_for_annotation(manager, index, model_id)
            modified = check_modified_annotation(manager, resolved_index, resolved_model, *values)
            
            if modified:
                # 有修改，显示弹窗
                return (
                    gr.update(value=resolved_index),
                    gr.update(visible=True),
                    gr.update(value=direction)
                ) + tuple([gr.update()] * 17)
            else:
                # 无修改，直接跳转
                if direction == "next":
                    new_index = min(len(manager.visible_keys) - 1, resolved_index + 1)
                else:
                    new_index = max(0, resolved_index - 1)
                
                return (
                    gr.update(value=new_index),
                    gr.update(visible=False),
                    gr.update()
                ) + tuple(load_annotation_data(manager, new_index))
        
        def save_and_nav_annotation(manager, index, model_id, direction, *values):
            """保存并继续"""
            if not manager:
                return tuple([gr.update()] * 20)
            
            # 先保存
            save_result = save_annotation_data(manager, index, model_id, *values)
            
            # 再跳转
            resolved_index, _ = _resolve_model_for_annotation(manager, index, model_id)
            if direction == "next":
                new_index = min(len(manager.visible_keys) - 1, resolved_index + 1)
            else:
                new_index = max(0, resolved_index - 1)
            
            return (
                gr.update(value=new_index),
                gr.update(visible=False)
            ) + tuple(load_annotation_data(manager, new_index))
        
        def skip_and_nav_annotation(manager, index, model_id, direction):
            """放弃更改并继续"""
            if not manager:
                return tuple([gr.update()] * 20)
            
            resolved_index, _ = _resolve_model_for_annotation(manager, index, model_id)
            if direction == "next":
                new_index = min(len(manager.visible_keys) - 1, resolved_index + 1)
            else:
                new_index = max(0, resolved_index - 1)
            
            return (
                gr.update(value=new_index),
                gr.update(visible=False)
            ) + tuple(load_annotation_data(manager, new_index))
        
        # 计算输出组件列表
        status_outputs = [annotation_components['status_box']] if 'status_box' in annotation_components else []
        annotation_outputs = [
            annotation_components['gif_display'],
            annotation_components['model_id_display'],
        ] + annotation_components['field_components'] + annotation_components['checkbox_components'] + status_outputs + [annotation_components['progress']]
        
        # 事件绑定 - 登录
        login_btn.click(
            do_login,
            inputs=[login_username, login_password],
            outputs=[
                login_status, 
                logged_in_user, 
                current_manager_state,
                login_panel, 
                annotation_panel,
            ] + annotation_outputs
        )
        
        # 事件绑定 - 标注界面（使用lambda包装以传递manager）
        annotation_components['save_btn'].click(
            lambda mgr, idx, mid, *vals: save_annotation_data(mgr, idx, mid, *vals),
            inputs=[current_manager_state, annotation_components['current_index'], annotation_components['model_id_display']] + 
                   annotation_components['field_components'] + annotation_components['checkbox_components'],
            outputs=annotation_outputs
        )
        
        annotation_components['prev_btn'].click(
            lambda mgr, idx, mid, dir, *vals: navigate_annotation_with_check(mgr, idx, mid, dir, *vals),
            inputs=[current_manager_state, annotation_components['current_index'], annotation_components['model_id_display'], 
                   gr.State("prev")] + annotation_components['field_components'] + annotation_components['checkbox_components'],
            outputs=[annotation_components['current_index'], annotation_components['confirm_modal'], annotation_components['nav_direction']] + annotation_outputs
        )
        
        annotation_components['next_btn'].click(
            lambda mgr, idx, mid, dir, *vals: navigate_annotation_with_check(mgr, idx, mid, dir, *vals),
            inputs=[current_manager_state, annotation_components['current_index'], annotation_components['model_id_display'], 
                   gr.State("next")] + annotation_components['field_components'] + annotation_components['checkbox_components'],
            outputs=[annotation_components['current_index'], annotation_components['confirm_modal'], annotation_components['nav_direction']] + annotation_outputs
        )
        
        annotation_components['save_and_continue'].click(
            lambda mgr, idx, mid, dir, *vals: save_and_nav_annotation(mgr, idx, mid, dir, *vals),
            inputs=[current_manager_state, annotation_components['current_index'], annotation_components['model_id_display'], 
                   annotation_components['nav_direction']] + annotation_components['field_components'] + annotation_components['checkbox_components'],
            outputs=[annotation_components['current_index'], annotation_components['confirm_modal']] + annotation_outputs
        )
        
        annotation_components['skip_changes'].click(
            lambda mgr, idx, mid, dir: skip_and_nav_annotation(mgr, idx, mid, dir),
            inputs=[current_manager_state, annotation_components['current_index'], annotation_components['model_id_display'], annotation_components['nav_direction']],
            outputs=[annotation_components['current_index'], annotation_components['confirm_modal']] + annotation_outputs
        )
        
        annotation_components['cancel_nav'].click(
            lambda: gr.update(visible=False),
            outputs=[annotation_components['confirm_modal']]
        )
        
        # 导出按钮事件
        if 'export_btn' in annotation_components:
            def export_annotation_data(manager):
                """导出标注数据"""
                if not manager or not hasattr(manager.data_handler, 'export_to_jsonl'):
                    return gr.update(value="❌ 导出功能不可用", visible=True)
                try:
                    filepath = manager.data_handler.export_to_jsonl()
                    filename = os.path.basename(filepath)
                    return gr.update(value=f"✅ 导出成功: {filename}", visible=True)
                except Exception as e:
                    return gr.update(value=f"❌ 导出失败: {str(e)}", visible=True)
            
            annotation_components['export_btn'].click(
                lambda mgr: export_annotation_data(mgr),
                inputs=[current_manager_state],
                outputs=[annotation_components['export_status']]
            )
        
        # 初始化标注界面（登录成功后自动加载第一项）
        def init_annotation_on_login(manager):
            """登录成功后初始化标注界面"""
            if manager:
                return tuple(load_annotation_data(manager, 0))
            return tuple([gr.update()] * len(annotation_outputs))
        
        # 当manager状态改变时，初始化标注界面
        current_manager_state.change(
            init_annotation_on_login,
            inputs=[current_manager_state],
            outputs=annotation_outputs
        )
    
    return unified_demo


def main():
    parser = argparse.ArgumentParser(description='标注工具 - 支持多任务')
    parser.add_argument('--port', type=int, default=None, help='端口（不指定则使用任务默认端口）')
    parser.add_argument('--task', type=str, default=None, help='任务名称（如: annotation, review）')
    parser.add_argument('-d', '--debug', action='store_true', help='Debug模式：使用test.jsonl文件')
    parser.add_argument('--dev', action='store_true', help='开发模式：跳过登录，直接使用指定用户')
    parser.add_argument('--uid', type=str, default='dev_user', help='开发模式下的用户ID（仅在--dev模式下使用）')
    parser.add_argument('--list-tasks', action='store_true', help='列出所有可用任务')
    
    args = parser.parse_args()
    
    # 列出所有任务
    if args.list_tasks:
        print("\n📋 可用任务列表:")
        print("=" * 60)
        for idx, route in enumerate(ROUTES, 1):
            print(f"{idx}. {route['task']}")
            print(f"   描述: {route['description']}")
            print(f"   端口: {route['port']}")
            print(f"   数据库: databases/{route['task']}.db")
            print(f"   配置: ui_configs/{route['task']}_config.py")
            print()
        print("使用方式: python src/main_multi.py --task <任务名>")
        print("=" * 60)
        return
    
    # 选择任务
    if args.task:
        # 根据任务名查找配置
        task_config = None
        for route in ROUTES:
            if route['task'] == args.task:
                task_config = route
                break
        
        if not task_config:
            print(f"❌ 错误: 未找到任务 '{args.task}'")
            print(f"\n可用任务: {', '.join([r['task'] for r in ROUTES])}")
            print(f"使用 --list-tasks 查看详细信息")
            return
    else:
        # 默认使用第一个任务
        task_config = ROUTES[0]
        print(f"💡 未指定任务，使用默认任务: {task_config['task']}")
    
    # 端口选择（命令行 > 任务配置 > 默认）
    if args.port is None:
        args.port = task_config.get('port', DEFAULT_PORT)
    
    # 判断是否需要登录
    if args.dev:
        # 开发模式：跳过登录，直接使用指定用户
        user_uid = args.uid
        print(f"\n{'='*60}")
        print(f"⚡ 开发模式（跳过登录）")
        print(f"{'='*60}")
        print(f"🚀 {task_config['description']}")
        print(f"用户: {user_uid}")
        print(f"端口: {args.port}")
        print(f"模式: {'🐛 Debug' if args.debug else '🗄️  正常'}")
        print(f"{'='*60}\n")
        
        # 直接创建标注界面
        manager = TaskManager(task_config, user_uid, debug=args.debug)
        demo = manager.build_interface()
        allowed_paths = manager.get_allowed_paths()
        demo.launch(server_port=args.port, server_name="0.0.0.0", allowed_paths=allowed_paths)
    else:
        # 生产模式：需要登录
        from src.auth_handler import AuthHandler
        auth_handler = AuthHandler()
        
        print(f"\n{'='*60}")
        print(f"🔐 物体属性标注工具")
        print(f"{'='*60}")
        print(f"端口: {args.port}")
        print(f"模式: {'🐛 Debug' if args.debug else '🗄️  正常'}")
        print(f"使用 --dev 参数可跳过登录（开发模式）")
        print(f"{'='*60}\n")
        
        # 创建登录界面
        demo = create_login_interface(auth_handler, task_config, args.debug)
        
        # 获取允许访问的路径（用于图片加载）
        temp_manager = TaskManager(task_config, "temp_user", debug=args.debug)
        allowed_paths = temp_manager.get_allowed_paths()
        
        demo.launch(server_port=args.port, server_name="0.0.0.0", allowed_paths=allowed_paths)


if __name__ == "__main__":
    main()

