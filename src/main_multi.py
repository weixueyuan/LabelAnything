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
from src.component_factory import ComponentFactory
from src.routes import ROUTES, DEFAULT_PORT


class TaskManager:
    """任务管理器"""
    
    def __init__(self, task_config, user_uid="default_user", debug=False, export_dir="exports", default_allowed_path="/mnt"):
        self.task_config = task_config
        # 保留user_uid作为初始值，但在函数中使用传入的user_uid
        self.user_uid = user_uid
        self.task_name = task_config['task']
        self.debug = debug
        self.export_dir = export_dir  # 添加导出目录配置，解决硬编码问题
        self.default_allowed_path = default_allowed_path  # 添加默认允许路径，解决硬编码问题
        
        # 加载UI配置（新架构）
        config_module = importlib.import_module(f"src.ui_configs.{self.task_name}_config")
        
        self.components_config = config_module.COMPONENTS
        self.layout_config = config_module.LAYOUT_CONFIG
        self.ui_config = config_module.UI_CONFIG
        self.task_info = config_module.TASK_INFO
        self.custom_css = getattr(config_module, 'CUSTOM_CSS', '')
        
        # 从COMPONENTS中提取字段配置（用于数据处理）
        # 新规则：任何定义了 'data_field' 的组件都将被视为一个需要与数据库交互的字段。
        # 'data_field' 的值就是它在数据库 'data' JSON对象中的key。
        self.field_configs = [
            {
                'key': comp.get('data_field', comp['id']), # 优先使用 data_field, 否则用 id
                'id': comp['id'], # 组件自身的ID
                'label': comp.get('label', comp['id']),
                'type': comp['type'],
                'lines': comp.get('lines', 1),
                'has_checkbox': comp.get('has_checkbox', False),
                'interactive': comp.get('interactive', True),
                'placeholder': comp.get('placeholder', ''),
                'process': comp.get('process'),
                'data_field': comp.get('data_field', comp['id']) # 显式存储
            }
            for comp in self.components_config
            if comp.get('data_field') is not None and comp.get('type') not in ['button', 'slider']
        ]
        
        # 数据库路径
        self.db_path = f"databases/{self.task_name}.db"
        
        # 初始化
        self.field_processor = FieldProcessor()
        self._load_data()
        
        # 组件引用
        self.components = {}
        self.factory = None
    
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
                print(f"   请先导入数据: python -m importers.generic_importer")
                self.data_handler = None
                self.all_data = {}
                self.visible_keys = []
                return
        
        # 加载所有数据
        self.all_data = self.data_handler.load_data()
        
        # 过滤可见数据
        self._refresh_visible_keys(self.user_uid)
        
        print(f"✓ 加载完成")
        print(f"  总数: {len(self.all_data)}, 可见: {len(self.visible_keys)}")
    
    def _refresh_visible_keys(self, user_uid):
        """重新计算用户可见的数据键列表"""
        visible_keys = []
        for key, value in self.all_data.items():
            attrs = self.data_handler.parse_item(value)
            item_uid = attrs.get('uid', '')
            if not item_uid or item_uid == user_uid:
                visible_keys.append(key)
        
        # 更新实例变量
        self.visible_keys = visible_keys
        return visible_keys
    
    def build_interface(self, demo, user_state):
        """
        在给定的Gradio Blocks实例中构建界面。
        这个方法不应该创建自己的Blocks实例。
        """
        # 创建组件工厂
        self.factory = ComponentFactory()
        
        gr.Markdown(f"# {self.ui_config['title']}")
        
        # 用户信息
        if self.ui_config.get('show_user_info'):
            other_count = len(self.all_data) - len(self.visible_keys)
            self.components['user_info'] = gr.HTML(self._render_user_info(len(self.visible_keys), other_count, self.user_uid))
        
        # State组件
        self.components['current_index'] = gr.State(value=0)
        self.components['nav_direction'] = gr.State(value="next")
        
        # 检查是否存在滑块组件
        self.has_slider = False
        self.slider_target_fields = []  # 存储所有滑块的目标字段
        
        # 动态查找所有滑块组件及其目标字段
        for comp_config in self.components_config:
            if comp_config.get('type') == 'slider':
                self.has_slider = True
                target_field = comp_config.get('target_field')
                if target_field:
                    self.slider_target_fields.append(target_field)
                    print(f"✓ 找到滑块组件，目标字段: {target_field}")
                else:
                    print(f"⚠️ 找到滑块组件，但未指定目标字段")
        
        # 打印调试信息
        print(f"滑块状态: has_slider={self.has_slider}, target_fields={self.slider_target_fields}")
        
        # 只有在存在滑块组件时才创建original_dimensions组件
        if self.has_slider:
            print(f"✓ 创建滑块相关状态组件: original_dimensions")
            self.components['original_dimensions'] = gr.State(value="")  # 存储原始值
        else:
            print(f"ℹ️ 当前任务不需要滑块组件，跳过创建相关组件")
        
        # 使用布局配置构建界面（同时创建和渲染组件）
        self.factory.build_layout(self.components_config, self.layout_config)
        
        # 获取创建的组件
        self.components.update(self.factory.get_all_components())
        
        # 导出按钮（仅在正常模式下显示）
        if not self.debug and self.data_source == 'database':
            with gr.Row():
                self.components['export_btn'] = gr.Button("📤 导出为JSONL", variant="secondary", size="lg")
                self.components['export_status'] = gr.Textbox(label="导出状态", interactive=False, visible=False)
        
        # 确认弹窗
        with gr.Column(visible=False, elem_id="confirm_modal") as confirm_modal:
            with gr.Column(elem_id="confirm_card"):
                gr.HTML("<h2>⚠️ 有未保存的修改</h2><p>是否继续？</p>")
                with gr.Row():
                    self.components['save_and_continue'] = gr.Button("💾 保存并继续", variant="primary", size="sm")
                    self.components['cancel_nav'] = gr.Button("❌ 取消", variant="secondary", size="sm")
                self.components['skip_changes'] = gr.Button("⚠️ 放弃更改", variant="stop", size="sm")
        
        self.components['confirm_modal'] = confirm_modal
        
        # 在Blocks上下文中绑定事件
        self._bind_events(demo, user_state)
    
    def _bind_events(self, demo, user_state):
        """
        绑定所有事件处理函数（重构版）
        核心原则：所有输入输出列表都由配置动态生成，确保顺序和内容的一致性。
        """
        # 1. 定义核心组件
        # 这些是所有事件处理中都可能用到的基本组件
        core_inputs = {
            'user_state': user_state,
            'current_index': self.components['current_index'],
            'model_id': self.components.get('model_id'),
            'nav_direction': self.components['nav_direction']
        }

        # 2. 构建动态的字段输入/输出列表
        # 这个列表的顺序是所有操作（加载、保存、检查）的唯一真实来源
        self.interactive_components = []  # 用于UI交互的组件列表
        self.field_component_map = {}     # 字段key -> 组件 的映射
        
        # 按照 field_configs 的顺序构建
        for field in self.field_configs:
            comp_id = field['id']
            comp = self.components.get(comp_id)
            if not comp:
                print(f"⚠️ 警告: 在 self.components 中未找到ID为 '{comp_id}' 的组件")
                continue

            self.field_component_map[field['key']] = comp
            if field.get('has_checkbox'):
                checkbox = self.factory.get_checkbox(comp_id)
                if checkbox:
                    self.interactive_components.append(checkbox)
            self.interactive_components.append(comp)

        # 3. 构建 `load_data` 的输出列表 (`load_outputs`)
        # 这个列表的顺序必须与 `load_data` 函数返回值的顺序严格一致
        self.load_outputs = []
        # 按照 components_config 的顺序构建，以匹配UI布局
        for comp_config in self.components_config:
            comp_id = comp_config['id']
            comp = self.components.get(comp_id)
            if comp_config['type'] == 'button': continue
            if not comp: continue

            # 如果是带复选框的字段，先加复选框
            if comp_config.get('has_checkbox'):
                checkbox = self.factory.get_checkbox(comp_id)
                if checkbox:
                    self.load_outputs.append(checkbox)
            self.load_outputs.append(comp)
        
        # 添加滑块的状态组件（如果存在）
        if self.has_slider:
            self.load_outputs.append(self.components['original_dimensions'])

        # 4. 构建事件的输入列表
        # 用于保存和导航检查的输入列表
        event_inputs = [
            core_inputs['user_state'],
            core_inputs['current_index'],
            core_inputs['model_id']
        ] + self.interactive_components

        # 5. 绑定事件
        # 页面加载
        demo.load(fn=self.load_data,
                  inputs=[core_inputs['current_index'], core_inputs['user_state']],
                  outputs=self.load_outputs)

        # 搜索
        if core_inputs['model_id']:
            search_outputs = [core_inputs['current_index']] + self.load_outputs
            core_inputs['model_id'].submit(
                fn=self.search_and_load,
                inputs=[core_inputs['user_state'], core_inputs['model_id']],
                outputs=search_outputs
            )

        # 保存
        save_btn = self.components.get('save_btn')
        if save_btn:
            save_btn.click(fn=self.save_data, inputs=event_inputs, outputs=self.load_outputs)

        # 导航
        prev_btn = self.components.get('prev_btn')
        next_btn = self.components.get('next_btn')
        nav_outputs = [core_inputs['current_index']] + self.load_outputs + \
                      [self.components['confirm_modal'], core_inputs['nav_direction']]
        if prev_btn:
            prev_btn.click(fn=self.check_and_nav_prev, inputs=event_inputs, outputs=nav_outputs)
        if next_btn:
            next_btn.click(fn=self.check_and_nav_next, inputs=event_inputs, outputs=nav_outputs)

        # 弹窗操作
        save_and_continue_inputs = [core_inputs['nav_direction']] + event_inputs
        save_and_continue_outputs = [core_inputs['current_index']] + self.load_outputs + [self.components['confirm_modal']]
        self.components['save_and_continue'].click(
            fn=self.save_and_continue_nav,
            inputs=save_and_continue_inputs,
            outputs=save_and_continue_outputs
        )
        
        skip_and_continue_inputs = [
            core_inputs['user_state'],
            core_inputs['current_index'],
            core_inputs['model_id'],
            core_inputs['nav_direction']
        ]
        skip_and_continue_outputs = [core_inputs['current_index']] + self.load_outputs + [self.components['confirm_modal']]
        self.components['skip_changes'].click(
            fn=self.skip_and_continue_nav,
            inputs=skip_and_continue_inputs,
            outputs=skip_and_continue_outputs
        )
        
        self.components['cancel_nav'].click(
            fn=lambda: gr.update(visible=False),
            outputs=[self.components['confirm_modal']]
        )

        # 导出
        if 'export_btn' in self.components:
            self.components['export_btn'].click(
                fn=self.export_to_jsonl,
                outputs=[self.components['export_status']]
            )
        
        # 滑块
        scale_slider = self.components.get('scale_slider')
        if scale_slider and self.slider_target_fields:
            for target_key in self.slider_target_fields:
                target_comp = self.field_component_map.get(target_key)
                if target_comp:
                    scale_slider.change(
                        fn=self.scale_dimensions,
                        inputs=[self.components['original_dimensions'], scale_slider],
                        outputs=[target_comp]
                    )
    
    def load_data(self, index, user_uid):
        """根据组件配置动态加载数据 (重构版)"""
        print(f"\n加载数据: index={index}, user_uid={user_uid}")
        self._refresh_visible_keys(user_uid)

        # 确定要加载的数据属性
        is_valid_item = self.visible_keys and 0 <= index < len(self.visible_keys)
        attrs = {}
        model_id = ""
        if is_valid_item:
            model_id = self.visible_keys[index]
            item = self.all_data.get(model_id)
            if item:
                attrs = self.data_handler.parse_item(item)
                # 浏览即占有
                if not attrs.get('uid'):
                    if hasattr(self.data_handler, "assign_to_user"):
                        self.data_handler.assign_to_user(model_id, user_uid)
                        # 简单刷新
                        self.all_data = self.data_handler.load_data()
                        self._refresh_visible_keys(user_uid)
                        item = self.all_data.get(model_id)
                        attrs = self.data_handler.parse_item(item) if item else {}

        # 根据 self.load_outputs 动态构建返回值
        result = []
        original_dims_value = ""
        for comp in self.load_outputs:
            comp_id = comp.elem_id
            
            # 在 components_config 中查找该组件的配置
            comp_config = next((c for c in self.components_config if c['id'] == comp_id), None)
            if not comp_config:
                # 处理特殊组件，如 original_dimensions state
                if comp_id == 'original_dimensions':
                    result.append(original_dims_value)
                else:
                    result.append(None) # 或者 gr.update()
                continue

            data_field = comp_config.get('data_field', comp_id)
            comp_type = comp_config['type']

            # 检查是否是复选框组件
            is_checkbox = comp_id.startswith('chk_')

            if is_checkbox:
                # 从 'chk_field_name' 中提取 'field_name'
                field_key = comp_id.replace('chk_', '', 1)
                result.append(attrs.get(f"chk_{field_key}", False))
            elif data_field == 'model_id':
                result.append(model_id)
            elif data_field == '_computed_status':
                result.append(self._render_status(attrs.get('annotated', False)))
            elif comp_id == 'progress_box':
                prog = f"{index + 1} / {len(self.visible_keys)}" if is_valid_item else "0 / 0"
                result.append(prog)
            elif comp_id == 'scale_slider':
                result.append(1.0)
            elif comp_type == 'image':
                img_path = attrs.get(data_field)
                result.append(img_path if img_path and os.path.exists(img_path) else None)
            elif comp_type == 'multiselect':
                value = attrs.get(data_field, [])
                # 确保 value 是列表格式
                if not isinstance(value, list):
                    value = [value] if value else []
                
                # 获取选项列表
                choices = attrs.get(f"{data_field}_choice", [])
                
                # 更新组件的值和选项
                result.append(gr.update(value=value, choices=choices))
            else: # Textbox, etc.
                value = attrs.get(data_field, '')
                processed_value = self.field_processor.process_load(comp_config, value)
                result.append(processed_value)
                if self.has_slider and data_field in self.slider_target_fields:
                    original_dims_value = value

        return result
    
    def scale_dimensions(self, original_dims, scale_value):
        """
        根据滑块值计算缩放后的值
        
        Args:
            original_dims: 原始值字符串，格式如 "0.78*0.41*0.54" 或其他格式
            scale_value: 缩放比例，浮点数
            
        Returns:
            缩放后的字符串
        """
        if not original_dims or not original_dims.strip():
            return ""
        try:
            parts = original_dims.replace('*', ' ').split()
            numbers = [float(p.strip()) for p in parts if p.strip()]
            if not numbers:
                return original_dims
            scaled_numbers = [n * scale_value for n in numbers]
            result = ' * '.join([f"{n:.2f}" if n >= 0.01 else f"{n:.4f}" for n in scaled_numbers])
            return result
        except Exception as e:
            print(f"⚠️  尺度计算错误: {e}")
            return original_dims
    
    def _resolve_model(self, index, model_id):
        """根据索引和model_id解析当前记录"""
        resolved_model = None
        resolved_index = index
        if model_id and model_id in self.visible_keys:
            resolved_model = model_id
            resolved_index = self.visible_keys.index(model_id)
        elif 0 <= index < len(self.visible_keys):
            resolved_model = self.visible_keys[index]
        return resolved_index, resolved_model
    
    def save_data(self, user_uid, index, model_id, *values):
        """保存数据 (重构版)"""
        resolved_index, resolved_model = self._resolve_model(index, model_id)
        if resolved_model is None:
            return self.load_data(resolved_index, user_uid)

        # 安全地解析 *values
        value_map = {}
        value_idx = 0
        for comp in self.interactive_components:
            if value_idx < len(values):
                value_map[comp.elem_id] = values[value_idx]
            else:
                value_map[comp.elem_id] = None # 预防性代码
            value_idx += 1

        attributes = {}
        has_error = False

        # 根据 field_configs 构建要保存的属性
        for field in self.field_configs:
            field_id = field['id']
            field_key = field['key']
            
            # 获取字段值
            field_value = value_map.get(field_id)
            
            # 对于 multiselect 类型的字段，确保值是列表格式
            if field.get('type') == 'multiselect' and not isinstance(field_value, list):
                field_value = [field_value] if field_value else []
            
            attributes[field_key] = self.field_processor.process_save(field, field_value)
            print(f"保存字段: {field_key} = {attributes[field_key]}")

            # 获取对应的复选框值
            if field.get('has_checkbox'):
                chk_id = f"{field_id}_checkbox"  # 直接构造checkbox的ID
                chk_value = value_map.get(chk_id, False)
                attributes[f"chk_{field_key}"] = chk_value
                if chk_value:
                    has_error = True
        
        score = 0 if has_error else 1
        
        # 直接使用data_handler保存（不使用缓存）
        result = self.data_handler.save_item(
            resolved_model,
            attributes,
            score=score,
            uid=user_uid
        )
        
        # 检查保存结果
        if isinstance(result, dict) and not result.get("success", True):
            # 保存失败，提供详细错误信息
            error_type = result.get("error", "UNKNOWN_ERROR")
            error_msg = result.get("message", "未知错误")
            print(f"❌ 保存失败 ({error_type}): {error_msg}")
            
            # 构建错误状态HTML
            error_status_html = f'''<div style="
                background-color: #f8d7da;
                border: 2px solid #f5c6cb;
                padding: 8px;
                font-size: 14px;
                text-align: center;
                font-weight: 600;
                border-radius: 6px;
                color: #721c24;
            ">❌ 保存失败: {error_msg}</div>'''
            
            # 返回当前数据并显示错误信息
            result = self.load_data(resolved_index, user_uid)
            # 如果状态框在加载的组件中，则替换状态框内容
            for i, comp in enumerate(self.load_outputs):
                comp_id = comp.elem_id if hasattr(comp, 'elem_id') else None
                comp_config = next((c for c in self.components_config if c['id'] == comp_id), None)
                if comp_config and comp_config.get('data_field') == '_computed_status':
                    result[i] = error_status_html
            
            return result
        else:
            # 保存成功
            print(f"✅ 保存: {resolved_model}, score={score}, uid={user_uid}")
            
            # 重新加载数据（简单直接）
            self.all_data = self.data_handler.load_data()
            
            # 重新计算可见键
            visible_keys = self._refresh_visible_keys(user_uid)
            
            # 确保索引在有效范围内
            if resolved_model in visible_keys:
                new_index = visible_keys.index(resolved_model)
            else:
                new_index = min(resolved_index, len(visible_keys) - 1) if visible_keys else 0
            
            # 返回更新后的数据
            return self.load_data(new_index, user_uid)
    
    def search_and_load(self, user_uid, search_value):
        """
        搜索功能：根据输入的值查找对应的 model_id
        只有在按下回车键时才会执行搜索
        
        Args:
            user_uid: 用户ID
            search_value: model_id输入框的值
            
        Returns:
            更新后的所有组件值
        """
        if not search_value or not search_value.strip():
            # 空搜索，不做任何操作，保持当前数据
            return [self.components['current_index'].value] + self.load_data(self.components['current_index'].value, user_uid)
        
        search_value = search_value.strip()
        
        # 确保visible_keys是最新的
        visible_keys = self._refresh_visible_keys(user_uid)
        
        # 查找 model_id（在 visible_keys 中）
        if search_value in self.visible_keys:
            # 找到了，跳转到该索引
            new_index = self.visible_keys.index(search_value)
            print(f"🔍 搜索成功: {search_value} (索引 {new_index})")
            return [new_index] + self.load_data(new_index, user_uid)
        else:
            # 未找到，提示用户，保持当前数据
            print(f"⚠️  未找到: {search_value}")
            return [self.components['current_index'].value] + self.load_data(self.components['current_index'].value, user_uid)
    
    def has_real_changes(self, user_uid, index, model_id, *values):
        """检查当前字段值是否与数据库中的原始值不同 (重构版)"""
        if not self.visible_keys or index >= len(self.visible_keys):
            return False
        
        current_model_id = self._resolve_model(index, model_id)[1]
        if not current_model_id:
            return False

        item = self.data_handler.get_item(current_model_id)
        if not item:
            return False
        
        attrs = self.data_handler.parse_item(item)
        
        # 打印调试信息，帮助诊断问题
        print(f"比较数据 - ID: {current_model_id}, 用户: {user_uid}")
        
        # 安全地解析 *values
        value_map = {}
        value_idx = 0
        for comp in self.interactive_components:
            if value_idx < len(values):
                value_map[comp.elem_id] = values[value_idx]
            else:
                value_map[comp.elem_id] = None
            value_idx += 1

        # 迭代 self.field_configs 来进行比较
        for field in self.field_configs:
            field_id = field['id']
            field_key = field['key']
            field_type = field['type']

            # 忽略 model_id 字段的变化
            if field_key == 'model_id':
                continue
                
            # 忽略计算字段和只读字段的变化
            if field_key.startswith('_computed_') or field.get('interactive') is False:
                continue

            # 比较字段值
            original_value = attrs.get(field_key, '')
            # 使用 process_load 处理原始值，确保与UI显示格式一致
            processed_original_value = self.field_processor.process_load(field, original_value)
            if processed_original_value is None:
                processed_original_value = ""
                
            current_value = value_map.get(field_id)
            if current_value is None:
                current_value = ""
            
            # 更智能的字符串对比
            original_str = str(processed_original_value).strip()
            current_str = str(current_value).strip()
            
            # 对 dimension 类字段，进行更宽松的比较（忽略内部空格差异）
            # 同时也适用于其他用*分隔的字符串
            if '*' in original_str or '*' in current_str:
                if original_str.replace(' ', '') != current_str.replace(' ', ''):
                    print(f"字段 '{field_key}' 已修改: '{processed_original_value}' -> '{current_value}'")
                    return True
            # 对列表类型进行特殊处理
            elif isinstance(original_value, list) and field_type == 'multiselect':
                # 确保 current_value 是列表格式
                if not isinstance(current_value, list):
                    current_list = [current_value] if current_value else []
                else:
                    current_list = current_value
                    
                if set(original_value) != set(current_list):
                    print(f"字段 '{field_key}' 已修改 (列表): {original_value} -> {current_list}")
                    return True
            else:
                # 其他字段，正常比较
                if original_str != current_str:
                    print(f"字段 '{field_key}' 已修改: '{processed_original_value}' -> '{current_value}'")
                    return True

            # 比较复选框值
            if field.get('has_checkbox'):
                chk_key = f"chk_{field_key}"
                chk_id = f"{field_id}_checkbox"  # 直接构造checkbox的ID
                original_checkbox = attrs.get(chk_key, False)
                current_checkbox = value_map.get(chk_id, False)
                if original_checkbox != current_checkbox:
                    print(f"复选框 '{field_key}' 已修改: {original_checkbox} -> {current_checkbox}")
                    return True
        
        return False
    
    def check_and_nav_prev(self, user_uid, index, model_id, *values):
        """检查并导航到上一个"""
        return self._check_and_nav(user_uid, index, model_id, "prev", *values)
    
    def check_and_nav_next(self, user_uid, index, model_id, *values):
        """检查并导航到下一个"""
        return self._check_and_nav(user_uid, index, model_id, "next", *values)
    
    def _check_and_nav(self, user_uid, index, model_id, direction, *values):
        """导航检查：对比当前值与数据库值，如果有差异显示弹窗，否则直接跳转"""
        if self.has_real_changes(user_uid, index, model_id, *values):
            # 有修改，显示弹窗，记录方向
            # 返回与 nav_outputs 数量匹配的 gr.update()
            num_load_outputs = len(self.load_outputs)
            updates = [gr.update()] * (1 + num_load_outputs)  # current_index + load_outputs
            return updates + [gr.update(visible=True), gr.update(value=direction)]
        else:
            # 无修改，直接跳转并加载新数据
            # 确保使用最新的索引
            resolved_index, _ = self._resolve_model(index, model_id)
            new_index, _ = self._go_direction(resolved_index, model_id, direction)
            new_data = self.load_data(new_index, user_uid)
            return [new_index] + new_data + [gr.update(visible=False), gr.update()]
    
    def _go_direction(self, index, model_id, direction):
        """根据方向导航, 返回 (new_index, new_model_id)"""
        # 确保visible_keys是最新的
        self._refresh_visible_keys(self.user_uid)
        
        resolved_index, _ = self._resolve_model(index, model_id)
        
        # 检查visible_keys是否为空
        if not self.visible_keys:
            return 0, ""
            
        if direction == "prev":
            new_index = max(0, resolved_index - 1)
        else:
            new_index = min(len(self.visible_keys) - 1, resolved_index + 1)
        
        new_model_id = self.visible_keys[new_index] if new_index < len(self.visible_keys) else ""
        return new_index, new_model_id
    
    def save_and_continue_nav(self, direction, user_uid, index, model_id, *values):
        """保存并继续 (重构版)"""
        # 先保存
        save_result_payload = self.save_data(user_uid, index, model_id, *values)
        
        # 检查保存是否成功
        has_error = any(isinstance(item, str) and "❌ 保存失败" in item for item in save_result_payload if isinstance(item, str))
        
        if has_error:
            # 保存失败, 不导航, 保持弹窗可见, 并更新UI以显示错误信息
            resolved_index, _ = self._resolve_model(index, model_id)
            return [resolved_index] + save_result_payload + [gr.update(visible=True)]
        
        # 保存成功后，获取当前索引（可能已经在save_data中更新）
        current_index = self.components['current_index'].value
        
        # 执行导航并加载新数据
        new_index, _ = self._go_direction(current_index, model_id, direction)
        new_data = self.load_data(new_index, user_uid)
        return [new_index] + new_data + [gr.update(visible=False)]
    
    def skip_and_continue_nav(self, user_uid, index, model_id, direction):
        """放弃修改并继续"""
        # 确保使用最新的索引
        resolved_index, _ = self._resolve_model(index, model_id)
        
        # 执行导航并加载新数据
        new_index, _ = self._go_direction(resolved_index, model_id, direction)
        new_data = self.load_data(new_index, user_uid)
        return [new_index] + new_data + [gr.update(visible=False)]
    
    def export_to_jsonl(self):
        """导出数据为JSONL文件"""
        try:
            # 使用TaskManager中配置的导出目录
            filepath = self.data_handler.export_to_jsonl(output_dir=self.export_dir)
            filename = os.path.basename(filepath)
            return gr.update(value=f"✅ 导出成功: {filename}", visible=True)
        except PermissionError:
            error_msg = f"导出失败: 没有写入权限，请检查目录 '{self.export_dir}' 的访问权限"
            print(f"❌ {error_msg}")
            return gr.update(value=f"❌ {error_msg}", visible=True)
        except OSError as e:
            error_msg = f"导出失败: 文件系统错误 - {str(e)}"
            print(f"❌ {error_msg}")
            return gr.update(value=f"❌ {error_msg}", visible=True)
        except Exception as e:
            # 记录详细错误信息
            error_msg = str(e)
            print(f"❌ 导出错误详情: {error_msg}")
            return gr.update(value=f"❌ 导出失败: {error_msg}", visible=True)
    
    def _render_status(self, annotated):
        """渲染标注状态"""
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
    
    def _render_user_info(self, visible, others, user_uid):
        """渲染用户信息"""
        return f'<div style="background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:12px;border-radius:8px;text-align:center;">👤 用户：{user_uid} | 📊 可见：{visible} | 🔒 其他：{others}</div>'
    
    def get_allowed_paths(self):
        """
        从数据库数据中提取允许访问的基础路径（用于Gradio的allowed_paths）
        
        从image_url字段中提取第一个路径段，适配不同项目的路径结构
        """
        # 如果数据库为空，使用配置的默认路径
        if not self.all_data:
            return [self.default_allowed_path]
        
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
        return [self.default_allowed_path]


def create_login_interface(auth_handler, task_config, debug, dev_user=None):
    """
    创建统一的登录和标注界面，登录成功后直接切换显示
    
    Args:
        auth_handler: 认证处理器
        task_config: 任务配置
        debug: 是否为调试模式
        dev_user: 开发模式用户，如果指定则自动跳过登录
    """
    
    # 统一创建任务管理器，使用 dev_user 或一个临时的占位用户
    initial_user = dev_user if dev_user else "pending_login"
    manager = TaskManager(task_config, initial_user, debug=debug)

    # 如果数据未初始化，直接返回错误提示
    if not manager.data_handler:
        with gr.Blocks() as error_demo:
            gr.Markdown("# ⚠️ 数据库未初始化\n运行: `python -m importers.annotation_importer`")
        return error_demo, None

    # 创建界面
    with gr.Blocks(title=manager.ui_config['title'], css=manager.custom_css) as unified_demo:
        # State to store the logged-in user
        user_state = gr.State(value=initial_user)

        # 登录面板（初始显示，如果是开发模式则隐藏）
        with gr.Column(visible=(dev_user is None), elem_id="login_panel") as login_panel:
            gr.Markdown(f"# 🔐 {manager.ui_config['title']}")
            gr.Markdown("## 登录")
            
            with gr.Column():
                login_username = gr.Textbox(label="用户名", placeholder="输入用户名")
                login_password = gr.Textbox(label="密码", type="password", placeholder="输入密码")
                login_btn = gr.Button("登录", variant="primary", size="lg")
                login_status = gr.Textbox(label="状态", interactive=False, visible=False)
        
        # 标注界面面板（登录后显示，如果是开发模式则初始显示）
        with gr.Column(visible=(dev_user is not None), elem_id="annotation_panel") as annotation_panel:
            # 总是构建界面
            manager.build_interface(unified_demo, user_state)
        
        # 登录逻辑
        def do_login(username, password):
            """处理登录，成功后更新用户状态"""
            if not username or not password:
                return gr.update(value="请输入用户名和密码", visible=True), gr.update(visible=True), gr.update(visible=False), username
            
            result = auth_handler.login(username, password)
            if result["success"]:
                username_value = result["user"]["username"]
                # 不要再更新共享的 manager.user_uid
                # manager.user_uid = username_value
                
                # 重新计算可见数据, 传递用户ID
                manager._refresh_visible_keys(username_value)
                
                # 返回成功状态和面板可见性，并更新user_state
                return gr.update(value="登录成功", visible=False), gr.update(visible=False), gr.update(visible=True), username_value
            else:
                return gr.update(value=result["message"], visible=True), gr.update(visible=True), gr.update(visible=False), ""

        # 加载数据的辅助函数
        def load_user_data(user):
            """根据用户加载数据"""
            if user and user != "pending_login":
                print(f"🔄 为用户 '{user}' 加载数据...")
                # 登录后，重置到第一条数据
                # 输出绑定要求返回 [index] + [component_values]
                # 将用户ID传递给load_data
                return [0] + manager.load_data(0, user)
            # 如果用户未登录，返回空数据
            return [-1] + manager.load_data(-1, "pending_login") # 使用无效索引返回空值

        # 绑定登录事件
        login_outputs = [login_status, login_panel, annotation_panel, user_state]
        login_btn.click(
            fn=do_login,
            inputs=[login_username, login_password],
            outputs=login_outputs
        ).then(
            fn=load_user_data,
            inputs=[user_state],
            outputs=[manager.components['current_index']] + manager.load_outputs
        )
    
    return unified_demo, manager


def main():
    """主函数"""
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
        
        # 创建登录界面（即使是开发模式也使用统一界面，只是自动登录）
        from src.auth_handler import AuthHandler
        auth_handler = AuthHandler()
        demo, manager = create_login_interface(auth_handler, task_config, args.debug, dev_user=user_uid)
        
        # 如果 manager 为 None，说明数据库未初始化，直接退出
        if manager is None:
            demo.launch(server_port=args.port, server_name="0.0.0.0")
            return
            
        allowed_paths = manager.get_allowed_paths()
        
        # 启动服务
        demo.launch(
            server_port=args.port,
            server_name="0.0.0.0",
            allowed_paths=allowed_paths,
            show_api=False  # 禁用API文档，避免启动检查问题
        )
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
        demo, manager = create_login_interface(auth_handler, task_config, args.debug)
        
        # 如果 manager 为 None，说明数据库未初始化，直接退出
        if manager is None:
            demo.launch(server_port=args.port, server_name="0.0.0.0")
            return

        allowed_paths = manager.get_allowed_paths()
        
        # 启动服务
        demo.launch(
            server_port=args.port,
            server_name="0.0.0.0",
            allowed_paths=allowed_paths,
            show_api=False  # 禁用API文档，避免启动检查问题
        )


if __name__ == "__main__":
    main()
